"""Route field judgments to clarification or review without parsing model prose."""
from enum import Enum
from typing import Annotated, get_args

from pydantic import BeforeValidator, Field, create_model
from pydantic_core import PydanticCustomError
from common.authoring import selection_targets
from common.contracts import named_record

from .spec import Coupling, Problem, Record, Text


def fixed_values():
    return {
        'problem.linearity': get_args(Problem.model_fields['linearity'].annotation),
        'problem.time_dependence': get_args(Problem.model_fields['time_dependence'].annotation),
        'problem.history_dependence': (False, True),
        'problem.coupling.type': get_args(Coupling.model_fields['type'].annotation),
    }


QUESTIONS = {
    'problem.linearity': ('How should linearity be specified?', (
        ('Linear', 'Use governing equations that are linear in the unknowns.'),
        ('Nonlinear', 'Include nonlinear effects, such as material or kinematic nonlinearity.'))),
    'problem.time_dependence': ('Should the problem depend on physical time?', (
        ('Time-independent', 'Do not model physical time evolution or rate effects.'),
        ('Time-dependent', 'Include physical time evolution or rate effects.'))),
    'problem.history_dependence': ('Should material history be considered?', (
        ('History-independent', 'Determine the material response from the current state alone.'),
        ('History-dependent', 'Include the influence of previous deformation or internal states.'))),
    'problem.coupling.type': ('How should the physical fields be coupled?', (
        ('Single physics', 'Use a single physical problem.'),
        ('One-way multiphysics', 'Pass effects to downstream fields without feedback.'),
        ('Fully coupled multiphysics', 'Include feedback between the unknown fields.'))),
}


class Option(Record):
    label: Text
    description: Text


def validate_ambiguity_fields(value):
    target=value.get('target') if isinstance(value,dict) else None
    if isinstance(target,str) and target in fixed_values() and 'options' in value:
        raise PydanticCustomError('fixed_options_forbidden',
            'Only free-choice targets may include options; {target} uses server-defined choices.',
            {'target':target})
    return value


def ambiguity_model():
    Target = Enum('FixedSelectionTarget', {f'field_{i}': target for i, target in enumerate(fixed_values())}, type=str)
    Fixed = create_model('FixedSelectionAmbiguity', __base__=Record,
        target=(Target, ...), explanation=(Text, Field(description='Explain which plausible model choices cannot be distinguished from the request.')))
    FreeTarget = Enum('SelectionQuestionTarget', {f'field_{i}': target
        for i, target in enumerate(selection_targets()) if target not in fixed_values()}, type=str)
    Free = create_model('SelectionAmbiguity', __base__=Record,
        target=(FreeTarget, ...), explanation=(Text, Field(description='Explain the unresolved model choice and ask for the information needed to distinguish it.')),
        options=(Annotated[list[Option], Field(min_length=2)] | None, Field(description='Plausible alternatives, or null if user input is needed.')))
    return Annotated[Fixed | Free, BeforeValidator(validate_ambiguity_fields)]


def ambiguity_record():
    """Each target has its own slot; fixed slots never expose an options property."""
    Fixed=create_model('FixedChoiceUncertainty',__base__=Record,explanation=(Text,...))
    Free=create_model('OpenChoiceUncertainty',__base__=Record,explanation=(Text,...),
        options=(Annotated[list[Option],Field(min_length=2)] | None,...))
    def fixed_slot(target):
        def check(value):
            if isinstance(value,dict) and 'options' in value:
                validate_ambiguity_fields({**value,'target':target})
            return value
        return Annotated[Fixed | None,BeforeValidator(check)]
    return named_record('SelectionUncertainties',[(target,fixed_slot(target) if target in fixed_values() else Free | None)
        for target in selection_targets()],
        'One slot per target; null when no unresolved choice needs explanation.')


def wire_assessment(value):
    """Encode validated or legacy judgments for the provider without changing saved turns."""
    if not isinstance(value.get('ambiguities'),list):return value
    slots={target:None for target in selection_targets()}
    for item in value['ambiguities']:
        target=item['target']
        if slots.get(target) is not None:raise ValueError('Explain each uncertain selection target once.')
        slots[target]={key:child for key,child in item.items() if key!='target'}
    return {**value,'ambiguities':slots}


def internal_assessment(value):
    if 'library_id' in value:return value
    return {**value,'ambiguities':[{'target':target,**item} for target,item in value['ambiguities'].items() if item is not None]}


def unresolved_targets(spec):
    """None means unresolved; false, zero and the single-physics null pair are values."""
    p = spec['problem']
    missing = ['problem.' + key for key in Problem.model_fields if key != 'coupling' and p[key] is None]
    missing += ['problem.coupling.' + key for key in Coupling.model_fields if p['coupling'][key] is None]
    models = [model for material in spec['materials'] or [] for model in material['constitutive_models'] or []]
    for key in ('model', 'fields', 'symmetry'):
        if not models or any(m[key] is None for m in models) or any(m['constitutive_models'] is None for m in spec['materials'] or []):
            missing.append('materials.constitutive_models.' + key)
    return missing


def select_question(assessment):
    """Known values cannot produce confirmation questions, even if an ambiguity is supplied."""
    missing = unresolved_targets(assessment['spec'])
    if not missing:
        return None
    item = next((a for a in assessment['ambiguities'] if a['target'] in missing), None)
    if item is None:
        raise ValueError('Explain a genuine ambiguity for an unresolved field: ' + ', '.join(missing))
    if item['target'] in fixed_values():
        return present_question(item)
    return {'kind': 'question', 'question_type': 'choice' if item['options'] else 'input',
        'question': item['explanation'], 'targets': [item['target']], 'options': item['options'] or []}


def empty_spec(dimension):
    """Represent legacy question turns without inferring values from their prose."""
    p = {key: None for key in Problem.model_fields}
    p.update(dimension=dimension, coupling={'type': None, 'dependencies': None})
    return {'problem': p, 'materials': None}


def present_question(value):
    """Only uncertainty and context come from the LLM; alternatives come from enums."""
    target = value['target']
    question, descriptions = QUESTIONS[target]
    options = [{'label': label, 'description': description, 'value': option}
        for option, (label, description) in zip(fixed_values()[target], descriptions, strict=True)]
    return {'kind': 'question', 'question_type': 'choice',
        'question': value['explanation'] + '\n' + question,
        'explanation': value['explanation'], 'targets': [target], 'fixed_target': target, 'options': options}


def provider_reply(turn, dimension):
    """Replay judgments; keep old checkpoints readable without rewriting them."""
    if 'assessment' in turn:
        return {key: turn['assessment'][key] for key in ('spec', 'ambiguities')}
    value = turn['response']
    if 'spec' in value:
        return {'spec': value['spec'], 'ambiguities': []}
    items = []
    for target in value.get('targets', []):
        item = {'target': target, 'explanation': value.get('explanation', value.get('question', ''))}
        if target not in fixed_values():
            item['options'] = value.get('options') if len(value.get('options', [])) >= 2 else None
        items.append(item)
    return {'spec': empty_spec(dimension), 'ambiguities': items}
