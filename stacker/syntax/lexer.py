from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator

from stacker.error import UnterminatedTokenError


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

    elements: list[object]

    def __repr__(self) -> str:
        return f"ListNode({self.elements})"


@dataclass
class TupleNode:
    """DEPRECATED: Tuples removed in v1.9.0.

    This class is kept for backward compatibility but should not be used.
    Parentheses () now create code blocks, not tuples.
    """

    elements: list[object]

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
        (
            TokenType.NUMBER,
            r"[+-]?(0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+)"
            r"|[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[jJ]?",
        ),
        (
            TokenType.STRING,
            # Triple-quoted alternatives must come first so they are not
            # consumed as an empty single-quoted string pair
            r"('''([^'\\]|\\.|'(?!''))*'''"
            r"|\"\"\"([^\"\\]|\\.|\"(?!\"\"))*\"\"\""
            r"|'([^'\\]|\\.)*'"
            r"|\"([^\"\\]|\\.)*\")",
        ),
        (TokenType.IDENTIFIER, r"[A-Za-z_][A-Za-z0-9_\-?!]*"),
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


@dataclass
class TerminalState:
    """Result of scanning input for unterminated constructs.

    Attributes:
        complete: True if no string / array / block / block comment is
            left open at the end of the input.
        open_construct: Kind of the innermost open construct
            ("string", "array", "block", or "block comment"), or None.
        start_line: 1-based line (within the scanned text) where the
            open construct started, or None when complete.
    """

    complete: bool
    open_construct: str | None = None
    start_line: int | None = None


#: Opening bracket -> closing bracket for structure-preserving tokens.
_OPEN_BRACKETS = {"[": "]", "(": ")", "{": "}"}

#: Opening bracket -> construct name reported by TerminalState.
_BRACKET_CONSTRUCTS = {"[": "array", "(": "block", "{": "block"}

#: Triple-quote string delimiters (must be checked before single quotes).
_TRIPLE_DELIMS = ('"""', "'''")


