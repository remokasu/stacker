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
    the classifier before these predicates are consulted, so its overridden
    ``startswith`` seeing no quotes no longer matters.

    The call sites previously inlined these checks as a hot-path
    optimization; benchmarks confirmed the function-call cost is
    negligible now that classification is cached per block (TokenList).

    The list / block / symbol / name predicates further down were moved here
    from ``parser.py`` and ``engine/core.py`` (1.16.0) so that the main
    lexer, the array lexer and the classifier agree on what a list, a block,
    a ``$name`` and a bare name are.
"""

from __future__ import annotations

import ast
from functools import lru_cache


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


#: First characters a Python literal can start with. A token starting with
#: any other character is a name, without consulting ``ast.literal_eval``
#: (keeps the classifier cheap).
LITERAL_START = frozenset("0123456789+-.([{'\"NTFbBrRuUfFs")


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


def is_code_block(expression: object) -> bool:
    """Return True if ``expression`` is a code-block token (``{...}`` or ``(...)``).

    Both delimiters are equivalent and create a substack. Only the outer
    delimiters and the brace balance are checked.

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
    if first_char == "{" and last_char == "}":
        return expression.count("{") == expression.count("}")
    elif first_char == "(" and last_char == ")":
        return expression.count("(") == expression.count(")")
    return False


def is_symbol(expression: object) -> bool:
    """Return True if ``expression`` is a ``$name`` token.

    A symbol token starts with exactly one ``$`` followed by at least one
    character and contains no other ``$``.

    Args:
        expression: Token value.

    Returns:
        True for ``$name``; False for ``$``, ``$$x``, ``$name$`` and non-str
        values.
    """
    if not isinstance(expression, str):
        return False
    if len(expression) < 2:
        return False
    if not expression.startswith("$"):
        return False
    return "$" not in expression[1:]


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
    try:
        return ast.literal_eval(token)
    except (ValueError, TypeError, SyntaxError):
        return token


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
    if not token or token[0] not in LITERAL_START:
        return True
    try:
        return isinstance(cached_literal_eval(token), str)
    except (MemoryError, RecursionError):
        return True


def is_bare_name(token: object) -> bool:
    """Return True if ``token`` is a bare name.

    A bare name is a raw ``str`` that is not a string literal, a list
    literal, a code block or a Python literal.

    Args:
        token: Token value.

    Returns:
        True for a bare name.
    """
    return (
        type(token) is str
        and not is_string_token(token)
        and not is_list(token)
        and not is_code_block(token)
        and reads_as_name(token)
    )
