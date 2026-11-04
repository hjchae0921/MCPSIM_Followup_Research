"""Function-space card schemas used by the approved authoring flow."""

from typing import Annotated

from pydantic import Field, model_validator, field_validator
from common.schema import Record, Text, Dimension
from common.coupling import CouplingType, normalized_coupling



class Space(Record):
    family: Text
    degree: Annotated[int, Field(ge=0)]


class Unknown(Record):
    name: Text
    quantity: Text
    shape: list[Dimension]
    function_space: Space


class StateVariable(Record):
    name: Text
    symbol: Text
    shape: list[Dimension]
    unit: str
    function_space: Space


class FunctionSpaceCard(Record):
    unknowns: Annotated[list[Unknown], Field(min_length=1)]
    coupling_type: CouplingType
    state_variables: list[StateVariable]

    @field_validator('coupling_type', mode='before')
    @classmethod
    def legacy_type(cls, value):
        return normalized_coupling(value)

    @model_validator(mode="after")
    def unique_names(self):
        names = [field.name for field in self.unknowns + self.state_variables]
        if len(set(names)) != len(names):
            raise ValueError("Unknown and state-variable names must be distinct.")
        return self
