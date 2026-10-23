from __future__ import annotations

from pathlib import Path

from stacker.error import ScriptReadError

#: Scripts are UTF-8; a byte order mark at the start is skipped
SCRIPT_ENCODING = "utf-8-sig"


def readtxt(file_path: str | Path) -> str:
    """Read a stacker script file verbatim, as UTF-8.

    Comment handling (``#`` line comments, ``#| ... |#`` block comments)
    and triple-quoted strings are the lexer scan core's responsibility;
    this function strips nothing but a trailing newline.

    Args:
        file_path: Path to the script file.

    Returns:
        The file content, without a trailing newline.

    Raises:
        ScriptReadError: The file is not UTF-8 text; the message names the line.
    """
    with open(file_path, "rb") as file:
        raw = file.read()
    try:
        return raw.decode(SCRIPT_ENCODING).rstrip("\n")
    except UnicodeDecodeError as error:
        line = raw[: error.start].count(b"\n") + 1
        raise ScriptReadError(f"{file_path} is not UTF-8 text at line {line}: {error.reason}") from error
