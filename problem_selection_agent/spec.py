"""Selection contracts and provider schemas constrained by verified inputs."""
from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator, field_validator
from pydantic_core import PydanticCustomError
from common.coupling import COUPLING, CouplingType, normalized_coupling

Text = Annotated[str, Field(min_length=1)]
Identifier = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]*$')]
PLACEHOLDERS = {'none', 'null', 'required', 'unknown', 'other', 'unregistered', 'new_model'}


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Dependency(Record):
    from_: Text | None = Field(alias='from')
    to: Text | None


class Coupling(Record):
    type: CouplingType
    dependencies: Annotated[list[Dependency], Field(min_length=1)]

    @field_validator('type', mode='before')
    @classmethod
    def legacy_type(cls, value):
        return normalized_coupling(value)


class Problem(Record):
    type: Identifier
    unknowns: Annotated[list[Identifier], Field(min_length=1)]
    linearity: Literal['linear', 'nonlinear']
    time_dependence: Literal['independent', 'dependent']
    history_dependence: bool
    dimension: Annotated[int, Field(ge=1, le=3)]
    coupling: Coupling

    @field_validator('type')
    @classmethod
    def meaningful_type(cls, value):
        if value in PLACEHOLDERS:
            raise ValueError('The problem type must name a meaningful physical problem.')
        return value


class MaterialModel(Record):
    model: Identifier
    fields: Annotated[list[Identifier], Field(min_length=1)]
    symmetry: Identifier

    @field_validator('model', 'symmetry')
    @classmethod
    def meaningful_model(cls, value):
        if value in PLACEHOLDERS:
            raise ValueError('Constitutive models and symmetry must have meaningful names.')
        return value


class Material(Record):
    constitutive_models: Annotated[list[MaterialModel], Field(min_length=1)]


class Selection(Record):
    problem: Problem
    materials: Annotated[list[Material], Field(min_length=1)]

    @model_validator(mode='after')
    def consistent_fields(self):
        p = self.problem
        if p.type in PLACEHOLDERS:
            raise ValueError('The problem type must name a meaningful physical problem.')
        fields = set(p.unknowns)
        if len(fields) != len(p.unknowns):
            raise ValueError('Primary unknown names must be unique.')
        covered = set()
        for material in self.materials:
            models = material.constitutive_models
            if len({model.model for model in models}) != len(models):
                raise ValueError('Constitutive models within a material must be unique.')
            for model in models:
                if model.model in PLACEHOLDERS or model.symmetry in PLACEHOLDERS:
                    raise ValueError('Constitutive models and symmetry must have meaningful names.')
                if len(set(model.fields)) != len(model.fields) or not set(model.fields) <= fields:
                    raise ValueError('Constitutive model fields must be unique and reference primary unknowns.')
                covered.update(model.fields)
        if covered != fields:
            raise ValueError('Associate every primary unknown with its constitutive model.')
        deps = p.coupling.dependencies
        if p.coupling.type == COUPLING[0]:
            if len(deps) != 1 or deps[0].from_ is not None or deps[0].to is not None:
                raise ValueError('Single physics requires one dependency entry with null from/to values.')
        else:
            edges = set()
            for dep in deps:
                if dep.from_ not in fields or dep.to not in fields or dep.from_ == dep.to:
                    raise ValueError('Coupling dependencies must connect distinct primary unknowns.')
                edges.add((dep.from_, dep.to))
            if len(edges) != len(deps):
                raise ValueError('Coupling dependencies must be unique.')
            def cyclic(node, path):
                if node in path:
                    return True
                return any(cyclic(dst, path | {node}) for src, dst in edges if src == node)
            cycle = any(cyclic(node, set()) for node in fields)
            if (p.coupling.type == COUPLING[1] and cycle) or (p.coupling.type == COUPLING[2] and not cycle):
                raise PydanticCustomError('coupling_directions', 'Dependency directions do not match the one-way or fully coupled classification.')
        return self


def normalized(value):
    """Normalize legacy coupling identifiers without changing stored files."""
    value = deepcopy(value)
    coupling = value['problem']['coupling']
    coupling['type'] = normalized_coupling(coupling['type'])
    if coupling['type'] == 'single_physics' and not coupling['dependencies']:
        coupling['dependencies'] = [{'from': None, 'to': None}]
    return Selection.model_validate(value).model_dump(by_alias=True)


def canonical(value):
    value = normalized(value)
    p = value['problem']
    p['unknowns'].sort()
    p['coupling']['dependencies'].sort(key=lambda d: (d['from'] or '', d['to'] or ''))
    for material in value['materials']:
        for model in material['constitutive_models']:
            model['fields'].sort()
        material['constitutive_models'].sort(key=lambda m: (m['model'], tuple(m['fields']), m['symmetry']))
    import json
    value['materials'].sort(key=lambda m: json.dumps(m, sort_keys=True))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def reply_model(types, models, dimension, answers=None, *, wire=False):
    """Collect field judgments; the server decides whether clarification is needed."""
    from .questions import fixed_values, ambiguity_model, ambiguity_record

    def partial(name, base, **overrides):
        fields = {key: (field.rebuild_annotation() | None, ...)
            for key, field in base.model_fields.items()}
        return create_model(name, __base__=base, **{**fields, **overrides})

    PartialCoupling = partial('PartialCoupling', Coupling)
    fields = {'dimension': (Literal[dimension] | None, ...), 'coupling': (PartialCoupling, ...)}
    answers = answers or {}
    coupling = {}
    for target, value in answers.items():
        if target not in fixed_values() or value not in fixed_values()[target]:
            raise ValueError('Check the confirmed selection fields and values.')
        name = target.removeprefix('problem.')
        if name == 'coupling.type':
            coupling['type'] = (Literal[value] | None, ...)
        else:
            fields[name] = (Literal[value] | None, ...)
    if coupling:
        ConfirmedCoupling = create_model('ConfirmedCoupling', __base__=PartialCoupling, **coupling)
        fields['coupling'] = (ConfirmedCoupling, ...)
    PartialProblem = partial('PartialProblem', Problem, **fields)
    PartialModel = partial('PartialMaterialModel', MaterialModel)
    PartialMaterial = create_model('PartialMaterial', __base__=Record,
        constitutive_models=(Annotated[list[PartialModel], Field(min_length=1)] | None, ...))
    PartialSelection = create_model('PartialSelection', __base__=Record,
        __doc__='Fill every field supported by the request and context. Use null only for genuine unresolved physical-model choices.',
        problem=(PartialProblem, ...), materials=(Annotated[list[PartialMaterial], Field(min_length=1)] | None, ...))
    Assessment = create_model('SelectionAssessment', __base__=Record,
        spec=(PartialSelection, ...),
        ambiguities=(ambiguity_record() if wire else list[ambiguity_model()], ...))
    return create_model('SelectionReply', __base__=Record, response=(Assessment, ...))
