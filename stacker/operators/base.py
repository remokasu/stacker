from __future__ import annotations

import re


def _convert_to_base(value: str | int, base: int) -> str | int:
    value = str(value)

    # Binary (0b...)
    binary_pattern = re.compile(r"^0b[01]+$")
    # octal (0o...)
    octal_pattern = re.compile(r"^0o[0-7]+$")
    # decimal
    decimal_pattern = re.compile(r"^[-+]?\d+$")
    # hexadecimal (0x...)
    hex_pattern = re.compile(r"^0x[\da-fA-F]+$")

    if not (
        binary_pattern.match(value)
        or octal_pattern.match(value)
        or decimal_pattern.match(value)
        or hex_pattern.match(value)
    ):
        raise ValueError("Invalid number format.(convert_to_base)")

    value_as_int = int(value, 0)
    # 0 means that binary, octal, and hexadecimal numbers are automatically detected and processed

    if base == 2:
        return bin(value_as_int)
    elif base == 8:
        return oct(value_as_int)
    elif base == 10:
        return value_as_int
    elif base == 16:
        return hex(value_as_int)
    else:
        raise ValueError("Invalid base.")


base_operators = {
    "bin": {
        "func": (lambda value: _convert_to_base(value, 2)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Binary representation",
    },
    "oct": {
        "func": (lambda value: _convert_to_base(value, 8)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Octal representation",
    },
    "dec": {
        "func": (lambda value: _convert_to_base(value, 10)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Decimal representation",
    },
    "hex": {
        "func": (lambda value: _convert_to_base(value, 16)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hexadecimal representation",
    },
}
