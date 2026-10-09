"""gensym / macroexpand / concat-block and the block form of expand."""

import pytest

from stacker.engine.data_type import String, UndefinedSymbol
from stacker.error import StackerSyntaxError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


def shape(value: object) -> object:
    """Token structure of a block (nested blocks become nested lists)."""
    if hasattr(value, "tokens") and hasattr(value, "bracket_type"):
        return [shape(token) for token in value.tokens]
    return value


class TestGensym:
    def test_returns_distinct_symbol_values(self):
        a, b = run("gensym gensym")
        assert a != b
        assert a.startswith("__g") and b.startswith("__g")
        assert type(a) is str  # same kind of value as `$name` pushes
        assert not isinstance(a, (String, UndefinedSymbol))

    def test_usable_as_a_name(self):
        assert run("gensym t =", "5 t set", "t eval") == [5]

    def test_unique_across_interpreters(self):
        first = Stacker().eval("gensym").pop()
        second = Stacker().eval("gensym").pop()
        assert first != second


class TestMacroexpand:
    def test_returns_expansion_without_evaluating(self):
        (block,) = run("{x} {{x x}} m defmacro", "3 {m} macroexpand")
        assert shape(block) == [3, 3]

    def test_accepts_dollar_name(self):
        (block,) = run("{} {{1}} m defmacro", "$m macroexpand")
        assert shape(block) == [1]

    def test_non_macro_is_a_syntax_error(self):
        with pytest.raises(StackerSyntaxError):
            run("{dup} macroexpand")


class TestConcatBlock:
    def test_joins_token_lists(self):
        (block,) = run("{a b} {c} concat-block")
        assert shape(block) == ["a", "b", "c"]

    def test_result_is_executable(self):
        assert run("{1 2} {+} concat-block eval") == [3]

    def test_non_block_is_a_syntax_error(self):
        with pytest.raises(StackerSyntaxError):
            run("5 {a} concat-block")


class TestExpandOnBlocks:
    def test_each_token_becomes_a_one_token_block(self):
        assert [shape(b) for b in run("{a {b c}} expand")] == [["a"], [["b", "c"]]]

    def test_pieces_are_executable(self):
        assert run("{5 dup} expand swap eval swap eval") == [5, 5]

    def test_empty_block_pushes_nothing(self):
        assert run("{} expand") == []

    def test_list_form_is_unchanged(self):
        assert run("[1 2 3] expand") == [1, 2, 3]

    def test_non_iterable_is_a_syntax_error(self):
        with pytest.raises(StackerSyntaxError):
            run("5 expand")
