from __future__ import annotations

from stacker.engine.data_type import Symbol
from stacker.error import (
    StackerTypeError,
    not_a_sequence_message,
    symbol_as_value_message,
)
from stacker.operators.arguments import integer_argument
from stacker.util.disp import plain_text


def _sequence(word: str, xs: object) -> object:
    """Returns ``xs`` when it is a list, an array or a string; a dictionary or a scalar is refused by name."""
    if isinstance(xs, dict):
        raise StackerTypeError(not_a_sequence_message(word))
    if isinstance(xs, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, xs.name))
    if not isinstance(xs, (list, tuple, str)):
        raise StackerTypeError(f"`{word}` expects a list, an array or a string, got {plain_text(xs)}")
    return xs


def _car(xs: list | tuple) -> object:
    """Returns the first element of a list."""
    _sequence("car", xs)
    if not xs:
        raise ValueError("car: empty list")
    return xs[0]


def _cdr(xs: list | tuple) -> list:
    """Returns the list without the first element."""
    _sequence("cdr", xs)
    if not xs:
        raise ValueError("cdr: empty list")
    return list(xs[1:])


def _cons(x: object, xs: list) -> list:
    """Prepends x to the list xs."""
    return [x] + list(_sequence("cons", xs))  # type: ignore[arg-type]


def _null(xs: object) -> bool:
    """Returns true if the value is null, and nothing else (an empty list is `empty?`)."""
    return xs is None


def _pair(xs: object) -> bool:
    """Returns true if xs is a non-empty list."""
    return isinstance(xs, (list, tuple)) and len(xs) > 0


list_operators = {
    "seq": {
        "func": (lambda x1, x2: list(range(integer_argument("seq", x1), integer_argument("seq", x2) + 1))),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate sequence from x1 to x2",
    },
    "car": {
        "func": (lambda xs: _car(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the first element of a list.",
    },
    "cdr": {
        "func": (lambda xs: _cdr(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the list without the first element.",
    },
    "cons": {
        "func": (lambda x, xs: _cons(x, xs)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Prepends x to the list xs.",
    },
    "null?": {
        "func": (lambda xs: _null(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is null (an empty list is not null: see empty?)",
    },
    "pair?": {
        "func": (lambda xs: _pair(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if xs is a non-empty list.",
    },
}
