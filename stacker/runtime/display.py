"""How the REPL shows the stack on a terminal: each kind of value in its own color.

The text comes from ``stacker.lang.text`` in pieces tagged by kind; this
module only chooses the colors and prints.
"""

from __future__ import annotations

from typing import TextIO

from stacker.lang.protocols import BLOCK
from stacker.lang.text import (
    ARRAY,
    BOOL,
    CALLABLE,
    COMPLEX,
    DICT,
    FLOAT,
    INT,
    LIST,
    NULL,
    STRING,
    SYMBOL,
    pieces,
    stack_text,
)
from stacker.runtime import color

#: The color of each kind of value
PALETTE: dict[str, str] = {
    INT: "default",
    FLOAT: "default",
    COMPLEX: "default",
    SYMBOL: "default",
    STRING: "lightgreen",  # every string, literal or computed
    BOOL: "lightblue",
    NULL: "lightblue",
    LIST: "red",
    ARRAY: "magenta",  # an array looks like a list; the color tells them apart
    DICT: "lightmagenta",
    BLOCK: "cyan",
    CALLABLE: "yellow",
}

#: The color of the brackets around the stack itself
STACK_COLOR = "yellow"


def colored_text(value: object) -> str:
    """One value as the colored stack display writes it.

    Args:
        value: Any value.

    Returns:
        The display text, each piece in the color of its kind; separators and
        values of unknown kinds uncolored.
    """
    return "".join([color.colored(text, PALETTE[kind]) if kind else text for kind, text in pieces(value)])


def disp_colored(stack_list: list[object]) -> str:
    """Formats the stack with colors: items space-separated inside yellow brackets.

    Args:
        stack_list: The stack contents, bottom first.

    Returns:
        The display text with ANSI color codes.
    """
    inner = " ".join(colored_text(item) for item in stack_list)
    return color.colored("[", STACK_COLOR) + inner + color.colored("]", STACK_COLOR)


def disp_stack(stack_list: list[object], colored: bool = False, file: TextIO | None = None) -> None:
    """Prints the stack as the REPL shows it.

    Args:
        stack_list: The values, bottom first.
        colored: Whether to color the values by kind.
        file: The stream to print to; ``sys.stdout`` when None.
    """
    print(disp_colored(stack_list) if colored else stack_text(stack_list), file=file)
