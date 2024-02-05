import inspect
from inspect import isclass
from types import NoneType

from pydantic import BaseModel, TypeAdapter
from typing import (
    Any,
    Type,
    List,
    TypeVar,
    get_args,
    get_origin,
    Tuple,
    Union,
    Optional,
    _GenericAlias,
    Literal,
)
from enum import Enum
import re

from llama_cpp.llama_grammar import SchemaConverter


T = TypeVar("T")

def type_to_grammar(type_: T) -> str:

    if isclass(type_) and issubclass(type_, BaseModel):
        schema = type_.model_json_schema()
    else:
        converted = TypeAdapter(type_)
        schema = converted.json_schema()
    schema_converter = SchemaConverter({})
    schema_converter.visit(schema, "")

    return schema_converter.format_grammar()

