"""How a value is written.

One set of type cases turns a value into pieces of text, each tagged with the
kind of value it came from; the plain text is the pieces joined. Nothing here
knows about terminals; a caller that wants colors takes the kind of each piece.
"""

from __future__ import annotations

import threading

from stacker.data_type import Array, Symbol
from stacker.error import StackerRuntimeError
from stacker.lang.protocols import BLOCK, kind_of
from stacker.syntax.token_rules import escape_for_display

#: The error for a value nested too deep for the display to walk
TOO_DEEP_TO_SHOW = "cannot show a value nested this deep; take it apart first (`at`, `dolist`)"

#: The kinds of value a piece of display text can come from; a block's kind is
#: ``protocols.BLOCK``. A piece with kind ``None`` is a separator or a value of
#: a kind the language does not know, shown with ``str()``.
INT = "int"
FLOAT = "float"
COMPLEX = "complex"
SYMBOL = "symbol"
STRING = "String"
BOOL = "bool"
NULL = "null"
LIST = "list"
ARRAY = "array"
DICT = "dict"
CALLABLE = "callable"

#: One piece of display text: the kind of value it came from, and the text
Piece = tuple[str | None, str]

_SEPARATOR: Piece = (None, " ")

#: Arrays and dictionaries nested deeper than this are shown as `[...]` / `{...}`
DISPLAY_NESTING_LIMIT = 8

#: The ids of the arrays and dictionaries being shown right now, outermost
#: first: one that shows up again inside itself is a cycle. Per thread, so
#: two interpreters showing values at once do not mistake each other's
_display_state = threading.local()


def _showing() -> list[int]:
    stack = getattr(_display_state, "showing", None)
    if stack is None:
        stack = _display_state.showing = []
    return stack


def _entered(value: object) -> bool:
    """Marks ``value`` as being shown; False when it is a cycle or too deep to show."""
    showing = _showing()
    if id(value) in showing or len(showing) >= DISPLAY_NESTING_LIMIT:
        return False
    showing.append(id(value))
    return True


def _left() -> None:
    _showing().pop()


def pieces(value: object) -> list[Piece]:
    """The display text of a value, in pieces tagged with the kind of value each came from.

    Containers contribute their brackets in their own kind and their items in
    theirs, with untagged separators between; so ``[1 'a']`` as an array is
    ``[(ARRAY, "["), (INT, "1"), (None, " "), (STRING, "'a'"), (ARRAY, "]")]``.

    Args:
        value: Any value.

    Returns:
        The pieces, in the order they are written.

    Raises:
        StackerRuntimeError: The value is nested too deep to show.
    """
    out: list[Piece] = []
    try:
        _write(value, out)
    except RecursionError:
        raise StackerRuntimeError(TOO_DEEP_TO_SHOW) from None
    return out


def _write(value: object, out: list[Piece]) -> None:
    if isinstance(value, bool):
        out.append((BOOL, str(value).lower()))
    elif value is None:
        out.append((NULL, "null"))
    elif isinstance(value, int):
        out.append((INT, str(value)))
    elif isinstance(value, float):
        out.append((FLOAT, str(value)))
    elif isinstance(value, complex):
        out.append((COMPLEX, str(value)))
    elif isinstance(value, Symbol):
        # A symbol is shown as its bare name
        out.append((SYMBOL, value.name))
    elif isinstance(value, str):
        # A string is shown quoted whether it is a literal or a computed value
        out.append((STRING, "'" + escape_for_display(str(value)) + "'"))
    elif isinstance(value, Array):
        _write_array(value, out)
    elif isinstance(value, list):
        _write_list(value, out)
    elif isinstance(value, dict):
        _write_dict(value, out)
    elif kind_of(value) == BLOCK:
        out.append((BLOCK, str(value)))
    elif callable(value):
        out.append((CALLABLE, str(value)))
    else:
        out.append((None, str(value)))


def _write_items(items: list[object], out: list[Piece]) -> None:
    for position, item in enumerate(items):
        if position:
            out.append(_SEPARATOR)
        _write(item, out)


def _write_array(value: Array, out: list[Piece]) -> None:
    """An array is shown like a list, `[1 2 3]`, in its own kind; one inside itself, or too deep, as `[...]`."""
    if not _entered(value):
        out.append((ARRAY, "[...]"))
        return
    try:
        out.append((ARRAY, "["))
        _write_items(value, out)
    finally:
        _left()
    out.append((ARRAY, "]"))


def _write_list(value: list[object], out: list[Piece]) -> None:
    # Element by element, so commas inside strings survive and each element
    # keeps its own kind; only the brackets take the list's
    out.append((LIST, "["))
    _write_items(value, out)
    out.append((LIST, "]"))


def _write_dict(value: dict[object, object], out: list[Piece]) -> None:
    """A dictionary is shown as `{'a' 1 b 2}`, keys and values in the order the keys were added."""
    if not value:
        out.append((DICT, "{:}"))  # an empty dictionary, told apart from an empty block `{}`
        return
    if not _entered(value):
        out.append((DICT, "{...}"))
        return
    try:
        out.append((DICT, "{"))
        for position, (key, item) in enumerate(value.items()):
            if position:
                out.append(_SEPARATOR)
            _write(key, out)
            out.append(_SEPARATOR)
            _write(item, out)
    finally:
        _left()
    out.append((DICT, "}"))


def plain_text(item: object) -> str:
    """Formats one stack item as the stack shows it, without colors.

    Args:
        item: A value from the stack.

    Returns:
        The item's display text.

    Raises:
        StackerRuntimeError: The value is nested too deep to show.
    """
    return "".join([text for _, text in pieces(item)])


def display_text(value: object) -> str:
    """The text a value is written as outside the stack: a string bare, the rest as the stack shows it.

    Args:
        value: Any value.

    Returns:
        The value itself for a string; ``plain_text`` of it otherwise.
    """
    return value if isinstance(value, str) else plain_text(value)


def disp_default(stack_list: list[object]) -> str:
    """Formats the stack without colors: items space-separated inside brackets.

    Built item by item rather than from ``str(list)`` with the commas
    removed, which used to delete commas inside strings as well
    (``"Hello, World!"`` showed as ``'Hello World!'``).

    Args:
        stack_list: The stack contents, bottom first.

    Returns:
        The display text, e.g. ``[3 'a, b' [1 2]]``.
    """
    return "[" + " ".join(plain_text(item) for item in stack_list) + "]"
