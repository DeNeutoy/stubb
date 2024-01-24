import inspect
from inspect import isclass
from types import NoneType

from pydantic import BaseModel
from typing import (
    Any,
    Type,
    List,
    get_args,
    get_origin,
    Tuple,
    Union,
    Optional,
    _GenericAlias,
)
from enum import Enum
import re


class PydanticDataType(Enum):
    """
    Defines the data types supported by the grammar_generator.
    Attributes:
        STRING (str): Represents a string data type.
        BOOLEAN (str): Represents a boolean data type.
        INTEGER (str): Represents an integer data type.
        FLOAT (str): Represents a float data type.
        OBJECT (str): Represents an object data type.
        ARRAY (str): Represents an array data type.
        ENUM (str): Represents an enum data type.
        CUSTOM_CLASS (str): Represents a custom class data type.
    """

    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"
    ANY = "any"
    NULL = "null"
    CUSTOM_CLASS = "custom-class"
    CUSTOM_DICT = "custom-dict"
    SET = "set"


def map_pydantic_type_to_gbnf(pydantic_type: Type[Any]) -> str:
    if isclass(pydantic_type) and issubclass(pydantic_type, str):
        return PydanticDataType.STRING.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, bool):
        return PydanticDataType.BOOLEAN.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, int):
        return PydanticDataType.INTEGER.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, float):
        return PydanticDataType.FLOAT.value
    elif isclass(pydantic_type) and issubclass(pydantic_type, Enum):
        return PydanticDataType.ENUM.value

    elif isclass(pydantic_type) and issubclass(pydantic_type, BaseModel):
        return format_model_and_field_name(pydantic_type.__name__)
    elif get_origin(pydantic_type) == list:
        element_type = get_args(pydantic_type)[0]
        return f"{map_pydantic_type_to_gbnf(element_type)}-list"
    elif get_origin(pydantic_type) == set:
        element_type = get_args(pydantic_type)[0]
        return f"{map_pydantic_type_to_gbnf(element_type)}-set"
    elif get_origin(pydantic_type) == Union:
        union_types = get_args(pydantic_type)
        union_rules = [map_pydantic_type_to_gbnf(ut) for ut in union_types]
        return f"union-{'-or-'.join(union_rules)}"
    elif get_origin(pydantic_type) == Optional:
        element_type = get_args(pydantic_type)[0]
        return f"optional-{map_pydantic_type_to_gbnf(element_type)}"
    elif isclass(pydantic_type):
        return f"{PydanticDataType.CUSTOM_CLASS.value}-{format_model_and_field_name(pydantic_type.__name__)}"
    elif get_origin(pydantic_type) == dict:
        key_type, value_type = get_args(pydantic_type)
        return f"custom-dict-key-type-{format_model_and_field_name(map_pydantic_type_to_gbnf(key_type))}-value-type-{format_model_and_field_name(map_pydantic_type_to_gbnf(value_type))}"
    else:
        return "unknown"


def format_model_and_field_name(model_name: str) -> str:
    parts = re.findall("[A-Z][^A-Z]*", model_name)
    if not parts:  # Check if the list is empty
        return model_name.lower().replace("_", "-")
    return "-".join(part.lower().replace("_", "-") for part in parts)


def generate_list_rule(element_type):
    """
    Generate a GBNF rule for a list of a given element type.
    :param element_type: The type of the elements in the list (e.g., 'string').
    :return: A string representing the GBNF rule for a list of the given type.
    """
    rule_name = f"{map_pydantic_type_to_gbnf(element_type)}-list"
    element_rule = map_pydantic_type_to_gbnf(element_type)
    list_rule = rf'{rule_name} ::= "["  {element_rule} (","  {element_rule})* "]"'
    return list_rule


def get_members_structure(cls, rule_name):
    if issubclass(cls, Enum):
        # Handle Enum types
        members = [
            f'"\\"{member.value}\\""' for name, member in cls.__members__.items()
        ]
        return f"{cls.__name__.lower()} ::= " + " | ".join(members)
    if cls.__annotations__ and cls.__annotations__ != {}:
        result = f'{rule_name} ::= "{{"'
        type_list_rules = []
        # Modify this comprehension
        members = [
            f'  "\\"{name}\\"" ":"  {map_pydantic_type_to_gbnf(param_type)}'
            for name, param_type in cls.__annotations__.items()
            if name != "self"
        ]

        result += '"," '.join(members)
        result += '  "}"'
        return result, type_list_rules
    elif rule_name == "custom-class-any":
        result = f"{rule_name} ::= "
        result += "value"
        type_list_rules = []
        return result, type_list_rules
    else:
        init_signature = inspect.signature(cls.__init__)
        parameters = init_signature.parameters
        result = f'{rule_name} ::=  "{{"'
        type_list_rules = []
        # Modify this comprehension too
        members = [
            f'  "\\"{name}\\"" ":"  {map_pydantic_type_to_gbnf(param.annotation)}'
            for name, param in parameters.items()
            if name != "self" and param.annotation != inspect.Parameter.empty
        ]

        result += '", "'.join(members)
        result += '  "}"'
        return result, type_list_rules


