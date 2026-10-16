"""`eval` on names, blocks and other values; text goes through `parse`."""

import pytest

from stacker.error import StackerTypeError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


class TestTextIsReadFirst:
    """A string is data, not code (1.16.0): `eval` rejects it and
    `parse` turns text into a code block, whose names resolve
    when the block runs (so `"6 x set x"` rebinds an existing `x`)."""

    def test_string_eval_is_a_type_error_with_a_hint(self):
        with pytest.raises(StackerTypeError) as info:
            run('"3 4 +" eval')
        assert "parse" in str(info.value)

    def test_assignment_inside_the_text_rebinds_an_existing_variable(self):
        assert run("5 :x set", '"6 :x set x" parse eval') == [6]

    def test_variables_are_resolved_when_the_block_runs(self):
        assert run("5 :x set", '"x x +" parse eval') == [10]

    def test_lambda_held_in_a_variable_is_a_value_inside_the_text(self):
        # The same as writing the name in a block: `f` pushes the lambda, `eval` calls it.
        assert run("{a} {a 1 +} lambda :f set", '"5 f eval" parse eval') == [6]


class TestEvalOnValues:
    def test_eval_of_a_list_pushes_it_back(self):
        # Used to raise TypeError: unhashable type: 'list'.
        assert run("[1 2] eval") == [[1, 2]]

    def test_eval_of_a_number_pushes_it_back(self):
        assert run("5 eval") == [5]
