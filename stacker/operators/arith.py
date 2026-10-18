from __future__ import annotations

from collections.abc import Callable

from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, symbol_as_value_message
from stacker.util.disp import plain_text


def checked_binary(word: str, operate: Callable[[object, object], object]) -> Callable[[object, object], object]:
    """Wraps a binary arithmetic word so a type error names the word and shows both values."""

    def apply(x1: object, x2: object) -> object:
        try:
            return operate(x1, x2)
        except TypeError as error:
            for value in (x1, x2):
                if isinstance(value, Symbol):
                    raise StackerTypeError(symbol_as_value_message(word, value.name)) from error
            advice = ""
            if word == "+" and (isinstance(x1, str) or isinstance(x2, str)):
                advice = "; to join text, make both values strings with `str`"
            raise StackerTypeError(
                f"`{word}` cannot use {plain_text(x1)} and {plain_text(x2)} together{advice}"
            ) from error

    return apply


arith_operators = {
    "+": {
        "func": (lambda x1, x2: x1 + x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Add",
    },
    "-": {
        "func": (lambda x1, x2: x1 - x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Subtract",
    },
    "*": {
        "func": (lambda x1, x2: x1 * x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Multiply",
    },
    "//": {
        "func": (lambda x1, x2: x1 // x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Integer divide",
    },
    "/": {
        "func": (lambda x1, x2: x1 / x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Divide",
    },
    "%": {
        "func": (lambda x1, x2: x1 % x2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Mod",
    },
    "++": {
        "func": (lambda x: x + 1),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Increment",
    },
    "--": {
        "func": (lambda x: x - 1),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Decrement",
    },
}

def checked_unary(word: str, operate: Callable[[object], object]) -> Callable[[object], object]:
    """Wraps a one-argument arithmetic word so a type error names the word and shows the value."""

    def apply(x: object) -> object:
        try:
            return operate(x)
        except TypeError as error:
            if isinstance(x, Symbol):
                raise StackerTypeError(symbol_as_value_message(word, x.name)) from error
            raise StackerTypeError(f"`{word}` expects a number, got {plain_text(x)}") from error

    return apply


for _name, _definition in arith_operators.items():
    if _definition["arg_count"] == 2:
        _definition["func"] = checked_binary(_name, _definition["func"])  # type: ignore[arg-type]
    else:
        _definition["func"] = checked_unary(_name, _definition["func"])  # type: ignore[arg-type]
