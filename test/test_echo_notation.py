"""`echo`, `str` and `format` write a value the way the stack display shows it."""

import pytest

from stacker import Stacker


def printed(program: str, capsys) -> str:
    Stacker().process_expression(program)
    return capsys.readouterr().out


def top(program: str) -> object:
    stacker = Stacker()
    stacker.process_expression(program)
    return stacker.stack[-1]


@pytest.mark.parametrize(
    "program, expected",
    [
        ("true echo", "true\n"),
        ("false echo", "false\n"),
        ("null echo", "null\n"),
        ("[:a :b] echo", "[a b]\n"),
        ('[1 "a" true null] echo', "[1 'a' true null]\n"),
        ("[[1 2] [3]] echo", "[[1 2] [3]]\n"),
        ('"hello" echo', "hello\n"),
        ('"a, b" echo', "a, b\n"),
        ("3 echo", "3\n"),
        ("1.5 echo", "1.5\n"),
        (":a echo", "a\n"),
        ("{1 2 +} echo", "3\n"),
    ],
)
def test_echo_uses_stacker_notation(program, expected, capsys):
    assert printed(program, capsys) == expected


def test_print_and_printc_use_the_same_notation(capsys):
    assert printed("true print null printc", capsys) == "true\nnull"


@pytest.mark.parametrize(
    "program, expected",
    [
        ("true str", "true"),
        ("null str", "null"),
        ("[1 2] str", "[1 2]"),
        ('[:a "b"] str', "[a 'b']"),
        (":a str", "a"),
        ("3 str", "3"),
        ("1.5 str", "1.5"),
        ('"x" str', "x"),
    ],
)
def test_str_uses_stacker_notation(program, expected):
    assert top(program) == expected


@pytest.mark.parametrize(
    "program, expected",
    [
        ('"v={}" null format', "v=null"),
        ('"v={}" true format', "v=true"),
        ('"v={}" [1 2] format', "v=[1 2]"),
        ('"v={}" :a format', "v=a"),
        ('"{:.2f}" 3.14159 format', "3.14"),
        ('"{:>3}" 7 format', "  7"),
        ('"v={}" "a" format', "v=a"),
    ],
)
def test_format_uses_stacker_notation(program, expected):
    assert top(program) == expected
