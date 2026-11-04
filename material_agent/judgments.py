"""Partial material judgments, recommendations and deterministic card assembly."""
from copy import deepcopy
from enum import Enum
import json
from typing import Annotated, Literal

from pydantic import Field, create_model, model_validator
from common.schema import Record, Text, Number, Vector, Matrix, Region, region_key
from common.units import convert_length
from common.provenance import decided, mark, material_fields, reconcile
from .schema import check_card

FIELDS = ('regions', 'value', 'unit')
Value = Number | Vector | Matrix


class Binding(Record):
    regions: list[Text] | None
    value: Value | None
    unit: str | None = Field(description='Physical unit; an empty string means dimensionless, null means unresolved.')

    @model_validator(mode='after')
    def rectangular(self):
        if isinstance(self.value, list) and self.value and isinstance(self.value[0], list):
            if len({len(row) for row in self.value}) != 1:
                raise ValueError('Material parameter matrices must be rectangular.')
        return self


class Update(Binding):
    binding: Annotated[int, Field(ge=0, description='Zero-based index within this parameter\'s binding list.')]

    @model_validator(mode='after')
    def nonempty(self):
        if all(getattr(self, key) is None for key in FIELDS):
            raise ValueError('A material candidate must supply at least one field value.')
        return self


def volumes(summary):
    return {f'volume_{i}': Region.model_validate({k: group[k] for k in ('name', 'dim', 'tags')}).model_dump()
        for i, group in enumerate(summary.get('volume_groups', []), 1)}


def assessment_model(formulation, summary):
    names = [p['name'] for p in formulation['constitutive_parameters']]
    Name = Enum('MaterialParameterName', {f'item_{i}': name for i, name in enumerate(names)}, type=str) if names else str
    groups = volumes(summary)
    if groups:
        RegionID = Enum('MaterialVolumeID', {key: key for key in groups}, type=str)
        RegionIDs = Annotated[list[RegionID], Field(min_length=1)] | None
    else:
        RegionIDs = type(None)
    KnownBinding = create_model('MaterialBinding', __base__=Binding, regions=(RegionIDs, ...))
    Parameters = create_model('MaterialParameterJudgments', __base__=Record,
        **{f'parameter_{i}': (Annotated[list[KnownBinding], Field(min_length=1)], Field(alias=name))
            for i, name in enumerate(names)})
    if not names:
        Parameters.model_config['json_schema_extra'] = {'required': []}
    Card = create_model('PartialMaterialCard', __base__=Record,
        __doc__='Use provided values and supported region assignments. Unresolved fields are null; numerical suggestions belong in ambiguity options.',
        constitutive_parameters=(Parameters, ...))
    Patch = create_model('MaterialUpdate', __base__=Update, parameter=(Name, ...), regions=(RegionIDs, ...))
    Candidate = create_model('MaterialCandidate', __base__=Record,
        label=(Text, ...), description=(Text, Field(description='Explain the assumptions and applicability in English.')),
        updates=(Annotated[list[Patch], Field(min_length=1)], Field(description='A coherent property set for one material and region, covering all recommendable unresolved parameters.')))
    Ambiguity = create_model('MaterialAmbiguity', __base__=Record,
        parameter=(Name, ...), binding=(Annotated[int, Field(ge=0, description='Zero-based index within this parameter\'s binding list.')], ...),
        fields=(Annotated[list[Literal['regions', 'value', 'unit']], Field(min_length=1)], ...),
        explanation=(Text, Field(description='Ask only about the missing material information, in English.')),
        options=(Annotated[list[Candidate], Field(min_length=1, max_length=2)] | None, ...))
    Evidence = create_model('MaterialUserInput', __base__=Record,
        parameter=(Name, ...), binding=(Annotated[int, Field(ge=0)], ...),
        fields=(Annotated[list[Literal['regions', 'value', 'unit']], Field(min_length=1)], ...),
        quote=(Text, Field(description='Verbatim user text explicitly specifying these fields; do not cite inferred or suggested values.')))
    Member = create_model('MaterialSetMember', __base__=Record,
        parameter=(Name, ...), binding=(Annotated[int, Field(ge=0)], ...))
    Ambiguity = create_model('InternalMaterialDecision', __base__=Ambiguity,
        members=(list[Member] | None, None))
    Assessment = create_model('MaterialAssessment', __base__=Record, card=(Card, ...),
        ambiguities=(Annotated[list[Ambiguity], Field(max_length=0)] if not names else list[Ambiguity], ...),
        user_inputs=(list[Evidence], ...))
    return create_model('MaterialResponse', __base__=Record, response=(Assessment, ...))


