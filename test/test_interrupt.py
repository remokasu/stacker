"""Ctrl-C: at the REPL it cancels the line and the session goes on; it ends a script or -e with no traceback.

The REPL's tests type through its real prompt: the keys come from a pipe and
the screen is discarded, so no terminal is involved.
"""

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from stacker.runtime.exec_modes import repl_mode
from stacker.runtime.exec_modes.repl_mode import ReplMode
from stacker.stacker import Stacker

REPO_ROOT = Path(__file__).resolve().parent.parent

ENTER = "\r"
CTRL_C = "\x03"
CTRL_D = "\x04"

#: Says when it is about to loop, on the stream that is not buffered
LONG_LOOP = '"kept" echo "ready" echo-err {1 drop} 100000000 times'

needs_signals = pytest.mark.skipif(os.name == "nt", reason="the signal cannot be sent to one process on Windows")


def _interrupt():
    raise KeyboardInterrupt


def _repl_with_interrupt() -> ReplMode:
    """A REPL with the word `interrupt`, which acts as Ctrl-C pressed while a line runs."""
    stacker = Stacker()
    stacker.register_plugin("interrupt", _interrupt, push_result_to_stack=False)
    return ReplMode(stacker)


@pytest.fixture
def typed(tmp_path, monkeypatch):
    """Types ``keys`` at a REPL's real prompt, then Ctrl-D; gives the REPL back."""
    monkeypatch.setattr(repl_mode, "history_file_path", tmp_path / "history")

    def run(keys: str, repl: ReplMode | None = None) -> ReplMode:
        repl = repl or ReplMode(Stacker())
        with create_pipe_input() as pipe:
            pipe.send_text(keys + CTRL_D)
            with create_app_session(input=pipe, output=DummyOutput()):
                try:
                    repl.run()
                except KeyboardInterrupt:  # (it would otherwise stop the whole test session)
                    pytest.fail("Ctrl-C ended the REPL")
                except SystemExit:
                    pass
        return repl

    return run


def _stack(repl: ReplMode) -> list:
    return list(repl.rpn_calculator.stack)


def test_the_prompt_runs_lines_and_continuations(typed):
    repl = typed(f"1 2 +{ENTER}3 *{ENTER}{{1{ENTER}3{ENTER}+}}{ENTER}")
    assert _stack(repl)[0] == 9
    assert len(_stack(repl)) == 2


def test_ctrl_c_at_the_prompt_keeps_the_stack_and_the_session(typed, capsys):
    repl = typed(f"1 2{ENTER}{CTRL_C}3{ENTER}")
    assert _stack(repl) == [1, 2, 3]
    err = capsys.readouterr().err
    assert "KeyboardInterrupt" in err
    assert "Traceback" not in err


def test_ctrl_c_drops_the_text_being_typed(typed):
    assert _stack(typed(f"1 2 3{CTRL_C}4{ENTER}")) == [4]


def test_ctrl_c_drops_a_continuation(typed):
    assert _stack(typed(f"{{1{ENTER}{CTRL_C}7{ENTER}")) == [7]


def test_ctrl_c_while_a_line_runs_leaves_what_it_had_done(typed, capsys):
    repl = typed(f"5{ENTER}1 interrupt 2{ENTER}6{ENTER}", _repl_with_interrupt())
    assert _stack(repl) == [5, 1, 6]
    assert "Traceback" not in capsys.readouterr().err


def test_ctrl_c_keeps_the_variables_and_the_definitions(typed):
    keys = f"1 :kept set{ENTER}{{x}} {{x 2 *}} :twice defun{ENTER}interrupt{ENTER}kept twice{ENTER}"
    assert _stack(typed(keys, _repl_with_interrupt())) == [2]


def test_ctrl_c_inside_read_comes_back_to_the_prompt(typed, monkeypatch):
    monkeypatch.setattr("builtins.input", _interrupt)
    assert _stack(typed(f"read{ENTER}8{ENTER}")) == [8]


def test_try_does_not_catch_ctrl_c(typed):
    repl = typed(f"{{interrupt}} {{drop 99}} try{ENTER}", _repl_with_interrupt())
    assert _stack(repl) == []


def test_a_file_interrupted_while_included_can_be_included_again(typed, tmp_path, capsys):
    calls = []

    def interrupt_once():
        calls.append(1)
        if len(calls) == 1:
            raise KeyboardInterrupt

    stacker = Stacker()
    stacker.register_plugin("interrupt_once", interrupt_once, push_result_to_stack=False)
    path = tmp_path / "interrupted.stk"
    path.write_text("interrupt_once\n1 :reached set\n")
    include = f"'{path}' include{ENTER}"

    repl = typed(f"{include}{include}reached script-path{ENTER}", ReplMode(stacker))

    assert _stack(repl) == [1, None]  # `reached` was set by the second include; `script-path` is None again
    assert "error" not in capsys.readouterr().err


