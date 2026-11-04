"""Function-space proposals based on an already approved selection and formulation."""
import json
from pathlib import Path
import re
from .schema import FunctionSpaceCard
from .judgments import response_model, assemble_draft, select_question, provider_reply
from common.coupling import normalized_coupling

HERE = Path(__file__).resolve().parent


def check_card(value,selection):
    card = FunctionSpaceCard.model_validate(value).model_dump()
    if {field['name'] for field in card['unknowns']} != set(selection['problem']['unknowns']):
        raise ValueError('Function-space unknowns must match the approved selection.')
    if card['coupling_type'] != normalized_coupling(selection['problem']['coupling']['type']):
        raise ValueError('The function-space stage cannot change the approved coupling.')
    return card


def messages(initial_request,selection,formulation,turns,current_message=''):
    source = (HERE/'functionspace_prompt.txt').read_text()
    header,marker,user = source.partition('=== USER MESSAGE ===')
    if not marker:
        raise ValueError('The function-space prompt is missing its USER MESSAGE delimiter.')
    context = {key: value for key, value in formulation.items()
        if key not in ('boundary_parameters', 'source_parameters')}
    values = {'INITIAL_USER_PROMPT':initial_request,
        'CONFIRMED_SELECTION_JSON':json.dumps(selection,ensure_ascii=False),
        'CONFIRMED_FORMULATION_JSON':json.dumps(context,ensure_ascii=False)}
    for key in values:
        if user.count('{{'+key+'}}')!=1:
            raise ValueError('Check the function-space prompt placeholder: '+key)
    user = re.sub(r'\{\{([A-Z_]+)\}\}',lambda match:values[match[1]],user).strip()
    result = [{'role':'system','content':header.removeprefix('=== SYSTEM MESSAGE ===').strip()},
        {'role':'user','content':user}]
    for turn in turns:
        if turn['message']:
            result.append({'role':'user','content':turn['message']})
        result.append({'role':'assistant','content':json.dumps({'response':provider_reply(turn,selection)},ensure_ascii=False)})
    if current_message:
        result.append({'role':'user','content':current_message})
    return result,{'functionspace_prompt.txt':source}
