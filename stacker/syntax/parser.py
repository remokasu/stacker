from __future__ import annotations

import ast
import re
from typing import List, Union, Iterator, Optional, Any
from stacker.syntax.lexer import lex_string

__transpose_symbol__ = "^T"


def evaluate_token_or_return_str(token: str) -> Any:
    """Evaluates a token if it is a number, otherwise returns the token as a string."""
    if is_block(token):
        return token  # {} is not dictionary
    try:
        return ast.literal_eval(token)
    except (ValueError, SyntaxError):
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
    if not isinstance(expression, str):
        return False
    return (expression.startswith("'") and expression.endswith("'")) or (
        expression.startswith('"') and expression.endswith('"')
    )


def is_list(expression: str) -> bool:
    if not isinstance(expression, str):
        return False
    return expression.startswith("[") and expression.endswith("]")


def is_symbol(expression: str) -> bool:
    return expression.startswith("$") and not expression.endswith("$")


def is_label_symbol(expression: str) -> bool:
    return expression.endswith(":") and not expression.startswith(":")


def is_transpose_command(expression: str) -> bool:
    return expression == __transpose_symbol__


def is_contains_transpose_command(expression: str) -> bool:
    if len(expression) > len(__transpose_symbol__):
        return expression[-len(__transpose_symbol__) :] == __transpose_symbol__
    return False


class Token:
    """Represents a single token."""

    def __init__(self, type_: str, value: str) -> None:
        self.type: str = type_
        self.value: str = value

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value})"


class Identifier:
    """Represents an identifier."""

    def __init__(self, name: str) -> None:
        self.name: str = name

    def __repr__(self) -> str:
        return f"Identifier({self.name})"


class ListNode:
    """Represents a list node."""

    def __init__(self, elements: List[Any]) -> None:
        self.elements: List[Any] = elements

    def __repr__(self) -> str:
        return f"ListNode({self.elements})"


class TupleNode:
    """Represents a tuple node."""

    def __init__(self, elements: List[Any]) -> None:
        self.elements: List[Any] = elements

    def __repr__(self) -> str:
        return f"TupleNode({self.elements})"


class Tokenizer:
    """Splits input string into tokens."""

    # Define token patterns
    token_specification: List[tuple] = [
        ("BRACED_CONTENT", r"\{[^}]*\}"),  # Content inside braces (highest priority)
        # Complex numbers with real and imaginary parts (e.g., 2+3j, -4.5-6.7j)
        (
            "COMPLEX_NUMBER",
            r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[+-](\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[jJ]",
        ),
        (
            "NUMBER",
            r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[jJ]?",
        ),  # Integer, float, complex (imaginary only)
        (
            "STRING",
            r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")",
        ),  # Strings with single or double quotes
        ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),  # Identifier
        ("LBRACKET", r"\["),  # Left bracket
        ("RBRACKET", r"\]"),  # Right bracket
        ("LPAREN", r"\("),  # Left parenthesis
        ("RPAREN", r"\)"),  # Right parenthesis
        ("SEMICOLON", r";"),  # Semicolon
        ("OPERATOR", r"[+\-]"),  # Plus or minus sign
        ("SPACE", r"\s+"),  # Space
        ("COMMA", r","),  # Comma
        ("OTHER", r"."),  # Other characters
    ]

    def __init__(self, text: str) -> None:
        self.text: str = text
        self.tokens: Iterator[Token] = self.tokenize()

    def tokenize(self) -> Iterator[Token]:
        tok_regex: str = "|".join(
            f"(?P<{name}>{pattern})" for name, pattern in self.token_specification
        )
        get_token = re.compile(tok_regex).match
        pos: int = 0
        mo: Optional[re.Match] = get_token(self.text, pos)
        while mo:
            kind: str = mo.lastgroup  # type: ignore
            value: str = mo.group()
            if kind != "SPACE":  # Ignore spaces
                yield Token(kind, value)
            pos = mo.end()
            mo = get_token(self.text, pos)
        if pos != len(self.text):
            raise SyntaxError(
                f"Unexpected character {self.text[pos]!r} at position {pos}"
            )


