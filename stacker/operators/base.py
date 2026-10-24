from __future__ import annotations

import re

from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, symbol_as_value_message
from stacker.util.disp import plain_text


def _convert_to_base(word: str, value: object, base: int) -> str | int:
    """``value word``: ``value`` (an integer, or a string such as ``"0b101"``) in the base of ``word``."""
    if isinstance(value, Symbol):
        raise StackerTypeError(symbol_as_value_message(word, value.name))
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise StackerTypeError(f'`{word}` expects an integer or a string such as "0b101", got {plain_text(value)}')
    if isinstance(value, int):
        # an integer goes straight to its base; no detour through its decimal text
        return {2: bin, 8: oct, 10: int, 16: hex}[base](value)
    shown = value
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
        raise StackerTypeError(f"`{word}` cannot read {plain_text(shown)} as a number")

    # a plain decimal (leading zeros allowed) is read as such; the prefixed forms by their prefix
    value_as_int = int(value, 10) if decimal_pattern.match(value) else int(value, 0)

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
        "func": (lambda value: _convert_to_base("bin", value, 2)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Binary representation",
    },
    "oct": {
        "func": (lambda value: _convert_to_base("oct", value, 8)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Octal representation",
    },
    "dec": {
        "func": (lambda value: _convert_to_base("dec", value, 10)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Decimal representation",
    },
    "hex": {
        "func": (lambda value: _convert_to_base("hex", value, 16)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Hexadecimal representation",
    },
}
