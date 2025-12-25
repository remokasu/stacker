from __future__ import annotations


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
        "func": (lambda value: ord(value)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the ASCII value of the specified character.",
    },
    "chr": {
        "func": (lambda value: chr(value)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns the character that matches the specified ASCII value.",
    },
    "concat": {
        "func": (lambda value1, value2: value1 + value2),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Concatenate two strings.",
    },
    "search": {
        "func": (lambda value1, value2: value1.find(value2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns the index of the first occurrence of the second string in the first string.",
    },
    "replace": {
        "func": (lambda value1, value2, value3: value1.replace(value2, value3)),
        "arg_count": 3,
        "push_result_to_stack": True,
        "desc": "Replaces all occurrences of the second string with the third string in the first string.",
    },
    "lower": {
        "func": (lambda value: value.lower()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to lowercase.",
    },
    "upper": {
        "func": (lambda value: value.upper()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to uppercase.",
    },
    "title": {
        "func": (lambda value: value.title()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Converts the specified string to title case.",
    },
    "strip": {
        "func": (lambda value: value.strip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes leading and trailing whitespace from the specified string.",
    },
    "lstrip": {
        "func": (lambda value: value.lstrip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes leading whitespace from the specified string.",
    },
    "rstrip": {
        "func": (lambda value: value.rstrip()),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Removes trailing whitespace from the specified string.",
    },
    # "split": {
    #     "func": (lambda value1, value2: value1.split(value2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Splits the specified string into a list of substrings using the specified delimiter.",
    # },
    "join": {
        "func": (lambda value1, value2: value2.join(value1)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Concatenates the elements of the specified list using the specified delimiter.",
    },
    # "len": {
    #     "func": (lambda value: len(value)),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "Returns the length of the specified string.",
    # },
    "contains": {
        "func": (lambda value1, value2: value2 in value1),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Returns whether the first string contains the second string.",
    },
    "subseq": {
        "func": (lambda value: value.split()[0]),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns a substring of the specified string.",
    },
    "format": {
        "func": (lambda value1, value2: value1.format(value2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Formats the specified string using the specified arguments.",
    },
}
