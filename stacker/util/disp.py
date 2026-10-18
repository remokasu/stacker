from __future__ import annotations

import threading

from stacker.engine.data_type import Array, Symbol
from stacker.syntax.token_rules import escape_for_display
from stacker.util import colored


class CustomPrinter:
    def __init__(self, value: object, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(str(self.value), self.color)

    def __repr__(self) -> str:
        return str(self.value)


class CustomIntPrinter(CustomPrinter):
    def __init__(self, value: int, color: str) -> None:
        self.value = value
        self.color = color


class CustomFloatPrinter(CustomPrinter):
    def __init__(self, value: float, color: str) -> None:
        self.value = value
        self.color = color


class CustromComplexPrinter(CustomPrinter):
    def __init__(self, value: complex, color: str) -> None:
        self.value = value
        self.color = color


class CustomSymbolPrinter(CustomPrinter):
    """A symbol is shown as its bare name."""

    def __init__(self, value: Symbol, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(self.value.name, self.color)

    def __repr__(self) -> str:
        return self.value.name


class CustomBoolPrinter(CustomPrinter):
    def __init__(self, value: bool, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(str(self.value).lower(), self.color)

    def __repr__(self) -> str:
        return str(self.value).lower()


class CustomNullPrinter(CustomPrinter):
    def __init__(self, value: None, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored("null", self.color)

    def __repr__(self) -> str:
        return "null"


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


class CustomArrayPrinter(CustomPrinter):
    """An array is shown like a list, `[1 2 3]`, in its own color; one inside itself, or too deep, as `[...]`."""

    def __init__(self, value: list[object], color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        if not _entered(self.value):
            return colored("[...]", self.color)
        try:
            inner = " ".join(str(custom_print(item)) for item in self.value)
        finally:
            _left()
        return colored("[", self.color) + inner + colored("]", self.color)

    def __repr__(self) -> str:
        if not _entered(self.value):
            return "[...]"
        try:
            inner = " ".join(plain_text(item) for item in self.value)
        finally:
            _left()
        return f"[{inner}]"


class CustomDictPrinter(CustomPrinter):
    """A dictionary is shown as `{'a' 1 b 2}`, keys and values in the order the keys were added, in its own color."""

    def __init__(self, value: dict[object, object], color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        if not _entered(self.value):
            return colored("{...}", self.color)
        try:
            inner = " ".join(f"{custom_print(k)} {custom_print(v)}" for k, v in self.value.items())
        finally:
            _left()
        return colored("{", self.color) + inner + colored("}", self.color)

    def __repr__(self) -> str:
        if not _entered(self.value):
            return "{...}"
        try:
            inner = " ".join(f"{plain_text(k)} {plain_text(v)}" for k, v in self.value.items())
        finally:
            _left()
        return f"{{{inner}}}"


class CustomListPrinter(CustomPrinter):
    def __init__(self, value: list[object], color: str) -> None:
        # self.value = [custom_print(item) for item in value]
        self.value = value
        self.color = color

    def __str__(self) -> str:
        # Element by element, so commas inside strings survive and each
        # element keeps its own color; only the brackets take the list color
        # (the same scheme the top-level stack display uses).
        inner = " ".join(str(custom_print(item)) for item in self.value)
        return colored("[", self.color) + inner + colored("]", self.color)

    def __repr__(self) -> str:
        inner = " ".join(plain_text(item) for item in self.value)
        return f"[{inner}]"


# REMOVED: CustomTuplePrinter - () now creates code blocks, not tuples
# Tuples are no longer a primary data type in Stacker


class OperatorPrinter(CustomPrinter):
    def __init__(self, value: object, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(str(self.value), self.color)

    def __repr__(self) -> str:
        return str(self.value)


class CustomBlockPrinter(CustomPrinter):
    def __init__(self, value: object, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(str(self.value), self.color)

    def __repr__(self) -> str:
        return str(self.value)


class CustomStringPrinter(CustomPrinter):
    def __init__(self, value: object, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(repr(self), self.color)

    def __repr__(self) -> str:
        return "'" + escape_for_display(str(self.value)) + "'"


class CutomCallablePrinter(CustomPrinter):
    def __init__(self, value: object, color: str) -> None:
        self.value = value
        self.color = color

    def __str__(self) -> str:
        return colored(str(self.value), self.color)

    def __repr__(self) -> str:
        return str(self.value)


color_map: dict[str, str] = {
    "int": "default",
    "float": "default",
    "complex": "default",
    "symbol": "default",
    "String": "lightgreen",  # every string, literal or computed
    "bool": "lightblue",
    "list": "red",
    "array": "magenta",  # an array looks like a list; the color tells them apart
    "dict": "lightmagenta",
    # "tuple": "red",  # REMOVED: Tuples no longer supported
    "block": "cyan",
    "callable": "yellow",
}


def custom_print(value: object) -> CustomPrinter | object:
    from stacker.stacker import Stacker

    if isinstance(value, bool):
        return CustomBoolPrinter(value, color_map["bool"])
    if value is None:
        return CustomNullPrinter(value, color_map["bool"])
    if isinstance(value, int):
        return CustomIntPrinter(value, color_map["int"])
    if isinstance(value, float):
        return CustomFloatPrinter(value, color_map["float"])
    if isinstance(value, complex):
        return CustromComplexPrinter(value, color_map["complex"])
    if isinstance(value, Symbol):
        return CustomSymbolPrinter(value, color_map["symbol"])
    if isinstance(value, str):
        # A string is shown quoted whether it is a literal or a computed value
        return CustomStringPrinter(value, color_map["String"])
    if isinstance(value, Array):
        return CustomArrayPrinter(value, color_map["array"])
    if isinstance(value, list):
        return CustomListPrinter(value, color_map["list"])
    if isinstance(value, dict):
        return CustomDictPrinter(value, color_map["dict"])
    # REMOVED: tuple handling - () now creates code blocks
    if isinstance(value, Stacker):
        return CustomBlockPrinter(value, color_map["block"])
    if callable(value):
        return CutomCallablePrinter(value, color_map["callable"])
    return value


def disp_colored(stack_list: list[object]) -> str:
    stack_str = colored("[", "yellow")
    for item in stack_list:
        stack_str += str(custom_print(item))
        stack_str += " "
    if stack_list:
        # Drop only the trailing separator; on an empty stack there is
        # none, and trimming would truncate the bracket's ANSI reset code
        stack_str = stack_str[0:-1]
    stack_str += colored("]", "yellow")
    return stack_str


def plain_text(item: object) -> str:
    """Formats one stack item exactly like the colored display, minus the colors.

    Each printer's ``__repr__`` is its color-free text, so the colored and the
    plain display share one set of type cases (``custom_print``).

    Args:
        item: A value from the stack.

    Returns:
        The item's display text.
    """
    printed = custom_print(item)
    # custom_print hands back unknown kinds of value unchanged; the colored
    # display shows those with str(), so do the same here.
    return repr(printed) if isinstance(printed, CustomPrinter) else str(printed)


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


def disp_stack(stack_list: list[object], colored: bool = False) -> None:
    if colored:
        print(disp_colored(stack_list))
    else:
        print(disp_default(stack_list))
