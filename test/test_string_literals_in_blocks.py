"""A string literal inside a code block is a string, never a name.

Blocks store their string literals as ``String`` values with the quotes
already stripped. They used to be looked up as names on evaluation, so a
variable, operator or macro with the same text captured the literal.
"""

import pytest

from stacker.engine.data_type import String
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


QUOTES = pytest.mark.parametrize(
    "literal", ['"foo"', "'foo'", '"""foo"""'], ids=["double", "single", "triple"]
)


@QUOTES
def test_variable_with_the_same_name_does_not_capture_the_literal(literal):
    result = run("5 foo set", f"{{{literal}}} eval")
    assert isinstance(result[0], String)
    assert result == ["foo"]


@QUOTES
def test_macro_with_the_same_name_does_not_capture_the_literal(literal):
    result = run("{} {{1}} foo defmacro", f"{{{literal}}} eval")
    assert isinstance(result[0], String)
    assert result == ["foo"]


def test_operator_with_the_same_name_is_not_executed():
    result = run('3 4 {"+"} eval')
    assert isinstance(result[-1], String)
    assert result == [3, 4, "+"]


def test_top_level_literal_is_not_captured_by_a_macro_either():
    result = run("{} {{1}} foo defmacro", '"foo"')
    assert isinstance(result[0], String)


@pytest.mark.parametrize(
    ("literal", "expected"),
    [('"$x"', "$x"), ('"[1 2]"', "[1 2]"), ('"{x}"', "{x}")],
    ids=["symbol-like", "list-like", "block-like"],
)
def test_literal_text_that_looks_like_other_syntax_stays_a_string(literal, expected):
    result = run("7 x set", f"{{{literal}}} eval")
    assert isinstance(result[0], String)
    assert result == [expected]


def test_literal_right_before_set_names_the_variable():
    # `"dup"` names the variable; it must not run the `dup` operator.
    assert run('{5 "dup" set} eval dup') == [5]


def test_literal_passed_to_a_macro_stays_a_literal_in_generated_code():
    assert run("5 hi set", "{v} {{v}} m defmacro", '"hi" m') == ["hi"]


class TestBlocksReadAsData:
    """Words that read a block's tokens as values must see plain strings."""

    def test_nth(self):
        # `nth` leaves the container on the stack and pushes the element.
        result = run('{"apple" "banana"} 0 nth')
        assert isinstance(result[-1], String)
        assert result[-1] == "apple"

    def test_list(self):
        assert run('{"a" "b"} list') == [["a", "b"]]

    def test_fold(self):
        assert run('{"a" "b"} "" acc x {acc x +} fold') == ["ab"]

    def test_map(self):
        assert run('{"a" "b"} {"!" +} map') == [["a!", "b!"]]


def test_block_display_shows_string_literals_with_quotes():
    (block,) = run('{"a b" echo}')
    assert str(block) == '{"a b" echo}'