def response_model(formulation, summary):
    from .recommendations import response_model as public_model
    return public_model(formulation, summary)


def empty_assessment(formulation):
    return {'card': {'constitutive_parameters': {p['name']: [{'regions': None, 'value': None, 'unit': None}]
        for p in formulation['constitutive_parameters']}}, 'ambiguities': [], 'user_inputs': []}


def binding_at(assessment, parameter, index):
    rows = assessment['card']['constitutive_parameters'].get(parameter)
    if rows is None:
        raise ValueError('A material ambiguity or update references an unknown parameter: '+parameter)
    if type(index) is not int or not 0 <= index < len(rows):
        raise ValueError(f'Binding {index} does not exist for {parameter}. Binding indices are local to each parameter; '
            f'use an index from 0 to {len(rows)-1} for this parameter.')
    return rows[index]


def assemble_draft(assessment, summary):
    registry = volumes(summary)
    rows, notes, assigned = [], [], set()
    for name, bindings in assessment['card']['constitutive_parameters'].items():
        for index, binding in enumerate(bindings):
            ids = binding['regions']
            if ids is not None and len(set(ids)) != len(ids):
                raise ValueError('Material volume references must be distinct.')
            regions = None if ids is None else [deepcopy(registry[key]) for key in ids]
            for region in regions or []:
                for tag in region['tags']:
                    if (name, tag) in assigned:
                        raise ValueError('Assignments of the same material parameter must not overlap.')
                    assigned.add((name, tag))
            value, unit, note = convert_length(binding['value'], binding['unit'], summary)
            rows.append({'name': name, 'regions': regions, 'value': value, 'unit': unit})
            if note:
                notes.append({'name': name, 'binding': index, **note})
    return {'constitutive_parameters': rows}, notes


def missing_fields(assessment):
    return {(name, index, key) for name, rows in assessment['card']['constitutive_parameters'].items()
        for index, binding in enumerate(rows) for key in FIELDS if binding[key] is None}


def target(name, index, key):
    return f'constitutive_parameters.{name}.{index}.{key}'


def field_provenance(assessment, previous=None, user_texts=(), current_message=''):
    fields = material_fields(assessment['card']['constitutive_parameters'])
    result = reconcile(fields, previous)
    claims = {}
    for item in assessment.get('user_inputs', []):
        row = binding_at(assessment, item['parameter'], item['binding'])
        if 'value' in item['fields'] and row['value'] is None:
            continue
        quote = item['quote']
        if not any(quote in text for text in user_texts):
            raise ValueError('Material input evidence must quote an actual user message verbatim.')
        for key in item['fields']:
            path = target(item['parameter'], item['binding'], key)
            if row[key] is None:
                continue
            claims[path] = quote
            result = mark(result, {path: row[key]}, 'user_input', 'specified', quote)
    for path, old in (previous or {}).items():
        if old.get('status') in ('specified', 'selected', 'approved') and fields.get(path) != old['value']:
            quote = claims.get(path)
            if not quote or quote not in current_message:
                raise ValueError('Preserve the user-decided material field unless the current user message explicitly revises it: '+path)
    return result


