"""Project approved Dirichlet data to one scalar condition per field component."""
from math import prod
from typing import Annotated, Literal, Union

import numpy as np
from pydantic import Field, create_model

from common.schema import Dimension, Number, Record, Region, Text, Value


class Unknown(Record):
    name: Text
    quantity: Text
    shape: list[Dimension]


class ApprovedCondition(Record):
    field: Text
    components: list[int]
    region: Region
    value: Value
    unit: str


class PrescribedValue(Record):
    value: Number
    unit: str


class Parameters(Record):
    value: PrescribedValue


class Condition(Record):
    field: Text
    components: list[int]
    region: Region
    kind: Literal['Dirichlet']
    parameters: Parameters


def card_model(unknowns):
    """Limit fields and components to the approved unknowns, with numeric scalar values."""
    fields=[Unknown.model_validate(u).model_dump() for u in unknowns]
    if not fields or len({u['name'] for u in fields})!=len(fields):
        raise ValueError("Unknown field information with different names is required.")
    variants=[]
    for i,unknown in enumerate(fields):
        if unknown['shape']:
            components=Annotated[list[Literal[tuple(range(prod(unknown['shape'])))]],Field(min_length=1,max_length=1)]
        else:
            components=Annotated[list[int],Field(max_length=0)]
        variants.append(create_model(f'DirichletField{i}',__base__=Condition,
            field=(Literal[unknown['name']],...),components=(components,...)))
    Target=variants[0] if len(variants)==1 else Union[tuple(variants)]
    return create_model('ComponentwiseBoundaryCard',__base__=Record,
        unknowns=(Annotated[list[Unknown],Field(min_length=1)],...),boundary_conditions=(list[Target],...))


def card(unknowns,conditions):
    """Expand vector/tensor values without changing component order, units or constraints."""
    fields=[Unknown.model_validate(u).model_dump() for u in unknowns]
    Model=card_model(fields);by_name={u['name']:u for u in fields}
    result=[];occupied=set()
    for raw in conditions:
        condition=ApprovedCondition.model_validate(raw).model_dump()
        if condition['field'] not in by_name:
            raise ValueError("The Dirichlet target field is not in the approved unknown fields.")
        unknown=by_name[condition['field']];shape=unknown['shape'];components=condition['components']
        if len(set(components))!=len(components) or any(c<0 or c>=prod(shape or [1]) for c in components):
            raise ValueError("The Dirichlet component number is duplicated or out of range for the unknown field.")
        try:value=np.asarray(condition['value'],dtype=float)
        except ValueError:raise ValueError("Please check the array shape of the Dirichlet values.") from None
        if not shape:
            if components or value.ndim!=0:
                raise ValueError("For a scalar field, use components: [] and a single number for the Dirichlet condition.")
            pairs=[([],float(value))]
        elif not components:
            if list(value.shape)!=shape:
                raise ValueError("The Dirichlet value specified for the entire field differs in shape from the unknown field.")
            pairs=[([i],float(v)) for i,v in enumerate(value.reshape(-1))]
        elif value.ndim==0:
            # The approved value collector already permits a shared scalar for selected components.
            pairs=[([i],float(value)) for i in components]
        elif value.shape==(len(components),):
            pairs=[([i],float(v)) for i,v in zip(components,value)]
        else:
            raise ValueError("The number of selected Dirichlet components and values does not match.")
        for component,number in pairs:
            region=condition['region']
            for tag in region['tags']:
                key=condition['field'],region['dim'],tag,tuple(component)
                if key in occupied:raise ValueError("A Dirichlet condition is duplicated on the same boundary, field, and component.")
                occupied.add(key)
            result.append({'field':condition['field'],'components':component,'region':region,
                'kind':'Dirichlet','parameters':{'value':{'value':number,'unit':condition['unit']}}})
    return Model.model_validate({'unknowns':fields,'boundary_conditions':result}).model_dump(mode='json')
