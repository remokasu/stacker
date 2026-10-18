from __future__ import annotations

import sys

from stacker.error import StackerRuntimeError
from stacker.util.disp import display_text


def _read_line() -> str | None:
    """``read-line``: one line of standard input without its line break, or null at the end."""
    try:
        line = sys.stdin.readline()
    except (OSError, ValueError) as error:
        raise StackerRuntimeError(f"`read-line` cannot read standard input: {error}") from error
    if line == "":
        return None
    return line.rstrip("\r\n") if line.endswith("\n") else line


def _read_stdin() -> str:
    """``read-stdin``: the rest of standard input as one string (empty at the end)."""
    try:
        return sys.stdin.read()
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
}
