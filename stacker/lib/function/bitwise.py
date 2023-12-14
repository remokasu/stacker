from __future__ import annotations


def _band(x1, x2):
    try:
        return x1 & x2
    except TypeError:
        raise TypeError(f"Cannot Bitwise and {x1} and {x2}.")


def _bor(x1, x2):
    try:
        return x1 | x2
    except TypeError:
        raise TypeError(f"Cannot Bitwise or {x1} and {x2}.")


def _bxor(x1, x2):
    try:
        return x1 ^ x2
    except TypeError:
        raise TypeError(f"Cannot Bitwise xor {x1} and {x2}.")


def _bnot(x):
    try:
        return ~x
    except TypeError:
        raise TypeError(f"Cannot Bitwise not {x}.")


def _invert(x):
    try:
        return ~x
    except TypeError:
        raise TypeError(f"Cannot Bitwise invert {x}.")


def _lshift(value, n):
    try:
        return value << n
    except TypeError:
        raise TypeError(f"Cannot Bitwise lshift {value} and {n}.")


def _rshift(value, n):
    try:
        return value >> n
    except TypeError:
        raise TypeError(f"Cannot Bitwise rshift {value} and {n}.")


def _rol(value, n):
    try:
        return (value << n) | (value >> (32 - n))
    except TypeError:
        raise TypeError(f"Cannot Bitwise rol {value} and {n}.")


def _ror(value, n):
    try:
        return (value >> n) | (value << (32 - n))
    except TypeError:
        raise TypeError(f"Cannot Bitwise ror {value} and {n}.")


bitwise_operators = {
    "band": {
        "func": (lambda x1, x2: _band(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise and",
    },
    "bor": {
        "func": (lambda x1, x2: _bor(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise or",
    },
    "bxor": {
        "func": (lambda x1, x2: _bxor(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise xor",
    },
    "~": {
        "func": (lambda x: _invert(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Bitwise invert",
    },
    ">>": {
        "func": (lambda value, n: _rshift(value, n)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise right shift",
    },
    "<<": {
        "func": (lambda value, n: _lshift(value, n)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Bitwise left shift",
    },
}
