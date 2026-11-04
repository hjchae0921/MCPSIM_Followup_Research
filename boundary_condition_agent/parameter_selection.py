"""Select required boundary/source parameters without assigning numerical values."""
import json
from copy import deepcopy
from math import prod
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, create_model, model_validator
from common.schema import Record, Text
from common.schema import Region, region_key
from common.contracts import named_record

HERE=Path(__file__).resolve().parent
SCOPES=('boundary_parameters','source_parameters','dirichlet_conditions')
Requirement=Literal['needed','not_needed'] | None


class ParameterUse(Record):
    name: Text
    requirement: Requirement = Field(description='Whether this condition is used in the physical problem; null if unresolved. This is separate from user approval.')
    regions: list[Region] | None
    reason: Text


class DirichletUse(Record):
    field: Text
    requirement: Requirement = Field(description='Whether this field uses Dirichlet constraints; null if unresolved. This is separate from user approval.')
    regions: list[Region] | None
    components: list[Annotated[int,Field(ge=0)]] | None = Field(description='Zero-based components; [] means the whole field, null means unresolved.')
    reason: Text


class Assessment(Record):
    boundary_parameters: list[ParameterUse]
    source_parameters: list[ParameterUse]
    dirichlet_conditions: list[DirichletUse]


class Recommendation(Record):
    label: Text
    description: Text
    assessment: Assessment


class Reply(Record):
    explanation: Text
    assessment: Assessment
    recommendations: list[Recommendation] = Field(max_length=2)


def canonical_assessment(value,unknowns=()):
    """Read older checkpoints without rewriting their saved payloads or API logs."""
    result=deepcopy(value)
    scalars={u['name'] for u in unknowns if u['shape']==[]}
    for scope in SCOPES:
        for item in result.get(scope,[]):
            if 'requirement' not in item and 'status' in item:
                previous=item.pop('status')
                item['requirement']=None if previous=='undetermined' else previous
                if previous=='undetermined':
                    if not item.get('regions'):item['regions']=None
                    if scope=='dirichlet_conditions' and not item.get('components'):item['components']=None
            if item.get('requirement')=='not_needed':
                if item.get('regions') is None:item['regions']=[]
                if scope=='dirichlet_conditions' and item.get('components') is None:item['components']=[]
            if scope=='dirichlet_conditions' and item.get('field') in scalars and (
                    item.get('components') is None or item.get('components')==[0]):
                item['components']=[]
    return result


def response_model(formulation,summary,unknowns=(), *, wire=False):
    def uses(key,groups_key,label):
        names=[p['name'] for p in formulation[key]]
        Name=Enum(label+'ParameterName',{f'item_{i}':name for i,name in enumerate(names)},type=str) if names else str
        groups=summary.get(groups_key,[])
        RegionName=Enum(label+'RegionName',{f'item_{i}':g['name'] for i,g in enumerate(groups)},type=str) if groups else str
        dim=summary['dimension']-1 if groups_key=='boundary_groups' else summary['dimension']
        KnownRegion=create_model(label+'Region',__base__=Region,name=(RegionName,...),dim=(Literal[dim],...))
        if wire:
            Use=create_model(label+'Use',__base__=Record,requirement=(Requirement,...),
                regions=(list[KnownRegion] | None,...),reason=(Text,...))
            return named_record(label+'ParameterUses',[(name,Use) for name in names])
        Use=create_model(label+'Use',__base__=ParameterUse,name=(Name,...),regions=(list[KnownRegion] | None,...))
        return Annotated[list[Use],Field(min_length=len(names),max_length=len(names))]
    fields=[u['name'] for u in unknowns]
    FieldName=Enum('DirichletTargetField',{f'item_{i}':name for i,name in enumerate(fields)},type=str) if fields else str
    groups=summary.get('boundary_groups',[])
    RegionName=Enum('DirichletRegionName',{f'item_{i}':g['name'] for i,g in enumerate(groups)},type=str) if groups else str
    Face=create_model('DirichletFace',__base__=Region,name=(RegionName,...),dim=(Literal[summary['dimension']-1],...))
    D=create_model('DirichletRequirement',__base__=DirichletUse,field=(FieldName,...),regions=(list[Face] | None,...))
    DirichletItems=Annotated[list[D],Field(min_length=len(fields),max_length=None if fields else 0)]
    if wire:
        slots=[]
        for index,unknown in enumerate(unknowns):
            properties={'requirement':(Requirement,...),'regions':(list[Face] | None,...),'reason':(Text,...)}
            if unknown['shape']:
                Component=Literal[tuple(range(prod(unknown['shape'])))]
                properties['components']=(list[Component] | None,Field(description='Zero-based constrained components of the approved field; [] means the whole field, null means unresolved.'))
            D=create_model(f'DirichletUse{index}',__base__=Record,**properties)
            slots.append((unknown['name'],Annotated[list[D],Field(min_length=1)]))
        DirichletItems=named_record('DirichletFieldUses',slots,
            'Assess condition use for each approved unknown, including not_needed when unused.')
    A=create_model('BoundarySourceParameterAssessment',__base__=Assessment,
        boundary_parameters=(uses('boundary_parameters','boundary_groups','Boundary'),...),
        source_parameters=(uses('source_parameters','volume_groups','Source'),...),
        dirichlet_conditions=(DirichletItems,...))
    R=create_model('BoundarySourceCombination',__base__=Recommendation,assessment=(A,...))
    @model_validator(mode='after')
    def consistent_uses(value):
        data=value.model_dump(mode='json',by_alias=True)
        check_reply(internal_reply(data,unknowns) if wire else data,formulation,summary,unknowns)
        return value
    return create_model('ParameterSelectionReply',__base__=Reply,__validators__={'consistent_uses':consistent_uses},assessment=(A,...),
        recommendations=(Annotated[list[R],Field(max_length=2)],...))


