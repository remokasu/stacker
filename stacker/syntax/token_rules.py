"""Shared string-token predicates — the single source of truth.

"What is a string token" and "how are its delimiters stripped" used to be
re-implemented inline at six call sites across the lexer, parser, and the
evaluation-loop classifier; that divergence caused real bugs. Every call
site must go through this module instead of re-implementing the checks.

Both single-character quote pairs (``'...'`` / ``"..."``) and
triple-quoted tokens (``\"\"\"...\"\"\"`` / ``'''...'''``, one token with
delimiters preserved, since 1.11.0) are recognized.

Note:
    These helpers intentionally duck-type ``startswith``/``endswith``
    instead of isinstance-checking, so that ``String`` subclass overrides
    behave exactly as they do in the evaluation loop (pinned by
    ``test_semantics_freeze.py::TestStringTokenQuirks``). Do not add an
    ``isinstance(token, str)`` guard here; callers that need one (e.g.
    ``parser.is_string``) apply it themselves.

    The call sites previously inlined these checks as a hot-path
    optimization; benchmarks confirmed the function-call cost is
    negligible now that classification is cached per block (TokenList).
"""


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
