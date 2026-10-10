"""Conversions between the token layer and the value layer.

A code block holds *tokens*: a raw ``str`` is a name (or an operator) to
resolve when the block runs, a ``String`` is a string literal, and any other
object is a value. The stack and the variables hold *values*: a name there
is a ``Symbol``, a string is a ``str`` (plain or ``String``).

Every word that moves data across that boundary goes through the two
functions below, so the rule is written once. ``value_to_token`` is used
when a value is spliced into a block (``sub`` / ``subn``, parameter
interpolation, words that return a block). Its inverse ``token_to_value``
is used when a block is read as data (``nth``, ``apply``, ``map`` / ``filter``,
``reduce`` / ``fold``, ``zip`` and the transforms).
"""

from __future__ import annotations

from stacker.engine.data_type import String, Symbol


def value_to_token(value: object) -> object:
    """Return the token that stands for ``value`` inside a code block.

    A ``Symbol`` becomes a bare name token (a plain ``str``), so the name is
    resolved when the block runs. A string, plain or ``String``, becomes a
    string-literal token (a ``String``), so it stays a string. Anything
    else (numbers, lists, blocks, lambdas, ...) is kept as a value token.

    Args:
        value: A value taken from the stack or a variable.

    Returns:
        The token to store in the block.
    """
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, str):
        return value if isinstance(value, String) else String(value)
    return value
