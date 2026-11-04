"""Collect values only for the approved boundary/source/Dirichlet requirements."""
import json
from enum import Enum
from pathlib import Path
from typing import Annotated

import numpy as np
from pydantic import Field, create_model
from common.schema import Record, Text
from common.dialogue import Question, scoped_questions
from common.authoring import value_targets
from common.units import unit_context
from common.schema import Value
from .parameter_selection import check_assessment, ready

HERE=Path(__file__).resolve().parent


class DraftValue(Record):
    id: Text
    value: Value|None = Field(description='Numerical value, including zero; null if unresolved.')
    unit: str|None = Field(description='Physical unit; an empty string for dimensionless quantities, null if unresolved.')


class Reply(Record):
    explanation: Text
    draft: list[DraftValue]
    question: Question|None


def requirements(assessment,formulation,summary,unknowns):
    assessment=check_assessment(assessment,formulation,summary,unknowns)
    if not ready(assessment):raise ValueError('Approve the required conditions and their regions, including Dirichlet constraints, first.')
    fields={u['name']:u for u in unknowns};result=[]
    for scope in ('boundary_parameters','source_parameters','dirichlet_conditions'):
        definitions={p['name']:p for p in formulation.get(scope,[])}
        for item in assessment[scope]:
            if item['requirement']!='needed':continue
            for region in item['regions']:
                row={'id':f'condition_{len(result)+1}','scope':scope,'region':region,'reason':item['reason']}
                if scope=='dirichlet_conditions':
                    components=item['components'];unknown=fields[item['field']]
                    shape=unknown['shape'] if not components else ([] if len(components)==1 else [len(components)])
                    row.update(field=item['field'],quantity=unknown['quantity'],components=components,shape=shape)
                else:
                    definition=definitions[item['name']]
                    row.update(name=item['name'],symbol=definition['symbol'])
                    if scope=='boundary_parameters' and definition.get('kind') is not None:
                        row['kind']=definition['kind']
                result.append(row)
    return result


def response_model(rows):
    Id=Enum('BoundaryValueId',{f'item_{i}':r['id'] for i,r in enumerate(rows)},type=str) if rows else str
    D=create_model('RequiredBoundaryValue',__base__=DraftValue,id=(Id,...))
    ScopedQuestion=scoped_questions('BoundaryValue',value_targets(rows),[r['id'] for r in rows]) if rows else None
    return create_model('BoundaryValueReply',__base__=Reply,
        draft=(Annotated[list[D],Field(min_length=len(rows),max_length=len(rows))],...),
        question=(ScopedQuestion|None if ScopedQuestion else type(None),...))


def check_draft(value,rows):
    result=[DraftValue.model_validate(v).model_dump() for v in value]
    required={r['id']:r for r in rows}
    if len(result)!=len(required) or {r['id'] for r in result}!=set(required):
        raise ValueError('Provide each approved boundary, source, and Dirichlet value exactly once.')
    for item in result:
        row=required[item['id']]
        if item['value'] is None:continue
        try:actual=list(np.asarray(item['value'],dtype=float).shape)
        except ValueError:raise ValueError('The numerical array has an invalid shape.') from None
        if row['scope']=='dirichlet_conditions' and actual!=row['shape']:
            if not (row['components'] and actual==[]):
                raise ValueError('The Dirichlet value shape must match its target field or components.')
    return result


def complete(draft):
    return all(item['value'] is not None and item['unit'] is not None for item in draft)


def unresolved_targets(draft):
    return {f'draft.{item["id"]}.{key}' for item in draft for key in ('value','unit') if item[key] is None}


def check_reply(value,rows):
    result=response_model(rows).model_validate_json(json.dumps(value)).model_dump(mode='json')
    result['draft']=check_draft(result['draft'],rows)
    missing=unresolved_targets(result['draft']);question=result['question']
    if question is None:
        if missing:raise ValueError('A clarification question is required for unresolved values or units.')
        return result
    targets=question['targets']
    if len(set(targets))!=len(targets) or not set(targets)<=missing:
        raise ValueError('Questions and recommendations must target distinct unresolved values or units.')
    if question['question_type']=='recommendation':
        target_ids={target.split('.')[1] for target in targets}
        for option in question['options']:
            names=[item['name'] for item in option['values']]
            if len(set(names))!=len(names) or not set(names)<=target_ids:
                raise ValueError('A recommendation must use distinct condition IDs addressed by the current question.')
            updates={}
            for item in option['values']:
                updates[item['name']]={'id':item['name'],'value':item['value'],'unit':item['unit']}
            check_draft([updates.get(item['id'],item) for item in result['draft']],rows)
    return result


def card(draft,rows):
    draft=check_draft(draft,rows)
    if not complete(draft):raise ValueError('Resolve every required value and unit before approval.')
    by_id={item['id']:item for item in draft}
    result={k:[] for k in ('boundary_parameters','source_parameters','dirichlet_conditions')}
    for row in rows:
        item={k:row[k] for k in (('field','components','region') if row['scope']=='dirichlet_conditions' else ('name','region'))}
        item.update(value=by_id[row['id']]['value'],unit=by_id[row['id']]['unit'])
        result[row['scope']].append(item)
    return result


def messages(state,summary,rows):
    source=(HERE/'boundary_values_prompt.txt').read_text()
    context={'user_request':state['initial_request'],'approved_conditions':state['boundary_parameter_assessment'],
        'unit_context':unit_context(summary),
        'required_values':rows,'unknowns':[{k:u[k] for k in ('name','quantity','shape')} for u in state['functionspace_card']['unknowns']],
        'weak_form':state['formulation']['weak_form'],
        'mesh':{k:summary.get(k) for k in ('dimension','coordinate_unit','boundary_groups','volume_groups')},
        'condition_dialogue':[{'message':t.get('message',''),'response':t['response']} for t in state.get('boundary_parameter_turns',[])],
        'current_draft':state.get('boundary_value_draft',[])}
    result=[{'role':'system','content':source},{'role':'user','content':json.dumps(context,ensure_ascii=False)}]
    for turn in state.get('boundary_value_turns',[]):
        if turn.get('message'):result.append({'role':'user','content':turn['message']})
        result.append({'role':'assistant','content':json.dumps(turn['response'],ensure_ascii=False)})
    if state.get('boundary_value_message'):result.append({'role':'user','content':state['boundary_value_message']})
    return result,{'boundary_values_prompt.txt':source}
