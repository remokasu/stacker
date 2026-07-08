"""Integration tests for REPL continuation input (SPEC-0001).

Drives ReplMode.run() with a mocked get_input: continuation for strings,
block comments, blocks, and arrays is judged by the lexer scan core, so
REPL behavior cannot diverge from script mode.
"""

from stacker.stacker import Stacker
from stacker.runtime.exec_modes.repl_mode import ReplMode


def _run_repl(monkeypatch, inputs):
    """Run the REPL over the given input lines, then simulate EOF."""
    stacker = Stacker()
    repl = ReplMode(stacker)
    remaining = list(inputs)

    def fake_input(prompt_text, multiline=False):
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    monkeypatch.setattr(repl, "get_input", fake_input)
    monkeypatch.setattr(repl, "disp", lambda: None)  # Silence stack printing
    repl.run()
    return stacker


def test_multiline_string_continuation(monkeypatch):
    stacker = _run_repl(monkeypatch, ['"abc', 'def"'])
    assert list(stacker.stack) == ["abc\ndef"]


def test_multiline_triple_string_continuation(monkeypatch):
    stacker = _run_repl(monkeypatch, ['"""first', 'second"""'])
    assert list(stacker.stack) == ["first\nsecond"]


def test_block_comment_continuation(monkeypatch):
    stacker = _run_repl(monkeypatch, ["#| note", "still |# 42"])
    assert list(stacker.stack) == [42]


def test_braces_inside_block_comment_do_not_trigger_continuation(monkeypatch):
    # Lexically complete on one line: must not ask for more input
    # (there are no more lines to give — a continuation request would
    # surface as an unexpected EOF ending the expression early)
    stacker = _run_repl(monkeypatch, ["{ #| a { b |# 1 2 + }", "eval"])
    assert list(stacker.stack) == [3]


def test_block_continuation(monkeypatch):
    stacker = _run_repl(monkeypatch, ["{1", "3", "+}", "eval"])
    assert list(stacker.stack) == [4]


def test_array_rows_joined_with_semicolon(monkeypatch):
    stacker = _run_repl(monkeypatch, ["[1 2 3", "4 5 6]"])
    assert list(stacker.stack) == [[[1, 2, 3], [4, 5, 6]]]


def test_array_continuation_end_escape(monkeypatch):
    # "end" aborts continuation; the unterminated array then surfaces
    # as an error (printed by the REPL loop) instead of hanging
    stacker = _run_repl(monkeypatch, ["[1 2", "end"])
    assert len(stacker.stack) == 0
