from __future__ import annotations


def _seq(x1, x2):
    """
    x1: int starting value
    x2: int ending value
    """
    try:
        return list(range(x1, x2 + 1))
    except TypeError:
        raise TypeError(f"Cannot generate sequence from {x1} to {x2}.")


def _range(x1, x2):
    """
    x1: int starting value
    x2: int ending value
    """
    try:
        return list(range(x1, x2))
    except TypeError:
        raise TypeError(f"Cannot generate range from {x1} to {x2}.")


def _min(xs):
    """
    xs: list of numbers
    """
    try:
        return min(xs)
    except TypeError:
        raise TypeError(f"Cannot get minimum of {xs}.")


def _max(xs):
    """
    xs: list of numbers
    """
    try:
        return max(xs)
    except TypeError:
        raise TypeError(f"Cannot get maximum of {xs}.")


def _sum(xs):
    """
    xs: list of numbers
    """
    try:
        return sum(xs)
    except TypeError:
        raise TypeError(f"Cannot sum {xs}.")


def _len(xs):
    """
    xs: list
    """
    try:
        return len(xs)
    except TypeError:
        raise TypeError(f"Cannot get length of {xs}.")


def _append(xs, x):
    """
    xs: list
    x: value to append to list
    """
    try:
        return xs.append(x)
    except TypeError:
        raise TypeError(f"Cannot append {x} to {xs}.")


def _extend(xs1, xs2):
    """
    xs1: list
    xs2: list to extend xs1 with
    """
    try:
        return xs1.extend(xs2)
    except TypeError:
        raise TypeError(f"Cannot extend {xs1} with {xs2}.")


# def _insert(xs, i, x):
#     """
#     xs: list
#     i: index to insert x at
#     x: value to insert into xs
#     """
#     try:
#         return xs.insert(i, x)
#     except TypeError:
#         raise TypeError(f"Cannot insert {x} into {xs} at index {i}.")


# def _reverse(xs):
#     """
#     xs: list
#     """
#     try:
#         return xs.reverse()
#     except TypeError:
#         raise TypeError(f"Cannot reverse {xs}.")


# def _sort(xs):
#     """
#     xs: list
#     """
#     try:
#         return xs.sort()
#     except TypeError:
#         raise TypeError(f"Cannot sort {xs}.")


# def _count(xs, x):
#     """
#     xs: list
#     x: value to count in xs
#     """
#     try:
#         return xs.count(x)
#     except TypeError:
#         raise TypeError(f"Cannot count {x} in {xs}.")


list_operators = {
    "seq": {
        "func": (lambda x1, x2: _seq(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate sequence from x1 to x2",
    },
    "range": {
        "func": (lambda x1, x2: _range(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate range from x1 to x2",
    },
    "min": {
        "func": (lambda xs: _min(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Get minimum of list of numbers",
    },
    "sum": {
        "func": (lambda xs: _sum(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Sum list of numbers",
    },
    "max": {
        "func": (lambda xs: _max(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Get maximum of list of numbers",
    },
    "len": {
        "func": (lambda xs: _len(xs)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Get length of list",
    },
}
