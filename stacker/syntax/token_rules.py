"""Shared token-shape predicates — the single source of truth.

"What is a string token" and "how are its delimiters stripped" used to be
re-implemented inline at six call sites across the lexer, parser, and the
evaluation-loop classifier; that divergence caused real bugs. Every call
site must go through this module instead of re-implementing the checks.

Both single-character quote pairs (``'...'`` / ``"..."``) and
triple-quoted tokens (``\"\"\"...\"\"\"`` / ``'''...'''``, one token with
delimiters preserved, since 1.11.0) are recognized.

Note:
    These helpers duck-type ``startswith``/``endswith`` instead of
    isinstance-checking, so any str-like token object works. Do not add an
    ``isinstance(token, str)`` guard here; callers that need one (e.g.
    ``parser.is_string``) apply it themselves. A ``String`` object (a
    literal whose delimiters are already stripped) is recognized by type in
    the classifier before these predicates are consulted.

    The call sites previously inlined these checks as a hot-path
    optimization; benchmarks confirmed the function-call cost is
    negligible now that classification is cached per block (TokenList).

    The list / block / symbol / name predicates further down were moved here
    from ``parser.py`` and ``engine/core.py`` (1.16.0) so that the main
    lexer, the array lexer and the classifier agree on what a list, a block,
    a ``:name`` and a bare name are.
"""

from __future__ import annotations

import ast
from functools import lru_cache

from stacker.error import StackerSyntaxError


def is_string_token(token) -> bool:
    """Return True if the token is a quote-delimited string literal.

    Args:
        token: Token value; anything exposing ``startswith``/``endswith``.

    Returns:
        True if the token starts and ends with the same quote character.
    """
    return (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    )


#: Length of a triple-quote delimiter (``\"\"\"`` or ``'''``).
TRIPLE_QUOTE_LEN = 3

#: Minimum length of a complete triple-quoted token (two delimiters).
_MIN_TRIPLE_TOKEN_LEN = 2 * TRIPLE_QUOTE_LEN


def strip_string_delimiters(token) -> str:
    """Return the string content with its quote delimiters removed.

    Handles both single-character quote pairs (``'...'`` / ``"..."``)
    and triple-quoted tokens (``\"\"\"...\"\"\"`` / ``'''...'''``, which
    the lexer emits as one token, delimiters included). Must only be
    called on tokens for which :func:`is_string_token` is True.

    Args:
        token: A quote-delimited string token.

    Returns:
        The token content between the delimiters.
    """
    if len(token) >= _MIN_TRIPLE_TOKEN_LEN and (
        (token.startswith('"""') and token.endswith('"""'))
        or (token.startswith("'''") and token.endswith("'''"))
    ):
        return token[TRIPLE_QUOTE_LEN:-TRIPLE_QUOTE_LEN]
    return token[1:-1]


#: Escapes a string literal reads, and what each stands for.
SIMPLE_ESCAPES: dict[str, str] = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

#: Digits each code-point escape takes: ``\xNN`` and ``\uNNNN``.
CODE_POINT_ESCAPE_DIGITS: dict[str, int] = {"x": 2, "u": 4}

#: Code points that are not characters (UTF-16 surrogates); an escape must not make one.
_SURROGATE_RANGE = range(0xD800, 0xE000)

#: How a character is shown inside quotes, when it is not shown as itself.
_DISPLAY_ESCAPES: dict[str, str] = {
    "\\": "\\\\",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
    "\0": "\\0",
}

#: Characters that show as nothing and so pass for a missing character: the byte
#: order mark, the zero-width space and word joiner, and the bidirectional
#: controls. (A joiner that shapes text, such as the one inside a family emoji,
#: and the soft hyphen are left as they are.)
INVISIBLE_CHARACTERS = frozenset("\ufeff\u200b\u2060\u180e\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")

#: Code points below this are control characters, shown as ``\xNN`` unless named above.
_CONTROL_LIMIT = 0x20
_DELETE = 0x7F


