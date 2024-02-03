from pydantic import BaseModel
from typing import List, Optional, Literal, Dict


from stubb.parser import type_to_grammar


def test_pydantic_model_generation():

    # Basic 
    class Response(BaseModel):
        code: int
        message: str

    class Composed(BaseModel):
        response: Response
        id: int

    class Inherited(Response):
        id: int

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
    ]:
        grammar = type_to_grammar(model)
        print(grammar)
        assert grammar is not None

def test_python_types():

    list_type = List[str]
    literal = Literal["a", "b", "c"]
    optional = Optional[str]
    list_optional = List[Optional[str]]

    for type_ in [list_type, literal, optional, list_optional]:
        grammar = type_to_grammar(type_)
        print(grammar)
        assert grammar is not None

def test_raise_on_dict_type():
    dict_type = Dict[str, int]
    try:
        grammar = type_to_grammar(dict_type)
    except AssertionError:
        assert True
    else:
        assert False
