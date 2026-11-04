"""Partial space judgments and server-owned clarification routing."""
from copy import deepcopy
from enum import Enum
from typing import Annotated

from pydantic import Field, create_model, model_validator

from common.authoring import space_targets
from common.coupling import normalized_coupling
from common.schema import Dimension, Record, Text


class PartialSpace(Record):
    family: Text | None
    degree: Annotated[int, Field(ge=0)] | None


class PartialUnknown(Record):
    quantity: Text | None
    shape: Annotated[list[Dimension], Field(description='Value shape: [] for a scalar; distinguish it from spatial dimension.')] | None
    function_space: PartialSpace


class PartialState(Record):
    name: Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]*$')]
    symbol: Text | None
    shape: list[Dimension] | None
    unit: str | None
    function_space: PartialSpace


class Option(Record):
    label: Text
    description: Text


class PartialCard(Record):
    state_variables: list[PartialState] | None

    @model_validator(mode='after')
    def distinct_names(self):
        names = list(self.unknowns.model_dump(by_alias=True))
        names += [state.name for state in self.state_variables or []]
        if len(set(names)) != len(names):
            raise ValueError('Unknown and state-variable names must be distinct.')
        return self


def response_model(selection):
    names = selection['problem']['unknowns']
    # Aliases keep approved names usable even when they match Pydantic attributes.
    Unknowns = create_model('ApprovedUnknownJudgments', __base__=Record,
        **{f'field_{i}': (PartialUnknown, Field(alias=name)) for i, name in enumerate(names)})
    Card = create_model('PartialFunctionSpaceCard', __base__=PartialCard,
        __doc__='Fill supported judgments. Null marks genuine uncertainty; [] and degree zero are resolved values.',
        unknowns=(Unknowns, ...))
    paths = [p for p in space_targets(selection) if p.startswith('unknowns.')]
    Target = Enum('FunctionSpaceTarget', {f'item_{i}': p
        for i, p in enumerate([*paths, 'state_variables', 'formulation'])}, type=str)
    StateTarget = Annotated[str, Field(pattern=
        r'^state_variables\.[a-z][a-z0-9_]*\.(symbol|shape|unit|function_space\.(family|degree))$')]
    Ambiguity = create_model('FunctionSpaceAmbiguity', __base__=Record,
        target=(Target | StateTarget, ...),
        explanation=(Text, Field(description='Explain in English what information is missing and how it affects the space or approved formulation.')),
        options=(Annotated[list[Option], Field(min_length=2)] | None,
            Field(description='Meaningful alternatives, or null for clarification or upstream formulation review.')))
    Assessment = create_model('FunctionSpaceAssessment', __base__=Record,
        card=(Card, ...),
        explanation=(Text, Field(description='An English explanation of the proposed spaces and assumptions.')),
        ambiguities=(list[Ambiguity], ...))
    return create_model('FunctionSpaceResponse', __base__=Record, response=(Assessment, ...))


def assemble_draft(assessment, selection):
    raw = assessment['card']
    return {'unknowns': [{'name': name, **deepcopy(raw['unknowns'][name])}
            for name in selection['problem']['unknowns']],
        'coupling_type': normalized_coupling(selection['problem']['coupling']['type']),
        'state_variables': deepcopy(raw['state_variables'])}


def unresolved_targets(card):
    missing = []
    groups = [('unknowns', card['unknowns'])]
    if card['state_variables'] is None:
        missing.append('state_variables')
    else:
        groups.append(('state_variables', card['state_variables']))
    for scope, fields in groups:
        for field in fields:
            prefix = scope + '.' + field['name']
            keys = ('quantity', 'shape') if scope == 'unknowns' else ('symbol', 'shape', 'unit')
            missing += [prefix + '.' + key for key in keys if field[key] is None]
            missing += [prefix + '.function_space.' + key for key in ('family', 'degree')
                if field['function_space'][key] is None]
    return missing


def select_question(assessment, card):
    missing = unresolved_targets(card)
    states = {s['name'] for s in card['state_variables'] or []}
    for ambiguity in assessment['ambiguities']:
        target = ambiguity['target']
        if target.startswith('state_variables.') and target.split('.')[1] not in states:
            raise ValueError('An internal-state ambiguity must target a declared state variable.')
    item = next((a for a in assessment['ambiguities'] if a['target'] == 'formulation'), None)
    if item is not None:
        return {'question_type': 'input', 'question': item['explanation'], 'options': [],
            'targets': ['formulation'], 'requires_formulation_review': True}
    if not missing:
        return None
    item = next((a for a in assessment['ambiguities'] if a['target'] in missing), None)
    if item is None:
        raise ValueError('Explain a genuine ambiguity for an unresolved function-space field: ' + ', '.join(missing))
    return {'question_type': 'choice' if item['options'] else 'input',
        'question': item['explanation'], 'options': item['options'] or [], 'targets': [item['target']]}


def empty_card(selection):
    return {'unknowns': {name: {'quantity': None, 'shape': None,
        'function_space': {'family': None, 'degree': None}} for name in selection['problem']['unknowns']},
        'state_variables': None}


def provider_reply(turn, selection):
    """Replay judgments and adapt legacy turns without rewriting their checkpoints."""
    if 'assessment' in turn:
        return turn['assessment']
    value = turn['response']
    if 'proposed_card' in value:
        card = value['proposed_card']
        return {'card': {'unknowns': {u['name']: {k: deepcopy(v) for k, v in u.items() if k != 'name'}
                for u in card['unknowns']}, 'state_variables': deepcopy(card['state_variables'])},
            'explanation': value.get('explanation', ''), 'ambiguities': []}
    items = []
    for target in value.get('targets', []):
        if target.startswith('state_variables.'):
            target = 'state_variables'
        items.append({'target': target, 'explanation': value.get('question', ''),
            'options': value.get('options') if len(value.get('options', [])) >= 2 else None})
    return {'card': empty_card(selection), 'explanation': value.get('question', ''), 'ambiguities': items}
