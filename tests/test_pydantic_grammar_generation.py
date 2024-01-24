from pydantic import BaseModel
from typing import List, Optional, Literal


from stubb.parser import generate_gbnf_grammar_from_pydantic_models


def test_pydantic_model_generation():
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
        grammar = generate_gbnf_grammar_from_pydantic_models(model)
        print(grammar)
        assert grammar is not None
