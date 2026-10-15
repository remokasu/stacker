from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.error import BreakException, StackerSyntaxError
from stacker.operators.block_exec import run_block

if TYPE_CHECKING:
    from stacker.engine.scope import ScopedVariables
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


def _update_nested_variables(tokens: list[object], new_variables: ScopedVariables) -> None:
    """Recursively update variable references in nested StackerCore instances."""
    from stacker.engine.core import StackerCore

    for token in tokens:
        if isinstance(token, StackerCore):
            token.variables = new_variables
            # Recursively update nested code blocks
            _update_nested_variables(token.tokens, new_variables)


def _loop(body: object, parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates ``body`` on ``stack`` forever until ``break`` is raised.

    This is the single looping primitive every other loop can be built on.
    Each iteration runs in the caller's scope; no Python recursion
    accumulates across iterations, so the recursion guard is unaffected.

    Args:
        body: Code block to repeat.
        parent: Interpreter evaluating the loop.
        stack: Evaluation stack the loop was invoked on.

    Raises:
        StackerSyntaxError: If ``body`` is not a code block (a bare value
            would otherwise be pushed forever).
    """
    if not isinstance(body, type(parent)):
        raise StackerSyntaxError(f"`loop` expects a code block, got {body}")
    while True:
        try:
            parent.evaluate(body.tokens, stack=stack)
        except BreakException:
            break


def _times(
    n_times: int,
    block: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code a specified number of times."""
    count = 0
    while count < n_times:  # a comparison, not range(): non-integer counts keep working
        try:
            run_block(block, parent, stack)
        except BreakException:
            return
        count += 1


def _do(
    start_value: int,
    end_value: int,
    symbol: str,
    block: Stacker,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    # Create child scope once for all iterations (optimization)
    original_parent_vars = parent.variables
    child_scope = parent.variables.create_child_scope()

    # Update nested StackerCore instances to use the child scope
    _update_nested_variables(block.tokens, child_scope)

    try:
        for i in range(start_value, end_value + 1):
            # Update loop variable
            child_scope[symbol] = i
            parent.variables = child_scope
            try:
                parent.evaluate(block.tokens, stack=stack)
            except BreakException:
                break
    finally:
        parent.variables = original_parent_vars


def _while(
    condition: Stacker,
    body: Stacker,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code while a condition is true."""
    while True:
        parent.evaluate(condition.tokens, stack=stack)
        if not stack.pop():
            break
        try:
            parent.evaluate(body.tokens, stack=stack)
        except BreakException:
            break


def _dolist(
    symbol: str,
    lst: list[object],
    block: Stacker,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    # Create child scope once for all iterations (optimization)
    original_parent_vars = parent.variables
    child_scope = parent.variables.create_child_scope()

    # Update nested StackerCore instances to use the child scope
    # This is necessary because block.tokens may contain nested code blocks
    _update_nested_variables(block.tokens, child_scope)

    try:
        for i in lst:
            # Update loop variable
            child_scope[symbol] = i
            parent.variables = child_scope
            try:
                parent.evaluate(block.tokens, stack=stack)
            except BreakException:
                break
    finally:
        parent.variables = original_parent_vars


loop_operators = {
    "loop": {
        "func": (lambda body, parent, stack: _loop(body, parent, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Repeats a block of code until `break`. {body} loop",
    },
    "while": {
        "func": (
            lambda condition, body, parent, stack: _while(condition, body, parent, stack)
        ),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Repeats a block while a condition block is true: {cond} {body} while",
    },
    "times": {
        "func": (lambda n_times, block, parent, stack: _times(n_times, block, parent, stack)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Repeats a block n times: {body} n times",
    },
    "do": {
        "func": (
            lambda start_value, end_value, symbol, block, parent, stack: _do(
                start_value, end_value, symbol, block, parent, stack
            )
        ),
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Runs a block for each integer of a range, bound to a name: 1 10 :i {i echo} do",
    },
    "dolist": {
        "func": (
            lambda symbol, lst, block, parent, stack: _dolist(
                symbol, lst, block, parent, stack
            )
        ),
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Runs a block for each element of a list, bound to a name: [1 2 3] :x {x echo} dolist",
    },
}
