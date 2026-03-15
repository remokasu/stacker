from __future__ import annotations

from typing import TYPE_CHECKING, Any
from stacker.reserved import __BREAK__

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def _update_nested_variables(tokens, new_variables):
    """Recursively update variable references in nested StackerCore instances."""
    from stacker.engine.core import StackerCore
    for token in tokens:
        if isinstance(token, StackerCore):
            token.variables = new_variables
            # Recursively update nested code blocks
            _update_nested_variables(token.tokens, new_variables)


def _times(
    n_times: int,
    block: Stacker | Any,
    parent: Stacker,
):
    """Executes a block of code a specified number of times."""
    i_count = 0
    parent.stack.append(i_count)
    while parent.stack[-1] < n_times:
        parent.stack.pop()
        if isinstance(block, type(parent)):
            parent.evaluate(block.tokens, stack=parent.stack)
        else:
            parent.stack.append(block)
        i_count = i_count + 1
        parent.stack.append(i_count)
    parent.stack.pop()


def _do(
    start_value: int,
    end_value: int,
    symbol: str,
    block: Stacker,
    parent: Stacker,
):
    # Create child scope once for all iterations (optimization)
    original_parent_vars = parent.variables
    child_scope = parent.variables.create_child_scope()

    # Update nested StackerCore instances to use the child scope
    _update_nested_variables(block.tokens, child_scope)

    for i in range(start_value, end_value + 1):
        # Update loop variable
        child_scope[symbol] = i
        parent.variables = child_scope
        # Use parent.evaluate to ensure proper context
        parent.evaluate(block.tokens, stack=parent.stack)
        if len(parent.stack) > 0 and parent.stack[-1] == __BREAK__:
            parent.stack.pop()
            break

    parent.variables = original_parent_vars


def _dolist(
    symbol: str,
    lst: list,
    block: Stacker,
    parent: Stacker,
):
    # Create child scope once for all iterations (optimization)
    original_parent_vars = parent.variables
    child_scope = parent.variables.create_child_scope()

    # Update nested StackerCore instances to use the child scope
    # This is necessary because block.tokens may contain nested code blocks
    _update_nested_variables(block.tokens, child_scope)

    for i in lst:
        # Update loop variable
        child_scope[symbol] = i
        parent.variables = child_scope
        # Use parent.evaluate to ensure proper context
        parent.evaluate(block.tokens, stack=parent.stack)
        if len(parent.stack) > 0 and parent.stack[-1] == __BREAK__:
            parent.stack.pop()
            break

    parent.variables = original_parent_vars


loop_operators = {
    "times": {
        "func": (lambda n_times, block, parent: _times(n_times, block, parent)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code a specified number of times.",
    },
    "do": {
        "func": (
            lambda start_value, end_value, symbol, block, parent: _do(
                start_value, end_value, symbol, block, parent
            )
        ),
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Executes a block of code a specified number of times.",
    },
    "dolist": {
        "func": (
            lambda symbol, lst, block, parent: _dolist(symbol, lst, block, parent)
        ),
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Executes a block of code a specified number of times.",
    },
}
