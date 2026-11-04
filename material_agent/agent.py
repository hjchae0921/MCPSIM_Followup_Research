"""Mesh-grounded material parameter authoring for approved formulations."""
import json
from pathlib import Path
import re
from common.schema import region_key
from common.units import unit_context
from .schema import Parameter, MaterialCard, check_card, validate_selection
from .judgments import response_model, evaluate, empty_assessment, volumes, provider_reply, apply_candidate, field_provenance, selection_status, verified_user_inputs
from .recommendations import to_assessment, prompt_reply

HERE=Path(__file__).resolve().parent


def messages(initial_request,selection,formulation,summary,selected,turns,current_message=''):
    source=(HERE/'material_prompt.txt').read_text()
    header,marker,user=source.partition('=== USER MESSAGE ===')
    if not marker:
        raise ValueError('The material prompt is missing its USER MESSAGE delimiter.')
    registry=volumes(summary)
    selected_keys={region_key(region) for region in selected}
    values={'INITIAL_USER_PROMPT':initial_request,'CONFIRMED_SELECTION_JSON':json.dumps(selection,ensure_ascii=False),
        'CONSTITUTIVE_JSON':json.dumps(formulation['constitutive'],ensure_ascii=False),
        'CONSTITUTIVE_PARAMETERS_JSON':json.dumps(formulation['constitutive_parameters'],ensure_ascii=False),
        'MESH_REGIONS_JSON':json.dumps({'dimension':summary['dimension'],
            'volume_groups':[{'id':key,**region} for key,region in registry.items()]},ensure_ascii=False),
        'UNIT_CONTEXT_JSON':json.dumps(unit_context(summary),ensure_ascii=False),
        'SELECTED_REGIONS_JSON':json.dumps([key for key,region in registry.items() if region_key(region) in selected_keys],ensure_ascii=False)}
    for key in values:
        if user.count('{{'+key+'}}')!=1:
            raise ValueError('Check the material prompt placeholder: '+key)
    user=re.sub(r'\{\{([A-Z_]+)\}\}',lambda match:values[match[1]],user).strip()
    result=[{'role':'system','content':header.removeprefix('=== SYSTEM MESSAGE ===').strip()},
        {'role':'user','content':user}]
    for turn in turns:
        if turn['message']:
            result.append({'role':'user','content':turn['message']})
        result.append({'role':'assistant','content':json.dumps({'response':prompt_reply(turn,formulation,summary)},ensure_ascii=False)})
    if turns:
        fixed={path:record['value'] for path,record in turns[-1].get('field_status',{}).items()
            if record['status'] in ('specified','selected','approved')}
        if fixed:
            result.append({'role':'user','content':'[User-decided material fields]\n'+json.dumps(fixed,ensure_ascii=False)})
    if current_message:
        result.append({'role':'user','content':current_message})
    return result,{'material_prompt.txt':source}
