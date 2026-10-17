"""`-e` reports an error the way the REPL does: on stderr, without a caret."""

import pytest

from stacker import Stacker
from stacker.runtime.exec_modes import CommandLineMode, ExecutionMode


def run_e(expression: str, capsys) -> tuple[int, str, str]:
    mode = CommandLineMode(Stacker())
    with pytest.raises(SystemExit) as info:
        mode.run(expression)
    out, err = capsys.readouterr()
    return info.value.code, out, err


def test_the_error_goes_to_stderr_with_status_1(capsys):
    code, out, err = run_e("1 zzz 2", capsys)
    assert code == 1
    assert out == ""
    assert "UndefinedSymbolError" in err
    assert "`zzz` is not defined" in err


def test_no_caret_under_the_last_word(capsys):
    _, out, err = run_e("1 zzz 2", capsys)
    assert "^" not in out + err


def test_no_color_escapes_when_not_a_terminal(capsys):
    _, out, err = run_e("drop 1 2", capsys)
    assert "\x1b[" not in out + err


def test_the_hint_is_the_same_as_in_a_script(capsys):
    _, _, err = run_e("1 zzz 2", capsys)
    assert "hint:" in err
    assert "`:zzz`" in err


def test_the_subscript_hint_does_not_suggest_brackets():
    hint = ExecutionMode(Stacker())._get_error_hint(TypeError("'int' object is not subscriptable"))
    assert hint is not None
    assert "'[]'" not in hint
    assert "nth" in hint
