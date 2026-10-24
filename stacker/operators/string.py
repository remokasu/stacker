from __future__ import annotations

import codecs
import string

from stacker.engine.data_type import Symbol
from stacker.error import (
    StackerIndexError,
    StackerRuntimeError,
    StackerTypeError,
    ValidationError,
    symbol_as_value_message,
)
from stacker.operators.arguments import byte_values, integer_argument
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
    for _literal, field, _spec, _conversion in string.Formatter().parse(text):
        if field is not None and not (field == "" or field.isdigit()):
            raise StackerTypeError(
                f"`format` fields are `{{}}` or `{{0}}` with a format spec (`{{:.2f}}`); {{{field}}} reaches into the value"
            )
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
    if isinstance(container, Symbol):
        raise StackerTypeError(symbol_as_value_message("contains", container.name))
    if not isinstance(container, (str, list, tuple)):
        raise StackerTypeError(f"`contains` expects a string, a list or an array to look through, got {plain_text(container)}")
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



def _subseq(value: object, start: object, end: object) -> str:
    """``s a b subseq``: the characters of ``s`` from ``a`` up to ``b``, as `slice` cuts a string."""
    text = _require_str("subseq", value)
    return text[integer_argument("subseq", start) : integer_argument("subseq", end)]


def _words(value: object) -> list[str]:
    """``s words``: the whitespace-separated words of ``s``, none of them empty."""
    return _require_str("words", value).split()


def _starts_with(value: object, prefix: object) -> bool:
    """``s p starts-with?``: whether ``s`` begins with ``p``."""
    return _require_str("starts-with?", value).startswith(_require_str("starts-with?", prefix))


def _ends_with(value: object, suffix: object) -> bool:
    """``s p ends-with?``: whether ``s`` ends with ``p``."""
    return _require_str("ends-with?", value).endswith(_require_str("ends-with?", suffix))


def _codec(word: str, encoding: object) -> str:
    """Returns ``encoding`` when it names a text encoding the host knows."""
    name = _require_str(word, encoding)
    try:
        codecs.lookup(name)
    except LookupError as error:
        raise StackerTypeError(f"`{word}` does not know the encoding {plain_text(name)}") from error
    return name


def _encode(value: object, encoding: object) -> list[int]:
    """``s encoding encode``: the bytes of ``s`` in ``encoding``, as a list of integers 0 to 255."""
    text = _require_str("encode", value)
    codec = _codec("encode", encoding)
    try:
        return list(text.encode(codec))
    except UnicodeEncodeError as error:
        raise StackerRuntimeError(f"`encode` cannot write {plain_text(text)} as {codec}: {error.reason}") from error


def _decode(value: object, encoding: object) -> str:
    """``bytes encoding decode``: the text the bytes spell in ``encoding``."""
    codec = _codec("decode", encoding)
    content = byte_values("decode", value)
    try:
        return content.decode(codec)
    except UnicodeDecodeError as error:
        raise StackerRuntimeError(f"`decode` cannot read the bytes as {codec}: {error.reason}") from error



def _concat(a: object, b: object) -> object:
    """``a b concat``: two strings, or two lists, joined; anything else is refused by name."""
    for value in (a, b):
        if isinstance(value, Symbol):
            raise StackerTypeError(symbol_as_value_message("concat", value.name))
    if isinstance(a, str) and isinstance(b, str):
        return a + b
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    raise StackerTypeError(f"`concat` expects two strings or two lists, got {plain_text(a)} and {plain_text(b)}")


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
        "func": _concat,
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
        "func": _subseq,
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "s a b subseq: the characters of s from index a up to (not including) b; the string form of slice",
    },
    "words": {
        "func": _words,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Splits a string at whitespace into a list of its words (no empty strings)",
    },
    "starts-with?": {
        "func": _starts_with,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "s p starts-with?: whether s begins with p",
    },
    "ends-with?": {
        "func": _ends_with,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "s p ends-with?: whether s ends with p",
    },
    "encode": {
        "func": _encode,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "s encoding encode: the bytes of a string in an encoding (\"utf-8\", \"latin-1\", ...), as a list of integers 0 to 255",
    },
    "decode": {
        "func": _decode,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "bytes encoding decode: the string a list or an array of bytes spells in an encoding",
    },
    "format": {
        "func": _format,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Formats the specified string using the specified arguments.",
    },
}
