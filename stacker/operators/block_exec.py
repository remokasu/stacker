"""Shared helpers for words that run a code block on the caller's stack."""

from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.error import NoValueProducedError

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


def resolve_condition(
    condition: object, parent: Stacker, stack: stack_data[object], word: str
) -> object:
    """Evaluate a condition block on ``stack``; any other value is the condition itself.

    The block is a function from the stack to the stack: it runs on the
    caller's stack, may consume what is below it, and whatever is on top
    afterwards is the condition (an empty block leaves the top as it was).
    A symbol or a string is never looked up as a variable here: a symbol is
    truthy, a string is truthy when non-empty. Write the bare name to test a
    variable's value.

    Args:
        condition: The value or block written at the condition's position.
        parent: Interpreter the block runs in.
        stack: The caller's stack.
        word: The word reading the condition (for the error message).

    Raises:
        NoValueProducedError: The block ran and the stack is empty, so there
            is nothing to read as the condition.
    """
    if isinstance(condition, type(parent)):
        parent.evaluate(condition.tokens, stack=stack)
        if not stack:
            raise NoValueProducedError(
                word, f"The condition block of `{word}` left nothing on the stack to test."
            )
        return stack.pop()
    return condition
