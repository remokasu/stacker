from __future__ import annotations

import os
from pathlib import Path

from stacker.engine.data_type import Symbol
from stacker.error import StackerRuntimeError, StackerTypeError, symbol_as_value_message
from stacker.operators.arguments import byte_values
from stacker.util.disp import display_text, plain_text


def _write(content: object, filename: Path | str) -> None:
    filename = Path(filename).resolve()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def _read(filename: Path | str) -> str | None:
    filename = Path(filename).resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"File {filename} not found.")
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} does not exist.")
    with open(filename, "r", encoding="utf-8-sig") as f:
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


def file_name_argument(word: str, filename: object) -> str:
    """Returns ``filename`` when it is a string; otherwise raises an error that names the word (shared by the OS words).

    A number is refused on purpose: ``open`` would read it as a file
    descriptor and ``1 write-to-file`` would close the standard output.
    """
    if isinstance(filename, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, filename.name))
    if not isinstance(filename, str):
        raise StackerTypeError(f"`{word}` expects a file name (a string), got {plain_text(filename)}")
    return filename


def cannot_open_error(word: str, filename: str, error: OSError, verb: str = "open") -> StackerRuntimeError:
    """The error for a file ``word`` could not open (or ``verb``) ``filename``, from the host's reason."""
    reason = error.strerror or str(error)
    return StackerRuntimeError(f"`{word}` cannot {verb} `{filename}`: {reason}")


def not_text_error(word: str, filename: str, error: UnicodeDecodeError) -> StackerRuntimeError:
    """The error for a file ``word`` could not read as text."""
    return StackerRuntimeError(f"`{word}` cannot read `{filename}` as text: {error.reason}")


def write_to_file(data: object, filename: object) -> None:
    """Writes ``data`` to a file, as the text `str` gives, replacing what the file held."""
    filename = file_name_argument("write-to-file", filename)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(display_text(data))
    except OSError as error:
        raise cannot_open_error("write-to-file", filename, error) from error


def read_from_file(filename: object) -> str:
    """Reads the whole content of a file as one string."""
    filename = file_name_argument("read-from-file", filename)
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError as error:
        raise cannot_open_error("read-from-file", filename, error) from error
    except UnicodeDecodeError as error:
        raise not_text_error("read-from-file", filename, error) from error


def append_to_file(data: object, filename: object) -> None:
    """Appends ``data`` to a file, as the text `str` gives."""
    filename = file_name_argument("append-to-file", filename)
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(display_text(data))
    except OSError as error:
        raise cannot_open_error("append-to-file", filename, error) from error


def read_lines_from_file(filename: object) -> list[str]:
    """Reads a file as a list of its lines, line breaks removed."""
    filename = file_name_argument("read-lines", filename)
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            return [line.rstrip("\n") for line in f]
    except OSError as error:
        raise cannot_open_error("read-lines", filename, error) from error
    except UnicodeDecodeError as error:
        raise not_text_error("read-lines", filename, error) from error


def file_exists(filename: object) -> bool:
    """Returns True when a file (or a directory) of that name exists."""
    return os.path.exists(file_name_argument("file-exists", filename))


def read_bytes(filename: object) -> list[int]:
    """``path read-bytes``: the whole file as a list of its bytes (integers 0 to 255)."""
    filename = file_name_argument("read-bytes", filename)
    try:
        with open(filename, "rb") as f:
            return list(f.read())
    except OSError as error:
        raise cannot_open_error("read-bytes", filename, error) from error


def write_bytes(data: object, filename: object) -> None:
    """``bytes path write-bytes``: writes the bytes to a file, replacing what it held."""
    filename = file_name_argument("write-bytes", filename)
    content = byte_values("write-bytes", data)
    try:
        with open(filename, "wb") as f:
            f.write(content)
    except OSError as error:
        raise cannot_open_error("write-bytes", filename, error) from error


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
    "read-bytes": {
        "func": read_bytes,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Read a whole file as a list of its bytes (integers 0 to 255)",
    },
    "write-bytes": {
        "func": write_bytes,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "bytes path write-bytes: write a list or an array of bytes (integers 0 to 255) to a file",
    },
    "file-exists": {
        "func": (lambda filename: file_exists(filename)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Check if file exists",
    },
}
