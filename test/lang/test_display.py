"""The display text of a value comes in pieces tagged by the kind of value each came from."""

from __future__ import annotations

import pytest

from stacker.data_type import Array, String, Symbol
from stacker.error import StackerRuntimeError
from stacker.lang import display
from stacker.lang.display import DISPLAY_NESTING_LIMIT, pieces, plain_text
from stacker.lang.protocols import BLOCK
from stacker.stacker import Stacker


def test_a_container_tags_its_brackets_and_each_item_by_kind():
    value = Array([1, String("a, b"), {"k": Symbol("v")}, [True, None]])
    assert pieces(value) == [
        (display.ARRAY, "["),
        (display.INT, "1"),
        (None, " "),
        (display.STRING, "'a, b'"),
        (None, " "),
        (display.DICT, "{"),
        (display.STRING, "'k'"),
        (None, " "),
        (display.SYMBOL, "v"),
        (display.DICT, "}"),
        (None, " "),
        (display.LIST, "["),
        (display.BOOL, "true"),
        (None, " "),
        (display.NULL, "null"),
        (display.LIST, "]"),
        (display.ARRAY, "]"),
    ]


def test_the_plain_text_is_the_pieces_joined():
    value = Array([1, String("a, b"), {"k": Symbol("v")}, [True, None]])
    assert plain_text(value) == "[1 'a, b' {'k' v} [true null]]"


def test_a_block_and_a_lambda_have_their_own_kinds():
    block, lam = Stacker().eval("{1 2 +} {x} {x 1 +} lambda", stack=None)
    assert pieces(block) == [(BLOCK, "{1 2 +}")]
    assert pieces(lam) == [(display.CALLABLE, "λx.{x 1 +}")]


def test_a_value_of_an_unknown_kind_is_shown_with_str_and_no_kind():
    class Odd:
        def __str__(self) -> str:
            return "odd!"

    assert pieces(Odd()) == [(None, "odd!")]


def test_an_empty_dictionary_is_told_apart_from_an_empty_block():
    assert pieces({}) == [(display.DICT, "{:}")]
    assert pieces(Array([])) == [(display.ARRAY, "["), (display.ARRAY, "]")]


def test_a_dictionary_inside_itself_is_shown_once():
    value: dict[object, object] = {"k": 1}
    value["self"] = value
    assert plain_text(value) == "{'k' 1 'self' {...}}"


def test_an_array_nested_past_the_limit_is_cut_short():
    value = Array([1])
    for _ in range(DISPLAY_NESTING_LIMIT + 3):
        value = Array([value])
    text = plain_text(value)
    assert text == "[" * DISPLAY_NESTING_LIMIT + "[...]" + "]" * DISPLAY_NESTING_LIMIT


def test_a_list_inside_itself_is_too_deep_to_show():
    value: list[object] = [1]
    value.append(value)
    with pytest.raises(StackerRuntimeError, match="nested this deep"):
        plain_text(value)
    assert display._showing() == []