class Parser:
    """Builds Python list or tuple structure from tokens."""

    def __init__(self, tokenizer: Tokenizer) -> None:
        self.tokens: Iterator[Token] = iter(tokenizer.tokens)
        self.current_token: Optional[Token] = None
        self.next_token()

    def next_token(self) -> None:
        """Get the next token."""
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            self.current_token = None

    def parse(self) -> Union[ListNode, TupleNode]:
        """Start parsing."""
        if self.current_token is None:
            return ListNode([])
        return self.parse_structure()

    def parse_structure(self) -> Union[ListNode, TupleNode]:
        """Parse a list or tuple structure."""
        elements: List[Any] = []
        if self.current_token.type == "LBRACKET":
            opening_bracket: str = "LBRACKET"
            closing_bracket: str = "RBRACKET"
            node_class = ListNode
        elif self.current_token.type == "LPAREN":
            opening_bracket = "LPAREN"
            closing_bracket = "RPAREN"
            node_class = TupleNode
        else:
            raise SyntaxError(
                f"Expected LBRACKET or LPAREN, got {self.current_token.type}"
            )
        self.expect(opening_bracket)
        while self.current_token and self.current_token.type != closing_bracket:
            if self.current_token.type == "BRACED_CONTENT":
                # Handle braced content
                content = self.current_token.value  # Includes the braces
                elements.append({"braced_content": content})
                self.next_token()
            elif self.current_token.type in ("LBRACKET", "LPAREN"):
                # Nested list or tuple
                elements.append(self.parse_structure())
            elif self.current_token.type == "COMPLEX_NUMBER":
                # Complex number with real and imaginary parts
                num_str = self.current_token.value
                number = ast.literal_eval(num_str)
                elements.append(number)
                self.next_token()
            elif self.current_token.type == "NUMBER":
                # Number (int, float, or imaginary-only complex)
                num_str = self.current_token.value
                number = ast.literal_eval(num_str)
                elements.append(number)
                self.next_token()
            elif self.current_token.type == "STRING":
                # String (remove quotes)
                string_value = self.current_token.value
                unquoted_string = ast.literal_eval(string_value)
                elements.append(unquoted_string)
                self.next_token()
            elif self.current_token.type == "IDENTIFIER":
                # Identifier
                elements.append(Identifier(self.current_token.value))
                self.next_token()
            elif self.current_token.type == "SEMICOLON":
                # Line separator (new substructure)
                self.next_token()
                elements.append(";")  # Keep semicolon as placeholder
            else:
                raise SyntaxError(f"Unexpected token {self.current_token}")
        self.expect(closing_bracket)
        # If there is at least one semicolon, we need to split
        if ";" in elements:
            split_elements = self.split_by_semicolon(elements, node_class)
            return node_class(split_elements)
        else:
            # No semicolons, return elements directly
            return node_class(elements)

    def split_by_semicolon(self, elements: List[Any], node_class: Any) -> List[Any]:
        """Create sublists or subtuples based on semicolons."""
        result: List[Any] = []
        current: List[Any] = []
        for item in elements:
            if item == ";":
                if current:
                    result.append(self.wrap_node(current, node_class))
                    current = []
            else:
                current.append(item)
        if current:
            result.append(self.wrap_node(current, node_class))
        return result

    def wrap_node(self, elements: List[Any], node_class: Any) -> Any:
        """Wrap elements into node_class, or return single element."""
        if len(elements) == 1 and isinstance(elements[0], (ListNode, TupleNode)):
            return elements[0]
        else:
            return node_class(elements)

    def expect(self, token_type: str) -> None:
        """Expect a specific token type and advance."""
        if self.current_token and self.current_token.type == token_type:
            self.next_token()
        else:
            expected: str = token_type
            actual: str = self.current_token.type if self.current_token else "EOF"
            raise SyntaxError(f"Expected token {expected}, got {actual}")


