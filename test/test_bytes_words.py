"""Bytes are lists of integers 0 to 255: read and written as they are, and made from or into strings."""

import io

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError, ValidationError


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


def test_a_file_is_read_and_written_as_bytes(tmp_path):
    path = tmp_path / "b.bin"
    path.write_bytes(bytes([0, 255, 128, 72]))
    assert run(f'"{path}" read-bytes') == [[0, 255, 128, 72]]
    out = tmp_path / "o.bin"
    run(f'[0 255 128] "{out}" write-bytes')
    assert out.read_bytes() == bytes([0, 255, 128])
    run(f'[1 2] array "{out}" write-bytes')
    assert out.read_bytes() == bytes([1, 2])


@pytest.mark.parametrize(
    "program, error, text",
    [
        ('[256] "x" write-bytes', ValidationError, "`write-bytes` expects bytes (integers 0 to 255), but element 0 is 256"),
        ('[1 -1] "x" write-bytes', ValidationError, "element 1 is -1"),
        ('[1 2.0] "x" write-bytes', ValidationError, "element 1 is 2.0"),
        ('[true] "x" write-bytes', ValidationError, "element 0 is true"),
        ('"abc" "x" write-bytes', StackerTypeError, "`write-bytes` expects a list or an array of bytes"),
        ("[1] 5 write-bytes", StackerTypeError, "`write-bytes` expects a file name"),
        ("5 read-bytes", StackerTypeError, "`read-bytes` expects a file name"),
        ('[1] "utf-8" "x" decode', StackerTypeError, "`decode` does not know the encoding"),
        ('"a" "no-such-codec" encode', StackerTypeError, "`encode` does not know the encoding"),
        ('[255] "utf-8" decode', StackerRuntimeError, "`decode` cannot read the bytes as utf-8"),
        ('"\\u3042" "latin-1" encode', StackerRuntimeError, "`encode` cannot write"),
    ],
)
def test_bad_bytes_and_encodings_are_refused_by_name(program, error, text):
    with pytest.raises(error, match=text.replace("(", "\\(").replace(")", "\\)").replace("?", "\\?")):
        run(program)


def test_a_missing_file_is_reported_by_the_word(tmp_path):
    with pytest.raises(StackerRuntimeError, match="`read-bytes` cannot open"):
        run(f'"{tmp_path}/nope" read-bytes')


@pytest.mark.parametrize(
    "program, expected",
    [
        ('"hi" "utf-8" encode', [104, 105]),
        ('"\\u3042" "utf-8" encode', [227, 129, 130]),
        ('"\\xe9" "latin-1" encode', [233]),
        ('[104 105] "utf-8" decode', "hi"),
        ('[233] "latin-1" decode', "é"),
        ('[104 105] array "ascii" decode', "hi"),
        ('"" "utf-8" encode', []),
        ('[] "utf-8" decode', ""),
    ],
)
def test_encode_and_decode(program, expected):
    assert run(program) == [expected]


def test_the_text_words_and_the_byte_word_read_the_same_input_in_turn(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b"ab\ncd\n\xff")))
    assert run("read-line read-stdin-bytes") == ["ab", [99, 100, 10, 255]]
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b"ab\ncd\nef")))
    assert run("read-line read-stdin") == ["ab", "cd\nef"]


def test_a_text_only_standard_input_is_reported_by_name(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("x"))
    with pytest.raises(StackerRuntimeError, match="`read-stdin-bytes` needs a standard input that carries bytes"):
        run("read-stdin-bytes")
    monkeypatch.setattr("sys.stdout", io.StringIO())
    with pytest.raises(StackerRuntimeError, match="`write-stdout-bytes` needs a standard output that takes bytes"):
        run("[65] write-stdout-bytes")


def test_standard_input_and_output_as_bytes(monkeypatch, capsysbinary):
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(bytes([0, 200, 10]))))
    assert run("read-stdin-bytes") == [[0, 200, 10]]
    run("[72 105 255] write-stdout-bytes")
    assert capsysbinary.readouterr().out == bytes([72, 105, 255])
