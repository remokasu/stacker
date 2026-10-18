"""Arrays and dictionaries: values that are changed in place.

The words here take their arguments as they are (a code block is stored,
not evaluated), like ``set`` and ``nth``. A word that changes its
container ends in ``!`` and pushes nothing (``pop!`` pushes what it took).
"""

from __future__ import annotations

from stacker.engine.boundary import token_to_value
from stacker.engine.data_type import VOID, Array, String, Symbol
from stacker.error import (
    KeyNotFoundError,
    StackerIndexError,
    StackerTypeError,
    ValidationError,
    symbol_as_value_message,
)
from stacker.operators.arguments import integer_argument
from stacker.util.disp import plain_text


def _is_block(value: object) -> bool:
    from stacker.engine.core import StackerCore

    return isinstance(value, StackerCore)


def _require_array(word: str, value: object) -> Array:
    """Returns ``value`` when it is an array; otherwise raises an error that names the word."""
    if isinstance(value, Array):
        return value
    if isinstance(value, list):
        raise StackerTypeError(f"`{word}` cannot change a list; make an array first: [1 2 3] array")
    if isinstance(value, dict):
        raise StackerTypeError(f"`{word}` expects an array, got {plain_text(value)}; change a dictionary with `put!`")
    raise StackerTypeError(f"`{word}` expects an array, got {plain_text(value)}")


def _require_dict(word: str, value: object) -> dict[object, object]:
    """Returns ``value`` when it is a dictionary; otherwise raises an error that names the word."""
    if isinstance(value, dict):
        return value
    if isinstance(value, Array):
        raise StackerTypeError(f"`{word}` expects a dictionary, got {plain_text(value)}; read an array with `at`")
    raise StackerTypeError(f"`{word}` expects a dictionary, got {plain_text(value)}")


def _is_nan(number: complex) -> bool:
    """Whether ``number`` is nan, which never equals itself and so could never be looked up."""
    return isinstance(number, (float, complex)) and number != number  # noqa: PLR0124


def _require_key(word: str, key: object) -> object:
    """Returns ``key`` when it can be a dictionary key: a string, a number or a symbol."""
    if isinstance(key, Symbol):
        return key
    if isinstance(key, str):
        return str(key)  # a String literal and a computed string are one key
    if isinstance(key, (int, float, complex)) and not isinstance(key, bool) and not _is_nan(key):
        return key
    raise StackerTypeError(
        f"`{word}` cannot use {plain_text(key)} as a key: a key is a string, a number or a symbol"
    )


def _require_index(word: str, index: object) -> int:
    """Returns ``index`` when it is an integer."""
    if isinstance(index, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, index.name))
    if isinstance(index, bool) or not isinstance(index, int):
        raise StackerTypeError(f"`{word}` expects an integer index, got {plain_text(index)}")
    return index


def _array(source: object) -> Array:
    """``xs array``: a new array holding the elements of a list, an array, a string or a block (one level)."""
    if isinstance(source, Symbol):
        raise StackerTypeError(symbol_as_value_message("array", source.name))
    if isinstance(source, dict):
        raise StackerTypeError(f"`array` expects a list, a string or a block, got {plain_text(source)}")
    if isinstance(source, (list, tuple)):
        return Array(source)
    if isinstance(source, str):
        return Array(String(ch) for ch in source)
    if _is_block(source):
        return Array(token_to_value(token) for token in source.tokens)  # type: ignore[attr-defined]
    raise StackerTypeError(f"`array` expects a list, a string or a block, got {plain_text(source)}")


def _array_of(count: object, fill: object) -> Array:
    """``n x array-of``: a new array of ``n`` slots that all hold ``x``."""
    if isinstance(count, Symbol):
        raise StackerTypeError(symbol_as_value_message("array-of", count.name))
    if isinstance(count, bool) or not isinstance(count, int):
        raise StackerTypeError(f"`array-of` expects a count of 0 or more, got {plain_text(count)}")
    if count < 0:
        raise ValidationError(f"`array-of` expects a count of 0 or more, got {count}")
    if isinstance(fill, (Array, dict)):
        raise StackerTypeError(
            "`array-of` would put the same array or dictionary in every slot; "
            "make each one: 0 2 seq {drop 3 0 array-of} map array"
        )
    try:
        return Array([fill] * count)
    except (OverflowError, MemoryError):
        raise ValidationError(f"`array-of` cannot make an array of {count} slots") from None


def _itself(value: object) -> object:
    return value


def _slice(container: object, start: object, end: object) -> object:
    """``xs a b slice``: elements ``a`` up to ``b`` of a list, an array or a string, as a new value of the same kind.

    Negative indexes count from the end and an index past either end is
    cut to it, so the result is never an error for a sequence.
    """
    a = integer_argument("slice", start)
    b = integer_argument("slice", end)
    if isinstance(container, Symbol):
        raise StackerTypeError(symbol_as_value_message("slice", container.name))
    if isinstance(container, Array):
        return Array(container[a:b])
    if isinstance(container, (str, list)):
        return container[a:b]
    raise StackerTypeError(f"`slice` expects a list, an array or a string, got {plain_text(container)}")


