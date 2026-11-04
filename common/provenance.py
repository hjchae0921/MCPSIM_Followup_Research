"""Server-owned field origins and decisions, kept outside physics/coder cards."""
from copy import deepcopy

DECIDED = {'specified', 'selected', 'approved'}


def flatten(value, prefix=''):
    if isinstance(value, dict):
        return {path: item for key, child in value.items()
            for path, item in flatten(child, f'{prefix}.{key}' if prefix else key).items()}
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        keys = [item.get('id', item.get('name', i)) for i, item in enumerate(value)]
        if len(set(keys)) != len(keys):
            keys = list(range(len(value)))
        return {path: item for key, child in zip(keys, value) for path, item in flatten(child, f'{prefix}.{key}').items()}
    return {prefix: deepcopy(value)}


def material_fields(parameters):
    if isinstance(parameters, list):
        grouped = {}
        for row in parameters:
            grouped.setdefault(row['name'], []).append(row)
        parameters = grouped
    return {f'constitutive_parameters.{name}.{index}.{key}': deepcopy(row[key])
        for name, rows in parameters.items() for index, row in enumerate(rows) for key in ('regions', 'value', 'unit')}


def reconcile(fields, previous=None):
    result = {}
    for path, value in fields.items():
        old = (previous or {}).get(path)
        result[path] = deepcopy(old) if old and old['value'] == value else {
            'value': deepcopy(value), 'source': 'model_proposal' if value is not None else 'unset',
            'status': 'proposed' if value is not None else 'unresolved'}
    return result


def decided(statuses, path, value):
    record = (statuses or {}).get(path, {})
    return record.get('status') in DECIDED and record.get('value') == value


def mark(statuses, fields, source, status, evidence=None):
    result = deepcopy(statuses)
    for path, value in fields.items():
        if value is None:
            continue
        result[path] = {'value': deepcopy(value), 'source': source, 'status': status}
        if evidence:
            result[path]['evidence'] = evidence
    return result


def material_history(turns):
    """Recover only recorded selections from older turns, without inferring approval."""
    result, previous = {}, None
    for turn in turns:
        if 'field_status' in turn:
            result = deepcopy(turn['field_status'])
        else:
            raw = turn.get('assessment', {}).get('card', {}).get('constitutive_parameters')
            card = turn.get('response', {}).get('proposed_card', turn.get('response', {}).get('draft_card', {}))
            parameters = raw if raw is not None else card.get('constitutive_parameters')
            if parameters is not None:
                fields = material_fields(parameters)
                result = reconcile(fields, result)
                if turn.get('origin') == 'recommendation_choice' and previous:
                    for option in previous.get('response', {}).get('options', []):
                        if turn.get('message') != 'Selected material candidate: '+option['label']:
                            continue
                        chosen = {f'constitutive_parameters.{v["name"]}.{v.get("binding",0)}.{key}': v[key]
                            for v in option.get('values', []) for key in ('value','unit')
                            if fields.get(f'constitutive_parameters.{v["name"]}.{v.get("binding",0)}.{key}') == v[key]}
                        result = mark(result, chosen, 'user_selection', 'selected')
        previous = turn
    return result


def sync(state):
    """Derive decisions from backend actions; a filled proposal is never approval."""
    previous = state.get('field_status', {})
    result = {}
    stages = [('selection', 'selection_draft', 'confirmed_selection', 'turns'),
        ('function_space', 'functionspace_draft', 'functionspace_card', 'functionspace_turns'),
        ('material', 'material_draft', 'material_card', 'material_turns'),
        ('boundary_parameters', None, 'boundary_parameter_assessment', 'boundary_parameter_turns'),
        ('boundary_values', 'boundary_value_draft', 'boundary_value_card', 'boundary_value_turns'),
        ('solver', None, 'solver_card', 'solver_turns')]
    for name, draft_key, approved_key, turns_key in stages:
        turns = state.get(turns_key, [])
        turn = turns[-1] if turns else {}
        reply = turn.get('response', {})
        approved = state.get(approved_key)
        draft = state.get(draft_key) if draft_key else reply.get('assessment') if name == 'boundary_parameters' else reply.get('proposed_card')
        if draft is None:
            draft = reply.get('spec') if name == 'selection' else reply.get('proposed_card', reply.get('draft_card'))
        raw_material = turn.get('assessment', {}).get('card', {}).get('constitutive_parameters') if name == 'material' else None
        if draft is None and raw_material is not None:
            draft = {'constitutive_parameters': raw_material}
        card = approved if approved is not None else draft
        if card is None:
            continue
        if name == 'material':
            fields = material_fields(raw_material if approved is None and raw_material is not None else card['constitutive_parameters'])
        else:
            fields = flatten(card)
        prior = turn.get('field_status', previous.get(name))
        if name == 'material' and not prior:
            prior = material_history(turns)
        statuses = reconcile(fields, prior)
        if approved is None:
            for record in statuses.values():
                if record['status'] == 'approved':
                    record['status'] = 'selected'
        if name == 'selection':
            if turn.get('library_match'):
                for record in statuses.values():
                    if record['source']=='model_proposal':
                        record['source']='library'
            if fields.get('problem.dimension') == state['mesh']['summary']['dimension']:
                statuses = mark(statuses, {'problem.dimension': fields['problem.dimension']}, 'mesh', 'specified')
            statuses = mark(statuses, {k: v for k, v in state.get('selection_answers', {}).items() if fields.get(k) == v},
                'user_selection', 'selected')
        if name != 'material' and turn.get('origin') in ('recommendation_choice', 'value_input', 'choose', 'manual'):
            source = 'user_selection' if turn['origin'] in ('recommendation_choice', 'choose') else 'user_input'
            statuses = mark(statuses, fields, source, 'selected' if source == 'user_selection' else 'specified')
        if approved is not None:
            for path, value in fields.items():
                old = turn.get('field_status', previous.get(name, {})).get(path, statuses[path])
                statuses[path] = {**deepcopy(old), 'value': deepcopy(value), 'status': 'approved'}
        result[name] = statuses
    if state.get('formulation') is not None:
        fields = flatten(state['formulation'])
        statuses = reconcile(fields, previous.get('formulation'))
        if state.get('saved_files') or (state.get('lookup') or {}).get('status') == 'ready':
            for record in statuses.values():
                record['status'] = 'approved'
                if (state.get('lookup') or {}).get('status') == 'ready':
                    record['source'] = 'library'
        result['formulation'] = statuses
    return result