class ArrayConverter:
    """Converts custom array string to Python list or tuple format string."""

    def __init__(self, text: str) -> None:
        self.text: str = text

    def convert(self) -> str:
        tokenizer = Tokenizer(self.text)
        parser = Parser(tokenizer)
        parsed: Union[ListNode, TupleNode] = parser.parse()
        # Flatten singleton lists or tuples at the top level
        while (
            isinstance(parsed, (ListNode, TupleNode))
            and len(parsed.elements) == 1
            and isinstance(parsed.elements[0], (ListNode, TupleNode))
        ):
            parsed = parsed.elements[0]
        return self.format_structure(parsed)

    def format_structure(
        self,
        obj: Union[ListNode, TupleNode, int, float, complex, str, Identifier, dict],
    ) -> str:
        """Format the parsed structure into a string."""
        if isinstance(obj, ListNode):
            return (
                "["
                + ",".join(self.format_structure(item) for item in obj.elements)
                + "]"
            )
        elif isinstance(obj, TupleNode):
            return (
                "("
                + ",".join(self.format_structure(item) for item in obj.elements)
                + ")"
            )
        elif isinstance(obj, dict) and "braced_content" in obj:
            content = obj["braced_content"]
            # Remove extra spaces inside braces if needed
            content = content.strip()
            return f'"{content}"'
        elif isinstance(obj, Identifier):
            return f"'{self.format_identifier(obj)}'"
        elif isinstance(obj, str):
            return f"'\"{obj}\"'"
        elif isinstance(obj, complex):
            return str(obj)
        else:
            return str(obj)

    def format_identifier(self, obj: Identifier) -> str:
        """Format an identifier."""
        # return f'${obj.name}'
        return f"{obj.name}"


def convert_custom_array_to_proper_list(input_str: str) -> str:
    """
    >>> convert_custom_array_to_proper_list("[1 2 3; 4 5 6]")
    '[[1,2,3],[4,5,6]]'
    >>> convert_custom_array_to_proper_list("[1 2 3]")
    '[1,2,3]'
    >>> convert_custom_array_to_proper_list("[1 2 3; 4 5 6; 7 8 9]")
    '[[1,2,3],[4,5,6],[7,8,9]]'
    >>> convert_custom_array_to_proper_list("[1 2 3; 4 5 6; 7 8 9; 10 11 12]")
    '[[1,2,3],[4,5,6],[7,8,9],[10,11,12]]'
    >>> convert_custom_array_to_proper_list("[[1 2 3; 4 5 6; 7 8 9]; [10 11 12; 13 14 15; 16 17 18]; [19 20 21; 22 23 24; 25 26 27]]")
    '[[[1,2,3],[4,5,6],[7,8,9]],[[10,11,12],[13,14,15],[16,17,18]],[[19,20,21],[22,23,24],[25,26,27]]]'
    >>> convert_custom_array_to_proper_list("[1 2 3; 4 5 6; 7 8 9; [10 11 12]]")
    '[[1,2,3],[4,5,6],[7,8,9],[10,11,12]]'
    >>> convert_custom_array_to_proper_list("[1 2 3; 4 5 6; 7 8 9; [10 11 12; 13 14 15]]")
    '[[1,2,3],[4,5,6],[7,8,9],[[10,11,12],[13,14,15]]]'
    >>> convert_custom_array_to_proper_list("[a b c]")
    "['a','b','c']"
    >>> convert_custom_array_to_proper_list("[1 2 {3 4 5}]")
    '[1,2,"{3 4 5}"]'
    """
    converter = ArrayConverter(input_str)
    return converter.convert()


def parse_expression(expression: str) -> list[str]:
    """
    input(str)  : [1 2 3] 4 5 a
    output(list): [[1, 2, 3], 4, 5, 'a']

    >>> parse_expression("[1 2 3] 4 5 a")
    ['[1 2 3]', '4', '5', 'a']
    >>> parse_expression("{0}")
    ['{0}']
    >>> parse_expression("-1 k ^ 2 k * 1 + / p + $p set  # calculate p")
    ['-1', 'k', '^', '2', 'k', '*', '1', '+', '/', 'p', '+', '$p', 'set']
    >>> parse_expression("{x}{x x +}lambda")
    ['{x}', '{x x +}', 'lambda']
    >>> parse_expression("3{x}{x x +}lambda")
    ['3', '{x}', '{x x +}', 'lambda']
    """
    ignore_tokens = ['"""', "'''"]
    lexed_expression: list = lex_string(expression)
    tokens = []

    for token in lexed_expression:
        if token in ignore_tokens:
            continue
        elif token.startswith("#"):
            return tokens
        elif is_array(token):
            tokens.append(token)
        elif is_tuple(token):
            tokens.append(token)
        elif is_string(token):
            tokens.append(token)
        else:
            tokens.append(token)
    return tokens


if __name__ == "__main__":
    import doctest

    doctest.testmod()
