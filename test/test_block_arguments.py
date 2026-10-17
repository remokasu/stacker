"""A code block handed to a word as an argument is evaluated to its value.

A block that leaves nothing has no value to hand over: that is an error,
never the interpreter's own "no value" marker.
"""

import pytest

from stacker import Stacker
from stacker.error import NoValueProducedError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program",
    [
        "{} echo",
        "{} str",
        "{} type",
        '{"side effect" echo} 1 +',
        "{} 1 +",
        "{} :v set v v ==",
        "{} {2 *} map echo",
        "{} :i {} do",
        "3 {} cond",
    ],
)
def test_a_block_argument_that_leaves_nothing_is_an_error(program):
    with pytest.raises(NoValueProducedError) as info:
        run(program)
    assert "left nothing on the stack" in str(info.value)


def test_the_error_names_the_word():
    with pytest.raises(NoValueProducedError) as info:
        run("{} echo")
    assert "`echo`" in str(info.value)


def test_a_block_that_leaves_a_value_is_its_value(capsys):
    run("{3 4 +} echo")
    assert capsys.readouterr().out == "7\n"


def test_a_function_without_a_result_pushes_nothing():
    assert run('{} {"x" :y set} :f defun f depth') == [0]


def test_apply_with_an_empty_argument_block_applies_to_nothing():
    assert run("{} {7} apply") == [7]
