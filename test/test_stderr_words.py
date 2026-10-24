"""`echo-err`, `print-err`, `printc-err` and `write-stderr-bytes` write to standard error what their twins write to standard output."""

import io

import pytest

from stacker import Stacker
from stacker.error import StackerError, StackerRuntimeError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestTheTextWords:
    @pytest.mark.parametrize("word", ["echo-err", "print-err"])
    def test_a_line_goes_to_standard_error_only(self, capsys, word):
        assert run(f'"warn" {word}') == []
        captured = capsys.readouterr()
        assert captured.err == "warn\n"
        assert captured.out == ""

    def test_values_show_as_echo_shows_them(self, capsys):
        run("[1 2 3] echo 3.5 echo :x echo true echo")
        by_echo = capsys.readouterr().out
        run("[1 2 3] echo-err 3.5 echo-err :x echo-err true echo-err")
        assert capsys.readouterr().err == by_echo == "[1 2 3]\n3.5\nx\ntrue\n"

    def test_printc_err_adds_no_line_break(self, capsys):
        run('"a" printc-err "b" printc-err')
        assert capsys.readouterr().err == "ab"

    def test_output_and_error_are_kept_apart(self, capsys):
        run('"out" echo "err" echo-err')
        captured = capsys.readouterr()
        assert captured.out == "out\n"
        assert captured.err == "err\n"

    def test_an_unwritable_character_names_standard_error(self, monkeypatch):
        monkeypatch.setattr("sys.stderr", io.TextIOWrapper(io.BytesIO(), encoding="ascii"))
        with pytest.raises(StackerRuntimeError, match="cannot write 'é' to standard error, whose encoding is ascii"):
            run('"é" echo-err')


class TestWriteStderrBytes:
    def test_bytes_go_to_standard_error_as_they_are(self, capsysbinary):
        assert run("[72 105 10] write-stderr-bytes") == []
        captured = capsysbinary.readouterr()
        assert captured.err == b"Hi\n"
        assert captured.out == b""

    def test_an_array_is_taken_too(self, capsysbinary):
        run("[72 105] array write-stderr-bytes")
        assert capsysbinary.readouterr().err == b"Hi"

    def test_a_bad_byte_is_refused_by_name(self):
        with pytest.raises(StackerError, match="write-stderr-bytes"):
            run("[256] write-stderr-bytes")

    def test_a_text_only_stream_is_reported(self, monkeypatch):
        monkeypatch.setattr("sys.stderr", io.StringIO())
        with pytest.raises(StackerRuntimeError, match="`write-stderr-bytes` needs a standard error that takes bytes"):
            run("[1] write-stderr-bytes")

    def test_the_standard_output_twin_still_names_its_stream(self, monkeypatch):
        monkeypatch.setattr("sys.stdout", io.StringIO())
        with pytest.raises(StackerRuntimeError, match="`write-stdout-bytes` needs a standard output that takes bytes"):
            run("[1] write-stdout-bytes")
