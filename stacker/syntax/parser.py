from __future__ import annotations

import ast
import re
from typing import List, Union, Iterator, Any
import warnings
from dataclasses import dataclass
from enum import Enum, auto

__transpose_symbol__ = "^T"


class TokenType(Enum):
    BRACED_CONTENT = auto()
    COMPLEX_NUMBER = auto()
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LPAREN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    OPERATOR = auto()
    SPACE = auto()
    COMMA = auto()
    OTHER = auto()


@dataclass
class Token:
    """Represents a single token."""

    type: TokenType
    value: str

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value})"


@dataclass
class Identifier:
    """Represents an identifier."""

    name: str

    def __repr__(self) -> str:
        return f"Identifier({self.name})"


@dataclass
class ListNode:
    """Represents a list node."""

    elements: List[Any]

    def __repr__(self) -> str:
        return f"ListNode({self.elements})"


@dataclass
class TupleNode:
    """Represents a tuple node."""

    elements: List[Any]

    def __repr__(self) -> str:
        return f"TupleNode({self.elements})"


class TokenPattern:
    """Token patterns for lexical analysis"""

    PATTERNS = [
        (TokenType.BRACED_CONTENT, r"\{[^}]*\}"),
        (
            TokenType.COMPLEX_NUMBER,
            r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[+-](\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[jJ]",
        ),
        (TokenType.NUMBER, r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[jJ]?"),
        (TokenType.STRING, r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")"),
        (TokenType.IDENTIFIER, r"[A-Za-z_][A-Za-z0-9_]*"),
        (TokenType.LBRACKET, r"\["),
        (TokenType.RBRACKET, r"\]"),
        (TokenType.LPAREN, r"\("),
        (TokenType.RPAREN, r"\)"),
        (TokenType.SEMICOLON, r";"),
        (TokenType.OPERATOR, r"[+\-]"),
        (TokenType.SPACE, r"\s+"),
        (TokenType.COMMA, r","),
        (TokenType.OTHER, r"."),
    ]


class UnifiedLexer:
    """Unified lexical analyzer that handles both simple and complex tokenization"""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.delimiter_mapping = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}
        self._setup_regex()

    def _setup_regex(self) -> None:
        """Setup regex patterns for tokenization"""
        self.tok_regex = "|".join(
            f"(?P<{pattern[0].name}>{pattern[1]})" for pattern in TokenPattern.PATTERNS
        )
        self.token_re = re.compile(self.tok_regex)

    def tokenize(self) -> list[str]:
        """Tokenize input preserving nested structures"""
        tokens = []
        current_token = ""
        bracket_stack = []

        for char in self.text:
            if char in self.delimiter_mapping:
                if current_token and current_token.strip().isdigit():
                    tokens.append(current_token)
                    current_token = ""

                if bracket_stack and self.delimiter_mapping[bracket_stack[-1]] == char:
                    current_token += char
                    bracket_stack.pop()
                    if not bracket_stack:
                        tokens.append(current_token)
                        current_token = ""
                else:
                    bracket_stack.append(char)
                    current_token += char
            elif bracket_stack:
                current_token += char
                if char == self.delimiter_mapping[bracket_stack[-1]]:
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

        if current_token:
            tokens.append(current_token)

        return tokens

    def get_tokens(self) -> Iterator[Token]:
        """Get tokens with type information"""
        pos = 0
        while pos < len(self.text):
            match = self.token_re.match(self.text, pos)
            if match is None:
                break

            kind = TokenType[match.lastgroup]  # type: ignore
            value = match.group()
            if kind != TokenType.SPACE:
                yield Token(kind, value)

            pos = match.end()

        if pos != len(self.text):
            raise SyntaxError(
                f"Unexpected character {self.text[pos]!r} at position {pos}"
            )


class Parser:
    """Unified parser that handles both simple and complex parsing"""

    def __init__(self, text: str) -> None:
        self.lexer = UnifiedLexer(text)
        self.tokens = iter(self.lexer.get_tokens())
        self.current_token = None
        self.next_token()

    def next_token(self) -> None:
        """Get the next token"""
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            self.current_token = None

    def parse(self) -> Union[ListNode, TupleNode]:
        """Parse input into appropriate node structure"""
        if self.current_token is None:
            return ListNode([])
        return self.parse_structure()

    def parse_structure(self) -> Union[ListNode, TupleNode]:
        """Parse a list or tuple structure"""
        elements = []

        if self.current_token.type == TokenType.LBRACKET:
            closing_type = TokenType.RBRACKET
            node_class = ListNode
        elif self.current_token.type == TokenType.LPAREN:
            closing_type = TokenType.RPAREN
            node_class = TupleNode
        else:
            raise SyntaxError(
                f"Expected LBRACKET or LPAREN, got {self.current_token.type}"
            )

        self.next_token()  # consume opening bracket/paren

        while self.current_token and self.current_token.type != closing_type:
            elements.append(self._parse_element())

        if self.current_token is None:
            raise SyntaxError(f"Expected {closing_type}, got EOF")

        self.next_token()  # consume closing bracket/paren

        if ";" in elements:
            return node_class(self._split_by_semicolon(elements, node_class))
        return node_class(elements)

    def _parse_element(self) -> Any:
        """Parse a single element within a structure"""
        if self.current_token is None:
            raise SyntaxError("Unexpected EOF while parsing element")

        if self.current_token.type in (TokenType.LBRACKET, TokenType.LPAREN):
            return self.parse_structure()

        token = self.current_token
        self.next_token()

        if token.type == TokenType.BRACED_CONTENT:
            return {"braced_content": token.value}
        elif token.type == TokenType.COMPLEX_NUMBER:
            return ast.literal_eval(token.value)
        elif token.type == TokenType.NUMBER:
            return ast.literal_eval(token.value)
        elif token.type == TokenType.STRING:
            return ast.literal_eval(token.value)
        elif token.type == TokenType.IDENTIFIER:
            return Identifier(token.value)
        elif token.type == TokenType.SEMICOLON:
            return ";"
        else:
            raise SyntaxError(f"Unexpected token {token}")

    def _split_by_semicolon(
        self, elements: List[Any], node_class: type[Union[ListNode, TupleNode]]
    ) -> List[Any]:
        """Split elements by semicolon into subnodes"""
        result = []
        current = []

        for item in elements:
            if item == ";":
                if current:
                    result.append(self._wrap_node(current, node_class))
                    current = []
            else:
                current.append(item)

        if current:
            result.append(self._wrap_node(current, node_class))

        return result

    def _wrap_node(
        self, elements: List[Any], node_class: type[Union[ListNode, TupleNode]]
    ) -> Any:
        """Wrap elements into appropriate node type"""
        if len(elements) == 1 and isinstance(elements[0], (ListNode, TupleNode)):
            return elements[0]
        return node_class(elements)


class Formatter:
    """Formats parsed structures back into string representation"""

    @staticmethod
    def format_structure(
        obj: Union[ListNode, TupleNode, int, float, complex, str, Identifier, dict],
    ) -> str:
        """Format any parsed structure back to string"""
        if isinstance(obj, ListNode):
            return f"[{','.join(Formatter.format_structure(item) for item in obj.elements)}]"
        elif isinstance(obj, TupleNode):
            return f"({','.join(Formatter.format_structure(item) for item in obj.elements)})"
        elif isinstance(obj, dict) and "braced_content" in obj:
            return f'"{obj["braced_content"].strip()}"'
        elif isinstance(obj, Identifier):
            return f"'{obj.name}'"
        elif isinstance(obj, str):
            return f"'\"{obj}\"'"
        elif isinstance(obj, complex):
            return str(obj)
        return str(obj)


def convert_custom_array_to_proper_list(input_str: str) -> str:
    """Convert custom array notation to proper list notation"""
    parser = Parser(input_str)
    parsed = parser.parse()

    # Flatten singleton structures
    while (
        isinstance(parsed, (ListNode, TupleNode))
        and len(parsed.elements) == 1
        and isinstance(parsed.elements[0], (ListNode, TupleNode))
    ):
        parsed = parsed.elements[0]

    return Formatter.format_structure(parsed)


def parse_expression(expression: str) -> list[str]:
    """Parse expression into tokens while preserving structure"""
    ignore_tokens = ['"""', "'''"]
    lexer = UnifiedLexer(expression)
    tokens = []

    for token in lexer.tokenize():
        if token in ignore_tokens:
            continue
        elif token.startswith("#"):
            return tokens
        elif any(token.startswith(c) for c in "[({'\""):
            tokens.append(token)
        else:
            tokens.append(token)
    return tokens


def evaluate_token_or_return_str(token: str) -> Any:
    if is_block(token):
        return token
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
    if expression.startswith("'") and expression.endswith("'"):
        return expression[1:-1]
    if expression.startswith('"') and expression.endswith('"'):
        return expression[1:-1]
    return expression


def is_balanced(expression: str, open_char: str, close_char: str) -> bool:
    return expression.count(open_char) == expression.count(close_char)


def is_single(expression: str, open_char: str, close_char: str) -> bool:
    return (
        is_balanced(expression, open_char, close_char)
        and expression.count(open_char) == 1
        and expression.count(close_char) == 1
    )


def is_array(expression: str) -> bool:
    return starts_with_char(expression, "[")


def is_tuple(expression: str) -> bool:
    return starts_with_char(expression, "(")


def is_brace(expression: str) -> bool:
    return starts_with_char(expression, "{")


def is_array_balanced(expression: str) -> bool:
    return is_balanced(expression, "[", "]")


def is_tuple_balanced(expression: str) -> bool:
    return is_balanced(expression, "(", ")")


def is_brace_balanced(expression: str) -> bool:
    return is_balanced(expression, "{", "}")


def is_single_array(expression: str) -> bool:
    return is_single(expression, "[", "]")


def is_single_tuple(expression: str) -> bool:
    return is_single(expression, "(", ")")


def is_single_brace(expression: str) -> bool:
    return is_single(expression, "{", "}")


def is_block(expression: str) -> bool:
    if not isinstance(expression, str):
        return False
    return expression.count("{") == expression.count("}") > 0


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
    return (
        len(expression) > len(__transpose_symbol__)
        and expression[-len(__transpose_symbol__) :] == __transpose_symbol__
    )


def lex_string(s: str) -> list:
    warnings.warn(
        "lex_string() is deprecated. Use UnifiedLexer(s).tokenize() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return UnifiedLexer(s).tokenize()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
