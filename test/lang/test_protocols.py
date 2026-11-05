"""The kind mark the lower layers read of the engine's values, and the shapes the protocols promise."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from stacker import Stacker
from stacker.data_type import Symbol
from stacker.lang import protocols
from stacker.lang.display import CustomBlockPrinter, custom_print, plain_text


def _block_and_lambda() -> tuple[object, object]:
    stacker = Stacker()
    stacker.process_expression("{1 2 +} {x} {x 1 +} lambda")
    function = stacker.stack.pop()
    block = stacker.stack.pop()
    return block, function


def test_a_block_and_a_lambda_carry_their_kind_on_the_class():
    block, function = _block_and_lambda()
    assert protocols.kind_of(block) == protocols.BLOCK
    assert protocols.kind_of(function) == protocols.LAMBDA
    assert type(block).stacker_kind == protocols.BLOCK
    assert type(function).stacker_kind == protocols.LAMBDA


@pytest.mark.parametrize("value", [1, "text", [1], {"a": 1}, Symbol("x"), None, Mock()], ids=repr)
def test_any_other_value_has_no_kind_even_one_that_answers_every_attribute(value):
    assert protocols.kind_of(value) is None


def test_the_display_shows_a_block_as_a_block_by_its_kind():
    block, function = _block_and_lambda()
    assert isinstance(custom_print(block), CustomBlockPrinter)
    assert plain_text(block) == "{1 2 +}"
    assert plain_text(function) == "λx.{x 1 +}"


def test_the_type_word_names_a_lambda_by_its_kind():
    stacker = Stacker()
    stacker.process_expression("{x} {x} lambda type {1} type")
    assert list(stacker.stack) == [Symbol("lambda"), Symbol("int")]


def test_the_collection_words_know_a_block_by_its_kind():
    # `array` and `at` read a block as data (its tokens), which they tell by its kind
    stacker = Stacker()
    stacker.process_expression("{a b c} array {a b c} 1 at")
    array, element = stacker.stack
    assert (list(array), element) == ([Symbol("a"), Symbol("b"), Symbol("c")], Symbol("b"))


@pytest.mark.parametrize("protocol", [protocols.CoreView, protocols.Block])
def test_the_interpreter_has_every_attribute_the_protocols_promise(protocol):
    # The protocols are for type checking only; this keeps them honest about the live core
    stacker = Stacker()
    stacker.process_expression("{1}")
    core = stacker.stack.pop() if protocol is protocols.Block else stacker
    missing = [name for name in protocol.__annotations__ if not hasattr(core, name)]
    assert missing == []


def test_the_word_tables_answer_what_the_protocol_promises():
    manager = Stacker().operator_manager
    assert callable(manager.words_changed) and callable(manager.get_groups)
