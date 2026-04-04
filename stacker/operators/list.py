from __future__ import annotations


def _car(xs: list | tuple) -> object:
    """Returns the first element of a list."""
    if not xs:
        raise ValueError("car: empty list")
    return xs[0]


def _cdr(xs: list | tuple) -> list:
    """Returns the list without the first element."""
    if not xs:
        raise ValueError("cdr: empty list")
    return list(xs[1:])


def _cons(x: object, xs: list) -> list:
    """Prepends x to the list xs."""
    return [x] + list(xs)


def _null(xs: object) -> bool:
    """Returns true if the value is null (None) or an empty list."""
    return xs is None or xs == [] or xs == ()


def _pair(xs: object) -> bool:
    """Returns true if xs is a non-empty list."""
    return isinstance(xs, (list, tuple)) and len(xs) > 0


list_operators = {
    "seq": {
        "func": (lambda x1, x2: list(range(x1, x2 + 1))),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate sequence from x1 to x2",
    },
    "car": {
        "func": (lambda xs: _car(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the first element of a list.",
    },
    "cdr": {
        "func": (lambda xs: _cdr(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the list without the first element.",
    },
    "cons": {
        "func": (lambda x, xs: _cons(x, xs)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Prepends x to the list xs.",
    },
    "null?": {
        "func": (lambda xs: _null(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the list is empty.",
    },
    "pair?": {
        "func": (lambda xs: _pair(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if xs is a non-empty list.",
    },
}
