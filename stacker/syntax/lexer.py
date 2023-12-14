from __future__ import annotations


def lex_string(s: str) -> list:
    """Parses a string into a list of tokens.
    :param s: The string to be parsed.
    :return: A list of tokens.
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


def test_lex_string():
    assert lex_string("a b c") == ["a", "b", "c"]
    assert lex_string("a [b c]") == ["a", "[b c]"]
    assert lex_string("a (b c)") == ["a", "(b c)"]
    assert lex_string("a {b c}") == ["a", "{b c}"]
    assert lex_string("a 'b c'") == ["a", "'b c'"]
    assert lex_string('a "b c"') == ["a", '"b c"']
    assert lex_string("a 'b c' d") == ["a", "'b c'", "d"]
    assert lex_string('a "b c" d') == ["a", '"b c"', "d"]
    assert lex_string("a 'b c' d 'e f'") == ["a", "'b c'", "d", "'e f'"]
    assert lex_string("a {b c} {d e}") == ["a", "{b c}", "{d e}"]
    assert lex_string("a {b c {d e}} {f h}") == ["a", "{b c {d e}}", "{f h}"]
    # assert lex_string("/* a b c */") == ["/* a b c */"]
    assert lex_string("[1]") == ["[1]"]
    assert lex_string("(1)") == ["(1)"]

    expr = "1 2 3 [4 5 6] 7 8 (9 10 11) a1 b1 c1 {1 2 +} '1+1' eval"
    exprs = [
        "1",
        "2",
        "3",
        "[4 5 6]",
        "7",
        "8",
        "(9 10 11)",
        "a1",
        "b1",
        "c1",
        "{1 2 +}",
        "'1+1'",
        "eval",
    ]
    tokens = lex_string(expr)
    assert tokens == exprs


if __name__ == "__main__":
    test_lex_string()
