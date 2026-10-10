"""Unit tests for ``stacker.engine.boundary`` (token layer <-> value layer)."""

import pytest

from stacker.engine.boundary import token_to_value, value_to_token
from stacker.engine.data_type import String, Symbol


class TestValueToToken:
    def test_symbol_becomes_a_bare_name_token(self):
        token = value_to_token(Symbol("x"))
        assert type(token) is str
        assert token == "x"

    def test_plain_str_becomes_a_string_literal_token(self):
        token = value_to_token("ab")
        assert isinstance(token, String)
        assert token == "ab"

    def test_string_literal_is_kept(self):
        literal = String("ab")
        assert value_to_token(literal) is literal

    @pytest.mark.parametrize("value", [5, 1.5, True, None, [1, 2], (1, 2)])
    def test_other_values_are_kept(self, value):
        assert value_to_token(value) is value


class TestTokenToValue:
    @pytest.mark.parametrize("token", ["x", "+", "1st", "x.y", "a-b?"])
    def test_bare_name_becomes_a_symbol(self, token):
        assert token_to_value(token) == Symbol(token)

    @pytest.mark.parametrize("token, name", [("$x", "x"), ("$+", "+"), ("$1st", "1st")])
    def test_dollar_token_becomes_the_symbol_without_the_dollar(self, token, name):
        assert token_to_value(token) == Symbol(name)

    def test_string_literal_is_kept(self):
        literal = String("x")
        assert token_to_value(literal) is literal

    @pytest.mark.parametrize("token", ["[1 2]", "$1", "$", "$$x", "$true", "{x}", '"x"', "5", "True"])
    def test_raw_text_that_is_not_a_name_is_kept_as_text(self, token):
        value = token_to_value(token)
        assert type(value) is str and value == token

    @pytest.mark.parametrize("value", [5, 1.5, True, None, [1, 2], (1, 2)])
    def test_other_values_are_kept(self, value):
        assert token_to_value(value) is value

    def test_a_symbol_object_in_a_block_is_kept(self):
        symbol = Symbol("x")
        assert token_to_value(symbol) is symbol


class TestRoundTrip:
    @pytest.mark.parametrize("value", [Symbol("x"), Symbol("+"), Symbol("a.b")])
    def test_symbol_survives_a_trip_through_a_block(self, value):
        assert token_to_value(value_to_token(value)) == value

    @pytest.mark.parametrize("value", ["x", "", "a b", "$x", "{x}", "5", "[1 2]", String("x")])
    def test_string_survives_a_trip_and_stays_a_string(self, value):
        result = token_to_value(value_to_token(value))
        assert result == value
        assert isinstance(result, str) and not isinstance(result, Symbol)

    @pytest.mark.parametrize("value", [5, 1.5, True, None, [1, 2]])
    def test_other_values_survive_a_trip(self, value):
        assert token_to_value(value_to_token(value)) is value

    def test_a_string_that_reads_as_a_name_does_not_become_a_symbol(self):
        assert not isinstance(token_to_value(value_to_token("x")), Symbol)
