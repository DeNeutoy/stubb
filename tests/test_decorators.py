
import pytest
import os
from pydantic import BaseModel

import stubb


# Skip if running in githb actions
@pytest.mark.skipif(
    "GITHUB_ACTIONS" in os.environ and os.environ["GITHUB_ACTIONS"] == "true",
    reason="Skipping this test on Github Actions",
)
def test_basic_parsing():

    from llama_cpp.llama import Llama
    class StructuredName(BaseModel):
        """What should I do with this docstring?"""
        city: str
        state_code: str

    llm = Llama("./models/phi-2.Q6_K.gguf", verbose=False)

    @stubb.llm_function(model=llm)
    def my_func2(placename: str) -> StructuredName:
        """Parse the following placename: {placename}"""

    response, parsed_model = my_func2("NYC.")
    assert parsed_model.city == "New York"
    assert parsed_model.state_code == "NY"
