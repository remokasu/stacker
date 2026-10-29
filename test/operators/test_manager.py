"""Tests for the operator tables each interpreter keeps."""

import pytest

from stacker import Stacker
from stacker.operators.manager import OperatorManager

# Every kind of word but "file": the file words are regular words too, and
# register_operator replaces a word in the first table that has it
CATEGORIES = [
    "priority",
    "regular",
    "hof",
    "aggregate",
    "collection",
    "transform",
    "stack",
    "settings",
    "system",
]


def a_word_only_in(category: str) -> str:
    """A word of ``category`` that no other table holds, so replacing it replaces it there."""
    tables = OperatorManager().operators
    return min(
        word
        for word in tables[category]
        if sum(word in table for table in tables.values()) == 1
    )


@pytest.fixture
def put_back():
    """Puts every built-in word a test replaced back as it was, once the test ends."""
    saved = []

    def remember(stacker: Stacker, word: str) -> None:
        saved.append(
            (stacker, word, dict(stacker.operator_manager.dispatch_table[word][1]))
        )

    yield remember
    for stacker, word, definition in saved:
        stacker.register_operator(
            word,
            definition["func"],
            definition["arg_count"],
            definition["push_result_to_stack"],
            definition.get("desc"),
        )


@pytest.mark.parametrize("category", CATEGORIES)
def test_a_word_replaced_in_one_interpreter_stays_in_it(category, put_back):
    word = a_word_only_in(category)

    def replacement() -> None:
        return None

    stacker = Stacker()
    put_back(stacker, word)
    stacker.register_operator(word, replacement, 0, False)
    assert stacker.operator_manager.dispatch_table[word][1]["func"] is replacement
    assert Stacker().operator_manager.dispatch_table[word][1]["func"] is not replacement


def test_an_interpreter_made_after_a_replacement_runs_the_built_in_word(put_back):
    first = Stacker()
    put_back(first, "sum")
    first.register_operator("sum", lambda values: 999, 1, True)
    assert list(first.eval("[1 2] sum")) == [999]
    assert list(Stacker().eval("[1 2] sum")) == [3]


def test_the_arg_count_of_a_replaced_word_is_the_replacement_s(put_back):
    stacker = Stacker()
    put_back(stacker, "sum")
    stacker.register_operator("sum", lambda values, extra: 0, 2, True)
    assert stacker.operator_manager.get_any_operator_arg_count("sum") == 2
