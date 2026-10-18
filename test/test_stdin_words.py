"""`read-line` and `read-stdin` read standard input as text; `read` keeps parsing it as code."""

import io

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError


def run(program: str, text: str, monkeypatch) -> list[object]:
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


def test_read_line_gives_one_line_without_its_break(monkeypatch):
    assert run("read-line read-line", "a b\nc\n", monkeypatch) == ["a b", "c"]


def test_read_line_strips_a_windows_line_break(monkeypatch):
    assert run("read-line", "a\r\n", monkeypatch) == ["a"]


def test_read_line_at_the_end_is_null(monkeypatch):
    assert run("read-line read-line", "only\n", monkeypatch) == ["only", None]


def test_a_last_line_without_a_break_is_still_a_line(monkeypatch):
    assert run("read-line read-line", "a", monkeypatch) == ["a", None]


def test_read_stdin_gives_the_rest(monkeypatch):
    assert run("read-line read-stdin read-stdin", "a\nb\nc\n", monkeypatch) == ["a", "b\nc\n", ""]


def test_the_lines_are_strings_not_code(monkeypatch):
    assert run("read-line", "3 4 +\n", monkeypatch) == ["3 4 +"]


@pytest.mark.parametrize("word", ["read-line", "read-stdin"])
def test_a_closed_input_is_reported_by_the_word(monkeypatch, word):
    closed = io.StringIO("x")
    closed.close()
    monkeypatch.setattr("sys.stdin", closed)
    with pytest.raises(StackerRuntimeError, match=f"`{word}` cannot read standard input"):
        Stacker().process_expression(word)
