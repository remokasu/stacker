from __future__ import annotations

import re


def convert_to_base(value: str | int, base: int) -> str | int:
    value = str(value)

    # 2進数 (0b...)
    binary_pattern = re.compile(r'^0b[01]+$')
    # 8進数 (0o...)
    octal_pattern = re.compile(r'^0o[0-7]+$')
    # 10進数
    decimal_pattern = re.compile(r'^[-+]?\d+$')
    # 16進数 (0x...)
    hex_pattern = re.compile(r'^0x[\da-fA-F]+$')

    if not (binary_pattern.match(value) or octal_pattern.match(value) or decimal_pattern.match(value) or hex_pattern.match(value)):
        raise ValueError("Invalid number format.(convert_to_base)")

    # 文字列を整数に変換
    value_as_int = int(value, 0)  # 0は、2進数、8進数、16進数を自動的に検出して処理することを意味する

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