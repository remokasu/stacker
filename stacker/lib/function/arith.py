from __future__ import annotations


def _add(x1, x2):
    try:
        return x1 + x2
    except TypeError:
        raise TypeError(f"Cannot add {x1} and {x2}.")


def _sub(x1, x2):
    try:
        return x1 - x2
    except TypeError:
        raise TypeError(f"Cannot subtract {x1} and {x2}.")


def _mul(x1, x2):
    try:
        return x1 * x2
    except TypeError:
        raise TypeError(f"Cannot multiply {x1} and {x2}.")


def _div(x1, x2):
    try:
        return x1 / x2
    except TypeError:
        raise TypeError(f"Cannot divide {x1} and {x2}.")


def _intdiv(x1, x2):
    try:
        return x1 // x2
    except TypeError:
        raise TypeError(f"Cannot integer divide {x1} and {x2}.")


def _mod(x1, x2):
    try:
        return x1 % x2
    except TypeError:
        raise TypeError(f"Cannot mod {x1} and {x2}.")


def _increment(x):
    try:
        return x + 1
    except TypeError:
        raise TypeError(f"Cannot increment {x}.")


def _decrement(x):
    try:
        return x - 1
    except TypeError:
        raise TypeError(f"Cannot decrement {x}.")


arith_operators = {
    "+": {
        "func": (lambda x1, x2: _add(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Add",
    },
    "-": {
        "func": (lambda x1, x2: _sub(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Subtract",
    },
    "*": {
        "func": (lambda x1, x2: _mul(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Multiply",
    },
    "//": {
        "func": (lambda x1, x2: _intdiv(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Integer divide",
    },
    "/": {
        "func": (lambda x1, x2: _div(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Divide",
    },
    "%": {
        "func": (lambda x1, x2: _mod(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Mod",
    },
    "++": {
        "func": (lambda x: _increment(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Increment",
    },
    "--": {
        "func": (lambda x: _decrement(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Decrement",
    },
}