def test_exit_ends_the_repl_after_ctrl_c(typed):
    repl = typed(f"{CTRL_C}9{ENTER}exit{ENTER}10{ENTER}")
    assert _stack(repl) == [9]


def test_a_compiled_loop_interrupted_once_runs_the_same_afterwards(typed):
    """The loop body is compiled by its eighth run; an interruption in the middle must not spoil it."""
    calls = []

    def interrupt_once():
        calls.append(1)
        if len(calls) == 50:
            raise KeyboardInterrupt

    stacker = Stacker()
    stacker.register_plugin("interrupt_once", interrupt_once, push_result_to_stack=False)
    defun = "{n} {0 :acc set 1 n :i {acc i + :acc set interrupt_once} do acc} :sum defun"
    keys = f"{defun}{ENTER}100 sum{ENTER}clear{ENTER}100 sum{ENTER}20 sum{ENTER}"

    repl = typed(keys, ReplMode(stacker))

    assert _stack(repl) == [5050, 210]
    assert len(calls) == 50 + 100 + 20


def test_debug_shows_where_ctrl_c_stopped_the_line(typed, capsys):
    repl = _repl_with_interrupt()
    repl.debug_mode()
    assert _stack(typed(f"interrupt{ENTER}1{ENTER}", repl)) == [1]
    assert "Traceback" in capsys.readouterr().err


#: How long a program gets to say `ready` or to end before the test kills it
PATIENCE = 30


@pytest.fixture
def started(tmp_path):
    """Starts the command line with ``tmp_path`` as its home and working directory; kills it when the test ends."""
    processes = []

    def start(*args: str) -> subprocess.Popen:
        # A new home would hide the user site-packages, so pass this sys.path on
        paths = [str(REPO_ROOT), *(path for path in sys.path if path)]
        env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONPATH=os.pathsep.join(paths))
        process = subprocess.Popen(
            [sys.executable, "-m", "stacker", *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        processes.append(process)
        return process

    yield start
    for process in processes:
        if process.poll() is None:
            process.kill()
            process.wait()


def _interrupt_once_ready(process: subprocess.Popen) -> None:
    """Waits for the program to say `ready`, then sends the signal Ctrl-C sends.

    The wait is cut short by killing the program, so a program that never
    says it is ready fails the test instead of hanging it.
    """
    timer = threading.Timer(PATIENCE, process.kill)
    timer.start()
    try:
        for line in process.stderr:  # (what is read here is gone for communicate(): it reads the rest)
            if line.strip() == "ready":
                process.send_signal(signal.SIGINT)
                return
    finally:
        timer.cancel()
    pytest.fail("the program ended before it said it was ready")


def test_the_command_line_starts_the_repl_on_piped_input(started):
    process = started()
    out, _ = process.communicate("1 2 +\n3 * echo\n", timeout=PATIENCE)
    assert process.returncode == 0
    assert "9\n" in out
    assert "See you!" in out


@needs_signals
def test_a_real_interrupt_stops_a_loop_at_the_repl_and_the_session_goes_on(started):
    process = started()
    process.stdin.write(LONG_LOOP + "\n")
    process.stdin.flush()
    _interrupt_once_ready(process)
    out, err = process.communicate("6 echo\n", timeout=PATIENCE)
    assert process.returncode == 0
    assert "6\n" in out
    assert "KeyboardInterrupt" in err
    assert "Traceback" not in err


@needs_signals
@pytest.mark.parametrize("mode", ["script", "-e"])
def test_an_interrupted_program_ends_by_the_signal_with_no_traceback(tmp_path, started, mode):
    (tmp_path / "s.stk").write_text(LONG_LOOP + "\n")
    process = started(*(["s.stk"] if mode == "script" else ["-e", LONG_LOOP]))
    _interrupt_once_ready(process)
    out, err = process.communicate(timeout=PATIENCE)
    assert err == ""
    assert out == "kept\n"  # what it printed is not lost
    # Ended by the signal, not by an exit code: a shell loop around the program then stops too
    assert process.returncode == -signal.SIGINT


@needs_signals
def test_debug_shows_where_the_interrupt_stopped_a_program(tmp_path, started):
    (tmp_path / "s.stk").write_text(LONG_LOOP + "\n")
    process = started("--debug", "s.stk")
    _interrupt_once_ready(process)
    _, err = process.communicate(timeout=PATIENCE)
    assert "Traceback" in err
    assert process.returncode == -signal.SIGINT


def test_any_other_uncaught_exception_still_prints_its_traceback(tmp_path, started):
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "crash.py").write_text(
        "class Crash(BaseException):\n"
        "    pass\n"
        "def crash():\n"
        "    raise Crash('crashed')\n"
        "def setup(stacker):\n"
        "    stacker.register_plugin('crash', crash)\n"
    )
    process = started("-e", "crash")
    _, err = process.communicate(timeout=PATIENCE)
    assert process.returncode == 1
    assert "Traceback" in err
    assert "crashed" in err
