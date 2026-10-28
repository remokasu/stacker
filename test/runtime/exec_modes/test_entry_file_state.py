"""Pins what running an entry file (a script, or ~/.stackerrc) does to the interpreter's location state.

A script leaves its file, line and source lines in place for the error
report; the rc file restores whatever was there before. Both keep the
include stack balanced, and a function the file defined keeps the file
as its own position.
"""

from __future__ import annotations

import pytest

from stacker.error import (
    UndefinedSymbolError,
    UnterminatedTokenError,
    include_location_of,
)
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.stacker import Stacker


@pytest.fixture
def mode():
    return ExecutionMode(Stacker())


@pytest.fixture
def rc(tmp_path):
    """An rc file defining a function, holding a REPL command and setting a variable."""
    path = tmp_path / "rc.stk"
    path.write_text("{x} {script-path} :rcfn defun\nhelp\nenable_disp_stack\n5 :v set\n", encoding="utf-8")
    return path


def _include_depth(calc: Stacker) -> int:
    """How many files the interpreter is inside of (zero after an entry file ends)."""
    return len(calc._includes.stack)


def test_script_sets_the_location_and_keeps_it(mode, tmp_path):
    script = tmp_path / "main.stk"
    script.write_text("1 :x set\n2 :y set\n", encoding="utf-8")
    calc = mode.rpn_calculator
    calc.source_lines[99] = "kept"  # lines are added to what is there, not replaced
    source_lines = calc.source_lines

    mode.execute_stacker_dotfile(script)

    assert calc.current_file == str(script.resolve())
    assert calc.current_line == 2
    assert calc.source_lines is source_lines  # child cores share this dict by reference
    assert calc.source_lines == {1: "1 :x set", 2: "2 :y set", 99: "kept"}
    assert calc.main_script is None  # the script runner sets it, not this method
    assert _include_depth(calc) == 0


def test_a_quoted_path_is_accepted(mode, tmp_path):
    script = tmp_path / "main.stk"
    script.write_text("1 :x set\n", encoding="utf-8")
    mode.execute_stacker_dotfile(f'"{script}"')
    assert mode.rpn_calculator.variables["x"] == 1


def test_rc_restores_the_location(mode, rc):
    calc = mode.rpn_calculator
    calc.current_file, calc.current_line = "earlier.stk", 7
    calc.source_lines[1] = "old"
    source_lines = calc.source_lines

    mode.execute_stacker_dotfile(rc, stackerrc=True)

    assert (calc.current_file, calc.current_line) == ("earlier.stk", 7)
    assert calc.source_lines is source_lines  # child cores share this dict by reference
    assert calc.source_lines == {1: "old"}
    assert calc.main_script is None
    assert _include_depth(calc) == 0


def test_rc_skips_repl_commands_and_runs_the_rest(mode, rc):
    mode.execute_stacker_dotfile(rc, stackerrc=True)
    assert mode.rpn_calculator.variables["v"] == 5


def test_a_function_the_rc_defined_keeps_the_rc_as_its_file(mode, rc):
    calc = mode.rpn_calculator
    mode.execute_stacker_dotfile(rc, stackerrc=True)
    calc.process_expression("1 rcfn")
    assert calc.stack[-1] == str(rc.resolve())


def test_a_repl_command_line_is_a_word_outside_the_rc(mode, tmp_path):
    script = tmp_path / "s.stk"
    script.write_text("help\n", encoding="utf-8")
    with pytest.raises(UndefinedSymbolError):
        mode.execute_stacker_dotfile(script)


def test_rc_error_carries_its_position_and_restores(mode, tmp_path):
    rc = tmp_path / "rc.stk"
    rc.write_text("1 :a set\nfoo\n", encoding="utf-8")
    calc = mode.rpn_calculator

    with pytest.raises(UndefinedSymbolError) as info:
        mode.execute_stacker_dotfile(rc, stackerrc=True)

    assert include_location_of(info.value) == ((str(rc.resolve()), 2, "foo"), [])
    assert (calc.current_file, calc.current_line, calc.source_lines) == (None, None, {})
    assert _include_depth(calc) == 0


def test_an_error_in_a_file_the_rc_includes_keeps_that_file_as_its_position(mode, tmp_path):
    included = tmp_path / "inc.stk"
    included.write_text("1\nfoo\n", encoding="utf-8")
    rc = tmp_path / "rc.stk"
    rc.write_text('"inc.stk" include\n', encoding="utf-8")

    with pytest.raises(UndefinedSymbolError) as info:
        mode.execute_stacker_dotfile(rc, stackerrc=True)

    assert include_location_of(info.value) == ((str(included.resolve()), 2, "foo"), [(str(rc.resolve()), 1)])


def test_script_error_leaves_the_position_for_the_report(mode, tmp_path):
    script = tmp_path / "s.stk"
    script.write_text("1\nfoo\n3\n", encoding="utf-8")
    calc = mode.rpn_calculator

    with pytest.raises(UndefinedSymbolError) as info:
        mode.execute_stacker_dotfile(script)

    assert include_location_of(info.value) is None
    assert calc.current_line == 2
    assert calc.source_lines[2] == "foo"
    assert _include_depth(calc) == 0


def test_unterminated_script_runs_what_came_before_and_names_the_start_line(mode, tmp_path):
    script = tmp_path / "s.stk"
    script.write_text("1 :a set\n{1 2\n3\n", encoding="utf-8")
    calc = mode.rpn_calculator

    with pytest.raises(UnterminatedTokenError) as info:
        mode.execute_stacker_dotfile(script)

    assert include_location_of(info.value) is None
    assert calc.variables["a"] == 1
    assert calc.current_line == 2
    assert _include_depth(calc) == 0


def test_unterminated_rc_reports_the_start_line_and_restores(mode, tmp_path):
    rc = tmp_path / "rc.stk"
    rc.write_text("1 :a set\n{1 2\n3\n", encoding="utf-8")
    calc = mode.rpn_calculator

    with pytest.raises(UnterminatedTokenError) as info:
        mode.execute_stacker_dotfile(rc, stackerrc=True)

    assert include_location_of(info.value) == ((str(rc.resolve()), 2, "{1 2"), [])
    assert calc.variables["a"] == 1
    assert (calc.current_file, calc.current_line, calc.source_lines) == (None, None, {})
