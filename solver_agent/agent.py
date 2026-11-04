"""Strict solver cards grounded in approved inputs and measured runtime capabilities."""
import hashlib
import json
from enum import Enum
from pathlib import Path
import re
from typing import Annotated

from pydantic import Field, create_model
from common.schema import Record, Text, Number
from common.dialogue import scoped_questions
from common.authoring import solver_targets

HERE=Path(__file__).resolve().parent
OPTION_NAME_PATTERN=r'^(?:snes|ksp|pc|fieldsplit|sub|mg|mat)_[a-z0-9_]+$'


class Option(Record):
    name: Annotated[str,Field(pattern=OPTION_NAME_PATTERN,
        description="The full official PETSc option name. Exclude only the leading - and the execution-specific options prefix, and keep the official name components such as ksp_/pc_/snes_. Do not add options that duplicate the basic card fields.")]
    value: str|int|Number|bool


class Linear(Record):
    type: Text
    ksp_type: Text
    pc_type: Text
    factor_solver: Text|None
    rtol: Number|None
    atol: Number|None
    max_iterations: int|None
    options: list[Option]


class Nonlinear(Record):
    method: Text
    line_search: Text|None
    rtol: Number|None
    atol: Number|None
    stol: Number|None
    max_iterations: int|None
    linear_solver: Linear
    options: list[Option]


class Solver(Record):
    linear: Linear|None
    nonlinear: Nonlinear|None


class Card(Record):
    solver: Solver


def context(state,environment):
    summary=state['mesh']['summary']
    return {'initial_request':state['initial_request'],'confirmed_selection':state['confirmed_selection'],
        'formulation':{key:state['formulation'].get(key) for key in ('weak_form','kinematics','constitutive')},
        'functionspace_card':state['functionspace_card'],'material_card':state['material_card'],
        'boundary_value_card':state['boundary_value_card'],
        'mesh':{key:summary.get(key) for key in ('dimension','nodes','cells','coordinate_unit')},
        'execution_environment':{key:value for key,value in environment.items() if key!='environment_id'}}


