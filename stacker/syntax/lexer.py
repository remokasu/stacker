from __future__ import annotations

from typing import Any


def lex_string(s: str) -> list:
    """
    Parses a string into a list of tokens.

    This function takes a string and splits it into tokens based on delimiters and whitespace.
    It handles nested delimiters and ensures that tokens are correctly formed even when delimiters are nested.

    Args:
        s (str): The string to be parsed.

    Returns:
        list: A list of tokens parsed from the input string.

    Example:
        >>> lex_string("a b c")
        ['a', 'b', 'c']
        >>> lex_string("a (b c)")
        ['a', '(b c)']
        >>> lex_string("a (b (c))")
        ['a', '(b (c))']
        >>> lex_string("a (b (c)) d")
        ['a', '(b (c))', 'd']
        >>> lex_string("a (b (c)) d (e)")
        ['a', '(b (c))', 'd', '(e)']
        >>> lex_string("a {b c} {d e}")
        ['a', '{b c}', '{d e}']
        >>> lex_string("a {b c {d e}} {f h}")
        ['a', '{b c {d e}}', '{f h}']
    """

    tokens = []
    current_token = ""
    delimiter_mapping = {
        "[": "]",
        "(": ")",
        "{": "}",
        "'": "'",
        '"': '"',
    }
    bracket_stack: list[Any] = []

    for char in s:
        if char in delimiter_mapping:
            if bracket_stack and delimiter_mapping[bracket_stack[-1]] == char:
                current_token += char
                bracket_stack.pop()
                if not bracket_stack:
                    tokens.append(current_token)
                    current_token = ""
            else:
                bracket_stack.append(char)
                current_token += char
        elif len(bracket_stack) > 0:
            current_token += char
            if char == delimiter_mapping[bracket_stack[-1]]:
                bracket_stack.pop()
                if not bracket_stack:
                    tokens.append(current_token)
                    current_token = ""
        elif char.isspace():
            if current_token:
                tokens.append(current_token)
                current_token = ""
        else:
            current_token += char
    if current_token:  # add the last token if any
        tokens.append(current_token)
    return tokens


if __name__ == "__main__":
    import doctest

    doctest.testmod()
