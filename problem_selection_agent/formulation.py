"""Strict formulation output with separate material, boundary, and volume-source inputs."""
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROMPT_PATH = Path(__file__).with_name('formulation_prompt.txt')
Equation = Annotated[str, Field(min_length=1, description='LaTeX equations only, without prose or Markdown delimiters.')]


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class FieldWeakForm(Record):
    field: Annotated[str, Field(min_length=1, description='The primary unknown field for this weak form. Treat a vector field as one field.')]
    unknown: Equation
    test_function: Equation


class LinearWeakForm(FieldWeakForm):
    type: Literal['linear']
    bilinear_form: Equation
    linear_form: Equation


class NonlinearWeakForm(FieldWeakForm):
    type: Literal['nonlinear']
    residual: Equation
    jacobian: Equation


class Parameter(Record):
    name: Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]*$', description='English snake_case name of an independent input parameter.')]
    symbol: Equation


BoundaryKind = Literal['neumann', 'robin']


class BoundaryParameter(Parameter):
    kind: BoundaryKind = Field(description='The Neumann or Robin boundary term that requires this input, as defined by the weak form.')


class Formulation(Record):
    weak_form: Annotated[list[LinearWeakForm | NonlinearWeakForm], Field(min_length=1)] | None
    kinematics: Annotated[list[Equation], Field(min_length=1)] | None
    constitutive: Annotated[list[Equation], Field(min_length=1)] | None
    constitutive_parameters: list[Parameter]
    boundary_parameters: list[BoundaryParameter]
    source_parameters: list[Parameter]

    @model_validator(mode='after')
    def unique_parameter_names(self):
        names = [parameter.name for parameter in self.constitutive_parameters + self.boundary_parameters + self.source_parameters]
        if len(names) != len(set(names)):
            raise ValueError('Constitutive, boundary, and source parameter names must be unique.')
        fields = [form.field for form in self.weak_form or []]
        if len(fields) != len(set(fields)):
            raise ValueError('Each primary field must have its own single weak-form entry.')
        return self


class StoredBoundaryParameter(Parameter):
    """Read earlier library records without guessing their missing classification."""
    kind: BoundaryKind | None = None


class StoredFormulation(Formulation):
    boundary_parameters: list[StoredBoundaryParameter]


class FormulationReview(Record):
    explanation: Annotated[str, Field(min_length=1,description='An English paragraph answering the expert or explaining revisions and their reasons.')]
    formulation: Annotated[Formulation | None,Field(description='The complete revised formulation, or null to preserve the current draft when only explaining or asking for clarification.')]


def output_format():
    return {'type': 'json_schema', 'json_schema': {
        'name': 'physics_formulation', 'strict': True, 'schema': Formulation.model_json_schema()}}
