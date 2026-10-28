"""Tests for the console: where the words that print and read go."""

from __future__ import annotations

import contextlib
import copy
import io
import os

import pytest

from stacker import Console, Stacker, StreamConsole
from stacker.engine import console
from stacker.error import StackerRuntimeError


def _console(stdin: str = "") -> StreamConsole:
    return StreamConsole(stdout=io.StringIO(), stderr=io.StringIO(), stdin=io.StringIO(stdin))


# --- the default console is the sys streams, looked up when a word runs


def test_outside_any_entry_point_the_default_console_is_in_effect():
    Stacker()
    assert console.current() is console.DEFAULT_CONSOLE


def test_default_console_writes_to_sys_stdout_replaced_after_construction(monkeypatch):
    stacker = Stacker()
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    stacker.eval('"a" echo 1 2 disp newline vars')
    assert out.getvalue().startswith("a\n[1 2]\n\n")


def test_default_console_honours_redirect_stdout():
    stacker = Stacker()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        stacker.eval('"b" echo')
    assert out.getvalue() == "b\n"


def test_default_console_reads_sys_stdin_replaced_after_construction(monkeypatch):
    stacker = Stacker()
    monkeypatch.setattr("sys.stdin", io.StringIO("1 2 +\nline\n"))
    assert list(stacker.eval("read eval read-line")) == [3, "line"]


# --- an injected console


def test_output_words_write_to_the_injected_console(capsys):
    con = _console()
    stacker = Stacker(console=con)
    stacker.eval('"e" echo "p" print "c" printc newline 1 2 disp 5 :x set vars "w" echo-err "q" print-err')
    out = con.stdout().getvalue()
    assert out.startswith("e\np\nc\n[1 2]\n")
    assert "x = 5" in out
    assert con.stderr().getvalue() == "w\nq\n"
    assert capsys.readouterr() == ("", "")


def test_listing_words_write_to_the_injected_console(capsys):
    con = _console()
    stacker = Stacker(console=con)
    stacker.eval("{x} {x 1 +} :inc defun {x} {x 1 +} :m defmacro funcs macros operators")
    out = con.stdout().getvalue()
    assert "inc: args=" in out
    assert "(prelude)" in out
    assert "m: " in out
    assert "Regular operators:" in out
    assert capsys.readouterr() == ("", "")


def test_read_reads_the_injected_console_and_ends_with_eof_error():
    con = _console("1 2 +\n")
    stacker = Stacker(console=con)
    assert list(stacker.eval("read eval")) == [3]
    with pytest.raises(EOFError):
        stacker.eval("read")


def test_read_line_and_read_stdin_read_the_injected_console():
    con = _console("first\nrest\nof it\n")
    stacker = Stacker(console=con)
    assert list(stacker.eval("read-line read-stdin")) == ["first", "rest\nof it\n"]


def test_byte_words_use_the_injected_streams():
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    con = StreamConsole(stdout=stdout, stdin=io.TextIOWrapper(io.BytesIO(bytes([1, 2]))))
    stacker = Stacker(console=con)
    stacker.eval('"hi" "utf-8" encode write-stdout-bytes')
    assert stdout.buffer.getvalue() == b"hi"
    assert list(stacker.eval("read-stdin-bytes")) == [[1, 2]]


