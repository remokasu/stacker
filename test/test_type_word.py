"""`type` names the kind of a value as a symbol."""

import pytest

from stacker import Stacker
from stacker.engine.data_type import Symbol


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program, name",
    [
        ("42 type", "int"),
        ("3.5 type", "float"),
        ("1+2j type", "complex"),
        ("1 3 frac type", "fraction"),
        ("true type", "bool"),
        ('"a" type', "str"),
        ('"a" "b" + type', "str"),
        ("[1] type", "list"),
        ("[1] array type", "array"),
        ("dict type", "dict"),
        ("{1 2 +} :b set :b type", "symbol"),
        ("{} {1} lambda type", "lambda"),
        ("{} {1} :f defun :f eval type", "int"),
        ("null type", "null"),
    ],
)
def test_the_kind_is_a_symbol(program, name):
    value = run(program)[-1]
    assert isinstance(value, Symbol) and value.name == name


def test_types_compare_as_symbols():
    assert run("42 type :int == 42 type 7 type == 42 type :str ==") == [True, True, False]


def test_the_name_as_text():
    assert run("[1] array type str") == ["array"]
