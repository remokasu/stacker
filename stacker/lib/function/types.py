from __future__ import annotations


def _int(x):
    try:
        return int(x)
    except TypeError:
        raise TypeError(f"Cannot take int of {x}.")


def _float(x):
    try:
        return float(x)
    except TypeError:
        raise TypeError(f"Cannot take float of {x}.")


def _str(x):
    try:
        return str(x)
    except TypeError:
        raise TypeError(f"Cannot take str of {x}.")


def _bool(x):
    try:
        return bool(x)
    except TypeError:
        raise TypeError(f"Cannot take bool of {x}.")


type_operators = {
    "int": {
        "func": (lambda x: _int(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to int",
    },
    "float": {
        "func": (lambda x: _float(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to float",
    },
    "str": {
        "func": (lambda x: _str(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to str",
    },
    "bool": {
        "func": (lambda x: _bool(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to bool",
    },
}
