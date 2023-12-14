from __future__ import annotations

import ast
import re
from typing import Any

from stacker.syntax.lexer import lex_string


def evaluate_token_or_return_str(token: str) -> Any:
    """Evaluates a token if it is a number, otherwise returns the token as a string."""
    try:
        return ast.literal_eval(token)
    except (ValueError, SyntaxError) as e:
        return token


def starts_with_char(expression: str, char: str) -> bool:
    try:
        return expression.strip().startswith(char)
    except Exception:
        return False


def remove_start_end_quotes(expression: str) -> str:
    """
    Removes the starting and ending quotes from the specified expression.

    :param expression: The expression to be processed.
    :return: The expression with the starting and ending quotes removed.
    """
    if expression.startswith("'") and expression.endswith("'"):
        return expression[1:-1]
    if expression.startswith('"') and expression.endswith('"'):
        return expression[1:-1]
    return expression


def is_balanced(expression: str, open_char: str, close_char: str) -> bool:
    """
    Checks if the specified expression is balanced.

    :param
        expression: The expression to be checked.
        open_char: The opening character.
        close_char: The closing character.
    :return: True if the expression is balanced, otherwise False.
    """
    open_count = expression.count(open_char)
    close_count = expression.count(close_char)
    return open_count == close_count


def is_single(expression: str, open_char: str, close_char: str) -> bool:
    """
    Checks if the specified expression is a single instance of the specified
    open and close characters.

    :param
        expression: The expression to be checked.
        open_char: The opening character.
        close_char: The closing character.
    :return: True if the expression is a single instance of the specified
    """
    if is_balanced(expression, open_char, close_char):
        return expression.count(open_char) == 1 and expression.count(close_char) == 1
    return False


def is_array(expression: str) -> bool:
    """
    Checks if the specified expression is an array.

    :param expression: The expression to be checked.
    :return: True if the expression is an array, otherwise False.
    """
    return starts_with_char(expression, "[")


def is_tuple(expression: str) -> bool:
    """
    Checks if the specified expression is a tuple.

    :param expression: The expression to be checked.
    :return: True if the expression is a tuple, otherwise False.
    """
    return starts_with_char(expression, "(")


def is_brace(expression: str) -> bool:
    """
    Checks if the specified expression is a brace.

    :param expression: The expression to be checked.
    :return: True if the expression is a brace, otherwise False.
    """
    return starts_with_char(expression, "{")


def is_array_balanced(expression: str) -> bool:
    """
    Checks if the specified array expression is balanced.

    :param expression: The expression to be checked.
    :return: True if the expression is a balanced array, otherwise False.
    """
    return is_balanced(expression, "[", "]")


def is_tuple_balanced(expression: str) -> bool:
    """
    Checks if the specified tuple expression is balanced.

    :param expression: The expression to be checked.
    :return: True if the expression is a balanced tuple, otherwise False.
    """
    return is_balanced(expression, "(", ")")


def is_brace_balanced(expression: str) -> bool:
    return is_balanced(expression, "{", "}")


def is_single_array(expression: str) -> bool:
    """
    Checks if the specified expression is a single array.

    :param expression: The expression to be checked.
    :return: True if the expression is a single array, otherwise False.
    """
    return is_single(expression, "[", "]")


def is_single_tuple(expression: str) -> bool:
    return is_single(expression, "(", ")")


def is_single_brace(expression: str) -> bool:
    return is_single(expression, "{", "}")


def is_block(expression: str) -> bool:
    if not isinstance(expression, str):
        return False
    opener = expression.count("{")
    closer = expression.count("}")
    if opener == 0 and closer == 0:
        return False
    return opener == closer


def is_string(expression: str) -> bool:
    return (expression.startswith("'") and expression.endswith("'")) or (
        expression.startswith('"') and expression.endswith('"')
    )


def is_undefined_symbol(expression: str) -> bool:
    return expression.startswith("$") and not expression.endswith("$")


def convert_custom_array_to_proper_list(token: str) -> str:
    """
    Converts a custom list token into a proper Python list.

    :param token: The custom list token to be converted.
    :return: The converted token as a proper Python list.

    Example:
    Input:  "[1 2 3; 4 5 6]"
    Output: "[[1, 2, 3], [4, 5, 6]]"
    Input:  "[1 2 3]"
    Output: "[1, 2, 3]"
    """

    token = token.replace(";", "], [")
    token = re.sub(r"(\d+(\.\d+)?)\s+", r"\1, ", token)
    open_brackets = token.count("[")
    close_brackets = token.count("]")
    if open_brackets > close_brackets:
        token += "]" * (open_brackets - close_brackets)
    if is_array(token) and not is_single_array(token):
        token = f"[{token}]"
    return token


def convert_custom_tuple_to_proper_tuple(token: str) -> str:
    """
    Converts a custom tuple token into a proper Python tuple.

    :param token: The custom tuple token to be converted.
    :return: The converted token as a proper Python tuple.

    Example:
    Input:  "(1 2 3; 4 5 6)"
    Output: "((1, 2, 3), (4, 5, 6))"
    """
    token = re.sub(r"(\d+(\.\d+)?)\s+", r"\1, ", token)
    token = re.sub(r";\s+", r"), (", token)

    open_parenthesis = token.count("(")
    close_parenthesis = token.count(")")
    if open_parenthesis > close_parenthesis:
        token += ")" * (open_parenthesis - close_parenthesis)
    if is_tuple(token) and not is_single_tuple(token):
        token = f"({token})"
    return token


def convert_custom_string_tuple_to_proper_tuple(token: str) -> str:
    """
    Converts a custom tuple token with string elements into a proper Python tuple.

    :param token: The custom tuple token to be converted.
    :return: The converted token as a proper Python tuple.

    Example:
    Input:  "(a b)"
    Output: "("a", "b")"
    Input:  "(x)"
    Output: "x"
    """
    # Convert sequences of non-number, non-punctuation characters to
    #    use commas and surround with quotes
    token = re.sub(r"([a-zA-Z_]\w*)\s*", r'"\1", ', token)
    # Change semicolons to tuple separators
    token = re.sub(r";\s*", r"), (", token)

    open_parenthesis = token.count("(")
    close_parenthesis = token.count(")")
    if open_parenthesis > close_parenthesis:
        token += ")" * (open_parenthesis - close_parenthesis)
    if is_tuple(token) and not is_single_tuple(token):
        token = f"({token})"

    # Clean up any trailing commas and quotes
    token = re.sub(r", \)", r")", token)
    token = re.sub(r'", ', r'",', token)
    return token


def parse_expression(expression: str) -> list:
    """
    input(str)  : [1 2 3] 4 5 a
    output(list): [[1, 2, 3], 4, 5, 'a']
    """
    ignore_tokens = ['"""', "'''"]
    lexed_expression: list = lex_string(expression)
    tokens = []
    for token in lexed_expression:
        if token in ignore_tokens:
            continue
        elif is_array(token):
            token = convert_custom_array_to_proper_list(token)
            tokens.append(evaluate_token_or_return_str(token))
        elif is_tuple(token):
            token = convert_custom_tuple_to_proper_tuple(token)
            tokens.append(evaluate_token_or_return_str(token))
        elif is_string(token):
            tokens.append(token)
        else:
            tokens.append(evaluate_token_or_return_str(token))
    return tokens


if __name__ == "__main__":
    print(parse_expression("[1 2 3] 4 5 a +"))
    print(parse_expression("(1)"))
