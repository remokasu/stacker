from __future__ import annotations

from stacker.engine.data_type import Symbol
from stacker.error import (
    StackerIndexError,
    StackerRuntimeError,
    StackerTypeError,
    ValidationError,
    symbol_as_value_message,
)
from stacker.util.disp import plain_text

#: The largest code point `chr` makes
CODE_POINT_MAX = 0x10FFFF


def _require_str(word: str, value: object, what: str = "a string") -> str:
    """Returns ``value`` when it is a string; otherwise raises an error naming the word.

    Args:
        word: The word checking its argument.
        value: The argument.
        what: What the word expects there, for the message.

    Returns:
        The string.

    Raises:
        StackerTypeError: ``value`` is not a string. A symbol gets the
            message every word gives a symbol used as a value.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, value.name))
    raise StackerTypeError(f"`{word}` expects {what}, got {plain_text(value)}")


def _search(text: object, part: object) -> int:
    """``s part search``: the index of ``part`` in ``s``, or -1.

    Returns:
        The index of the first occurrence, or -1.
    """
    return _require_str("search", text, "a string to search in").find(
        _require_str("search", part, "a string to search for")
    )


def _replace(text: object, old: object, new: object) -> str:
    """``s old new replace``: ``s`` with every ``old`` replaced by ``new``.

    Returns:
        The replaced string.
    """
    return _require_str("replace", text).replace(
        _require_str("replace", old, "a string to replace"),
        _require_str("replace", new, "a replacement string"),
    )


def _format(template: object, value: object) -> str:
    """``template value format``: the template with ``value`` filled in.

    Returns:
        The formatted string.
    """
    text = _require_str("format", template, "a format string")
    try:
        return text.format(_format_value(value))
    except (IndexError, KeyError) as error:
        raise StackerIndexError(
            f"`format` fills one value into the template, but {plain_text(template)} asks for more"
        ) from error


def _asc(value: object) -> int:
    """``c asc``: the code point of a one-character string."""
    text = _require_str("asc", value, "a string of one character")
    if len(text) != 1:
        raise StackerTypeError(f"`asc` expects a string of one character, got {plain_text(value)}")
    return ord(text)


def _chr(value: object) -> str:
    """``n chr``: the character with code point ``n``."""
    if isinstance(value, Symbol):
        raise StackerTypeError(symbol_as_value_message("chr", value.name))
    if not isinstance(value, int):
        raise StackerTypeError(f"`chr` expects an integer from 0 to {CODE_POINT_MAX}, got {plain_text(value)}")
    if not 0 <= value <= CODE_POINT_MAX:
        raise ValidationError(f"`chr` expects an integer from 0 to {CODE_POINT_MAX}, got {value}")
    return chr(value)


def _join(parts: object, sep: object) -> str:
    """``list sep join``: the strings of ``parts`` joined by ``sep``.

    Returns:
        The joined string.
    """
    sep = _require_str("join", sep, "a separator string")
    if isinstance(parts, Symbol):
        raise StackerTypeError(symbol_as_value_message("join", parts.name))
    if not isinstance(parts, (list, tuple)):
        raise StackerTypeError(f"`join` expects a list of strings, got {plain_text(parts)}")
    for part in parts:
        if isinstance(part, Symbol):
            raise StackerTypeError(symbol_as_value_message("join", part.name))
        if not isinstance(part, str):
            raise StackerTypeError(
                f"`join` expects a list of strings, got {plain_text(parts)}. "
                "Make the elements strings first: {str} map"
            )
    return sep.join(parts)


def _contains(container: object, value: object) -> bool:
    """``c v contains``: whether a string or a sequence holds ``v``."""
    if isinstance(container, dict):
        raise StackerTypeError("`contains` cannot look through a dictionary; ask for a key with `has?`, or look through its keys")
    try:
        return value in container  # type: ignore[operator]
    except RecursionError:
        raise StackerRuntimeError(
            "`contains` cannot compare arrays or dictionaries nested this deep or containing themselves"
        ) from None


def _format_value(value: object) -> object:
    """The value handed to ``str.format``: numbers and strings as they are, the rest as text.

    A number keeps its type so a format spec such as ``{:.2f}`` works;
    ``true``, ``null``, a symbol or a list is written in Stacker's notation.

    Returns:
        The value, or its display text.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, complex, str)):
        return plain_text(value)
    return value


# def _contains(value1: str, value2: str) -> bool:
#     """Returns whether the first string contains the second string."""
#     return value2 in value1


# def _endswith(value1: str, value2: str) -> bool:
#     """Returns whether the first string ends with the second string."""
#     return value1.endswith(value2)


# def _startswith(value1: str, value2: str) -> bool:
#     """Returns whether the first string starts with the second string."""
#     return value1.startswith(value2)


# def _find(value1: str, value2: str) -> int:
#     """Returns the index of the first occurrence of the second string in the first string."""
#     return value1.find(value2)


# def _join(value1: str, value2: str) -> str:
#     """Concatenate two strings."""
#     return value1.join(value2)


string_operators = {
    "asc": {
        "func": _asc,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the ASCII value of the specified character.",
    },
    "chr": {
        "func": _chr,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the character that matches the specified ASCII value.",
    },
    "concat": {
        "func": (lambda value1, value2: value1 + value2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Concatenate two strings.",
    },
    "search": {
        "func": _search,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns the index of the first occurrence of the second string in the first string.",
    },
    "replace": {
        "func": _replace,
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Replaces all occurrences of the second string with the third string in the first string.",
    },
    "lower": {
        "func": (lambda value: _require_str("lower", value).lower()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to lowercase.",
    },
    "upper": {
        "func": (lambda value: _require_str("upper", value).upper()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to uppercase.",
    },
    "title": {
        "func": (lambda value: _require_str("title", value).title()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to title case.",
    },
    "strip": {
        "func": (lambda value: _require_str("strip", value).strip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes leading and trailing whitespace from the specified string.",
    },
    "lstrip": {
        "func": (lambda value: _require_str("lstrip", value).lstrip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes leading whitespace from the specified string.",
    },
    "rstrip": {
        "func": (lambda value: _require_str("rstrip", value).rstrip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes trailing whitespace from the specified string.",
    },
    # "split": {
    #     "func": (lambda value1, value2: value1.split(value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Splits the specified string into a list of substrings using the specified delimiter.",
    # },
    "join": {
        "func": _join,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Concatenates the elements of the specified list using the specified delimiter.",
    },
    # "len": {
    #     "func": (lambda value: len(value)),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "Returns the length of the specified string.",
    # },
    "contains": {
        "func": (lambda value1, value2: _contains(value1, value2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns whether the first string contains the second string.",
    },
    "subseq": {
        "func": (lambda value: value.split()[0]),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns a substring of the specified string.",
    },
    "format": {
        "func": _format,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Formats the specified string using the specified arguments.",
    },
}
