from __future__ import annotations

from typing import Any
from pathlib import Path
import os


def _write(content, filename: Path | str) -> None:
    filename = Path(filename).resolve()
    with open(filename, "w") as f:
        f.write(content)


def _read(filename: Path | str) -> str | None:
    filename = Path(filename).resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} does not exist.")
    with open(filename, "r") as f:
        return f.read()


class FileIterator:
    def __init__(self, filename: str, mode: str = "r"):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def readline(self):
        if self.file:
            line = self.file.readline()
            if line:
                return line.rstrip("\n")
            return None
        return None


def write_to_file(data: Any, filename: str) -> None:
    """Write data to a file"""
    with open(filename, "w") as f:
        f.write(str(data))


def read_from_file(filename: str) -> str:
    """Read all content from a file"""
    content = None
    with open(filename, "r") as f:
        content = f.read()
    return content


def append_to_file(data: Any, filename: str) -> None:
    """Append data to a file"""
    with open(filename, "a") as f:
        f.write(str(data))


def read_lines_from_file(filename: str) -> list[str]:
    """Read all lines from a file"""
    lines = []
    with open(filename, "r") as f:
        lines = [line.rstrip("\n") for line in f]
    return lines


def file_exists(filename: str) -> bool:
    """Check if a file exists"""
    exists = os.path.exists(filename)
    return exists


file_operators = {
    "write-to-file": {
        "func": (lambda data, filename: write_to_file(data, filename)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Write data to file",
    },
    "append-to-file": {
        "func": (lambda filename, content: append_to_file(filename, content)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Append content to file",
    },
    "read-lines": {
        "func": (lambda filename: read_lines_from_file(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Read all lines from file",
    },
    "read-from-file": {
        "func": (lambda filename: read_from_file(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Read all content from file",
    },
    "file-exists": {
        "func": (lambda filename: file_exists(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Check if file exists",
    },
}