def decode_string_token(token: str) -> str:
    """Return the text a string token stands for: delimiters removed, escapes read.

    The escapes are ``\\n`` ``\\t`` ``\\r`` ``\\0`` ``\\\\`` ``\\"`` ``\\'``
    ``\\xNN`` and ``\\uNNNN``; a triple-quoted token reads them too. Any other
    escape is an error, never left in the text, so a mistyped escape is
    found where it is written.

    Args:
        token: A quote-delimited string token (``is_string_token`` is True).

    Returns:
        The decoded text.

    Raises:
        StackerSyntaxError: An escape that is not one of the above, a
            code-point escape short of digits, a code point that is not a
            character, or a lone backslash at the end.
    """
    content = strip_string_delimiters(token)
    if "\\" not in content:
        return content
    out: list[str] = []
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        if i + 1 >= n:
            raise StackerSyntaxError("a string cannot end with a lone backslash; write `\\\\` for a backslash")
        key = content[i + 1]
        if key in SIMPLE_ESCAPES:
            out.append(SIMPLE_ESCAPES[key])
            i += 2
            continue
        digits = CODE_POINT_ESCAPE_DIGITS.get(key)
        if digits is None:
            raise StackerSyntaxError(f"unknown escape `\\{key}` in a string; write `\\\\` for a backslash")
        hex_text = content[i + 2 : i + 2 + digits]
        if len(hex_text) < digits or not all(c in "0123456789abcdefABCDEF" for c in hex_text):
            raise StackerSyntaxError(f"`\\{key}` in a string takes {digits} hex digits, got `\\{key}{hex_text}`")
        code = int(hex_text, 16)
        if code in _SURROGATE_RANGE:
            raise StackerSyntaxError(f"`\\{key}{hex_text}` is not a character")
        out.append(chr(code))
        i += 2 + digits
    return "".join(out)


def escape_for_display(text: str, quote: str | None = None) -> str:
    """Return ``text`` as it is shown inside quotes: control characters and backslashes escaped.

    The inverse of ``decode_string_token`` for what cannot be shown as
    itself: ``\\`` and the named control characters come out as their
    escapes, other control characters as ``\\xNN``. With ``quote``, that
    quote character is escaped too, so the result reads back as the same
    text when wrapped in it.

    Args:
        text: The text of a string value.
        quote: The quote the text will be wrapped in, or None to leave quotes alone.

    Returns:
        The text with escapes written out.
    """
    out: list[str] = []
    for ch in text:
        if ch in _DISPLAY_ESCAPES:
            out.append(_DISPLAY_ESCAPES[ch])
        elif ch == quote:
            out.append("\\" + ch)
        elif ord(ch) < _CONTROL_LIMIT or ord(ch) == _DELETE:
            out.append(f"\\x{ord(ch):02x}")
        elif ch in INVISIBLE_CHARACTERS:
            out.append(f"\\u{ord(ch):04x}")  # a character that shows as nothing (a byte order mark, a zero-width space)
        else:
            out.append(ch)
    return "".join(out)


#: First characters a Python literal can start with. A token starting with
#: any other character is a name, without consulting ``ast.literal_eval``
#: (keeps the classifier cheap).
LITERAL_START = frozenset("0123456789+-.([{'\"NTFbBrRuUfFs")

#: Word literals: these tokens are values, never names. ``true`` / ``false``
#: / ``null`` are the Stacker spellings, the Python spellings work too.
KEYWORD_LITERALS: dict[str, object] = {
    "true": True,
    "false": False,
    "null": None,
    "True": True,
    "False": False,
    "None": None,
}

#: Signed spellings of the two special floats; `inf` and `nan` themselves are constants (variables)
SIGNED_SPECIAL_FLOATS: dict[str, float] = {
    "-inf": float("-inf"),
    "+inf": float("inf"),
    "-nan": float("nan"),
    "+nan": float("nan"),
}


def is_list(expression: object) -> bool:
    """Return True if ``expression`` is a list-literal token (``[...]``).

    Args:
        expression: Token value.

    Returns:
        True for a ``str`` that starts with ``[`` and ends with ``]``.
    """
    if not isinstance(expression, str):
        return False
    return expression.startswith("[") and expression.endswith("]")


def count_outside_strings(text: str, char: str) -> int:
    """Counts ``char`` in ``text``, skipping the inside of string literals (escapes and triple quotes included).

    Args:
        text: A token's text.
        char: The character to count.

    Returns:
        How many times ``char`` appears outside quotes.
    """
    if '"' not in text and "'" not in text:
        return text.count(char)  # no string literal to skip: the host's count is far faster
    count = 0
    i = 0
    n = len(text)
    quote: str | None = None
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if text.startswith(quote, i):
                i += len(quote)
                quote = None
                continue
            i += 1
            continue
        if ch in ("'", '"'):
            triple = ch * 3
            quote = triple if text.startswith(triple, i) else ch
            i += len(quote)
            continue
        if ch == char:
            count += 1
        i += 1
    return count


