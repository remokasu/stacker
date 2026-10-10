"""Unit tests for the value types in ``stacker.engine.data_type``."""

import copy
import operator

import pytest

from stacker import Symbol as ExportedSymbol
from stacker.engine.data_type import String, Symbol


class TestSymbolIdentity:
    def test_equal_when_names_match(self):
        assert Symbol("x") == Symbol("x")
        assert (Symbol("x") != Symbol("x")) is False

    def test_different_names_differ(self):
        assert Symbol("x") != Symbol("y")

    @pytest.mark.parametrize("other", ["x", String("x"), 1, None, ["x"]])
    def test_never_equal_to_a_non_symbol(self, other):
        # Both directions: str.__eq__ returns NotImplemented, Symbol.__eq__ False.
        assert Symbol("x") != other
        assert other != Symbol("x")
        assert (Symbol("x") == other) is False
        assert (other == Symbol("x")) is False

    def test_is_not_a_str(self):
        assert not isinstance(Symbol("x"), str)

    def test_hash_follows_the_name(self):
        assert hash(Symbol("x")) == hash(Symbol("x"))
        table = {"x": 1, Symbol("x"): 2}
        assert len(table) == 2
        assert table[Symbol("x")] == 2
        assert table["x"] == 1

    def test_truthy(self):
        assert bool(Symbol("x"))


class TestSymbolText:
    def test_str_is_the_name(self):
        assert str(Symbol("abc")) == "abc"

    def test_repr(self):
        assert repr(Symbol("abc")) == "Symbol('abc')"


class TestSymbolImmutability:
    def test_setattr_raises(self):
        with pytest.raises(AttributeError):
            Symbol("x").name = "y"

    def test_delattr_raises(self):
        with pytest.raises(AttributeError):
            del Symbol("x").name

    def test_copy_and_deepcopy_return_self(self):
        sym = Symbol("x")
        assert copy.copy(sym) is sym
        assert copy.deepcopy(sym) is sym
        assert copy.deepcopy([sym, [sym]])[1][0] is sym


class TestSymbolOrdering:
    def test_orders_by_name(self):
        assert Symbol("a") < Symbol("b")
        assert Symbol("b") > Symbol("a")
        assert Symbol("a") <= Symbol("a")
        assert sorted([Symbol("c"), Symbol("a"), Symbol("b")]) == [
            Symbol("a"),
            Symbol("b"),
            Symbol("c"),
        ]

    def test_not_ordered_against_other_types(self):
        with pytest.raises(TypeError):
            operator.lt(Symbol("a"), "b")


def test_symbol_is_exported_from_the_package():
    assert ExportedSymbol is Symbol
