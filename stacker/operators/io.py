from __future__ import annotations

import sys

from stacker.error import StackerRuntimeError
from stacker.operators.arguments import byte_values
from stacker.util.disp import display_text

#: Text read from standard input is decoded with this when the host does not say
_DEFAULT_STDIN_ENCODING = "utf-8"


def _stdin_bytes() -> object | None:
    """The byte layer of standard input, or None when there is none (a text-only stream)."""
    return getattr(sys.stdin, "buffer", None)


def _stdin_text(word: str, raw: bytes) -> str:
    """Decodes bytes read from standard input, naming ``word`` when they are not text."""
    encoding = getattr(sys.stdin, "encoding", None) or _DEFAULT_STDIN_ENCODING
    try:
        return raw.decode(encoding)
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


def _write_stdout_bytes(data: object) -> None:
    """``bytes write-stdout-bytes``: writes the bytes to standard output, as they are."""
    content = byte_values("write-stdout-bytes", data)
    try:
        sys.stdout.flush()
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.flush()
    except AttributeError as error:
        raise StackerRuntimeError("`write-stdout-bytes` needs a standard output that takes bytes; this one is text only") from error
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`write-stdout-bytes` cannot write to standard output: {error}") from error


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
        return _stdin_text("read-stdin", buffer.read()) if buffer is not None else sys.stdin.read()
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`read-stdin` cannot read standard input: {error}") from error


io_operators = {
    "echo": {
        "func": (lambda content: print(display_text(content))),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "print": {
        "func": (lambda content: print(display_text(content))),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Prints the specified content to the console.",
    },
    "printc": {
        "func": (lambda content: print(display_text(content), end="")),
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
}
