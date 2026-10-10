"""Unit tests for the shared token-shape predicates in ``stacker.syntax.token_rules``."""

import pytest

from stacker.engine.data_type import String
from stacker.syntax import parser, token_rules
from stacker.syntax.token_rules import (
    cached_literal_eval,
    is_bare_name,
    is_code_block,
    is_list,
    is_symbol,
    is_symbol_name,
    not_a_symbol_message,
    reads_as_name,
)


@pytest.mark.parametrize(
    "token, expected",
    [
        ("[1 2]", True),
        ("[]", True),
        ("[", False),
        ("x", False),
        ("{1}", False),
        (5, False),
    ],
)
def test_is_list(token, expected):
    assert is_list(token) is expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("{1 2 +}", True),
        ("(1 2 +)", True),
        ("{a {b c}}", True),
        ("{}", True),
        ("{1", False),
        ("{1}}", False),
        ("[1]", False),
        ("x", False),
        ("{", False),
        (5, False),
    ],
)
def test_is_code_block(token, expected):
    assert is_code_block(token) is expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("$x", True),
        ("$+", True),
        ("$x.y", True),
        ("$1st", True),
        ("$", False),
        ("$$x", False),
        ("$x$", False),
        ("$1", False),
        ("${x}", False),
        ('$"x"', False),
        ("$[1 2]", False),
        ("$(x)", False),
        ("$true", False),
        ("x", False),
        (String("$x"), False),
        (5, False),
    ],
)
def test_is_symbol(token, expected):
    assert is_symbol(token) is expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("x", True),
        ("1st", True),
        ("+", True),
        ("x-y?", True),
        ("5", False),
        ("1.5", False),
        ("-3", False),
        ("True", False),
        ("None", False),
        ("true", False),
        ("false", False),
        ("null", False),
        ("", True),
    ],
)
def test_reads_as_name(token, expected):
    assert reads_as_name(token) is expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("x", True),
        ("+", True),
        ("1st", True),
        ("$x", False),
        ("", False),
        ("5", False),
        ("True", False),
        ("true", False),
        ('"x"', False),
        ("'x'", False),
        ("[1 2]", False),
        ("{x}", False),
        (String("x"), False),
        (5, False),
        (None, False),
    ],
)
def test_is_bare_name(token, expected):
    assert is_bare_name(token) is expected


@pytest.mark.parametrize(
    "token, expected",
    [
        ("5", 5),
        ("1.5", 1.5),
        ("True", True),
        ("None", None),
        ("[1, 2]", [1, 2]),
        ("x", "x"),
        ("1st", "1st"),
        ("true", True),
        ("false", False),
        ("null", None),
    ],
)
def test_cached_literal_eval(token, expected):
    assert cached_literal_eval(token) == expected


def test_parser_reexports_the_predicates():
    assert parser.is_list is is_list
    assert parser.is_code_block is is_code_block
    assert parser.is_symbol is is_symbol


@pytest.mark.parametrize(
    "name, expected",
    [
        ("x", True),
        ("+", True),
        ("x.y", True),
        ("1st", True),
        ("a-b?", True),
        ("", False),
        ("1", False),
        ("a b", False),
        ("a\tb", False),
        ("a\nb", False),
        ("$x", False),
        ("a$", False),
        ('a"b', False),
        ("a'b", False),
        ("a[b", False),
        ("a]b", False),
        ("a(b", False),
        ("a#b", False),
        ("a;b", False),
        ("true", False),
        ("None", False),
        (String("x"), False),
        (5, False),
        (None, False),
    ],
)
def test_is_symbol_name(name, expected):
    assert is_symbol_name(name) is expected


@pytest.mark.parametrize("name", ["x", "+", "x.y", "1st", "a-b?"])
def test_is_symbol_name_agrees_with_is_symbol(name):
    assert is_symbol_name(name) is is_symbol("$" + name)


def test_keyword_literals_are_values_not_names():
    assert token_rules.KEYWORD_LITERALS == {
        "true": True,
        "false": False,
        "null": None,
        "True": True,
        "False": False,
        "None": None,
    }
    for word in token_rules.KEYWORD_LITERALS:
        assert not is_bare_name(word)
        assert not is_symbol("$" + word)


def test_not_a_symbol_message_quotes_the_token():
    assert not_a_symbol_message("$1") == "`$1` is not a symbol: `$` must be followed by a name"
