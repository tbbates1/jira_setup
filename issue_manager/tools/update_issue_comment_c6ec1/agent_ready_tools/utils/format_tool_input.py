import ast
from enum import Enum
import json
from typing import Any, List, Type, TypeVar, Union

from agent_ready_tools.clients.error_handling import ErrorDetails

T = TypeVar("T", bound=Enum)


def string_to_list_of_strings(input_string: Union[str, list, None]) -> List[str]:
    """
    Convert various string formats to list of strings.

    Supports:
        - JSON arrays: '["foo", "bar"]'
        - Python lists: "['foo', 'bar']"
        - Comma-separated: "foo, bar"
        - Single values: "foo"

    Args:
        input_string: String, list, or None to convert

    Returns:
        List of strings

    Raises:
        TypeError: If input is not str, list, or None

    Examples:
        >>> string_to_list_of_strings("['foo', 'bar']")
        ['foo', 'bar']
        >>> string_to_list_of_strings("foo,bar")
        ['foo', 'bar']
    """

    # Handle None and empty
    if not input_string:
        return []

    # Handle list input
    if isinstance(input_string, list):
        return [str(item) for item in input_string]

    # Type validation
    if not isinstance(input_string, str):
        raise TypeError(f"Expected str, got {type(input_string).__name__}")

    input_string = input_string.strip()
    if not input_string:
        return []

    # Try parsing list-like strings
    if input_string.startswith("[") and input_string.endswith("]"):
        # Try JSON first (fastest and most reliable)
        try:
            result = json.loads(input_string)
            if isinstance(result, list):
                return [str(item) for item in result]
        except json.JSONDecodeError:
            pass

        # Try ast.literal_eval (handles Python syntax)
        try:
            result = ast.literal_eval(input_string)
            if isinstance(result, list):
                return [str(item) for item in result]
        except (ValueError, SyntaxError):
            pass

        # Fallback: simple manual parsing for edge cases
        content = input_string[1:-1].strip()
        if not content:
            return []

        # Split by comma and clean up quotes
        items = []
        for item in content.split(","):
            item = item.strip()
            # Remove surrounding quotes (single or double)
            if len(item) >= 2 and item[0] in ('"', "'") and item[-1] == item[0]:
                item = item[1:-1]
            if item:
                items.append(item)

        return items

    # Comma-separated values (simple split)
    if "," in input_string:
        return [s.strip() for s in input_string.split(",") if s.strip()]

    # Single value
    return [input_string]


def string_to_list_of_enums(input_string: str, enum_class: Type[T]) -> List[T]:
    """
    Some tools take a string from an LLM output which can have two formats:

    1) "foo"
    2) "['foo', 'bar', 'baz']"

    Convert this input to a list of enums.

    Args:
        input_string: "['foo', 'bar', 'baz']" or "foo"
        enum_class: the enum class to convert to

    Returns:
        A python list of enums, i.e. [MyClass.foo, MyClass.bar, MyClass.baz] or [MyClass.foo]
    """
    # TODO: Handle possibility that LLM hallucainates a non Enum string, add backoff logic to recover from KeyError.
    return [enum_class[s] for s in string_to_list_of_strings(input_string)]


def string_to_list_of_ints(value: Union[str, list[int]]) -> Union[list[int], ErrorDetails]:
    """
    Convert a comma-separated string or list to a list of integers.

    Args:
        value: A string (e.g. "1,2,3") or list of ints.

    Returns:
        A list of integers parsed from the input, or ErrorDetails if parsing fails.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list) and all(isinstance(i, int) for i in parsed):
                return parsed
            elif isinstance(parsed, int):
                return [parsed]
        except json.JSONDecodeError:
            pass

        if value.strip().isdigit():
            return [int(value.strip())]

        # Parse comma-separated integers
        result = []
        for v in value.split(","):
            v = v.strip()
            if not v:
                continue
            if not v.lstrip("-").isdigit():
                return ErrorDetails(
                    status_code=None,
                    url=None,
                    reason=f"Invalid integer value: '{v}' in input '{value}'",
                    details=f"Expected a valid integer or comma-separated list of integers, but received '{value}'. The value '{v}' cannot be converted to an integer.",
                    recommendation="Please provide valid integer values. Examples: '123', '1,2,3', or '[1, 2, 3]'.",
                )
            result.append(int(v))
        return result

    raise ValueError("Invalid input type for string_to_list_of_ints")


def string_to_boolean(value: str) -> bool:
    """
    Convert a string to a boolean.

    Args:
        value: A string (e.g. "true" or "false").

    Returns:
        A boolean parsed from the input.
    """

    if isinstance(value, str):
        value = value.strip().lower()
        if value == "true":
            return True
        elif value == "false":
            return False
    return False


def is_empty_value(value: Any) -> bool:
    """
    Checks whether the given value is empty.

    Args:
        value: The value to check. Can be of any type.

    Returns:
        True if the value is None, null, an empty string, an empty list, or an empty dictionary; False otherwise.
    """
    return value in (None, "null", "", [], {})


def truncate_str(s: str | None, limit: int) -> str | None:
    """
    Truncate a string to a maximum length.

    If the input string `s` is longer than `limit`, returns the first `limit` characters, otherwise returns `s` unchanged.

    Args:
        s (str | None): Input string, or None.
        limit (int): Maximum allowed length for the returned string.

    Returns:
        str | None: Truncated string (or original string if no truncation), or None if input was None.
    """
    if s is None:
        return None
    if len(s) <= limit:
        return s
    return s[:limit]
