from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO

from stacker.error import StackerRuntimeError
from stacker.operators.arguments import byte_values
from stacker.util.disp import display_text

#: Standard input is read as UTF-8, as scripts and files are, whatever the host's locale says
STDIN_ENCODING = "utf-8"


def _stdin_bytes() -> object | None:
    """The byte layer of standard input, or None when there is none (a text-only stream)."""
    return getattr(sys.stdin, "buffer", None)


def _stdin_text(word: str, raw: bytes) -> str:
    """Decodes bytes read from standard input as UTF-8 (as scripts and files are), naming ``word`` when they are not text."""
    try:
        return raw.decode(STDIN_ENCODING)
    except UnicodeDecodeError as error:
        raise StackerRuntimeError(f"`{word}` cannot read standard input as text: {error.reason}") from error


def _cannot_read(word: str, error: Exception) -> StackerRuntimeError:
    if isinstance(error, AttributeError):
        return StackerRuntimeError(f"`{word}` needs a standard input that carries bytes; this one is text only")
    return StackerRuntimeError(f"`{word}` cannot read standard input: {error}")


def _read_stdin_bytes() -> list[int]:
    """``read-stdin-bytes``: the rest of standard input as a list of its bytes (integers 0 to 255)."""
    buffer = _stdin_bytes()
    try:
        if buffer is None:
            raise AttributeError("no byte layer")
        return list(buffer.read())
    except (OSError, ValueError, AttributeError) as error:
        raise _cannot_read("read-stdin-bytes", error) from error


#: The two output streams a word can write to, by the name a message calls them
STDOUT = "standard output"
STDERR = "standard error"


def _stream(name: str) -> TextIO:
    """The stream called ``name``, looked up when the word runs so a redirected stream is honoured."""
    return sys.stderr if name == STDERR else sys.stdout


def _write_bytes(word: str, stream_name: str, data: object) -> None:
    """Writes the bytes ``data`` holds to the stream called ``stream_name``, as they are, for ``word``."""
    content = byte_values(word, data)
    stream = _stream(stream_name)
    try:
        stream.flush()
        stream.buffer.write(content)
        stream.buffer.flush()
    except AttributeError as error:
        raise StackerRuntimeError(f"`{word}` needs a {stream_name} that takes bytes; this one is text only") from error
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`{word}` cannot write to {stream_name}: {error}") from error


def _write_stdout_bytes(data: object) -> None:
    """``bytes write-stdout-bytes``: writes the bytes to standard output, as they are."""
    _write_bytes("write-stdout-bytes", STDOUT, data)


def _write_stderr_bytes(data: object) -> None:
    """``bytes write-stderr-bytes``: writes the bytes to standard error, as they are."""
    _write_bytes("write-stderr-bytes", STDERR, data)


def write_text(text: str, end: str = "\n", stream_name: str = STDOUT) -> None:
    """Prints ``text`` to the stream called ``stream_name``; a character the stream cannot carry is the output's fault, not the value's."""
    stream = _stream(stream_name)
    try:
        print(text, end=end, file=stream)
    except UnicodeEncodeError as error:
        encoding = getattr(stream, "encoding", None) or "the host's"
        raise StackerRuntimeError(
            f"cannot write {text[error.start:error.end]!r} to {stream_name}, whose encoding is {encoding}"
        ) from error


def _printer(stream_name: str, end: str = "\n") -> Callable[[object], None]:
    """The function behind ``echo`` and its kin: shows a value as ``echo`` does, on the stream called ``stream_name``, followed by ``end``."""

    def show(content: object) -> None:
        write_text(display_text(content), end=end, stream_name=stream_name)

    return show


def _read_line() -> str | None:
    """``read-line``: one line of standard input without its line break, or null at the end.

    The line is read from the byte layer when there is one, so the text
    words and `read-stdin-bytes` share one position in the input.
    """
    buffer = _stdin_bytes()
    try:
        line = _stdin_text("read-line", buffer.readline()) if buffer is not None else sys.stdin.readline()
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`read-line` cannot read standard input: {error}") from error
    if line == "":
        return None
    return line.rstrip("\r\n") if line.endswith("\n") else line


def _read_stdin() -> str:
    """``read-stdin``: the rest of standard input as one string (empty at the end)."""
    buffer = _stdin_bytes()
    try:
        text = _stdin_text("read-stdin", buffer.read()) if buffer is not None else sys.stdin.read()
        return text.replace("\r\n", "\n").replace("\r", "\n")  # line ends as a file read gives them
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`read-stdin` cannot read standard input: {error}") from error


io_operators = {
    "echo": {
        "func": _printer(STDOUT),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "print": {
        "func": _printer(STDOUT),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "printc": {
        "func": _printer(STDOUT, end=""),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console without a newline.",
    },
    "newline": {
        "func": (lambda: print("")),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Prints a newline to the console.",
    },
    "read-line": {
        "func": _read_line,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Reads one line of standard input as a string, without the line break; null at the end of input (`read` parses a line as code)",
    },
    "read-stdin": {
        "func": _read_stdin,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Reads the rest of standard input as one string; empty at the end of input",
    },
    "read-stdin-bytes": {
        "func": _read_stdin_bytes,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Reads the rest of standard input as a list of its bytes (integers 0 to 255)",
    },
    "write-stdout-bytes": {
        "func": _write_stdout_bytes,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "bytes write-stdout-bytes: writes a list or an array of bytes (integers 0 to 255) to standard output",
    },
    "echo-err": {
        "func": _printer(STDERR),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to standard error, shown as echo shows it (warnings, errors and progress stay out of the output)",
    },
    "print-err": {
        "func": _printer(STDERR),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to standard error, shown as echo shows it",
    },
    "printc-err": {
        "func": _printer(STDERR, end=""),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to standard error without a newline",
    },
    "write-stderr-bytes": {
        "func": _write_stderr_bytes,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "bytes write-stderr-bytes: writes a list or an array of bytes (integers 0 to 255) to standard error",
    },
}