def test_include_require_and_run_file_run_under_the_console(tmp_path, monkeypatch):
    (tmp_path / "inc.stk").write_text('"from include" echo\n', encoding="utf-8")
    (tmp_path / "req.stk").write_text('"from require" echo\n', encoding="utf-8")
    (tmp_path / "main.stk").write_text('"from run_file" echo\n"req.stk" require\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    con = _console()
    stacker = Stacker(console=con)
    stacker.include("inc.stk")
    stacker.run_file(tmp_path / "main.stk")
    assert con.stdout().getvalue() == "from include\nfrom run_file\nfrom require\n"


def test_a_block_or_function_runs_under_the_console_of_the_call():
    con = _console()
    stacker = Stacker(console=con)
    stacker.process_expression('{x} {x echo} :show defun [1 2] {x} {x show} dolist')
    assert con.stdout().getvalue() == "1\n2\n"


def test_two_interpreters_keep_their_own_consoles():
    a, b = _console(), _console()
    first, second = Stacker(console=a), Stacker(console=b)
    first.eval('"a" echo')
    second.eval('"b" echo')
    first.eval('"a again" echo')
    assert (a.stdout().getvalue(), b.stdout().getvalue()) == ("a\na again\n", "b\n")


def test_a_nested_entry_point_restores_the_outer_console():
    a, b = _console(), _console()
    inner = Stacker(console=b)
    outer = Stacker(console=a)
    outer.register_plugin("call-inner", lambda: inner.eval('"inner" echo'), push_result_to_stack=False)
    outer.eval('"before" echo call-inner "after" echo')
    assert a.stdout().getvalue() == "before\nafter\n"
    assert b.stdout().getvalue() == "inner\n"
    assert console.current() is console.DEFAULT_CONSOLE


def test_an_error_restores_the_previous_console():
    stacker = Stacker(console=_console())
    with pytest.raises(Exception):  # noqa: B017 - any error will do
        stacker.eval("foo")
    assert console.current() is console.DEFAULT_CONSOLE


def test_exit_still_raises_system_exit_and_try_does_not_catch_it():
    con = _console()
    stacker = Stacker(console=con)
    with pytest.raises(SystemExit) as info:
        stacker.eval('{3 exit-code} {"caught" echo} try')
    assert info.value.code == 3
    assert con.stdout().getvalue() == ""
    assert console.current() is console.DEFAULT_CONSOLE


def test_copies_share_the_console():
    con = StreamConsole(stdout=open(os.devnull, "w"))  # noqa: SIM115 - closed below
    try:
        stacker = Stacker(console=con)
        assert copy.deepcopy(stacker).console is con
        assert stacker.copy().console is con
        assert copy.copy(con) is con
    finally:
        con.stdout().close()


def test_a_child_core_takes_its_parents_console():
    con = _console()
    stacker = Stacker(console=con)
    assert Stacker(parent=stacker).console is con


def test_a_stream_console_falls_back_to_sys_for_streams_not_given(monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    con = StreamConsole(stderr=io.StringIO())
    Stacker(console=con).eval('"x" echo')
    assert out.getvalue() == "x\n"


def test_input_line_flushes_output_first_and_drops_the_line_break():
    class Recording(io.StringIO):
        def __init__(self, log: list[str], name: str) -> None:
            super().__init__()
            self.log, self.name = log, name

        def flush(self) -> None:
            self.log.append(self.name)

    log: list[str] = []
    con = StreamConsole(stdout=Recording(log, "out"), stderr=Recording(log, "err"), stdin=io.StringIO("a\r\nb"))
    assert con.input_line() == "a\r"
    assert log == ["err", "out"]
    assert con.input_line() == "b"


def test_a_subclass_can_override_one_stream():
    class Collecting(Console):
        def __init__(self) -> None:
            self.out = io.StringIO()

        def stdout(self):
            return self.out

    con = Collecting()
    Stacker(console=con).eval('"z" echo')
    assert con.out.getvalue() == "z\n"


# --- a stream that cannot carry a character fails the same way, injected or not


def _ascii_stream() -> io.TextIOWrapper:
    return io.TextIOWrapper(io.BytesIO(), encoding="ascii")


@pytest.mark.parametrize("program", ['"\\u00e9" echo', '"\\u00e9" :x set vars', '"\\u00e9" 1 disp'])
def test_an_unencodable_character_fails_alike_injected_or_through_sys(monkeypatch, program):
    def outcome(run):
        try:
            run()
        except Exception as error:  # noqa: BLE001 - the outcome is what is compared
            return type(error), str(error)
        return None

    injected = outcome(lambda: Stacker(console=StreamConsole(stdout=_ascii_stream())).eval(program))
    monkeypatch.setattr("sys.stdout", _ascii_stream())
    through_sys = outcome(lambda: Stacker().eval(program))
    assert injected == through_sys
    assert injected is not None


def test_echo_reports_an_unencodable_character_as_a_runtime_error():
    stacker = Stacker(console=StreamConsole(stdout=_ascii_stream()))
    with pytest.raises(StackerRuntimeError, match="cannot write"):
        stacker.eval('"\\u00e9" echo')


# --- where the console is in effect, and where it is not


def test_evaluate_is_not_an_entry_point_and_keeps_the_callers_console(capsys):
    from stacker.syntax.parser import parse_expression

    con = _console()
    Stacker(console=con).evaluate(parse_expression('"x" echo'))
    assert capsys.readouterr().out == "x\n"
    assert con.stdout().getvalue() == ""


def test_a_new_thread_starts_with_the_default_console():
    import threading

    seen = []
    threads = []

    def start_thread():
        thread = threading.Thread(target=lambda: seen.append(console.current()))
        thread.start()
        threads.append(thread)

    stacker = Stacker(console=_console())
    stacker.register_plugin("in-thread", start_thread, push_result_to_stack=False)
    stacker.eval("in-thread")
    threads[0].join(timeout=5)
    assert seen == [console.DEFAULT_CONSOLE]


@pytest.mark.parametrize(
    "run",
    [
        pytest.param(lambda s, tmp: s.process_expression("break"), id="process_expression-break"),
        pytest.param(lambda s, tmp: s.eval("{x} {x} 1 2 3"), id="eval-ok"),
        pytest.param(lambda s, tmp: s.run_file(_script(tmp, "foo\n")), id="run_file-error"),
        pytest.param(lambda s, tmp: s.include(str(_script(tmp, "1 0 /\n"))), id="include-error"),
    ],
)
def test_every_entry_point_restores_the_previous_console(tmp_path, run):
    stacker = Stacker(console=_console())
    with contextlib.suppress(Exception):
        run(stacker, tmp_path)
    assert console.current() is console.DEFAULT_CONSOLE


def test_keyboard_interrupt_restores_the_previous_console():
    stacker = Stacker(console=_console())

    def interrupt():
        raise KeyboardInterrupt

    stacker.register_plugin("interrupt", interrupt, push_result_to_stack=False)
    with pytest.raises(KeyboardInterrupt):
        stacker.eval("interrupt")
    assert console.current() is console.DEFAULT_CONSOLE


def _script(tmp_path, text):
    path = tmp_path / "s.stk"
    path.write_text(text, encoding="utf-8")
    return path


def test_stream_console_passes_over_an_output_that_cannot_be_flushed():
    closed = io.StringIO()
    closed.close()
    con = StreamConsole(stdout=closed, stderr=closed, stdin=io.StringIO("ok\n"))
    assert con.input_line() == "ok"


def test_stream_console_without_any_stdin_says_so(monkeypatch):
    monkeypatch.setattr("sys.stdin", None)
    with pytest.raises(RuntimeError, match="lost sys.stdin"):
        StreamConsole(stdout=io.StringIO()).input_line()
