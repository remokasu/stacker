"""`listn` / `subn` with too few values say so and leave the stack as it was."""

import pytest

from stacker import Stacker
from stacker.error import StackUnderflowError


@pytest.mark.parametrize("word", ["listn", "subn"])
def test_too_few_values_is_reported_as_such(word):
    stacker = Stacker()
    with pytest.raises(StackUnderflowError) as info:
        stacker.process_expression(f"1 2 5 {word}")
    assert f"`{word}` needs 5 values" in str(info.value)
    assert "the stack has 2" in str(info.value)


@pytest.mark.parametrize("word", ["listn", "subn"])
def test_the_stack_is_left_as_it_was(word):
    stacker = Stacker()
    with pytest.raises(StackUnderflowError):
        stacker.process_expression(f"1 2 5 {word}")
    assert list(stacker.stack) == [1, 2, 5]


def test_exactly_enough_values_still_works():
    stacker = Stacker()
    stacker.process_expression("1 2 2 listn")
    assert list(stacker.stack) == [[1, 2]]
