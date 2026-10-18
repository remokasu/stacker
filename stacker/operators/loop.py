from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.data_type import Symbol
from stacker.engine.scope import ScopedVariables
from stacker.error import BreakException, StackerSyntaxError
from stacker.operators.block_exec import resolve_condition, run_block
from stacker.util.disp import plain_text

if TYPE_CHECKING:
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


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
    """Executes a block of code a specified number of times.

    Raises:
        StackerSyntaxError: If ``n_times`` is not a number, which is what
            the block and the count written the wrong way round gives.
    """
    # A symbol here is reported by the caller as a type error, like any
    # symbol where a value is needed; anything else that is not a number is
    # the block and the count written the wrong way round
    if not isinstance(n_times, (int, float, Symbol)):
        raise StackerSyntaxError(
            f"`times` expects a number of repetitions on top, got {plain_text(n_times)}: "
            "write `{body} n times`"
        )
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
    # Each iteration gets a scope of its own holding the loop variable, so
    # a lambda or block kept from one iteration sees that iteration's
    # value; a name the body is first to set goes to the caller's scope
    # (see loop_scope)
    original_parent_vars = parent.variables
    try:
        for i in range(start_value, end_value + 1):
            child_scope = ScopedVariables.loop_scope(original_parent_vars, {symbol: i})
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
    """Executes a block of code while a condition block is true.

    Raises:
        StackerSyntaxError: If ``condition`` is not a code block (a plain
            value would test the same every time, looping for ever or never).
    """
    if not isinstance(condition, type(parent)):
        raise StackerSyntaxError(f"`while` expects a condition block, got {condition}")
    while True:
        if not resolve_condition(condition, parent, stack, "while"):
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
    # Each iteration gets a scope of its own holding the loop variable, so
    # a lambda or block kept from one iteration sees that iteration's
    # value; a name the body is first to set goes to the caller's scope
    # (see loop_scope)
    original_parent_vars = parent.variables
    try:
        for i in lst:
            child_scope = ScopedVariables.loop_scope(original_parent_vars, {symbol: i})
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