def verified_user_inputs(assessment, field_status):
    result=[]
    for item in assessment.get('user_inputs', []):
        fields=[key for key in item['fields'] if
            field_status.get(target(item['parameter'],item['binding'],key),{}).get('evidence')==item['quote']]
        if fields:
            result.append({**item,'fields':fields})
    return result


def selection_status(assessment, candidate, previous=None, source='user_selection'):
    fields = material_fields(assessment['card']['constitutive_parameters'])
    result = reconcile(fields, previous)
    supplied = {target(patch['parameter'], patch['binding'], key): fields[target(patch['parameter'], patch['binding'], key)]
        for patch in candidate['updates'] for key in FIELDS if patch[key] is not None}
    return mark(result, supplied, source, 'selected' if source == 'user_selection' else 'specified')


def apply_candidate(assessment, candidate, field_status=None, user_edit=False):
    result = deepcopy(assessment)
    changed = set()
    revised = set()
    for update in candidate['updates']:
        row = binding_at(result, update['parameter'], update['binding'])
        for key in FIELDS:
            value = update[key]
            if value is None:
                continue
            path = target(update['parameter'], update['binding'], key)
            if not user_edit and decided(field_status, path, row[key]) and row[key] != value:
                raise ValueError('A material recommendation cannot overwrite a user-decided field: '+path)
            if key == 'unit' and row[key] is not None and row[key] != value and row['value'] is not None and update['value'] is None:
                raise ValueError('Supply the material value together with a changed unit.')
            if user_edit or not decided(field_status, path, row[key]):
                changed.add((update['parameter'], update['binding'], key))
            if row[key] != value:
                revised.add((update['parameter'], update['binding'], key))
            row[key] = deepcopy(value)
    if not changed:
        raise ValueError('A material candidate must resolve or revise a field that has not been decided by the user.')
    result['user_inputs'] = [{**item, 'fields': [key for key in item['fields']
        if (item['parameter'], item['binding'], key) not in revised]}
        for item in result.get('user_inputs', [])]
    result['user_inputs'] = [item for item in result['user_inputs'] if item['fields']]
    return result


def describe_card(card):
    if not card['constitutive_parameters']:
        return 'The approved formulation requires no constitutive parameter inputs.'
    return ' '.join(f"{p['name']} = {json.dumps(p['value'], ensure_ascii=False)} {p['unit'] or '(dimensionless)'} on " +
        ', '.join(r['name'] for r in p['regions']) + '.' for p in card['constitutive_parameters'])


