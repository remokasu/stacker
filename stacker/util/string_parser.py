from __future__ import annotations

import ast
import logging
import re

from typing import Any


def parse_string(s: str) -> list:
    """ Parses a string into a list of tokens.
    :param s: The string to be parsed.
    :return: A list of tokens.
    """
    result = []
    current_token = ""
    brackets = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}
    # brackets = {"[": "]", "(": ")", "{": "}"}  # TODO: fix bug ?
    bracket_stack: list[Any] = []
    for char in s:
        if char in brackets:
            if bracket_stack and brackets[bracket_stack[-1]] == char:
                current_token += char
                bracket_stack.pop()
                if not bracket_stack:
                    if current_token[0] == "'" or current_token[0] == '"':
                        result.append(current_token[1:-1])  # remove quotes
                    else:
                        result.append(current_token)
                    current_token = ""
            else:
                bracket_stack.append(char)
                current_token += char
        elif bracket_stack:
            current_token += char
            if char == brackets[bracket_stack[-1]]:
                bracket_stack.pop()
                if not bracket_stack:
                    if current_token[0] == "'" or current_token[0] == '"':
                        result.append(current_token[1:-1])  # remove quotes
                    else:
                        result.append(current_token)
                    current_token = ""
        elif char.isspace():
            if current_token:
                result.append(current_token)
                current_token = ""
        else:
            current_token += char
    if current_token:  # add the last token if any
        result.append(current_token)
    logging.debug("parse string: %s", s)
    logging.debug("parsed: %s", str(result))
    return result


def evaluate_token_or_return_str(token: str) -> Any:
    """ Evaluates a token if it is a number, otherwise returns the token as a string.
    """
    logging.debug("evaluate_token_or_return_str: %s", token)
    try:
        return ast.literal_eval(token)
    except (ValueError, SyntaxError) as e:
        logging.debug("token (%s) is str", token)
        return token


def starts_with_char(expression: str, char: str) -> bool:
    try:
        return expression.strip().startswith(char)
    except Exception:
        return False


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
        return (
            expression.count(open_char) == 1 and
            expression.count(close_char) == 1
        )
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
    opener = expression.count('{')
    closer = expression.count('}')
    if opener == 0 and closer == 0:
        return False
    return opener == closer

def is_string(expression: str) -> bool:
    return (
        (expression.startswith("'") and expression.endswith("'")) or
        (expression.startswith('"') and expression.endswith('"'))
    )

def convert_custom_array_to_proper_list(token: str) -> str:
    """
    Converts a custom list token into a proper Python list.

    :param token: The custom list token to be converted.
    :return: The converted token as a proper Python list.

    Example:
    Input:  "[1 2 3; 4 5 6]"
    Output: "[[1, 2, 3], [4, 5, 6]]"
    """
    token = re.sub(r"(\d+(\.\d+)?)\s+", r"\1, ", token)
    token = re.sub(r";\s+", r"], [", token)

    open_brackets = token.count('[')
    close_brackets = token.count(']')
    if open_brackets > close_brackets:
        token += ']' * (open_brackets - close_brackets)
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

    open_parenthesis = token.count('(')
    close_parenthesis = token.count(')')
    if open_parenthesis > close_parenthesis:
        token += ')' * (open_parenthesis - close_parenthesis)
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
    """
    # Convert sequences of non-number, non-punctuation characters to
    #    use commas and surround with quotes
    token = re.sub(r"([a-zA-Z_]\w*)\s*", r'"\1", ', token)
    # Change semicolons to tuple separators
    token = re.sub(r";\s*", r"), (", token)

    open_parenthesis = token.count('(')
    close_parenthesis = token.count(')')
    if open_parenthesis > close_parenthesis:
        token += ')' * (open_parenthesis - close_parenthesis)
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
    parsed_expressions = parse_string(expression)
    logging.debug("parsed_expressions: %s", parsed_expressions)
    tokens = []
    for token in parsed_expressions:
        if token in ignore_tokens:
            continue
        elif is_array(token):
            token = convert_custom_array_to_proper_list(token)
            tokens.append(evaluate_token_or_return_str(token))
        elif is_tuple(token):
            token = convert_custom_tuple_to_proper_tuple(token)
            tokens.append(evaluate_token_or_return_str(token))
        else:
            tokens.append(evaluate_token_or_return_str(token))
    return tokens