def signature(state,environment):
    return hashlib.sha256(json.dumps({'version':1,'context':context(state,environment),
        'environment_id':environment.get('environment_id')},ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def check_card(value,selection,environment):
    # Report a useful error for manual input before strict schema validation.
    raw=value.get('solver',{}) if isinstance(value,dict) else {}
    if isinstance(raw,dict):
        items=[raw.get('linear'),raw.get('nonlinear')]
        if isinstance(raw.get('nonlinear'),dict):items.append(raw['nonlinear'].get('linear_solver'))
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('options'),list):continue
            for option in item['options']:
                name=option.get('name') if isinstance(option,dict) else None
                if isinstance(name,str) and not re.fullmatch(OPTION_NAME_PATTERN,name):
                    raise ValueError("Please enter the full official PETSc option name: "+name+
                        ". Omit only the execution-specific prefix and keep the official option name components such as pc_, ksp_, and snes_.")
    card=Card.model_validate(value).model_dump()
    solver=card['solver']
    nonlinear=selection['problem']['linearity']=='nonlinear'
    if nonlinear != (solver['nonlinear'] is not None) or nonlinear == (solver['linear'] is not None):
        raise ValueError("Fill in only the solver items corresponding to the finalized linearity and leave the rest as null.")

    def member(value,key,nullable=False):
        if value is None and nullable:return
        if value not in environment[key]:raise ValueError("This is a solver type that has not been initialized in the execution environment: "+str(value))
        if value in ('python','shell'):
            raise ValueError("This type requires a separate user callback. Please choose a type that can be configured with the current settings card alone.")

    def tolerances(item):
        for key in ('rtol','atol','stol'):
            v=item.get(key)
            if v is not None and (v<0 or key=='rtol' and v>=1):raise ValueError("Please check the solver tolerance range: "+key)
        if item['max_iterations'] is not None and item['max_iterations']<=0:
            raise ValueError("The maximum number of iterations must be a positive integer.")

    def options(item,nonlinear=False):
        seen=set();normalized=[]
        reserved={'snes_type','snes_linesearch_type','snes_rtol','snes_atol','snes_stol','snes_max_it',
                  'ksp_type','pc_type','pc_factor_mat_solver_type','ksp_rtol','ksp_atol','ksp_max_it'}
        declared=({'snes_type':item['method'],'snes_linesearch_type':item['line_search'],
            'snes_rtol':item['rtol'],'snes_atol':item['atol'],'snes_stol':item['stol'],
            'snes_max_it':item['max_iterations']} if nonlinear else
            {'ksp_type':item['ksp_type'],'pc_type':item['pc_type'],'pc_factor_mat_solver_type':item['factor_solver'],
             'ksp_rtol':item['rtol'],'ksp_atol':item['atol'],'ksp_max_it':item['max_iterations']})
        for option in item['options']:
            name=option['name']
            if name in reserved:
                if name in declared and declared[name] is not None and not isinstance(option['value'],bool) and option['value']==declared[name]:
                    # Keep one representation of the same setting; never choose between conflicting values.
                    continue
                raise ValueError("The values or application locations of the basic card fields and additional PETSc options conflict: "+name)
            if not re.fullmatch(r'[a-z][a-z0-9_]*',name) or name in seen:
                raise ValueError("Please check the format, duplication, and conflicts with the default settings of the additional PETSc option names: "+name)
            seen.add(name)
            for suffix,key in (('ksp_type','ksp_types'),('pc_type','pc_types'),
                               ('pc_factor_mat_solver_type','factor_solvers'),('snes_type','snes_types'),
                               ('snes_linesearch_type','line_search_types')):
                if name.endswith(suffix):member(option['value'],key)
            if not name.startswith(('snes_','ksp_','pc_','fieldsplit_','sub_','mg_','mat_')):
                raise ValueError("Please enter only the PETSc options corresponding to the solver settings: "+name)
            if not nonlinear and name.startswith('snes_'):
                raise ValueError("SNES settings cannot be included in the additional options for a linear solver.")
            normalized.append(option)
        item['options']=normalized

    def linear(item):
        member(item['ksp_type'],'ksp_types');member(item['pc_type'],'pc_types')
        member(item['factor_solver'],'factor_solvers',True)
        tolerances(item);options(item)

    if nonlinear:
        item=solver['nonlinear']
        member(item['method'],'snes_types');member(item['line_search'],'line_search_types',True)
        tolerances(item);linear(item['linear_solver']);options(item,True)
        # The nested solver owns its linear options; do not silently override it.
        if any(o['name'].startswith(('ksp_','pc_')) for o in item['options']):
            raise ValueError("Please specify the internal linear settings of the nonlinear solver in linear_solver.")
    else:linear(solver['linear'])
    return card


def response_model(selection,environment):
    def enum(name,key):return Enum(name,{f'item_{i}':v for i,v in enumerate(environment[key])},type=str)
    KSP=enum('InstalledKSP','ksp_types');PC=enum('InstalledPC','pc_types')
    Factor=enum('InstalledFactor','factor_solvers') if environment['factor_solvers'] else None
    SNES=enum('InstalledSNES','snes_types');Search=enum('InstalledLineSearch','line_search_types')
    Lin=create_model('RuntimeLinearSolver',__base__=Linear,ksp_type=(KSP,...),pc_type=(PC,...),
        factor_solver=((Factor|None) if Factor else type(None),...))
    Nonlin=create_model('RuntimeNonlinearSolver',__base__=Nonlinear,method=(SNES,...),
        line_search=(Search|None,...),linear_solver=(Lin,...))
    nonlinear=selection['problem']['linearity']=='nonlinear'
    Sol=create_model('RuntimeSolver',__base__=Solver,
        linear=(type(None) if nonlinear else Lin,...),nonlinear=(Nonlin if nonlinear else type(None),...))
    SolverCard=create_model('SolverCard',__base__=Card,solver=(Sol,...))
    Proposal=create_model('SolverProposal',__base__=Record,explanation=(Text,...),proposed_card=(SolverCard,...))
    Recommendation=create_model('SolverRecommendation',__base__=Record,
        label=(Text,...),description=(Text,...),card=(SolverCard,...))
    Recommendations=create_model('SolverRecommendations',__base__=Record,explanation=(Text,...),
        recommendations=(Annotated[list[Recommendation],Field(min_length=1,max_length=2)],...))
    Question=scoped_questions('Solver',solver_targets(selection))
    return create_model('SolverResponse',__base__=Record,
        response=(Recommendations|Proposal|Question,...))


def check_reply(value,selection,environment):
    if 'proposed_card' in value:value['proposed_card']=check_card(value['proposed_card'],selection,environment)
    for item in value.get('recommendations',[]):item['card']=check_card(item['card'],selection,environment)
    return value


def messages(state,environment):
    source=(HERE/'solver_prompt.txt').read_text()
    header,marker,user=source.partition('=== USER MESSAGE ===')
    if not marker or user.count('{{CONTEXT_JSON}}')!=1:raise ValueError("Please check the solver prompt placeholder.")
    result=[{'role':'system','content':header.removeprefix('=== SYSTEM MESSAGE ===').strip()},
        {'role':'user','content':user.replace('{{CONTEXT_JSON}}',json.dumps(context(state,environment),ensure_ascii=False)).strip()}]
    for turn in state.get('solver_turns',[]):
        if turn.get('message'):result.append({'role':'user','content':turn['message']})
        result.append({'role':'assistant','content':json.dumps({'response':turn['response']},ensure_ascii=False)})
    if state.get('solver_message'):result.append({'role':'user','content':state['solver_message']})
    return result,{'solver_prompt.txt':source}
