"""Shared helper for words that run a code block on the caller's stack."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


def run_block(block: object, parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates ``block`` on ``stack``; a non-block value is pushed as-is.

    Args:
        block: Code block to evaluate, or any other value to push.
        parent: Interpreter doing the evaluation.
        stack: Evaluation stack the calling word was invoked on.
    """
    if isinstance(block, type(parent)):
        parent.evaluate(block.tokens, stack=stack)
    else:
        stack.append(block)
