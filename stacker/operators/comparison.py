from __future__ import annotations

import operator
from collections.abc import Callable

from stacker.engine.data_type import Array
from stacker.error import StackerRuntimeError


def _compare(word: str, compare: Callable[[object, object], bool], x1: object, x2: object) -> bool:
    """Compares two values with ``compare``, naming ``word`` when the values cannot be compared by contents.

    Raises:
        StackerRuntimeError: Arrays or dictionaries that contain themselves,
            or are nested too deep, cannot be compared by contents.
    """
    try:
        return compare(x1, x2)
    except RecursionError:
        raise StackerRuntimeError(
            f"`{word}` cannot compare arrays or dictionaries nested this deep or containing themselves; "
            "compare with `same?` or compare their fields"
        ) from None


def _equal(x1: object, x2: object) -> bool:
    """``x1 x2 ==``: whether the two values have equal contents."""
    return _compare("==", operator.eq, x1, x2)


def _same(x1: object, x2: object) -> bool:
    """``x1 x2 same?``: the same array or dictionary; equal contents for any other value."""
    if isinstance(x1, (Array, dict)) or isinstance(x2, (Array, dict)):
        return x1 is x2
    return _equal(x1, x2)


compare_operators = {
    "==": {
        "func": (lambda x1, x2: _equal(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "same?": {
        "func": (lambda x1, x2: _same(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns true if two arrays or dictionaries are the same one, not two with equal contents; other values compare with ==: a b same?",
    },
    "!=": {
        "func": (lambda x1, x2: not _equal(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "<=": {
        "func": (lambda x1, x2: _compare("<=", operator.le, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "<": {
        "func": (lambda x1, x2: _compare("<", operator.lt, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    ">=": {
        "func": (lambda x1, x2: _compare(">=", operator.ge, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    ">": {
        "func": (lambda x1, x2: _compare(">", operator.gt, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
    "eq": {
        "func": (lambda x1, x2: _equal(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Equal",
    },
    "neq": {
        "func": (lambda x1, x2: not _equal(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Not equal",
    },
    "le": {
        "func": (lambda x1, x2: _compare("<=", operator.le, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than or equal to",
    },
    "lt": {
        "func": (lambda x1, x2: _compare("<", operator.lt, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Less than",
    },
    "ge": {
        "func": (lambda x1, x2: _compare(">=", operator.ge, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than or equal to",
    },
    "gt": {
        "func": (lambda x1, x2: _compare(">", operator.gt, x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Greater than",
    },
}
