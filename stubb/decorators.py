from typing import Callable, Optional, Dict, Any
from typing import ParamSpec, TypeVar

import inspect
from functools import wraps
from stubb.parser import generate_gbnf_grammar_from_pydantic_models
from llama_cpp.llama_grammar import LlamaGrammar


T = TypeVar("T")
P = ParamSpec("P")

"""
TODO:
- default llama model creation functions
- actually call models
- append docstring to prompt 
- be able to generate lists and dicts also.
- Throw errors if functions have no return type.

"""


def llm_function(
    func_: Callable = None,
    *,
    model_kwargs: Optional[Dict[str, Any]] = None,
    model_fn: Optional[Callable] = None,
    model=None,
):
    """Decorator for conformable functions.

    Usage:

    @function
    def my_func(a: int, b: int) -> int:
        return "hi"

    alternatively, if you would like the functions to type check, you can define the return type
    in the function arguments, using the `return_type` keyword argument:

    @function(model_kwargs={"max_tokens": -1})
    def my_func(a: int, b: int, return_type: int):
        return "hi"
    """

    def function_wrapper(func: Callable[P, T]) -> Callable[P, T]:
        signature = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Pair the arguments with the signature
            with_args = signature.bind(*args, **kwargs)
            # get the return value if any
            return_type = signature.return_annotation
            with_args.apply_defaults()

            # Get the docstring and format it with the arguments
            doc = inspect.getdoc(func)
            if doc is not None:
                # This with_args has the default values applied
                doc = doc.format(**with_args.arguments)

            # If the user passed in a return_type argument, use that instead
            if "return_type" in with_args.arguments:
                return_type = with_args.arguments["return_type"]

            return_value = func(**with_args.arguments)
            print("return type: ", return_type)
            print("return value: ", return_value)

            resp = None
            parsed = None
            if model:
                grammar_str = generate_gbnf_grammar_from_pydantic_models([return_type])
                grammar = LlamaGrammar.from_string(grammar_str)
                resp = model(doc, grammar=grammar, max_tokens=-1)
                json_output = resp['choices'][0]['text']
                json_output = json_output.replace("\n", "")
                parsed = return_type.model_validate_json(resp['choices'][0]['text'])

            return resp, parsed

        return wrapper

    if func_ is None:
        return function_wrapper
    else:
        return function_wrapper(func_)


if __name__ == "__main__":
    from llama_cpp.llama import Llama, LlamaGrammar

    from pydantic import BaseModel


    class StructuredName(BaseModel):
        """What should I do with this docstring?"""
        city: str
        state_code: str

    llm = Llama("../models/phi-2.Q6_K.gguf")

    @llm_function(model_kwargs={"max_tokens": -1})
    def my_func(a: int, b: int, c: str = "hi") -> int:
        """docstring {c}"""

    @llm_function(model=llm)
    def my_func2(placename: str) -> StructuredName:
        """Parse the following placename: {placename}"""

    response, parsed_model = my_func2("NYC.")

    print(response)
    print(parsed_model)