"""Unit tests for ``stacker.engine.boundary`` (token layer <-> value layer)."""

import pytest

from stacker.engine.boundary import value_to_token
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