def _at(container: object, index: object) -> object:
    """``c i at``: element ``i`` of an array, a list, a string or a block; the container is taken off."""
    i = _require_index("at", index)
    if isinstance(container, Symbol):
        raise StackerTypeError(symbol_as_value_message("at", container.name))
    if isinstance(container, dict):
        raise StackerTypeError(f"`at` expects an array, a list, a string or a block, got {plain_text(container)}; read a dictionary with `get`")
    if _is_block(container):
        items: object = container.tokens  # type: ignore[attr-defined]
        pick = token_to_value
    elif isinstance(container, str):
        items = container
        pick = String
    elif isinstance(container, (list, tuple)):
        items = container
        pick = _itself
    else:
        raise StackerTypeError(f"`at` expects an array, a list, a string or a block, got {plain_text(container)}")
    try:
        return pick(items[i])  # type: ignore[index]
    except IndexError:
        raise StackerIndexError(f"`at` index {i} is out of range for a length of {len(items)}") from None  # type: ignore[arg-type]


def _at_bang(value: object, array: object, index: object) -> object:
    """``v a i at!``: stores ``v`` at index ``i`` of an array."""
    a = _require_array("at!", array)
    i = _require_index("at!", index)
    try:
        a[i] = value
    except IndexError:
        raise StackerIndexError(f"`at!` index {i} is out of range for an array of length {len(a)}") from None
    return VOID


def _append_bang(value: object, array: object) -> object:
    """``v a append!``: adds ``v`` at the end of an array."""
    _require_array("append!", array).append(value)
    return VOID


def _pop_bang(array: object) -> object:
    """``a pop!``: takes the last element off an array and pushes it."""
    a = _require_array("pop!", array)
    if not a:
        raise StackerIndexError("`pop!` cannot take from an empty array")
    return a.pop()


def _get(dictionary: object, key: object) -> object:
    """``d k get``: the value of key ``k``, or null when the key is not there."""
    return _require_dict("get", dictionary).get(_require_key("get", key))


def _put_bang(value: object, dictionary: object, key: object) -> object:
    """``v d k put!``: stores ``v`` under key ``k``."""
    _require_dict("put!", dictionary)[_require_key("put!", key)] = value
    return VOID


def _has(dictionary: object, key: object) -> bool:
    """``d k has?``: whether the dictionary has key ``k``."""
    return _require_key("has?", key) in _require_dict("has?", dictionary)


def _del_bang(dictionary: object, key: object) -> object:
    """``d k del!``: removes key ``k``."""
    d = _require_dict("del!", dictionary)
    k = _require_key("del!", key)
    if k not in d:
        raise KeyNotFoundError(f"`del!` found no key {plain_text(key)} in the dictionary")
    del d[k]
    return VOID


def _keys(dictionary: object) -> list[object]:
    """``d keys``: the keys as a list, in the order they were added."""
    return list(_require_dict("keys", dictionary).keys())


def _values(dictionary: object) -> list[object]:
    """``d values``: the values as a list, in the order their keys were added."""
    return list(_require_dict("values", dictionary).values())


collection_operators = {
    "array": {
        "func": _array,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Makes an array, a list that can be changed in place, from a list, a string or a block: [1 2 3] array",
    },
    "slice": {
        "func": _slice,
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "xs a b slice: the elements of a list, an array or a string from index a up to (not including) b, as a new value of the same kind; negative indexes count from the end",
    },
    "array-of": {
        "func": _array_of,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Makes an array of n slots that all hold x: 5 0 array-of -> [0 0 0 0 0]",
    },
    "at": {
        "func": _at,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Pushes element i of an array, a list, a string or a block, taking the container off: [10 20 30] 1 at -> 20",
    },
    "at!": {
        "func": _at_bang,
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Stores v at index i of an array: v a i at!",
    },
    "append!": {
        "func": _append_bang,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Adds v at the end of an array: v a append!",
    },
    "pop!": {
        "func": _pop_bang,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Takes the last element off an array and pushes it: a pop!",
    },
    "dict": {
        "func": dict,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Makes an empty dictionary: dict",
    },
    "get": {
        "func": _get,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Pushes the value of key k in a dictionary, or null when k is not there: d k get",
    },
    "put!": {
        "func": _put_bang,
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Stores v under key k in a dictionary: v d k put!",
    },
    "has?": {
        "func": _has,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns true if a dictionary has key k: d k has?",
    },
    "del!": {
        "func": _del_bang,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Removes key k from a dictionary: d k del!",
    },
    "keys": {
        "func": _keys,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Pushes the keys of a dictionary as a list, in the order they were added: d keys",
    },
    "values": {
        "func": _values,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Pushes the values of a dictionary as a list, in the order their keys were added: d values",
    },
}