def generate_gbnf_rule_for_type(
    model_name,
    field_name,
    field_type,
    is_optional,
    processed_models,
    created_rules,
    field_info=None,
) -> Tuple[str, list]:
    """
    Generate GBNF rule for a given field type.
    :param model_name: Name of the model.
    :param field_name: Name of the field.
    :param field_type: Type of the field.
    :param is_optional: Whether the field is optional.
    :param processed_models: List of processed models.
    :param created_rules: List of created rules.
    :param field_info: Additional information about the field (optional).
    :return: Tuple containing the GBNF type and a list of additional rules.
    :rtype: Tuple[str, list]
    """
    rules = []

    field_name = format_model_and_field_name(field_name)
    gbnf_type = map_pydantic_type_to_gbnf(field_type)

    if isclass(field_type) and issubclass(field_type, BaseModel):
        nested_model_name = format_model_and_field_name(field_type.__name__)
        nested_model_rules = generate_gbnf_grammar(
            field_type, processed_models, created_rules
        )
        rules.extend(nested_model_rules)
        gbnf_type, rules = nested_model_name, rules
    elif isclass(field_type) and issubclass(field_type, Enum):
        enum_values = [
            f'"\\"{e.value}\\""' for e in field_type
        ]  # Adding escaped quotes
        enum_rule = f"{model_name}-{field_name} ::= {' | '.join(enum_values)}"
        rules.append(enum_rule)
        gbnf_type, rules = model_name + "-" + field_name, rules
    elif (get_origin(field_type) == list or field_type == list) or (get_origin(field_type) == set or field_type == set):  # Array
        element_type = get_args(field_type)[0]
        element_rule_name, additional_rules = generate_gbnf_rule_for_type(
            model_name,
            f"{field_name}-element",
            element_type,
            is_optional,
            processed_models,
            created_rules,
        )
        rules.extend(additional_rules)
        array_rule = f"""{model_name}-{field_name} ::= "[" ws {element_rule_name} ("," ws {element_rule_name})*  "]" """
        rules.append(array_rule)
        gbnf_type, rules = model_name + "-" + field_name, rules

    elif gbnf_type.startswith("custom-class-"):
        nested_model_rules, field_types = get_members_structure(field_type, gbnf_type)
        rules.append(nested_model_rules)
    elif gbnf_type.startswith("custom-dict-"):
        key_type, value_type = get_args(field_type)

        additional_key_type, additional_key_rules = generate_gbnf_rule_for_type(
            model_name,
            f"{field_name}-key-type",
            key_type,
            is_optional,
            processed_models,
            created_rules,
        )
        additional_value_type, additional_value_rules = generate_gbnf_rule_for_type(
            model_name,
            f"{field_name}-value-type",
            value_type,
            is_optional,
            processed_models,
            created_rules,
        )
        gbnf_type = rf'{gbnf_type} ::= "{{"  ( {additional_key_type} ":"  {additional_value_type} (","  {additional_key_type} ":"  {additional_value_type})*  )? "}}" '

        rules.extend(additional_key_rules)
        rules.extend(additional_value_rules)
    elif gbnf_type.startswith("union-"):
        union_types = get_args(field_type)
        union_rules = []

        for union_type in union_types:
            if isinstance(union_type, _GenericAlias):
                union_gbnf_type, union_rules_list = generate_gbnf_rule_for_type(
                    model_name,
                    field_name,
                    union_type,
                    False,
                    processed_models,
                    created_rules,
                )
                union_rules.append(union_gbnf_type)
                rules.extend(union_rules_list)

            elif not issubclass(union_type, NoneType):
                union_gbnf_type, union_rules_list = generate_gbnf_rule_for_type(
                    model_name,
                    field_name,
                    union_type,
                    False,
                    processed_models,
                    created_rules,
                )
                union_rules.append(union_gbnf_type)
                rules.extend(union_rules_list)

        # Defining the union grammar rule separately
        if len(union_rules) == 1:
            union_grammar_rule = f"{model_name}-{field_name}-optional ::= {' | '.join(union_rules)} | null"
        else:
            union_grammar_rule = (
                f"{model_name}-{field_name}-union ::= {' | '.join(union_rules)}"
            )
        rules.append(union_grammar_rule)
        if len(union_rules) == 1:
            gbnf_type = f"{model_name}-{field_name}-optional"
        else:
            gbnf_type = f"{model_name}-{field_name}-union"
    elif isclass(field_type) and issubclass(field_type, str):
        gbnf_type = PydanticDataType.STRING.value

    elif isclass(field_type) and issubclass(field_type, float):
        gbnf_type = PydanticDataType.FLOAT.value
    elif isclass(field_type) and issubclass(field_type, int):
        gbnf_type = PydanticDataType.INTEGER.value
    else:
        gbnf_type, rules = gbnf_type, []

    if gbnf_type not in created_rules:
        return gbnf_type, rules
    else:
        if gbnf_type in created_rules:
            return gbnf_type, rules


