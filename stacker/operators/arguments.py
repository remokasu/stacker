"""Checks on the arguments a word receives, each raising an error that names the word."""

from __future__ import annotations

import operator

from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, symbol_as_value_message
from stacker.util.disp import plain_text


def integer_argument(word: str, value: object) -> int:
    """Returns ``value`` as an integer when it is one (a bool included).

    Any value that counts as an integer for the host (one with
    ``__index__``, as a plugin may push) is taken, as `range` takes it.

    Args:
        word: The word that received the value, named in the error.
        value: The value to check.

    Returns:
        The integer.

    Raises:
        StackerTypeError: ``value`` is a symbol or not an integer. A whole
            float such as ``2.0`` is not an integer either; the message
            says how to make one.
    """
    if isinstance(value, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, value.name))
    try:
        return operator.index(value)
    except TypeError as error:
        hint = "; `int` makes an integer of a number" if isinstance(value, float) else ""
        raise StackerTypeError(f"`{word}` expects an integer, got {plain_text(value)}{hint}") from error
