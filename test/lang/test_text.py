"""The display text of a value comes in pieces tagged by the kind of value each came from."""

from __future__ import annotations

import pytest

from stacker.data_type import Array, String, Symbol
from stacker.error import StackerRuntimeError
from stacker.lang import text as lang_text
from stacker.lang.text import DISPLAY_NESTING_LIMIT, pieces, plain_text
from stacker.lang.protocols import BLOCK
from stacker.stacker import Stacker


def test_a_container_tags_its_brackets_and_each_item_by_kind():
    value = Array([1, String("a, b"), {"k": Symbol("v")}, [True, None]])
    assert pieces(value) == [
        (lang_text.ARRAY, "["),
        (lang_text.INT, "1"),
        (None, " "),
        (lang_text.STRING, "'a, b'"),
        (None, " "),
        (lang_text.DICT, "{"),
        (lang_text.STRING, "'k'"),
        (None, " "),
        (lang_text.SYMBOL, "v"),
        (lang_text.DICT, "}"),
        (None, " "),
        (lang_text.LIST, "["),
        (lang_text.BOOL, "true"),
        (None, " "),
        (lang_text.NULL, "null"),
        (lang_text.LIST, "]"),
        (lang_text.ARRAY, "]"),
    ]


def test_the_plain_text_is_the_pieces_joined():
    value = Array([1, String("a, b"), {"k": Symbol("v")}, [True, None]])
    assert plain_text(value) == "[1 'a, b' {'k' v} [true null]]"


def test_a_block_and_a_lambda_have_their_own_kinds():
    block, lam = Stacker().eval("{1 2 +} {x} {x 1 +} lambda", stack=None)
    assert pieces(block) == [(BLOCK, "{1 2 +}")]
    assert pieces(lam) == [(lang_text.CALLABLE, "λx.{x 1 +}")]


def test_a_value_of_an_unknown_kind_is_shown_with_str_and_no_kind():
    class Odd:
        def __str__(self) -> str:
            return "odd!"

    assert pieces(Odd()) == [(None, "odd!")]


def test_an_empty_dictionary_is_told_apart_from_an_empty_block():
    assert pieces({}) == [(lang_text.DICT, "{:}")]
    assert pieces(Array([])) == [(lang_text.ARRAY, "["), (lang_text.ARRAY, "]")]


def test_a_dictionary_inside_itself_is_shown_once():
    value: dict[object, object] = {"k": 1}
    value["self"] = value
    assert plain_text(value) == "{'k' 1 'self' {...}}"


def test_an_array_nested_past_the_limit_is_cut_short():
    value = Array([1])
    for _ in range(DISPLAY_NESTING_LIMIT + 3):
        value = Array([value])
    shown = plain_text(value)
    assert shown == "[" * DISPLAY_NESTING_LIMIT + "[...]" + "]" * DISPLAY_NESTING_LIMIT


def test_a_list_inside_itself_is_too_deep_to_show():
    value: list[object] = [1]
    value.append(value)
    with pytest.raises(StackerRuntimeError, match="nested this deep"):
        plain_text(value)
    assert lang_text._showing() == []
