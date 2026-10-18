from __future__ import annotations

import os
from pathlib import Path

from stacker.engine.data_type import Symbol
from stacker.error import StackerRuntimeError, StackerTypeError, symbol_as_value_message
from stacker.util.disp import display_text, plain_text


def _write(content: object, filename: Path | str) -> None:
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

    def __enter__(self) -> FileIterator:
        self.file = open(self.filename, self.mode)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self.file:
            self.file.close()

    def readline(self) -> str | None:
        if self.file:
            line = self.file.readline()
            if line:
                return line.rstrip("\n")
            return None
        return None


def _file_name(word: str, filename: object) -> str:
    """Returns ``filename`` when it is a string; otherwise raises an error that names the word.

    A number is refused on purpose: ``open`` would read it as a file
    descriptor and ``1 write-to-file`` would close the standard output.
    """
    if isinstance(filename, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, filename.name))
    if not isinstance(filename, str):
        raise StackerTypeError(f"`{word}` expects a file name (a string), got {plain_text(filename)}")
    return filename


def _cannot_open(word: str, filename: str, error: OSError) -> StackerRuntimeError:
    """The error for a file ``word`` could not open or go through, from the host's reason."""
    reason = error.strerror or str(error)
    return StackerRuntimeError(f"`{word}` cannot open `{filename}`: {reason}")


def _not_text(word: str, filename: str, error: UnicodeDecodeError) -> StackerRuntimeError:
    """The error for a file ``word`` could not read as text."""
    return StackerRuntimeError(f"`{word}` cannot read `{filename}` as text: {error.reason}")


def write_to_file(data: object, filename: object) -> None:
    """Writes ``data`` to a file, as the text `str` gives, replacing what the file held."""
    filename = _file_name("write-to-file", filename)
    try:
        with open(filename, "w") as f:
            f.write(display_text(data))
    except OSError as error:
        raise _cannot_open("write-to-file", filename, error) from error


def read_from_file(filename: object) -> str:
    """Reads the whole content of a file as one string."""
    filename = _file_name("read-from-file", filename)
    try:
        with open(filename, "r") as f:
            return f.read()
    except OSError as error:
        raise _cannot_open("read-from-file", filename, error) from error
    except UnicodeDecodeError as error:
        raise _not_text("read-from-file", filename, error) from error


def append_to_file(data: object, filename: object) -> None:
    """Appends ``data`` to a file, as the text `str` gives."""
    filename = _file_name("append-to-file", filename)
    try:
        with open(filename, "a") as f:
            f.write(display_text(data))
    except OSError as error:
        raise _cannot_open("append-to-file", filename, error) from error


def read_lines_from_file(filename: object) -> list[str]:
    """Reads a file as a list of its lines, line breaks removed."""
    filename = _file_name("read-lines", filename)
    try:
        with open(filename, "r") as f:
            return [line.rstrip("\n") for line in f]
    except OSError as error:
        raise _cannot_open("read-lines", filename, error) from error
    except UnicodeDecodeError as error:
        raise _not_text("read-lines", filename, error) from error


def file_exists(filename: object) -> bool:
    """Returns True when a file (or a directory) of that name exists."""
    return os.path.exists(_file_name("file-exists", filename))


file_operators = {
    "write-to-file": {
        "func": (lambda data, filename: write_to_file(data, filename)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Write data to file",
    },
    "append-to-file": {
        "func": (lambda data, filename: append_to_file(data, filename)),
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
