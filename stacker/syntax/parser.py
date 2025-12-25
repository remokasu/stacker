from __future__ import annotations

import ast
from functools import lru_cache
from typing import Any, List

# Import lexer components from the separate lexer module
from stacker.syntax.lexer import (
    Identifier,
    ListNode,
    Token,
    TokenType,
    TupleNode,
    UnifiedLexer,
    lex_string,
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


@lru_cache(maxsize=512)
def _parse_expression_cached(expression: str) -> tuple[str, ...]:
    """Cached version of parse_expression that returns a tuple."""
    ignore_tokens = ['"""', "'''"]
    lexer = UnifiedLexer(expression)
    tokens = []

    for token in lexer.tokenize():
        if token in ignore_tokens:
            continue
        elif token.startswith("#"):
            return tuple(tokens)
        elif any(token.startswith(c) for c in "[({'\""):
            tokens.append(token)
        else:
            tokens.append(token)
    return tuple(tokens)


def parse_expression(expression: str) -> list[str]:
    """Parse expression into tokens while preserving structure"""
    # Use cached version and convert back to list
    return list(_parse_expression_cached(expression))


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


def is_code_block(expression: str) -> bool:
    """Check if expression is a code block (either {} or ()).

    Code blocks can be delimited by either curly braces {} or parentheses ().
    Both notations are functionally identical and create StackerCore substack objects.

    Args:
        expression: String to check

    Returns:
        True if expression has balanced braces or parentheses (non-empty), False otherwise

    Examples:
        >>> is_code_block("{1 2 +}")
        True
        >>> is_code_block("(1 2 +)")
        True
        >>> is_code_block("[1 2 3]")
        False
    """
    if not isinstance(expression, str):
        return False
    has_braces = expression.count("{") == expression.count("}") > 0
    has_parens = expression.count("(") == expression.count(")") > 0
    return has_braces or has_parens


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
    """Check if expression is a valid symbol (e.g., $name, $my_var).

    Valid symbols:
    - Start with exactly one $
    - Followed by at least one character
    - Do not contain $ elsewhere

    Examples:
        $name -> True
        $x -> True
        $ -> False (no name after $)
        $$x -> False (multiple $ at start)
        $name$ -> False ($ at end)
    """
    if not isinstance(expression, str):
        return False
    if len(expression) < 2:  # At least "$x"
        return False
    if not expression.startswith("$"):
        return False
    if "$" in expression[1:]:  # No $ after the first character
        return False
    return True


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
