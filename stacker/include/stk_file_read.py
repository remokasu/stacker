from __future__ import annotations

from pathlib import Path


def readtxt(file_path: str | Path) -> str:
    """Read a stacker script file verbatim.

    Comment handling (``#`` line comments, ``#| ... |#`` block comments)
    and triple-quoted strings are the lexer scan core's responsibility
    ; this function no longer strips anything. The historical
    behavior of dropping triple-quote "docstring" blocks was removed in
    1.11.0 — triple quotes are always string literals now.

    Args:
        file_path: Path to the script file.

    Returns:
        The file content, without a trailing newline.
    """
    with open(file_path, "r") as file:
        return file.read().rstrip("\n")