def is_code_block(expression: object) -> bool:
    """Return True if ``expression`` is a code-block token (``{...}`` or ``(...)``).

    Both delimiters are equivalent and create a substack. Only the outer
    delimiters and the brace balance are checked; a bracket inside a
    string literal does not count.

    Args:
        expression: Token value.

    Returns:
        True for a balanced, non-empty ``{...}`` or ``(...)`` token.

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
    if len(expression) < 2:
        return False
    first_char = expression[0]
    last_char = expression[-1]
    # A bracket inside a string literal is text, not structure
    if first_char == "{" and last_char == "}":
        return count_outside_strings(expression, "{") == count_outside_strings(expression, "}")
    elif first_char == "(" and last_char == ")":
        return count_outside_strings(expression, "(") == count_outside_strings(expression, ")")
    return False


#: The character that marks a symbol: ``:name`` is the name itself, as a value.
SYMBOL_PREFIX = ":"

#: The symbol prefix of versions before 1.16.0. A token starting with it is a
#: syntax error that points at the new spelling, so old code fails loudly
#: instead of binding a name that happens to start with ``$``.
OLD_SYMBOL_PREFIX = "$"

#: Characters a name cannot hold: the symbol prefixes, and the characters
#: the lexer splits a token on (or that start a string, a block, a list or a
#: comment), so every name can be written back as one ``:name`` token.
NAME_DELIMITERS = frozenset(" \t\n\r:$\"'()[]{}#;")


def is_symbol(expression: object) -> bool:
    """Return True if ``expression`` is a ``:name`` token.

    A symbol token is a raw ``str`` made of one ``:`` followed by a symbol
    name (:func:`is_symbol_name`). So every symbol can be written back as
    ``:name``.

    Args:
        expression: Token value.

    Returns:
        True for ``:x``, ``:+``, ``:x.y``; False for ``:``, ``::x``, ``:1``,
        ``:{x}``, ``:"x"``, ``:[1 2]``, a ``String`` and non-str values.
    """
    if type(expression) is not str or not expression.startswith(SYMBOL_PREFIX):
        return False
    return is_symbol_name(expression[1:])


def is_symbol_name(name: object) -> bool:
    """Return True if ``name`` can be the name of a symbol (written back as ``:name``).

    A bare name (:func:`is_bare_name`), or the name of a literal: ``:null``,
    ``:true`` and ``:false`` are symbols (the value `type` gives for null is
    `:null`), while the bare word is the value.

    Args:
        name: The candidate name.

    Returns:
        True if ``:name`` would be one symbol token.
    """
    return is_bare_name(name) or name in KEYWORD_LITERALS  # `:null` is the name, `null` the value


def not_a_symbol_message(token: str) -> str:
    """The error message for a ``:`` or ``$`` token that is not a symbol.

    For the old ``$`` spelling the message shows the new one when the rest
    of the token is a name (``$x`` -> ``:x``).
    """
    name = token[1:]
    if token.startswith(OLD_SYMBOL_PREFIX):
        if is_symbol_name(name):
            return f"`{token}` is not a symbol: a symbol is written `:{name}` (`$` is no longer used)"
        return f"`{token}` is not a symbol: `$` is no longer used, and `:` must be followed by a name"
    return f"`{token}` is not a symbol: `:` must be followed by a name"


@lru_cache(maxsize=1024)
def cached_literal_eval(token: str) -> object:
    """Evaluate ``token`` as a Python literal, caching the result.

    Args:
        token: Raw source token.

    Returns:
        The literal's value, or ``token`` itself when it is not a literal.
        ``MemoryError`` / ``RecursionError`` from pathological input
        propagate instead of becoming a bogus value.
    """
    if token in KEYWORD_LITERALS:
        return KEYWORD_LITERALS[token]
    if token in SIGNED_SPECIAL_FLOATS:
        return SIGNED_SPECIAL_FLOATS[token]
    try:
        value = ast.literal_eval(token)
    except (ValueError, TypeError, SyntaxError):
        return token
    if isinstance(value, (set, frozenset, tuple, dict, bytes)):
        return token  # a value only the host has (`{1, 2}`): the token is a name, not that value
    return value


def reads_as_name(token: str) -> bool:
    """Return True if a raw token is a name rather than a Python literal.

    A fatal error from a pathological token (``MemoryError`` /
    ``RecursionError``) is swallowed here and the token is treated as a
    name; the error is then raised at the token's execution position, not
    during classification.

    Args:
        token: Raw source token.

    Returns:
        True if the token does not read as a literal.
    """
    if token in KEYWORD_LITERALS:
        return False
    if not token or token[0] not in LITERAL_START:
        return True
    try:
        return isinstance(cached_literal_eval(token), str)
    except (MemoryError, RecursionError):
        return True


def is_bare_name(token: object) -> bool:
    """Return True if ``token`` is a bare name.

    A bare name is a non-empty raw ``str`` that is not a string literal, a
    list literal, a code block or a literal, and holds none of
    :data:`NAME_DELIMITERS` (so it is not a ``:name`` or ``$name`` token
    either).

    Args:
        token: Token value.

    Returns:
        True for a bare name.
    """
    return (
        type(token) is str
        and bool(token)
        and not is_string_token(token)
        and not is_list(token)
        and not is_code_block(token)
        and reads_as_name(token)
        and not any(ch in NAME_DELIMITERS for ch in token)
    )
