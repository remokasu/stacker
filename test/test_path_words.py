"""`path-join`, `list-dir`, `path-base` and `path-dir` work on paths as strings."""

import os

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


def test_path_join_puts_the_separator_in():
    assert run('"data" "in.txt" path-join') == [os.path.join("data", "in.txt")]
    assert run('"data/" "in.txt" path-join') == [os.path.join("data/", "in.txt")]
    assert run('"a" "b" path-join "c" path-join') == [os.path.join("a", "b", "c")]


def test_an_absolute_second_part_stands_alone():
    assert run('"data" "/tmp/x" path-join') == ["/tmp/x"]


def test_list_dir_gives_the_names_in_order(tmp_path):
    for name in ("b.txt", "a.txt", "c"):
        (tmp_path / name).write_text("")
    assert run(f'"{tmp_path}" list-dir') == [["a.txt", "b.txt", "c"]]


def test_path_base_and_path_dir():
    assert run('"a/b/c.txt" path-base "a/b/c.txt" path-dir "c.txt" path-dir') == ["c.txt", "a/b", ""]


@pytest.mark.parametrize("program, word", [('1 "a" path-join', "path-join"), ('"a" 1 path-join', "path-join"), ("1 list-dir", "list-dir"), ("1 path-base", "path-base"), ("[1] path-dir", "path-dir")])
def test_a_path_must_be_a_string(program, word):
    with pytest.raises(StackerTypeError, match=f"`{word}` expects a file name"):
        run(program)


def test_a_directory_that_cannot_be_listed_is_reported_by_the_word(tmp_path):
    with pytest.raises(StackerRuntimeError, match="`list-dir` cannot list"):
        run(f'"{tmp_path}/nope" list-dir')
