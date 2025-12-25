from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Iterator, List


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
    """DEPRECATED: Tuples removed in v1.9.0.

    This class is kept for backward compatibility but should not be used.
    Parentheses () now create code blocks, not tuples.
    """

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

    # Class-level cache for regex patterns (optimization)
    _cached_token_re = None

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.delimiter_mapping = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}
        self._setup_regex()

    def _setup_regex(self) -> None:
        """Setup regex patterns for tokenization (cached at class level)"""
        if UnifiedLexer._cached_token_re is None:
            tok_regex = "|".join(
                f"(?P<{pattern[0].name}>{pattern[1]})"
                for pattern in TokenPattern.PATTERNS
            )
            UnifiedLexer._cached_token_re = re.compile(tok_regex)
        self.token_re = UnifiedLexer._cached_token_re

    def tokenize(self) -> list[str]:
        """Tokenize input preserving nested structures"""
        tokens = []
        current_token = ""
        bracket_stack = []
        escaped = False  # Track if previous char was backslash

        for char in self.text:
            # Check if we're inside a string literal
            in_string = bracket_stack and bracket_stack[-1] in ['"', "'"]

            # Handle escaped characters in strings
            if in_string and escaped:
                current_token += char
                escaped = False
                continue

            # Check for escape character in strings
            if in_string and char == '\\':
                current_token += char
                escaped = True
                continue

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
                # If we're inside a string, only the matching quote closes it
                # All other characters (including other quotes) are literal
                elif in_string:
                    current_token += char
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


def lex_string(s: str) -> list:
    """
    Deprecated: Use UnifiedLexer(s).tokenize() instead.

    Tokenize a string into a list of tokens.
    """
    warnings.warn(
        "lex_string() is deprecated. Use UnifiedLexer(s).tokenize() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return UnifiedLexer(s).tokenize()
