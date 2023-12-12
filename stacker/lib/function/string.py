from __future__ import annotations


def _asc(value: str) -> int:
    """Returns the ASCII value of the specified character."""
    if len(value) != 1:
        raise ValueError(f"Length of value must be 1. `value`: {value}")
    try:
        return ord(value)
    except TypeError:
        raise TypeError(f"Cannot convert {value} to ASCII.")


def _chr(value: int) -> str:
    """Returns the character that matches the specified ASCII value."""
    try:
        return chr(value)
    except TypeError:
        raise TypeError(f"Cannot convert {value} to character.")


def _concat(value1: str, value2: str) -> str:
    """Concatenate two strings."""
    return value1 + value2


# def _contains(value1: str, value2: str) -> bool:
#     """Returns whether the first string contains the second string."""
#     return value2 in value1


# def _endswith(value1: str, value2: str) -> bool:
#     """Returns whether the first string ends with the second string."""
#     return value1.endswith(value2)


# def _startswith(value1: str, value2: str) -> bool:
#     """Returns whether the first string starts with the second string."""
#     return value1.startswith(value2)


# def _find(value1: str, value2: str) -> int:
#     """Returns the index of the first occurrence of the second string in the first string."""
#     return value1.find(value2)


# def _join(value1: str, value2: str) -> str:
#     """Concatenate two strings."""
#     return value1.join(value2)


string_operators = {
    "asc": {
        "func": (lambda value: _asc(value)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the ASCII value of the specified character.",
    },
    "chr": {
        "func": (lambda value: _chr(value)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the character that matches the specified ASCII value.",
    },
    "concat": {
        "func": (lambda value1, value2: _concat(value1, value2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Concatenate two strings.",
    },
    # "contains": {
    #     "func": (lambda value1, value2: _contains(value1, value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Returns whether the first string contains the second string.",
    # },
    # "endswith": {
    #     "func": (lambda value1, value2: _endswith(value1, value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Returns whether the first string ends with the second string.",
    # },
    # "startswith": {
    #     "func": (lambda value1, value2: _startswith(value1, value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Returns whether the first string starts with the second string.",
    # },
    # "find": {
    #     "func": (lambda value1, value2: _find(value1, value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Returns the index of the first occurrence of the second string in the first string.",
    # },
    # "join": {
    #     "func": (lambda value1, value2: _join(value1, value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Concatenate two strings.",
    # },
}
