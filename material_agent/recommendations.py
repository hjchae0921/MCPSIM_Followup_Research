"""One material-property decision per application region, enforced by schema."""
from copy import deepcopy
from enum import Enum
import json
from typing import Annotated

from pydantic import Field, create_model
from common.schema import Record, Text
from common.contracts import named_record
from .judgments import Value, assessment_model, binding_at, volumes


def response_model(formulation, summary):
    Internal = assessment_model(formulation, summary).model_fields['response'].annotation
    Decision = Internal.model_fields['ambiguities'].annotation.__args__[0]
    names = [p['name'] for p in formulation['constitutive_parameters']]
    registry = volumes(summary)
    RegionID = Enum('MaterialSetRegion', {key:key for key in registry}, type=str) if registry else str
    ValueUnit = create_model('MaterialPropertyValue', __base__=Record, value=(Value,...), unit=(str,...))
    Values = named_record('MaterialPropertySetValues',[(name,ValueUnit | None) for name in names],
        'Known constitutive inputs only; propose value/unit pairs together and leave unrelated inputs null.')
    Candidate = create_model('MaterialPropertySetCandidate', __base__=Record,
        label=(Text,...), description=(Text,Field(description='The shared material grade, conditions, and assumptions.')),
        values=(Values,...))
    Group = create_model('MaterialPropertySet', __base__=Record,
        regions=(Annotated[list[RegionID],Field(min_length=1)],...),
        explanation=(Text,...), options=(Annotated[list[Candidate],Field(min_length=1,max_length=2)],...))
    Sets = create_model('MaterialSetsByRegion', __base__=Record,
        __doc__='At most one material-property decision per region; shared regions use one entry and null for the others.',
        **{key:(Group | None,...) for key in registry})
    if not registry:
        Sets.model_config['json_schema_extra'] = {'required':[]}
    Input = create_model('MaterialInputClarification', __base__=Record,
        **{key:(Decision.model_fields[key].annotation,...) for key in ('parameter','binding','fields','explanation')},
        options=(type(None),Field(description='Clarifications are direct input. Numerical alternatives belong in material_sets.')))
    Assessment = create_model('MaterialPropertySetAssessment', __base__=Record,
        card=(Internal.model_fields['card'].annotation,...),
        user_inputs=(Internal.model_fields['user_inputs'].annotation,...),
        material_sets=(Sets,...),
        ambiguities=(list[Input],Field(description='Only independent inputs that cannot be proposed as part of the material choice.')))
    return create_model('MaterialPropertySetResponse', __base__=Record,response=(Assessment,...))


def member_bindings(assessment, parameter, regions):
    rows = assessment['card']['constitutive_parameters'][parameter]
    matched=[]
    for index,row in enumerate(rows):
        support=set(row['regions'] or [])
        if support & regions:
            if not support <= regions:
                raise ValueError('Split a material binding before assigning different materials to parts of its regions.')
            matched.append({'parameter':parameter,'binding':index})
    if not matched:
        unassigned=[i for i,row in enumerate(rows) if row['regions'] is None]
        if len(unassigned)==1:
            matched=[{'parameter':parameter,'binding':unassigned[0]}]
    if not matched:
        raise ValueError('Assign unambiguous regions to each property before offering a material set: '+parameter)
    return matched


def to_assessment(value, formulation, summary):
    """Compile named property sets into existing, server-indexed binding updates."""
    public=response_model(formulation,summary).model_validate_json(json.dumps({'response':value})).model_dump(mode='json',by_alias=True)['response']
    assessment={key:deepcopy(public[key]) for key in ('card','user_inputs')}
    grouped=[];used_regions=set();used_members=set()
    for key,group in public['material_sets'].items():
        if group is None:
            continue
        regions=set(group['regions'])
        parameter_sets=[{name for name,item in option['values'].items() if item is not None} for option in group['options']]
        if not parameter_sets[0] or any(names!=parameter_sets[0] for names in parameter_sets):
            raise ValueError('Every material candidate must provide the same complete property set from the formulation.')
        parameters=[p['name'] for p in formulation['constitutive_parameters'] if p['name'] in parameter_sets[0]]
        if key not in regions or len(regions)!=len(group['regions']) or regions & used_regions:
            raise ValueError('Combine all material-property recommendations on the same region into one material_sets entry.')
        used_regions.update(regions)
        members=[member for name in parameters for member in member_bindings(assessment,name,regions)]
        keys={(member['parameter'],member['binding']) for member in members}
        if keys & used_members:
            raise ValueError('A material binding cannot belong to two material-set decisions.')
        used_members.update(keys)
        options=[]
        for option in group['options']:
            updates=[]
            for member in members:
                row=binding_at(assessment,member['parameter'],member['binding'])
                updates.append({**member,'regions':row['regions'] or group['regions'],**deepcopy(option['values'][member['parameter']])})
            options.append({'label':option['label'],'description':option['description'],'updates':updates})
        first=members[0]
        grouped.append({**first,'members':members,'fields':['value','unit'],
            'explanation':group['explanation'],'options':options})
    inputs={}
    for item in public['ambiguities']:
        row=binding_at(assessment,item['parameter'],item['binding'])
        if (item['parameter'],item['binding']) in used_members:
            group=next(g for g in grouped if any(m['parameter']==item['parameter'] and m['binding']==item['binding'] for m in g['members']))
            if item['explanation'] not in group['explanation']:
                group['explanation']+='\n'+item['explanation']
            continue
        support=tuple(sorted(row['regions'])) if row['regions'] else (item['parameter'],item['binding'])
        inputs.setdefault(support,[]).append(item)
    clarifications=[]
    for items in inputs.values():
        first=deepcopy(items[0])
        if len(items)>1:
            first['members']=[{'parameter':item['parameter'],'binding':item['binding']} for item in items]
            first['fields']=list(dict.fromkeys(field for item in items for field in item['fields']))
            first['explanation']='\n'.join(dict.fromkeys(item['explanation'] for item in items))
        clarifications.append(first)
    assessment['ambiguities']=grouped+clarifications
    return assessment,public


def prompt_reply(turn, formulation, summary):
    """Preserve new proposals; replay older judgments without per-property choices."""
    from .judgments import provider_reply
    raw=provider_reply(turn,formulation,summary)
    if turn.get('proposal') is not None:
        value=deepcopy(turn['proposal'])
        for group in value.get('material_sets',{}).values():
            if group is not None:group.pop('parameters',None)
        value['card']=deepcopy(raw['card']);value['user_inputs']=deepcopy(raw.get('user_inputs',[]))
        return value
    return {'card':deepcopy(raw['card']),'user_inputs':deepcopy(raw.get('user_inputs',[])),
        'material_sets':{key:None for key in volumes(summary)},
        'ambiguities':[{key:item[key] for key in ('parameter','binding','fields','explanation','options')}
            for item in raw['ambiguities'] if item.get('options') is None]}
