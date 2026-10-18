"""`null?` is true for null alone; `empty?` is true for a list, an array, a string or a dictionary with nothing in it."""

import pytest

from stacker import Stacker
from stacker.error import StackerTypeError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program, expected",
    [
        ("null null?", True),
        ("[] null?", False),
        ("[] array null?", False),
        ('"" null?', False),
        ("dict null?", False),
        ("0 null?", False),
        ("false null?", False),
    ],
)
def test_null_is_true_for_null_alone(program, expected):
    assert run(program) == [expected]


@pytest.mark.parametrize(
    "program, expected",
    [
        ("[] empty?", True),
        ("[] array empty?", True),
        ('"" empty?', True),
        ("dict empty?", True),
        ("[1] empty?", False),
        ("[1] array empty?", False),
        ('"a" empty?', False),
        ('dict :d set 1 d "k" put! d empty?', False),
    ],
)
def test_empty_counts_the_elements(program, expected):
    assert run(program) == [expected]


@pytest.mark.parametrize("program", ["null empty?", "0 empty?", "true empty?", ":s empty?", "{} empty?", "{[]} empty?"])
def test_a_value_without_elements_is_refused(program):
    with pytest.raises(StackerTypeError, match="`empty\\?` expects a list, an array, a string or a dictionary"):
        run(program)
