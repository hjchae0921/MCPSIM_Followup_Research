"""Constrain library reuse in code; reserve natural-language equivalence for review."""
from copy import deepcopy
from enum import Enum
import json
from pathlib import Path

from pydantic import ValidationError, create_model
from .spec import Record, normalized, reply_model
from .questions import fixed_values, select_question

HERE=Path(__file__).resolve().parent


def enforce_answers(payload, answers):
    if not isinstance(payload,dict) or not isinstance(payload.get('response'),dict):
        raise ValueError('The model response must be a JSON object containing a response object.')
    value=deepcopy(payload)
    spec=value.get('response',{}).get('spec')
    if not isinstance(spec,dict):
        return value
    problem=spec.get('problem')
    if not isinstance(problem,dict):
        return value
    for path,choice in answers.items():
        if path not in fixed_values() or choice not in fixed_values()[path]:
            raise ValueError('Check the user-confirmed physical choices.')
        if path=='problem.coupling.type':
            if isinstance(problem.get('coupling'),dict) and problem['coupling'].get('type') is not None:
                problem['coupling']['type']=choice
        else:
            key=path.removeprefix('problem.')
            if problem.get(key) is not None:
                problem[key]=choice
    return value


def response_model(types, models, dimension, answers, candidates, *, wire=False):
    if not candidates:
        return reply_model(types,models,dimension,answers,wire=wire)
    Assessment=reply_model(types,models,dimension,answers,wire=wire).model_fields['response'].annotation
    Id=Enum('ReusableLibraryEntry',{f'entry_{i}':item['id'] for i,item in enumerate(candidates)},type=str)
    Existing=create_model('ExistingLibrarySelection',__base__=Record,library_id=(Id,...))
    return create_model('LibrarySelectionReview',__base__=Record,response=(Existing | Assessment,...))


def messages(state, assessment, candidates):
    source=(HERE/'library_review_prompt.txt').read_text()
    followups=[turn['message'] for turn in state.get('turns',[])[1:] if turn.get('message')]
    current=state.get('user_message','')
    if current and current!=state['initial_request'] and (not followups or followups[-1]!=current):
        followups.append(current)
    context={'initial_request':state['initial_request'],'follow_up_requests':followups,
        'confirmed_choices':state.get('selection_answers',{}),'mesh_dimension':state['mesh']['summary']['dimension'],
        'initial_draft':assessment['spec'],'library_candidates':candidates}
    return [{'role':'system','content':source},{'role':'user','content':json.dumps(context,ensure_ascii=False)}],{'library_review_prompt.txt':source}


def resolve(value, candidates, catalog, answers=None):
    if 'library_id' in value:
        entry=next((item for item in candidates if item['id']==value['library_id']),None)
        if entry is None:
            raise ValueError('Select a library candidate compatible with the mesh and confirmed choices.')
        assessment={'spec':deepcopy(entry['spec']),'ambiguities':[]}
        found=catalog.lookup(assessment['spec'],preferred_file=entry['id'])
        if found['status']!='ready':
            raise ValueError('The selected library entry has changed; review the current candidates.')
        return assessment,None,found
    assessment=value
    coupling=assessment['spec']['problem']['coupling']
    if coupling['type']=='single_physics' and coupling['dependencies'] is None:
        coupling['dependencies']=[{'from':None,'to':None}]
    question=select_question(assessment)
    if question is not None:
        return assessment,question,None
    try:
        spec=normalized(assessment['spec'])
    except ValidationError as error:
        if not any(item['type']=='coupling_directions' for item in error.errors()):
            raise
        assessment=deepcopy(assessment)
        coupling=assessment['spec']['problem']['coupling']
        fixed=(answers or {}).get('problem.coupling.type')
        if fixed:
            coupling['type']=fixed;coupling['dependencies']=None
            item={'target':'problem.coupling.dependencies','options':None,
                'explanation':'The proposed dependency directions conflict with your selected coupling type. Specify which fields influence which other fields.'}
        else:
            coupling['type']=None
            item={'target':'problem.coupling.type',
                'explanation':'The draft coupling classification and dependency directions disagree. Confirm the intended physical coupling before proceeding.'}
        assessment['ambiguities']=[item]+[a for a in assessment['ambiguities'] if a['target']!=item['target']]
        return assessment,select_question(assessment),None
    assessment={**assessment,'spec':spec}
    return assessment,None,catalog.lookup(assessment['spec'])


def total_usage(*values):
    values=[value for value in values if value]
    if not values:
        return None
    result={key:sum(value.get(key,0) or 0 for value in values)
        for key in ('prompt_tokens','completion_tokens','total_tokens')}
    for key in ('prompt_tokens_details','completion_tokens_details'):
        details=[value.get(key) or {} for value in values]
        result[key]={name:sum(item.get(name,0) or 0 for item in details)
            for name in set().union(*(item.keys() for item in details))
            if any(type(item.get(name)) in (int,float) for item in details)}
    if all(type(value.get('cost')) in (int,float) for value in values):
        result['cost']=sum(value['cost'] for value in values)
    return result