def generate_gbnf_grammar(
    model: Type[BaseModel], processed_models: set, created_rules: dict
) -> list:
    """
    Generate GBnF Grammar
    Generates a GBnF grammar for a given model.
    :param model: A Pydantic model class to generate the grammar for. Must be a subclass of BaseModel.
    :param processed_models: A set of already processed models to prevent infinite recursion.
    :param created_rules: A dict containing already created rules to prevent duplicates.
    :return: A list of GBnF grammar rules in string format.
    Example Usage:
    ```
    model = MyModel
    processed_models = set()
    created_rules = dict()
    gbnf_grammar = generate_gbnf_grammar(model, processed_models, created_rules)
    ```
    """
    if model in processed_models:
        return []

    processed_models.add(model)
    model_name = format_model_and_field_name(model.__name__)

    if not issubclass(model, BaseModel):
        # For non-Pydantic classes, generate model_fields from __annotations__ or __init__
        if hasattr(model, "__annotations__") and model.__annotations__:
            model_fields = {
                name: (typ, ...) for name, typ in model.__annotations__.items()
            }
        else:
            init_signature = inspect.signature(model.__init__)
            parameters = init_signature.parameters
            model_fields = {
                name: (param.annotation, param.default)
                for name, param in parameters.items()
                if name != "self"
            }
    else:
        # For Pydantic models, use model_fields and check for ellipsis (required fields)
        model_fields = model.__annotations__

    model_rule_parts = []
    nested_rules = []
    for field_name, field_info in model_fields.items():
        if not issubclass(model, BaseModel):
            field_type, default_value = field_info
            # Check if the field is optional (not required)
            is_optional = (default_value is not inspect.Parameter.empty) and (
                default_value is not Ellipsis
            )
        else:
            field_type = field_info
            field_info = model.model_fields[field_name]
            is_optional = (
                field_info.is_required is False and get_origin(field_type) is Optional
            )
        rule_name, additional_rules = generate_gbnf_rule_for_type(
            model_name,
            format_model_and_field_name(field_name),
            field_type,
            is_optional,
            processed_models,
            created_rules,
            field_info,
        )

        if rule_name not in created_rules:
            created_rules[rule_name] = additional_rules
        model_rule_parts.append(
            f' ws "\\"{field_name}\\"" ": "  {rule_name}'
        )  # Adding escaped quotes
        nested_rules.extend(additional_rules)

    fields_joined = r' "," "\n" '.join(model_rule_parts)
    model_rule = rf'{model_name} ::= "{{" "\n" {fields_joined} "\n" ws "}}"'

    all_rules = [model_rule] + nested_rules

    return all_rules


def get_primitive_grammar(grammar):
    """
    Returns the needed GBNF primitive grammar for a given GBNF grammar string.
    Args:
    grammar (str): The string containing the GBNF grammar.
    Returns:
    str: GBNF primitive grammar string.
    """
    type_list = []
    if "string-list" in grammar:
        type_list.append(str)
    if "boolean-list" in grammar:
        type_list.append(bool)
    if "integer-list" in grammar:
        type_list.append(int)
    if "float-list" in grammar:
        type_list.append(float)
    additional_grammar = [generate_list_rule(t) for t in type_list]
    primitive_grammar = r"""
boolean ::= "true" | "false"
null ::= "null"
string ::= "\"" (
        [^"\\] |
        "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
      )* "\"" ws
ws ::= ([ \t\n] ws)?
float ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws
integer ::= [0-9]+"""

    any_block = ""
    if "custom-class-any" in grammar:
        any_block = """
value ::= object | array | string | number | boolean | null
object ::=
  "{" ws (
            string ":" ws value
    ("," ws string ":" ws value)*
  )? "}" ws
array  ::=
  "[" ws (
            value
    ("," ws value)*
  )? "]" ws
number ::= integer | float"""

    return "\n" + "\n".join(additional_grammar) + any_block + primitive_grammar


def remove_empty_lines(string):
    """
    Remove empty lines from a string.
    Args:
    string (str): Input string.
    Returns:
    str: String with empty lines removed.
    """
    lines = string.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    string_no_empty_lines = "\n".join(non_empty_lines)
    return string_no_empty_lines


def generate_gbnf_grammar_from_pydantic_models(
    model: Type[BaseModel],
    list_of_outputs: bool = False,
) -> str:
    """
    Generate GBNF Grammar from Pydantic Models.
    Parameters:
    model (Type[BaseModel]): A Pydantic models to generate the grammar from.
    list_of_outputs (str, optional): Allows a list of output objects
    Returns:
    str: The generated GBNF grammar string.
    """
    model_rules = generate_gbnf_grammar(model, processed_models=set(), created_rules={})


    root_model_name = format_model_and_field_name(model.__name__)
    if list_of_outputs:
        root_rule = (
            r'root ::= ws "["  grammar-models (","  grammar-models)*  "]"' + "\n"
        )
    else:
        root_rule = r"root ::= ws grammar-models" + "\n"
    root_rule += "grammar-models ::= " + root_model_name

    model_rules.insert(0, root_rule)
    final_grammar = "\n".join(model_rules)
    return remove_empty_lines(final_grammar + get_primitive_grammar(final_grammar))