def evaluate(assessment, formulation, summary, allow_generic=False, field_status=None):
    Reply = assessment_model(formulation, summary)
    assessment = {**assessment, 'user_inputs': assessment.get('user_inputs', [])}
    assessment = Reply.model_validate_json(json.dumps({'response': assessment})).model_dump(mode='json', by_alias=True)['response']
    draft, notes = assemble_draft(assessment, summary)
    missing = missing_fields(assessment)
    for item in assessment['ambiguities']:
        binding_at(assessment, item['parameter'], item['binding'])
        if len(set(item['fields'])) != len(item['fields']):
            raise ValueError('Material ambiguity fields must be distinct.')
    def pending(name, index, key):
        return not decided(field_status, target(name, index, key), binding_at(assessment, name, index)[key])
    def members(item):
        return item.get('members') or [{'parameter':item['parameter'],'binding':item['binding']}]
    chosen = next(((i, a) for i, a in enumerate(assessment['ambiguities'])
        if any(pending(member['parameter'], member['binding'], key) for member in members(a) for key in a['fields'])), None)
    if not missing and chosen is None:
        card = check_card(draft, formulation, summary)
        return {'proposed_card': card, 'explanation': describe_card(card)}, assessment, draft, notes
    if chosen is None:
        if not allow_generic:
            raise ValueError('Explain the unresolved material fields: ' + ', '.join(target(*p) for p in sorted(missing)))
        question = {'question_type': 'input', 'question': 'Provide the remaining material values, units, or volume assignments.',
            'targets': [target(*p) for p in sorted(missing)], 'options': [], 'draft_card': draft}
        return question, assessment, draft, notes
    index, item = chosen
    options = []
    question_fields = {(member['parameter'], member['binding'], key): None for member in members(item) for key in item['fields']
        if pending(member['parameter'], member['binding'], key)}
    for option_index, candidate in enumerate(item['options'] or []):
        try:
            updated = apply_candidate(assessment, candidate, field_status)
            if not any(patch['parameter'] == member['parameter'] and patch['binding'] == member['binding'] and patch[key] is not None
                for member in members(item) for patch in candidate['updates'] for key in item['fields'] if pending(member['parameter'], member['binding'], key)):
                raise ValueError('A material candidate must address an unresolved field of its question.')
        except ValueError:
            if allow_generic:
                continue
            raise
        _, candidate_notes = assemble_draft(updated, summary)
        for patch in candidate['updates']:
            for key in FIELDS:
                field = patch['parameter'], patch['binding'], key
                if patch[key] is not None and pending(*field):
                    question_fields[field] = None
        values = []
        seen = set()
        for patch in candidate['updates']:
            key = patch['parameter'], patch['binding']
            if key in seen or (patch['value'] is None and patch['unit'] is None):
                continue
            seen.add(key)
            raw = binding_at(updated, *key)
            value, unit, _ = convert_length(raw['value'], raw['unit'], summary)
            if value is not None and unit is not None:
                region_names = ', '.join(volumes(summary)[r]['name'] for r in raw['regions'] or [])
                values.append({'name': key[0], 'binding': key[1], 'display_name': key[0] + (f' ({region_names})' if region_names else ''),
                    'value': value, 'unit': unit})
        options.append({'label': candidate['label'], 'description': candidate['description'],
            'values': values, 'candidate_index': option_index})
        updated_keys = {(patch['parameter'], patch['binding']) for patch in candidate['updates']}
        notes.extend({'option_index': option_index, **note} for note in candidate_notes
            if (note['name'], note['binding']) in updated_keys)
    kind = 'recommendation' if any(o['values'] for o in options) else 'choice' if options else 'input'
    question = {'question_type': kind, 'question': item['explanation'],
        'targets': [target(*field) for field in question_fields],
        'options': options, 'ambiguity_index': index, 'draft_card': draft}
    return question, assessment, draft, notes


def provider_reply(turn, formulation, summary):
    if 'assessment' in turn:
        return {**deepcopy(turn['assessment']), 'user_inputs': turn['assessment'].get('user_inputs', [])}
    value = turn['response']
    result = empty_assessment(formulation)
    registry = {region_key(region): key for key, region in volumes(summary).items()}
    if 'proposed_card' in value:
        parameters = result['card']['constitutive_parameters']
        for name in parameters:
            parameters[name] = []
        for row in value['proposed_card']['constitutive_parameters']:
            parameters[row['name']].append({'regions': [registry[region_key(r)] for r in row['regions']],
                'value': row['value'], 'unit': row['unit']})
        return result
    grouped = {}
    for path in value.get('targets', []):
        parts = path.split('.')
        if len(parts) >= 3 and parts[0] == 'constitutive_parameters' and parts[1] in result['card']['constitutive_parameters']:
            grouped.setdefault(parts[1], []).append(parts[-1])
    for name, fields in grouped.items():
        options = None
        if value.get('question_type') == 'recommendation':
            options = [{'label': o['label'], 'description': o['description'], 'updates': [
                {'parameter': v['name'], 'binding': 0, 'regions': None, 'value': v['value'], 'unit': v['unit']}
                for v in o['values']]} for o in value['options']]
        result['ambiguities'].append({'parameter': name, 'binding': 0, 'fields': list(dict.fromkeys(fields)),
            'explanation': value.get('question', ''), 'options': options})
    return result
