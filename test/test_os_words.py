"""`cat` and `cd` take a file name (a string) and name themselves in errors, as the file words do."""

import os

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


@pytest.mark.parametrize("program, word", [("1 cat", "cat"), ("0 cat", "cat"), ("true cat", "cat"), ("5 cd", "cd"), ("true cd", "cd"), ("[1] cd", "cd")])
def test_a_path_must_be_a_string(program, word, capsys):
    with pytest.raises(StackerTypeError, match=f"`{word}` expects a file name"):
        run(program)
    print("still open")
    assert capsys.readouterr().out == "still open\n"


def test_cat_prints_the_file(tmp_path, capsys):
    path = tmp_path / "t.txt"
    path.write_text("hello")
    run(f'"{path}" cat')
    assert capsys.readouterr().out == "hello\n"


def test_a_file_that_is_not_text_is_reported_by_cat(tmp_path):
    path = tmp_path / "b.bin"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(StackerRuntimeError, match="`cat` cannot read .* as text"):
        run(f'"{path}" cat')


def test_cd_changes_the_directory(tmp_path):
    before = os.getcwd()
    try:
        assert run(f'"{tmp_path}" cd pwd') == [str(tmp_path.resolve())]
    finally:
        os.chdir(before)


@pytest.mark.parametrize(
    "program, text",
    [
        ('"{tmp}/nope.txt" cat', "`cat` cannot open `{tmp}/nope.txt`"),
        ('"{tmp}/nope_dir" cd', "`cd` cannot change to `{tmp}/nope_dir`"),
        ('"{tmp}/t.txt" cd', "`cd` cannot change to `{tmp}/t.txt`"),
    ],
)
def test_an_os_error_names_the_word_and_the_path(tmp_path, program, text):
    (tmp_path / "t.txt").write_text("x")
    with pytest.raises(StackerRuntimeError) as info:
        run(program.format(tmp=tmp_path))
    assert text.format(tmp=tmp_path) in str(info.value) and "Errno" not in str(info.value)
