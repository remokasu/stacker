"""`exit`, `abort` and `exit-code` end the program with their exit status."""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.error import StackerTypeError


def test_abort_exits_with_status_1():
    with pytest.raises(SystemExit) as info:
        Stacker().eval("abort")
    assert info.value.code == 1


def test_exit_code_exits_with_the_given_status():
    with pytest.raises(SystemExit) as info:
        Stacker().eval("3 exit-code")
    assert info.value.code == 3


def test_exit_code_stops_the_program_before_the_next_word(capsys):
    with pytest.raises(SystemExit):
        Stacker().eval('5 exit-code "after" echo')
    assert capsys.readouterr().out == ""


def test_abort_stops_the_program_before_the_next_word(capsys):
    with pytest.raises(SystemExit):
        Stacker().eval('"before" echo abort "after" echo')
    assert capsys.readouterr().out == "before\n"


@pytest.mark.parametrize("program", ['"3" exit-code', "true exit-code", "1.5 exit-code"])
def test_exit_code_needs_an_integer(program):
    with pytest.raises(StackerTypeError) as info:
        Stacker().eval(program)
    assert "`exit-code`" in str(info.value)


def test_every_priority_word_has_a_handler():
    # `ans` is the REPL's word and is handled before evaluation
    names = set(Stacker().operator_manager._priority_operators) - {"ans"}
    assert names <= set(StackerCore._PRIORITY_HANDLERS)
