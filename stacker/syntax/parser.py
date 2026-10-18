from __future__ import annotations

import ast
from functools import lru_cache

# Import lexer components from the separate lexer module
from stacker.syntax.lexer import (
    Identifier,
    ListNode,
    TokenType,
    TupleNode,
    UnifiedLexer,
)
from stacker.error import StackerSyntaxError, word_in_list_literal_message
from stacker.syntax.token_rules import (  # noqa: F401 -- is_code_block / is_list / is_symbol are re-exported
    is_code_block,
    is_list,
    is_string_token,
    is_symbol,
    not_a_symbol_message,
)

__transpose_symbol__ = "^T"


class Parser:
    """DEPRECATED: This parser includes tuple support which was removed in v1.9.0.

    Unified parser that handles both simple and complex parsing.
    Note: LPAREN now creates code blocks, not tuples.
    """

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

    def parse(self) -> ListNode | TupleNode:
        """Parse input into appropriate node structure"""
        if self.current_token is None:
            return ListNode([])
        return self.parse_structure()

    def parse_structure(self) -> ListNode | TupleNode:
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

    def _parse_element(self) -> object:
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
        elif token.type == TokenType.SYMBOL:
            if not is_symbol(token.value):
                raise StackerSyntaxError(not_a_symbol_message(token.value))
            return Identifier(token.value)  # formatted as ':name', a symbol element
        elif token.type == TokenType.SEMICOLON:
            return ";"
        elif token.type == TokenType.COMMA:
            raise StackerSyntaxError(
                "Commas are not used in Stacker lists; "
                "separate elements with spaces: [1 2 3]"
            )
        elif token.type in (TokenType.OPERATOR, TokenType.OTHER):
            # A symbolic word (`+`, `^`, `==`): the lexer hands it over one
            # character at a time, so the characters that follow are joined
            word = token.value
            while self.current_token is not None and self.current_token.type in (TokenType.OPERATOR, TokenType.OTHER):
                word += self.current_token.value
                self.next_token()
            raise StackerSyntaxError(word_in_list_literal_message(word))
        else:
            raise StackerSyntaxError(f"Unexpected token `{token.value}`")

    def _split_by_semicolon(
        self, elements: list[object], node_class: type[ListNode | TupleNode]
    ) -> list[object]:
        """Splits ``elements`` at each `;` into rows, every row a node of its own: `[a; b]` is `[[a] [b]]`."""
        result = []
        current = []

        for item in elements:
            if item == ";":
                if current:
                    result.append(node_class(current))
                    current = []
            else:
                current.append(item)

        if current:
            result.append(node_class(current))

        return result


class Formatter:
    """Formats parsed structures back into string representation"""

    @staticmethod
    def format_structure(
        obj: ListNode | TupleNode | int | float | complex | str | Identifier | dict[str, object],
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
    # The nesting is kept as written: `[[1 2]]` is a list holding one list
    return Formatter.format_structure(parser.parse())


@lru_cache(maxsize=512)
def _parse_expression_cached(expression: str) -> tuple[str, ...]:
    """Cached version of parse_expression that returns a tuple.

    Comment handling (``#`` line comments, ``#| |#`` block comments) and
    triple-quote strings are fully handled by the lexer scan core, so no
    token-level filtering is needed here.
    """
    return tuple(UnifiedLexer(expression).tokenize())


def parse_expression(expression: str) -> list[str]:
    """Parse expression into tokens while preserving structure"""
    # Use cached version and convert back to list
    return list(_parse_expression_cached(expression))


def evaluate_token_or_return_str(token: str) -> object:
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
    """DEPRECATED: Tuples removed in v1.9.0. Use is_code_block() instead.

    This function now checks for parenthesized code blocks, not tuples.
    """
    return starts_with_char(expression, "(")


def is_brace(expression: str) -> bool:
    return starts_with_char(expression, "{")


def is_array_balanced(expression: str) -> bool:
    return is_balanced(expression, "[", "]")


def is_tuple_balanced(expression: str) -> bool:
    """DEPRECATED: Tuples removed in v1.9.0. Use is_brace_balanced() instead.

    This function checks if parentheses are balanced (for code blocks).
    """
    return is_balanced(expression, "(", ")")


def is_brace_balanced(expression: str) -> bool:
    """Check if both {} and () code block delimiters are balanced."""
    return is_balanced(expression, "{", "}") and is_balanced(expression, "(", ")")


def is_single_array(expression: str) -> bool:
    return is_single(expression, "[", "]")


def is_single_tuple(expression: str) -> bool:
    """DEPRECATED: Tuples removed in v1.9.0.

    This function checks for single-level parenthesized code blocks.
    """
    return is_single(expression, "(", ")")


def is_single_brace(expression: str) -> bool:
    return is_single(expression, "{", "}")


def is_block(expression: str) -> bool:
    """Check if expression is a code block with {} delimiters.

    Note: For checking both {} and () code blocks, use is_code_block() instead.
    This function is kept for backward compatibility.
    """
    if not isinstance(expression, str):
        return False
    return expression.count("{") == expression.count("}") > 0


def is_string(expression: str) -> bool:
    if not isinstance(expression, str):
        return False
    return is_string_token(expression)


def is_label_symbol(expression: str) -> bool:
    return expression.endswith(":") and not expression.startswith(":")


def is_transpose_command(expression: str) -> bool:
    return expression == __transpose_symbol__


def is_contains_transpose_command(expression: str) -> bool:
    return (
        len(expression) > len(__transpose_symbol__)
        and expression[-len(__transpose_symbol__) :] == __transpose_symbol__
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
