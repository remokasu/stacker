"""Errors Stacker raises on purpose share the StackerError base class."""

import pytest

from stacker.error import (
    DropError,
    DupError,
    InsertError,
    NipError,
    OverError,
    PickError,
    RollError,
    RotError,
    StackerError,
    SwapError,
)
from stacker.stacker import Stacker


@pytest.mark.parametrize(
    "expression, error",
    [
        ("drop", DropError),
        ("dup", DupError),
        ("1 over", OverError),
        ("1 swap", SwapError),
        ("1 roll", RollError),
        ("rot", RotError),
        ("5 pick", PickError),
        ("nip", NipError),
        ("9 5 ins", InsertError),
    ],
)
def test_stack_word_failure_is_caught_as_stacker_error(expression, error):
    with pytest.raises(StackerError) as info:
        Stacker().eval(expression)
    assert info.type is error


def test_stack_word_failure_in_a_macro_names_the_macro():
    # Like every StackerError, it gains the macro context and keeps its type.
    stacker = Stacker()
    stacker.eval("{} {drop} :d defmacro")
    with pytest.raises(DropError, match=r"while expanding macro 'd'"):
        stacker.eval("d")
