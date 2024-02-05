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

    @stubb.llm_function
    def my_func2(placename: str) -> StructuredName:
        """Parse the following placename: {placename} into the city name (NOT abbreviated) and 2 letter state code."""

    response, parsed_model = my_func2("New York baybeeee")
    print(response, parsed_model)
    assert parsed_model.city == "New York"
    assert parsed_model.state_code == "NY"


def test_llm_function_requires_type():
    @stubb.llm_function
    def my_func2(placename: str) -> None:
        """Test"""

    @stubb.llm_function
    def my_func3(placename: str):
        """Test"""

    with pytest.raises(ValueError):
        my_func2("test")

    with pytest.raises(ValueError):
        my_func3("test")