def check_assessment(value,formulation,summary,unknowns=()):
    result=Assessment.model_validate(canonical_assessment(value,unknowns)).model_dump()
    for key,groups_key in [('boundary_parameters','boundary_groups'),('source_parameters','volume_groups')]:
        expected={p['name'] for p in formulation[key]};items=result[key]
        if len(items)!=len(expected) or {p['name'] for p in items}!=expected:
            raise ValueError('Assess each formulation parameter exactly once.')
        regions={region_key(g) for g in summary.get(groups_key,[])}
        for parameter in items:
            keys=[region_key(r) for r in parameter['regions'] or []]
            if len(set(keys))!=len(keys) or any(key not in regions for key in keys):
                raise ValueError('Use actual boundary or volume regions from the mesh.')
            if parameter['requirement']=='needed' and parameter['regions']==[]:
                raise ValueError('Use null for unresolved regions or specify the nonempty regions of each required parameter.')
            if parameter['requirement']=='not_needed' and parameter['regions']!=[]:
                raise ValueError('Unused parameters must have no application regions.')
    fields={u['name']:u for u in unknowns}
    items=result['dirichlet_conditions']
    if {item['field'] for item in items}!=set(fields):
        raise ValueError('Assess whether Dirichlet constraints are required for every primary unknown.')
    known={region_key(g) for g in summary.get('boundary_groups',[])}
    occupied=set()
    for item in items:
        shape=fields[item['field']]['shape'];components=item['components']
        if components is not None and (len(set(components))!=len(components) or (not shape and components) or any(c>=prod(shape or [1]) for c in components)):
            raise ValueError('Dirichlet components must be unique valid zero-based indices; [] denotes the whole field.')
        keys=[region_key(r) for r in item['regions'] or []]
        if len(set(keys))!=len(keys) or any(key not in known for key in keys):
            raise ValueError('Dirichlet constraints must use actual boundary regions.')
        if item['requirement']=='needed' and item['regions']==[]:
            raise ValueError('Use null for unresolved regions or specify the nonempty regions of each required Dirichlet constraint.')
        if item['requirement']=='not_needed' and (item['regions']!=[] or components!=[] or sum(i['field']==item['field'] for i in items)!=1):
            raise ValueError(f"{item['field']}: not_needed means the whole field has no Dirichlet constraints. "
                'It cannot coexist with other entries for that field, and regions and components must be [].')
        if item['requirement']=='needed' and components is not None:
            for r in item['regions'] or []:
                for tag in r['tags']:
                    for c in components or range(prod(shape or [1])):
                        key=item['field'],tag,c
                        if key in occupied:raise ValueError('Duplicate Dirichlet constraints affect the same boundary, field, and component.')
                        occupied.add(key)
    return result


def unresolved_targets(assessment,unknowns=()):
    assessment=canonical_assessment(assessment,unknowns);targets=set()
    for scope in SCOPES:
        if scope not in assessment:
            targets.add(scope);continue
        for item in assessment[scope]:
            name=item['field'] if scope=='dirichlet_conditions' else item['name']
            prefix=f'{scope}.{name}'
            requirement=item.get('requirement')
            if requirement is None:targets.add(prefix+'.requirement')
            elif requirement=='needed':
                if item['regions'] is None:targets.add(prefix+'.regions')
                if scope=='dirichlet_conditions' and item['components'] is None:targets.add(prefix+'.components')
    return targets


def ready(assessment,unknowns=()):
    return all(scope in assessment for scope in SCOPES) and not unresolved_targets(assessment,unknowns)


