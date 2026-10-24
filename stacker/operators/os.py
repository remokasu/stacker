from __future__ import annotations

import os
from pathlib import Path

from stacker.operators.file import cannot_open_error, file_name_argument, not_text_error
from stacker.operators.io import write_text


def _ls() -> list[str]:
    return [p.name for p in Path(".").iterdir()]


def _cd(path: object) -> None:
    """``path cd``: makes ``path`` the current directory; a path must be a string (an integer would be a descriptor)."""
    path = file_name_argument("cd", path)
    try:
        os.chdir(path)
    except OSError as error:
        raise cannot_open_error("cd", path, error, verb="change to") from error


def _path_join(head: object, tail: object) -> str:
    """``a b path-join``: ``b`` under ``a``, with the separator put in (an absolute ``b`` stands alone).

    ``b`` may be a list of parts, joined in turn: ``script-dir ["data" "x.txt"] path-join``.
    """
    parts = list(tail) if isinstance(tail, list) else [tail]
    return os.path.join(file_name_argument("path-join", head), *(file_name_argument("path-join", p) for p in parts))


def _list_dir(path: object) -> list[str]:
    """``path list-dir``: the names inside a directory, in name order."""
    path = file_name_argument("list-dir", path)
    try:
        return sorted(os.listdir(path))
    except OSError as error:
        raise cannot_open_error("list-dir", path, error, verb="list") from error


def _path_base(path: object) -> str:
    """``path path-base``: the last part of a path (the file's name)."""
    return os.path.basename(file_name_argument("path-base", path))


def _path_dir(path: object) -> str:
    """``path path-dir``: the directory part of a path."""
    return os.path.dirname(file_name_argument("path-dir", path))


def _pwd() -> str:
    return os.getcwd()


def _cat(filename: object) -> None:
    """``path cat``: prints the text of a file; a path must be a string."""
    filename = file_name_argument("cat", filename)
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            write_text(f.read())
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
    "path-join": {
        "func": _path_join,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "a b path-join: joins two parts of a path with the separator; b may be a list of parts (a [b c] path-join)",
    },
    "list-dir": {
        "func": _list_dir,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "List the names inside a directory, in name order",
    },
    "path-base": {
        "func": _path_base,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The last part of a path (the file's name)",
    },
    "path-dir": {
        "func": _path_dir,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The directory part of a path",
    },
    "cat": {
        "func": _cat,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Print the contents of a file",
    },
}
