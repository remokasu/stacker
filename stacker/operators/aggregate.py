from __future__ import annotations

from stacker.error import StackerTypeError, ValidationError
from stacker.util.disp import plain_text


def _empty(xs: object) -> bool:
    """Returns True when a list, an array, a string or a dictionary has nothing in it.

    Raises:
        StackerTypeError: ``xs`` has no elements to count (``null`` included:
            whether a value is null is `null?`'s question).
    """
    if isinstance(xs, (list, str, dict)):
        return len(xs) == 0
    raise StackerTypeError(f"`empty?` expects a list, an array, a string or a dictionary, got {plain_text(xs)}")


def _uncomparable_message(word: str, items: object) -> str:
    """The message for ``word`` given items that have no order between them."""
    seen: list[object] = []
    for item in items:  # type: ignore[attr-defined]
        for other in seen:
            try:
                other < item  # noqa: B015
            except TypeError:
                return f"`{word}` cannot compare {plain_text(other)} with {plain_text(item)}"
        seen.append(item)
    return f"`{word}` cannot order these values"


def ordered(word: str, operate):  # type: ignore[no-untyped-def]
    """Wraps a word that orders its items so a type error names the word and the two values."""

    def apply(items: object) -> object:
        if isinstance(items, (int, float, complex, bool)) or items is None:
            raise StackerTypeError(f"`{word}` expects a list, got {plain_text(items)}")
        try:
            return operate(items)
        except ValueError as error:
            raise ValidationError(f"`{word}` expects at least one value, got an empty list") from error
        except TypeError as error:
            raise StackerTypeError(_uncomparable_message(word, items)) from error

    return apply


aggregate_operators = {
    "any": {
        "func": (lambda xs: any(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns True if any element of an iterable is True.",
    },
    "all": {
        "func": (lambda xs: all(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns True if all elements of an iterable are True.",
    },
    "sum": {
        "func": (lambda xs: sum(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Sums a iterable.",
    },
    "len": {
        "func": (lambda xs: len(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the length of an iterable.",
    },
    "empty?": {
        "func": (lambda xs: _empty(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if a list, an array, a string or a dictionary has no elements",
    },
    "min": {
        "func": ordered("min", min),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the minimum value in an iterable.",
    },
    "max": {
        "func": ordered("max", max),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the maximum value in an iterable.",
    },
}
