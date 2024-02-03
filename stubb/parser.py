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
    Dict,
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


if __name__ == "__main__":


    class Response(BaseModel):
        code: Union[int, str]
        message: str


    class Composed(BaseModel):
        response: Union[Response, List[Response]]
        id: int


    class Inherited(Response):
        id: int
        f: float


    class ListType(BaseModel):
        l: List[int]


    class ListResponse(BaseModel):
        l: List[Response]


    class LiteralType(BaseModel):
        l: Literal["a", "b", "c"]


    class OptionalType(BaseModel):
        l: Optional[int] = None


    for model in [
        Response,
        Composed,
        Inherited,
        ListType,
        ListResponse,
        LiteralType,
        OptionalType,
        List[str],
        List[List[str]],
        List[Optional[str]],
        List[Optional[Response]],
        Optional[Response],
        Union[Response, List[Response]],
    ]:
        grammar = type_to_grammar(model)
        print("Grammar for model: ", model)
        print(grammar)
        print()
        print()
        assert grammar is not None