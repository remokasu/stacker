from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.data_type import Symbol
from stacker.engine.scope import ScopedVariables
from stacker.error import BreakException, StackerSyntaxError, StackerTypeError
from stacker.operators.arguments import integer_argument
from stacker.util.disp import plain_text

if TYPE_CHECKING:
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


def _body_scope(word: str, block: object, parent: Stacker) -> ScopedVariables:
    """Returns the scope the loop body ``block`` is bound to; a value that is not a block is refused by name."""
    if not isinstance(block, type(parent)):
        raise StackerTypeError(f"`{word}` expects a code block as the body, got {plain_text(block)}")
    return block.variables


def _loop(body: object, parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates ``body`` on ``stack`` forever until ``break`` is raised.

    This is the single looping primitive every other loop can be built on.
    Each iteration runs the body in its own scope; no Python recursion
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
            parent._run_block(body, stack)
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
            parent._run_block(block, stack)
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
    # Each iteration runs in a scope of its own holding the loop variable,
    # a child of the body's own scope: a lambda or block kept from one
    # iteration sees that iteration's value, and a name the body is first
    # to set goes to the body's scope (see loop_scope)
    start_value = integer_argument("do", start_value)
    end_value = integer_argument("do", end_value)
    body_scope = _body_scope("do", block, parent)
    for i in range(start_value, end_value + 1):
        try:
            parent._run_bound(block, ScopedVariables.loop_scope(body_scope, {symbol: i}), stack)
        except BreakException:
            break


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
        if not parent._condition_of(condition, stack, "while"):
            break
        try:
            parent._run_block(body, stack)
        except BreakException:
            break


def _dolist(
    symbol: str,
    lst: list[object],
    block: Stacker,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    # Each iteration runs in a scope of its own holding the loop variable,
    # a child of the body's own scope (see _do)
    body_scope = _body_scope("dolist", block, parent)
    for i in lst:
        try:
            parent._run_bound(block, ScopedVariables.loop_scope(body_scope, {symbol: i}), stack)
        except BreakException:
            break


loop_operators = {
    "loop": {
        "func": _loop,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Repeats a block of code until `break`. {body} loop",
    },
    "while": {
        "func": _while,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Repeats a block while a condition block is true: {cond} {body} while",
    },
    "times": {
        "func": _times,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Repeats a block n times: {body} n times",
    },
    "do": {
        "func": _do,
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Runs a block for each integer of a range, bound to a name: 1 10 :i {i echo} do",
    },
    "dolist": {
        "func": _dolist,
        "arg_count": 4,
        "push_result_to_stack": False,
        "desc": "Runs a block for each element of a list, bound to a name: [1 2 3] :x {x echo} dolist",
    },
}