class TerminalScanner:
    """Incremental scan core shared by all lexical judgments.

    Single state machine that understands strings (single and triple
    quoted), line comments (``#`` to end of line), nestable block
    comments (``#| ... |#``), and bracket nesting — so tokenization and
    continuation-input judgment can never diverge.

    The scanner is resumable: ``feed`` consumes only the newly appended
    text and updates the internal state, so accumulating callers (script
    line loop, REPL continuation) stay O(total input) instead of
    re-scanning the whole buffer per line.
    """

    def __init__(self) -> None:
        self.tokens: list[str] = []
        self._current = ""
        self._bracket_stack: list[tuple[str, int]] = []  # (open char, line)
        self._in_string: str | None = None  # "'", '"', "'''", or '"""'
        self._string_start_line: int | None = None
        self._escaped = False
        self._in_line_comment = False
        self._comment_depth = 0
        self._comment_start_line: int | None = None
        self._line = 1
        # Unconsumed tail shorter than a delimiter lookahead (e.g. a
        # chunk ending in '#' or '""') — kept until the next feed
        self._pending = ""

    def feed(self, text: str) -> TerminalState:
        """Consume the next chunk of input and return the new state.

        Chunk-boundary contract: chunks must end at natural source
        boundaries (whole lines), so that a multi-character delimiter
        (``\"\"\"``, ``'''``, ``#|``, ``|#``) is never split across two
        ``feed`` calls in the normal state — delimiters cannot contain
        newlines, so line-based feeding satisfies this automatically.
        Inside an already-open triple-quoted string or block comment, a
        split closing delimiter IS handled (buffered in ``_pending``).

        Args:
            text: Newly appended source text (not the whole buffer).

        Returns:
            The terminal state after consuming the chunk, as if the
            input might still continue (a trailing partial closing
            delimiter is held back rather than misjudged).
        """
        # Normalize str subclasses (e.g. engine String, whose startswith
        # override takes no position argument) to plain str for scanning
        if type(text) is not str:
            text = str(text)
        text = self._pending + text
        self._pending = ""

        i = 0
        n = len(text)
        while i < n:
            # Multi-char closing delimiters ('"""'/''''''/"|#") need
            # lookahead; if the chunk ends mid-delimiter while such a
            # construct is open, hold the tail for the next feed
            # instead of misclassifying it
            if n - i <= 2 and self._hold_tail(text[i:]):
                self._pending = text[i:]
                break
            i = self._step(text, i)

        return self.state()

    def _hold_tail(self, tail: str) -> bool:
        """Return True if the chunk tail may be part of a closing delimiter.

        Only applies inside constructs whose closing delimiter spans
        multiple characters (triple-quoted strings, block comments);
        everywhere else a trailing quote or ``#`` has an immediate,
        unambiguous meaning and must be consumed now.
        """
        if self._in_string is not None and len(self._in_string) == 3:
            return self._in_string.startswith(tail)
        if self._comment_depth > 0:
            return tail in ("#", "|")
        return False

    def _step(self, text: str, i: int) -> int:
        """Consume one lexical element at position i; return the new i."""
        ch = text[i]
        if ch == "\n":
            self._line += 1

        # Line comments run to the end of the physical line
        if self._in_line_comment:
            if ch == "\n":
                self._in_line_comment = False
                # The newline itself separates tokens (handled below)
            else:
                return i + 1

        # Block comments: only nesting markers matter inside
        if self._comment_depth > 0:
            if text.startswith("#|", i):
                self._comment_depth += 1
                return i + 2
            if text.startswith("|#", i):
                self._comment_depth -= 1
                if self._comment_depth == 0:
                    self._comment_start_line = None
                return i + 2
            return i + 1

        # String literals: everything is content until the closing
        # delimiter; backslash escapes the next character
        if self._in_string is not None:
            if self._escaped:
                self._current += ch
                self._escaped = False
                return i + 1
            if ch == "\\":
                self._current += ch
                self._escaped = True
                return i + 1
            if text.startswith(self._in_string, i):
                delim = self._in_string
                self._current += delim
                self._in_string = None
                self._string_start_line = None
                if not self._bracket_stack and self._current:
                    self.tokens.append(self._current)
                    self._current = ""
                return i + len(delim)
            self._current += ch
            return i + 1

        # Comment openers (never inside strings)
        if text.startswith("#|", i):
            if not self._bracket_stack and self._current:
                self.tokens.append(self._current)
                self._current = ""
            self._comment_depth = 1
            self._comment_start_line = self._line
            return i + 2
        if ch == "#":
            if not self._bracket_stack and self._current:
                self.tokens.append(self._current)
                self._current = ""
            self._in_line_comment = True
            return i + 1

        # String openers (triple before single; both glue onto the
        # current token except after a bare integer, matching the
        # historical digit-flush quirk)
        opener = None
        if text.startswith(_TRIPLE_DELIMS[0], i) or text.startswith(
            _TRIPLE_DELIMS[1], i
        ):
            opener = text[i : i + 3]
        elif ch in ("'", '"'):
            opener = ch
        if opener is not None:
            if (
                not self._bracket_stack
                and self._current
                and self._current.strip().isdigit()
            ):
                self.tokens.append(self._current)
                self._current = ""
            self._in_string = opener
            self._string_start_line = self._line
            self._current += opener
            return i + len(opener)

        # Bracket handling
        if ch in _OPEN_BRACKETS:
            if (
                not self._bracket_stack
                and self._current
                and self._current.strip().isdigit()
            ):
                self.tokens.append(self._current)
                self._current = ""
            self._bracket_stack.append((ch, self._line))
            self._current += ch
            return i + 1
        if self._bracket_stack and ch == _OPEN_BRACKETS[self._bracket_stack[-1][0]]:
            self._bracket_stack.pop()
            self._current += ch
            if not self._bracket_stack:
                self.tokens.append(self._current)
                self._current = ""
            return i + 1
        if self._bracket_stack:
            self._current += ch
            return i + 1

        # Top level: whitespace separates tokens
        if ch.isspace():
            if self._current:
                self.tokens.append(self._current)
                self._current = ""
            return i + 1

        self._current += ch
        return i + 1

    def state(self) -> TerminalState:
        """Return the terminal state of the input consumed so far."""
        if self._in_string is not None:
            return TerminalState(False, "string", self._string_start_line)
        if self._comment_depth > 0:
            return TerminalState(False, "block comment", self._comment_start_line)
        if self._bracket_stack:
            open_char, start = self._bracket_stack[-1]
            return TerminalState(False, _BRACKET_CONSTRUCTS[open_char], start)
        return TerminalState(True)

    def finalize(self) -> tuple[list[str], TerminalState]:
        """Mark the input as final and return tokens and state.

        A held-back partial delimiter is flushed as ordinary text and
        the trailing token (if any) is emitted.
        """
        if self._pending:
            pending, self._pending = self._pending, ""
            i = 0
            while i < len(pending):
                i = self._step(pending, i)
        state = self.state()
        if state.complete and self._current:
            self.tokens.append(self._current)
            self._current = ""
        return self.tokens, state


def _scan(text: str) -> tuple[list[str], TerminalState]:
    """One-shot scan of a complete text (see TerminalScanner)."""
    scanner = TerminalScanner()
    scanner.feed(text)
    return scanner.finalize()


def analyze_terminals(text: str) -> TerminalState:
    """Report whether the input is complete, without raising.

    Interactive callers (REPL continuation, script line accumulation)
    use this to decide whether to keep reading lines; ``tokenize`` is
    the single place that turns an unterminated final input into an
    ``UnterminatedTokenError``. Accumulating callers should prefer an
    incremental ``TerminalScanner`` to stay O(total input).

    Args:
        text: Source text accumulated so far.

    Returns:
        The terminal state of the scan.
    """
    scanner = TerminalScanner()
    scanner.feed(text)
    _, state = scanner.finalize()
    return state


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
        """Tokenize input preserving nested structures.

        Raises:
            UnterminatedTokenError: If the input ends inside an
                unterminated string, array, block, or block comment.
                Interactive callers should check ``analyze_terminals``
                first and offer continuation input instead.
        """
        tokens, state = _scan(self.text)
        if not state.complete:
            raise UnterminatedTokenError(state.open_construct, state.start_line)
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


def lex_string(s: str) -> list[str]:
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