def present_review(value,unknowns=()):
    """Derive completion and clarification from field values, independently of approval."""
    result=deepcopy(value)
    result['assessment']=canonical_assessment(result['assessment'],unknowns)
    for proposal in result.get('recommendations',[]):
        proposal['assessment']=canonical_assessment(proposal['assessment'],unknowns)
    missing=unresolved_targets(result['assessment'])
    result['determination']='undetermined' if missing else 'determined'
    result['unresolved_fields']=sorted(missing)
    result['question_targets']=sorted(missing)
    lines=[]
    for scope in SCOPES:
        if scope not in result['assessment']:
            lines.append('Review the '+scope.replace('_',' ')+'.');continue
        for item in result['assessment'][scope]:
            name=item.get('field',item.get('name'));prefix=f'{scope}.{name}'
            label=('Dirichlet constraints for '+name) if scope=='dirichlet_conditions' else scope.replace('_',' ')+': '+name
            if prefix+'.requirement' in missing:lines.append('Should this problem use '+label+'?')
            else:
                if prefix+'.regions' in missing:lines.append('Select the application regions for '+label+'.')
                if prefix+'.components' in missing:lines.append('Select the constrained components for '+label+'.')
    result['question']='\n'.join(dict.fromkeys(lines)) if lines else None
    return result


def check_reply(value,formulation,summary,unknowns=()):
    result=Reply.model_validate(value).model_dump()
    result['assessment']=check_assessment(result['assessment'],formulation,summary,unknowns)
    for proposal in result['recommendations']:
        proposal['assessment']=check_assessment(proposal['assessment'],formulation,summary,unknowns)
        if not ready(proposal['assessment']):
            raise ValueError('Recommended combinations must resolve all condition requirements and regions.')
    return present_review(result,unknowns)


def provider_reply(value,unknowns=()):
    """Replay physical judgments without server-generated questions or completion metadata."""
    result=present_review(value,unknowns)
    return {'explanation':result['explanation'],'assessment':result['assessment'],
        'recommendations':result.get('recommendations',[])}


def wire_reply(value,unknowns=()):
    """Move server-owned identifiers into closed provider object keys."""
    result=deepcopy(value)
    scalars={u['name'] for u in unknowns if u['shape']==[]}
    def encode(assessment):
        if isinstance(assessment.get('boundary_parameters'),dict):
            for name,rows in assessment.get('dirichlet_conditions',{}).items():
                if name in scalars:
                    for row in rows:row.pop('components',None)
            return assessment
        assessment=canonical_assessment(assessment,unknowns)
        for scope in ('boundary_parameters','source_parameters'):
            if isinstance(assessment.get(scope),list):
                rows=assessment[scope]
                if len({row['name'] for row in rows})!=len(rows):raise ValueError('Assess each parameter once.')
                assessment[scope]={row['name']:{k:v for k,v in row.items() if k!='name'} for row in rows}
        if isinstance(assessment.get('dirichlet_conditions'),list):
            rows=assessment['dirichlet_conditions'];grouped={}
            for row in rows:
                omitted={'field','components'} if row['field'] in scalars else {'field'}
                grouped.setdefault(row['field'],[]).append({k:v for k,v in row.items() if k not in omitted})
            assessment['dirichlet_conditions']=grouped
        return assessment
    result['assessment']=encode(result['assessment'])
    for proposal in result.get('recommendations',[]):proposal['assessment']=encode(proposal['assessment'])
    return result


def internal_reply(value,unknowns=()):
    result=deepcopy(value)
    scalars={u['name'] for u in unknowns if u['shape']==[]}
    def decode(assessment):
        for scope in ('boundary_parameters','source_parameters'):
            assessment[scope]=[{'name':name,**item} for name,item in assessment[scope].items()]
        assessment['dirichlet_conditions']=[{'field':name,**({'components':[]} if name in scalars else {}),**item}
            for name,rows in assessment['dirichlet_conditions'].items() for item in rows]
        return assessment
    result['assessment']=decode(result['assessment'])
    for proposal in result.get('recommendations',[]):proposal['assessment']=decode(proposal['assessment'])
    return result


def messages(state,summary):
    source=(HERE/'parameter_selection_prompt.txt').read_text()
    unknowns=state['functionspace_card']['unknowns']
    def regions(key):
        return [{k:g[k] for k in ('name','dim','tags','bounds','centroid') if k in g} for g in summary.get(key,[])]
    context={'user_request':state['initial_request'],
        'unknowns':[{k:u[k] for k in ('name','quantity','shape')} for u in unknowns],
        'weak_form':state['formulation']['weak_form'],
        'boundary_parameters':state['formulation']['boundary_parameters'],
        'source_parameters':state['formulation']['source_parameters'],
        'boundary_regions':regions('boundary_groups'),'volume_regions':regions('volume_groups'),
        'coordinate_unit':summary.get('coordinate_unit')}
    result=[{'role':'system','content':source},{'role':'user','content':json.dumps(context,ensure_ascii=False)}]
    for turn in state.get('boundary_parameter_turns',[]):
        if turn.get('message'):result.append({'role':'user','content':turn['message']})
        result.append({'role':'assistant','content':json.dumps(wire_reply(provider_reply(turn['response'],unknowns),unknowns),ensure_ascii=False)})
    if state.get('boundary_parameter_message'):
        result.append({'role':'user','content':state['boundary_parameter_message']})
    return result,{'parameter_selection_prompt.txt':source}
