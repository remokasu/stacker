from __future__ import annotations

import os
from pathlib import Path

from stacker.operators.file import cannot_open_error, file_name_argument, not_text_error


def _ls() -> list[str]:
    return [p.name for p in Path(".").iterdir()]


def _cd(path: object) -> None:
    """``path cd``: makes ``path`` the current directory; a path must be a string (an integer would be a descriptor)."""
    path = file_name_argument("cd", path)
    try:
        os.chdir(path)
    except OSError as error:
        raise cannot_open_error("cd", path, error, verb="change to") from error


def _pwd() -> str:
    return os.getcwd()


def _cat(filename: object) -> None:
    """``path cat``: prints the text of a file; a path must be a string."""
    filename = file_name_argument("cat", filename)
    try:
        with open(filename, "r") as f:
            print(f.read())
    except OSError as error:
        raise cannot_open_error("cat", filename, error) from error
    except UnicodeDecodeError as error:
        raise not_text_error("cat", filename, error) from error


os_operators = {
    "ls": {
        "func": _ls,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "List files in the current directory",
    },
    "cd": {
        "func": _cd,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Change directory to the specified path",
    },
    "pwd": {
        "func": _pwd,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Print the current working directory",
    },
    "cat": {
        "func": _cat,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Print the contents of a file",
    },
}
