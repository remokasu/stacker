from __future__ import annotations

from pathlib import Path
import os


def _ls() -> list[str]:
    return [p.name for p in Path(".").iterdir()]


def _cd(path: str) -> None:
    os.chdir(path)


def _pwd() -> str:
    return os.getcwd()


def _cat(filename: str) -> str:
    with open(filename, "r") as f:
        print(f.read())


os_operators = {
    "ls": {
        "func": lambda: _ls(),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "List files in the current directory",
    },
    "cd": {
        "func": lambda path: _cd(path),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Change directory to the specified path",
    },
    "pwd": {
        "func": lambda: _pwd(),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Print the current working directory",
    },
    "cat": {
        "func": lambda filename: _cat(filename),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Print the contents of a file",
    },
}
