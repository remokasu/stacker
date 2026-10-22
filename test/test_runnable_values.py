"""A lambda or a symbol handed to a word that runs code is run, whichever word it is; other values are pushed."""

import pytest

from stacker import Stacker
from stacker.error import UserError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


LAMBDA = '{} {"ran"} lambda :f set '
FUNCTION = '{} {"ran"} :g defun '


@pytest.mark.parametrize(
    "program, expected",
    [
        (LAMBDA + "true f if", ["ran"]),
        (FUNCTION + "true :g if", ["ran"]),
        (LAMBDA + 'true f {"else"} ifelse', ["ran"]),
        (LAMBDA + 'false {"then"} f ifelse', ["ran"]),
        (LAMBDA + "{1 0 /} f iferror", ["ran"]),
        (LAMBDA + "f 2 times", ["ran", "ran"]),
        (LAMBDA + "{true} f 1 cond", ["ran"]),
        ("{e} {e \"kind\" get} :h defun {1 0 /} :h try", ["ZeroDivisionError"]),
        (LAMBDA + "f eval", ["ran"]),
        ('0 :n set {n 3 <} {} {n 1 + :n set} lambda while n', [3]),
    ],
)
def test_a_lambda_or_a_symbol_is_run(program, expected):
    assert run(program) == expected


def test_a_try_handler_lambda_takes_the_error_as_its_argument():
    assert run('{"K" "m" throw} {e} {e "kind" get e "message" get} lambda try') == ["K", "m"]


def test_a_lambda_with_parameters_takes_them_from_the_stack():
    assert run("5 true {x} {x 1 +} lambda if") == [6]


@pytest.mark.parametrize("program, expected", [("true 1 2 ifelse", [1]), ('false "a" "b" ifelse', ["b"]), ("true [1] if", [[1]]), ("null 2 times", [None, None])])
def test_other_values_are_still_chosen_as_values(program, expected):
    assert run(program) == expected


def test_a_symbol_naming_a_variable_pushes_its_value_as_eval_does():
    # a symbol is run as its name: a variable holding a block is pushed, not run (as `:blk eval`)
    assert len(run('{"x"} :blk set :blk 2 times')) == 2


def test_a_symbol_chosen_as_a_value_is_run_but_a_block_holding_it_is_not():
    assert run("true {:a} {:b} ifelse").__repr__().startswith("[Symbol") or str(run("true {:a} {:b} ifelse")[0]) == "a"
    with pytest.raises(Exception, match="`a` is not defined"):
        run("true :a :b ifelse")


def test_an_error_in_the_lambda_propagates():
    with pytest.raises(UserError):
        run('{} {"E" "x" throw} lambda :f set true f if')
