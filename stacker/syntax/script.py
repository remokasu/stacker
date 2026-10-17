"""Splits the text of a script into the expressions a script runner evaluates one by one."""

from __future__ import annotations

from collections.abc import Iterator

from stacker.error import UnterminatedTokenError
from stacker.syntax.lexer import TerminalScanner

#: A `;` right before the closing bracket of a list or block at the end of an
#: expression is dropped: `[1 2 3;]` written on a line of its own is `[1 2 3]`.
_TRAILING_ROW_SEPARATORS = frozenset({";]", ";)"})


def iter_expressions(code: str) -> Iterator[tuple[int, str]]:
    """Yields the expressions of ``code`` with the line each one starts on.

    An expression ends where no string, list, block or block comment is
    left open, as a script and an included file are read. Blank lines
    between expressions are skipped; inside an open construct every line
    is kept as written, so a string spanning lines survives.

    Args:
        code: The text of a script.

    Yields:
        ``(line_number, expression)`` pairs; the line number is 1-based and
        is the first line of the expression.

    Raises:
        UnterminatedTokenError: The text ends inside a string, list, block
            or block comment; the error names the line it started on.
    """
    lines = code.splitlines()
    expression = ""
    start_line = 0
    # Incremental scanner: fed only the newly appended chunk, so a
    # multi-line expression stays O(total size)
    scanner = TerminalScanner()

    for index, raw in enumerate(lines):
        line_number = index + 1
        if scanner.state().complete:
            line = raw.strip()
            if not expression and not line:
                continue
            if not expression:
                start_line = line_number
            chunk = line + "\n"
        else:
            chunk = raw + "\n"

        expression += chunk
        state = scanner.feed(chunk)

        if state.complete:
            candidate = expression.strip()
            if candidate:
                if candidate[-2:] in _TRAILING_ROW_SEPARATORS:
                    candidate = candidate[:-2] + candidate[-1]
                yield start_line, candidate
            expression = ""
            start_line = 0
            scanner = TerminalScanner()

    if expression.strip():
        _, state = scanner.finalize()
        if not state.complete:
            start = start_line
            if state.start_line is not None:
                start = start + state.start_line - 1
            raise UnterminatedTokenError(state.open_construct, start)
