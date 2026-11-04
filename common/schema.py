"""Strict records and physical value/region types shared by authoring agents."""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

Text=Annotated[str,Field(min_length=1)]
Dimension=Annotated[int,Field(gt=0)]

class Record(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

Number=Annotated[float,Field(allow_inf_nan=False)]
Vector=Annotated[list[Number],Field(min_length=1)]
Matrix=Annotated[list[Vector],Field(min_length=1)]


class Region(Record):
    name: Text
    dim: Annotated[int,Field(gt=0)]
    tags: Annotated[list[Annotated[int,Field(gt=0)]],Field(min_length=1)]


Value=Number|Vector|Matrix

def region_key(region):
    return region['name'],region['dim'],tuple(sorted(region['tags']))
