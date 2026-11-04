"""Final material cards and mesh-grounded structural validation."""
from typing import Annotated

from pydantic import Field, model_validator
from common.schema import Record, Text, Number, Vector, Matrix, Region, region_key


class Parameter(Record):
    name: Text
    regions: Annotated[list[Region], Field(min_length=1)]
    value: Number | Vector | Matrix
    unit: str

    @model_validator(mode='after')
    def rectangular(self):
        if isinstance(self.value, list) and self.value and isinstance(self.value[0], list):
            if len({len(row) for row in self.value}) != 1:
                raise ValueError('Material parameter matrices must be rectangular.')
        return self


class MaterialCard(Record):
    constitutive_parameters: list[Parameter]


class MaterialValueInput(Record):
    parameter: Text
    binding: Annotated[int, Field(ge=0)]
    value: Number | Vector | Matrix
    unit: str


def validate_selection(value, summary):
    if not isinstance(value, list):
        raise ValueError('Selected material regions must be a list.')
    known = {region_key(group) for group in summary.get('volume_groups', [])}
    selected = [Region.model_validate(region).model_dump() for region in value]
    for region in selected:
        if region_key(region) not in known:
            raise ValueError('Select a volume Physical Group present in the mesh.')
    return selected


def check_card(value, formulation, summary):
    card = MaterialCard.model_validate(value).model_dump()
    required = {parameter['name'] for parameter in formulation['constitutive_parameters']}
    if {parameter['name'] for parameter in card['constitutive_parameters']} != required:
        raise ValueError('Bind every approved constitutive parameter without adding new names.')
    assigned = set()
    for parameter in card['constitutive_parameters']:
        validate_selection(parameter['regions'], summary)
        for region in parameter['regions']:
            if len(set(region['tags'])) != len(region['tags']):
                raise ValueError('Material region tags must be distinct.')
            for tag in region['tags']:
                key = parameter['name'], tag
                if key in assigned:
                    raise ValueError('Assignments of the same material parameter must not overlap.')
                assigned.add(key)
    return card
