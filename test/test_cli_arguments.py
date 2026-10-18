"""The command line passes what follows the script name to the program, and `args` reads it."""

import os
import subprocess
import sys

import pytest


def stacker(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    # HOME points nowhere so that a ~/.stackerrc of the developer does not run;
    # the module search path is handed over since a user site lives under HOME
    env = {**os.environ, "HOME": "/nonexistent", "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    return subprocess.run(
        [sys.executable, "-m", "stacker", *argv],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def script(tmp_path):
    path = tmp_path / "s.stk"
    path.write_text("args echo\n")
    return str(path)


def test_the_arguments_after_the_script_are_strings(script):
    result = stacker(script, "200", "100")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "['200' '100']\n"


def test_no_arguments_is_an_empty_list(script):
    assert stacker(script).stdout == "[]\n"


def test_a_double_dash_lets_an_option_like_argument_through(script):
    assert stacker(script, "--", "--flag", "-x").stdout == "['--flag' '-x']\n"


def test_an_option_before_the_script_is_an_option(script):
    assert stacker("--recursion-limit", "100", script, "x").stdout == "['x']\n"


def test_with_e_every_positional_is_an_argument():
    assert stacker("-e", "args echo", "a", "b").stdout == "['a' 'b']\n"


def test_the_arguments_are_read_as_text_and_converted_by_the_program(tmp_path):
    path = tmp_path / "add.stk"
    path.write_text("args 0 at int args 1 at int + echo\n")
    assert stacker(str(path), "2", "40").stdout == "42\n"


def test_read_line_and_read_stdin_from_the_command_line():
    result = stacker("-e", "read-line echo read-line echo read-stdin echo", stdin="first\nsecond\nrest\nof it\n")
    assert result.stdout == "first\nsecond\nrest\nof it\n\n"
