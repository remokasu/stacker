"""The file words take a file name (a string), write values as `str` does, and name themselves in errors."""

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError
from stacker.runtime.exec_modes.execution_mode import ExecutionMode


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program, word",
    [
        ('"x" 1 write-to-file', "write-to-file"),
        ('"x" true write-to-file', "write-to-file"),
        ('"x" 2 append-to-file', "append-to-file"),
        ("0 read-lines", "read-lines"),
        ("1 read-from-file", "read-from-file"),
        ("2.5 file-exists", "file-exists"),
        ("1 file-exists", "file-exists"),
        ("[1] file-exists", "file-exists"),
    ],
)
def test_a_file_name_must_be_a_string(program, word, capsys):
    with pytest.raises(StackerTypeError) as info:
        run(program)
    assert f"`{word}`" in str(info.value) and "file name" in str(info.value)
    # and the standard streams are still there
    print("still open")
    assert capsys.readouterr().out == "still open\n"


def test_a_symbol_file_name_is_reported_as_a_symbol():
    with pytest.raises(StackerTypeError, match="cannot use the symbol `f`"):
        run('"x" :f write-to-file')


@pytest.mark.parametrize(
    "value, expected",
    [
        ('[1 "a" true null 2.5]', "[1 'a' true null 2.5]"),
        ("[1 2] array", "[1 2]"),
        ('dict :d set 1 d "k" put! d', "{'k' 1}"),
        ("true", "true"),
        ("null", "null"),
        ('"plain text"', "plain text"),
        ("1 3 frac", "1/3"),
    ],
)
def test_write_to_file_writes_what_str_gives(tmp_path, value, expected):
    path = tmp_path / "out.txt"
    run(f'{value} "{path}" write-to-file')
    assert path.read_text() == expected
    run(f'{value} "{path}" append-to-file')
    assert path.read_text() == expected + expected


def test_read_back_round_trip(tmp_path):
    path = tmp_path / "lines.txt"
    run(f'"a\nb" "{path}" write-to-file')
    assert run(f'"{path}" read-lines') == [["a", "b"]]
    assert run(f'"{path}" read-from-file') == ["a\nb"]
    assert run(f'"{path}" file-exists "{path}x" file-exists') == [True, False]


@pytest.mark.parametrize(
    "program, word, shown",
    [
        ('"{tmp}/nope.txt" read-lines', "read-lines", "nope.txt"),
        ('"{tmp}/nope.txt" read-from-file', "read-from-file", "nope.txt"),
        ('"{tmp}" read-lines', "read-lines", "{tmp}"),
    ],
)
def test_an_os_error_names_the_word_and_the_file(tmp_path, program, word, shown):
    with pytest.raises(StackerRuntimeError) as info:
        run(program.format(tmp=tmp_path))
    text = str(info.value)
    assert f"`{word}`" in text and shown.format(tmp=tmp_path) in text and "Errno" not in text


def test_the_hint_still_says_the_file_was_not_found(tmp_path):
    with pytest.raises(StackerRuntimeError) as info:
        run(f'"{tmp_path}/nope.txt" read-lines')
    assert "File not found" in ExecutionMode(Stacker())._get_error_hint(info.value)


@pytest.mark.parametrize("word", ["read-lines", "read-from-file"])
def test_a_file_that_is_not_text_is_reported_by_the_word(tmp_path, word):
    path = tmp_path / "b.bin"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(StackerRuntimeError) as info:
        run(f'"{path}" {word}')
    text = str(info.value)
    assert f"`{word}`" in text and "as text" in text and "codec" not in text
