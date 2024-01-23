from pydantic import BaseModel
from llama_cpp import Llama
from llama_cpp.llama_grammar import LlamaGrammar, json_schema_to_gbnf
from typing import TypeVar
import json


T = TypeVar("T", bound=BaseModel)


def generate(model: Llama, prompt: str, return_type: T, **kwargs) -> T:
    """Generate a new example from a prompt.

    Args:
        model (Llama): The model to use for generation.
        prompt (str): The prompt to generate from.
        return_type (T): The type of the return value.
        **kwargs: Additional arguments to pass to the model.

    Returns:
        T: The generated pydantic model.
    """

    if "grammar" in kwargs:
        raise ValueError("Cannot pass grammar to generate")

    schema = return_type.model_json_schema()
    schema_str = json.dumps(schema)

    gbnf = json_schema_to_gbnf(schema_str)

    grammar = LlamaGrammar.from_string(gbnf)
    result = model(prompt, grammar=grammar, max_tokens=-1, **kwargs)

    resp = result["choices"][0]["text"]
    return return_type.model_validate_json(resp)
