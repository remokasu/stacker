"""Tests for ``Stacker.run_file``: running a script file as the one the interpreter was started on."""

from __future__ import annotations

import pytest

from stacker.engine.include import expressions_of
from stacker.error import (
    IncludeError,
    StackerSyntaxError,
    UndefinedSymbolError,
    UnterminatedTokenError,
    include_location_of,
)
from stacker.stacker import Stacker


@pytest.fixture
def stacker():
    return Stacker()


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_runs_on_the_root_stack_and_ans_sees_the_result(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1 2 +\n10\n")
    stacker.run_file(script)
    assert list(stacker.stack) == [3, 10]
    stacker.process_expression("ans")
    assert stacker.stack[-1] == 10


def test_main_script_words(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "main-script-path\nmain?\nscript-path\nscript-dir\n")
    stacker.run_file(script)
    resolved = str(script.resolve())
    assert list(stacker.stack) == [resolved, True, resolved, str(script.resolve().parent)]
    assert stacker.main_script == resolved


def test_not_the_main_script(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "main-script-path\nmain?\nscript-path\n")
    stacker.run_file(script, main=False)
    assert list(stacker.stack) == [None, False, str(script.resolve())]
    assert stacker.main_script is None


def test_accepts_a_string_path(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "7\n")
    stacker.run_file(str(script))
    assert list(stacker.stack) == [7]


def test_the_location_stays_after_the_file_ends(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1\n2\n")
    stacker.run_file(script)
    assert stacker.current_file == str(script.resolve())
    assert stacker.current_line == 2
    assert stacker.source_lines == {1: "1", 2: "2"}


def test_restore_location_puts_the_previous_position_back(stacker, tmp_path):
    script = _write(tmp_path, "rc.stk", "1 :a set\n")
    stacker.current_file, stacker.current_line = "earlier.stk", 3
    stacker.source_lines[3] = "old"
    source_lines = stacker.source_lines
    stacker.run_file(script, main=False, restore_location=True)
    assert (stacker.current_file, stacker.current_line) == ("earlier.stk", 3)
    assert stacker.source_lines is source_lines
    assert stacker.source_lines == {3: "old"}
    assert stacker.variables["a"] == 1


def test_restore_location_attaches_the_position_to_an_error(stacker, tmp_path):
    script = _write(tmp_path, "rc.stk", "1\nfoo\n")
    with pytest.raises(UndefinedSymbolError) as info:
        stacker.run_file(script, main=False, restore_location=True)
    assert include_location_of(info.value) == ((str(script.resolve()), 2, "foo"), [])
    assert (stacker.current_file, stacker.current_line, stacker.source_lines) == (None, None, {})


def test_without_restore_an_error_carries_no_position(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1\nfoo\n")
    with pytest.raises(UndefinedSymbolError) as info:
        stacker.run_file(script)
    assert include_location_of(info.value) is None
    assert stacker.current_line == 2


def test_intercept_skips_the_expressions_it_claims(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1\nskip me\n2\n")
    seen = []

    def intercept(expression):
        seen.append(expression)
        return expression == "skip me"

    stacker.run_file(script, intercept=intercept)
    assert seen == ["1", "skip me", "2"]
    assert list(stacker.stack) == [1, 2]


def test_an_unterminated_file_runs_what_came_before_it(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1 :a set\n{1 2\n3\n")
    with pytest.raises(UnterminatedTokenError):
        stacker.run_file(script)
    assert stacker.variables["a"] == 1
    assert stacker.current_line == 2


def test_a_function_the_file_defines_keeps_the_file_as_its_own(stacker, tmp_path):
    rc = _write(tmp_path, "rc.stk", "{x} {script-path} :where defun\n")
    stacker.run_file(rc, main=False, restore_location=True)
    stacker.process_expression("1 where")
    assert stacker.stack[-1] == str(rc.resolve())


def test_relative_includes_resolve_against_the_file(stacker, tmp_path):
    _write(tmp_path, "lib/helper.stk", "{x} {x 10 +} :add10 defun\n")
    script = _write(tmp_path, "lib/main.stk", '"helper.stk" include\n5 add10\n')
    stacker.run_file(script)
    assert list(stacker.stack) == [15]


def test_a_file_including_itself_is_circular(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", '"s.stk" include\n')
    with pytest.raises(IncludeError, match="Circular include"):
        stacker.run_file(script)
    assert stacker._includes.stack == []


def test_break_outside_a_loop_is_a_syntax_error(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "break\n")
    with pytest.raises(StackerSyntaxError, match="inside a loop"):
        stacker.run_file(script)


def test_a_missing_file_leaves_the_interpreter_untouched(stacker, tmp_path):
    with pytest.raises(FileNotFoundError):
        stacker.run_file(tmp_path / "nope.stk")
    assert stacker.main_script == str((tmp_path / "nope.stk").resolve())  # set before the file is opened
    assert stacker.current_file is None
    assert stacker._includes.stack == []


def test_source_lines_keep_line_endings_out(stacker, tmp_path):
    script = tmp_path / "s.stk"
    script.write_bytes(b"1\r\n2\r\n3")  # CRLF, no newline at the end
    stacker.run_file(script)
    assert stacker.source_lines == {1: "1", 2: "2", 3: "3"}
    assert list(stacker.stack) == [1, 2, 3]


def test_an_empty_file_runs_nothing(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "")
    stacker.run_file(script)
    assert list(stacker.stack) == []
    assert stacker.current_line is None


def test_exit_inside_the_file_still_restores_the_location(stacker, tmp_path):
    rc = _write(tmp_path, "rc.stk", "1\n3 exit-code\n")
    stacker.current_file = "earlier.stk"
    with pytest.raises(SystemExit) as info:
        stacker.run_file(rc, main=False, restore_location=True)
    assert info.value.code == 3
    assert stacker.current_file == "earlier.stk"
    assert stacker._includes.stack == []


def test_an_error_inside_a_file_the_rc_includes_keeps_that_position(stacker, tmp_path):
    included = _write(tmp_path, "inc.stk", "1\nfoo\n")
    rc = _write(tmp_path, "rc.stk", '"inc.stk" include\n')
    with pytest.raises(UndefinedSymbolError) as info:
        stacker.run_file(rc, main=False, restore_location=True)
    assert include_location_of(info.value) == ((str(included.resolve()), 2, "foo"), [(str(rc.resolve()), 1)])


def test_an_error_leaves_the_include_stack_balanced(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "foo\n")
    with pytest.raises(UndefinedSymbolError):
        stacker.run_file(script)
    assert stacker._includes.stack == []


def test_an_error_raised_by_intercept_carries_the_line(stacker, tmp_path):
    script = _write(tmp_path, "s.stk", "1\n2\n")

    def intercept(expression):
        if expression == "2":
            raise ValueError("stop")
        return False

    with pytest.raises(ValueError) as info:
        stacker.run_file(script, intercept=intercept, restore_location=True)
    assert include_location_of(info.value) == ((str(script.resolve()), 2, "2"), [])
    assert list(stacker.stack) == [1]


class TestExpressionsOf:
    def test_tells_each_line_before_yielding(self):
        lines = []
        got = list(expressions_of("1 2 +\n\n[1\n2]\n", lines.append))
        assert got == ["1 2 +", "[1\n2]"]
        assert lines == [1, 3]

    def test_an_empty_text_yields_nothing(self):
        lines = []
        assert list(expressions_of("", lines.append)) == []
        assert lines == []

    def test_an_unterminated_construct_is_reported_after_what_came_before(self):
        lines = []
        expressions = expressions_of("1\n{2\n3\n", lines.append)
        assert next(expressions) == "1"
        with pytest.raises(UnterminatedTokenError):
            next(expressions)
        assert lines == [1, 2]


class TestLocation:
    """``Stacker.location``: the file, line and line text the interpreter is on."""

    def test_is_empty_before_anything_ran(self, stacker):
        assert stacker.location == (None, None, None)

    def test_names_the_last_expression_after_a_script_ran(self, stacker, tmp_path):
        script = _write(tmp_path, "s.stk", "1\n\n2 drop\n")
        stacker.run_file(script)
        assert stacker.location == (str(script.resolve()), 3, "2 drop")

    def test_names_the_line_a_script_failed_on(self, stacker, tmp_path):
        script = _write(tmp_path, "s.stk", "1\n{\n  foo\n} eval\n")
        with pytest.raises(UndefinedSymbolError):
            stacker.run_file(script)
        assert stacker.location == (str(script.resolve()), 2, "{")

    def test_names_the_line_an_unterminated_construct_started_on(self, stacker, tmp_path):
        script = _write(tmp_path, "s.stk", '"a" drop\n{1 2\n3\n')
        with pytest.raises(UnterminatedTokenError):
            stacker.run_file(script)
        assert stacker.location == (str(script.resolve()), 2, "{1 2")

    def test_is_put_back_when_the_location_is_restored(self, stacker, tmp_path):
        first = _write(tmp_path, "first.stk", "1 drop\n2 drop\n")
        rc = _write(tmp_path, "rc.stk", "3 drop\n")
        stacker.run_file(first)
        stacker.run_file(rc, main=False, restore_location=True)
        assert stacker.location == (str(first.resolve()), 2, "2 drop")

    def test_is_put_back_when_a_file_run_with_the_location_restored_fails(self, stacker, tmp_path):
        first = _write(tmp_path, "first.stk", "1 drop\n2 drop\n")
        rc = _write(tmp_path, "rc.stk", "3 drop\nfoo\n")
        stacker.run_file(first)
        with pytest.raises(UndefinedSymbolError):
            stacker.run_file(rc, main=False, restore_location=True)
        assert stacker.location == (str(first.resolve()), 2, "2 drop")

    def test_names_the_including_line_when_an_included_file_fails(self, stacker, tmp_path):
        _write(tmp_path, "inc.stk", "1 drop\nbar\n")
        script = _write(tmp_path, "main.stk", '1 drop\n"inc.stk" include\n')
        with pytest.raises(UndefinedSymbolError) as info:
            stacker.run_file(script)
        assert stacker.location == (str(script.resolve()), 2, '"inc.stk" include')
        assert include_location_of(info.value)[0] == (str((tmp_path / "inc.stk").resolve()), 2, "bar")

    def test_cannot_be_assigned(self, stacker):
        with pytest.raises(AttributeError):
            stacker.location = ("x", 1, "y")
