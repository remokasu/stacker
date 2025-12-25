from __future__ import annotations

from typing import TYPE_CHECKING, Any
from stacker.reserved import __BREAK__

if TYPE_CHECKING:
    from stacker.stacker import Stacker


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
    for i in range(start_value, end_value + 1):
        # Create a child scope for the loop variable to avoid modifying parent scope
        # We need to temporarily set the parent's variables to use the child scope
        original_parent_vars = parent.variables
        parent.variables = parent.variables.create_child_scope()
        parent.variables[symbol] = i
        parent.evaluate(block.tokens, stack=parent.stack)
        parent.variables = original_parent_vars
        if len(parent.stack) > 0 and parent.stack[-1] == __BREAK__:
            parent.stack.pop()
            break


def _dolist(
    symbol: str,
    lst: list,
    block: Stacker,
    parent: Stacker,
):
    for i in lst:
        # Create a child scope for the loop variable to avoid modifying parent scope
        # We need to temporarily set the parent's variables to use the child scope
        original_parent_vars = parent.variables
        parent.variables = parent.variables.create_child_scope()
        parent.variables[symbol] = i
        parent.evaluate(block.tokens, stack=parent.stack)
        parent.variables = original_parent_vars
        if len(parent.stack) > 0 and parent.stack[-1] == __BREAK__:
            parent.stack.pop()
            break


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
