"""Closed, required object fields owned by the server rather than repeated by models."""
from pydantic import Field, create_model
from .schema import Record


def generation_schema(value):
    """Keep structural constraints portable; validate array lengths in Python.

    Repeated, bounded arrays can exceed provider grammar limits. This projection
    preserves closed properties, required fields, item types, and allowed values.
    It never changes the Pydantic model used to accept the response.
    """
    if isinstance(value,dict):
        return {key:generation_schema(child) for key,child in value.items()
            if not (value.get('type')=='array' and key in ('minItems','maxItems'))}
    if isinstance(value,list):return [generation_schema(child) for child in value]
    return value


def named_record(label, fields, description=None):
    """Use aliases so physical identifiers and dotted targets stay exact JSON keys."""
    fields=list(fields)
    names=[name for name,_ in fields]
    if len(names)!=len(set(names)):
        raise ValueError('Contract field names must be unique.')
    result=create_model(label,__base__=Record,__doc__=description,
        **{f'item_{i}':(annotation,Field(alias=name)) for i,(name,annotation) in enumerate(fields)})
    if not fields:result.model_config['json_schema_extra']={'required':[]}
    return result
