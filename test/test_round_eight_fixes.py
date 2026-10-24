"""Files skip a byte order mark, the standard streams are UTF-8, and a format field cannot reach into a value."""

import io
import os
import subprocess
import sys

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError
from stacker.util.disp import plain_text


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestAByteOrderMark:
    def test_is_skipped_by_the_reading_words(self, tmp_path):
        path = tmp_path / "excel.csv"
        path.write_bytes(b"\xef\xbb\xbfid,score\r\n1,90\r\n")
        assert run(f'"{path}" read-lines 0 at "," split 0 at') == ["id"]
        assert run(f'"{path}" read-from-file 0 2 slice') == ["id"]

    def test_is_not_written(self, tmp_path):
        path = tmp_path / "w.txt"
        run(f'"x" "{path}" write-to-file')
        assert path.read_bytes() == b"x"

    def test_shows_as_an_escape_on_the_stack(self):
        assert plain_text("﻿id") == "'\\ufeffid'"
        assert plain_text("a\u200bb") == "'a\\u200bb'"
        assert plain_text("\U0001f468\u200d\U0001f469") == "'\U0001f468\u200d\U0001f469'"  # a joiner that shapes text stays
        assert run('"\\ufeffid" str') == ["﻿id"]  # raw through str


class TestStandardStreams:
    def test_read_stdin_gives_line_ends_as_a_file_does(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b"ab\r\ncd\r\n")))
        assert run("read-stdin") == ["ab\ncd\n"]

    def test_stdin_is_read_as_utf8_whatever_the_host_says(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO("é日本\n".encode()), encoding="ascii"))
        assert run("read-line") == ["é日本"]

    def test_an_unwritable_character_is_the_outputs_fault(self, monkeypatch):
        monkeypatch.setattr("sys.stdout", io.TextIOWrapper(io.BytesIO(), encoding="ascii"))
        with pytest.raises(StackerRuntimeError, match="cannot write 'é' to standard output, whose encoding is ascii"):
            run('"é" echo')

    def test_the_command_line_prints_utf8_even_under_a_narrow_locale(self, tmp_path):
        script = tmp_path / "e.stk"
        script.write_text('"日本 🎉" echo\n', encoding="utf-8")
        env = {**os.environ, "HOME": "/nonexistent", "PYTHONIOENCODING": "cp1252", "LC_ALL": "C", "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
        result = subprocess.run([sys.executable, "-m", "stacker", str(script)], capture_output=True, env=env, check=False)
        assert result.returncode == 0, result.stderr
        assert result.stdout == "日本 🎉\n".encode()


class TestFormatFields:
    @pytest.mark.parametrize("program, expected", [('"x={}" 3 format', "x=3"), ('"{:.2f}" 3.14159 format', "3.14"), ('"{0}-{0}" 7 format', "7-7"), ('"{:>5}" "a" format', "    a")])
    def test_plain_fields_and_specs_still_work(self, program, expected):
        assert run(program) == [expected]

    @pytest.mark.parametrize("program", ['"{0.__class__}" 5 format', '"{0[0]}" [7 8] format', '"{0.__class__.__mro__}" 5 format', '"{x}" 5 format', '"{0:{0.real}}" 5 format', '"{:{0.__class__}}" 5 format'])
    def test_a_path_into_the_value_is_refused_by_name(self, program):
        with pytest.raises(StackerTypeError, match="`format` fields are"):
            run(program)
