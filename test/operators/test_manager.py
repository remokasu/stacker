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


GROUP_KEYS_AND_HEADINGS = [
    ("regular", "Regular operators:"),
    ("hof", "Higher-order operators:"),
    ("aggregate", "Aggregate operators:"),
    ("transform", "Transform operators:"),
    ("collection", "Array and dictionary operators:"),
    ("stack", "Stack operators:"),
    ("settings", "Settings operators:"),
    ("system", "System operators:"),
]


def test_the_operator_groups_come_in_the_order_operators_lists_them():
    groups = Stacker().get_operator_groups()
    assert [(key, heading) for key, heading, _ in groups] == GROUP_KEYS_AND_HEADINGS


def test_the_regular_group_holds_the_regular_and_then_the_priority_words():
    stacker = Stacker()
    manager = stacker.operator_manager
    regular = stacker.get_operator_groups()[0][2]
    expected = {
        **manager.get_regular_descriptions(),
        **manager.get_priority_descriptions(),
    }
    assert list(regular.items()) == list(expected.items())
    assert {"+", "if", "defun"} <= set(regular)


def test_the_operator_groups_are_built_anew_on_every_call():
    stacker = Stacker()
    stacker.get_operator_groups()[0][2]["+"] = "changed by the caller"
    assert stacker.get_operator_groups()[0][2]["+"] != "changed by the caller"


def test_a_replaced_word_is_listed_with_its_new_description_at_the_end_of_its_group(
    put_back,
):
    stacker = Stacker()
    before = stacker.get_operator_groups()
    put_back(stacker, "dup")
    stacker.register_operator("dup", lambda x: x, 1, True, "replaced dup")
    after = {key: words for key, _, words in stacker.get_operator_groups()}
    assert list(after["stack"].items())[-1] == ("dup", "replaced dup")
    assert {key: words for key, _, words in before}["stack"]["dup"] != "replaced dup"
