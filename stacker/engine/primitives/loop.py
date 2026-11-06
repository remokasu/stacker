from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.data_type import Symbol
from stacker.error import BreakException, StackerSyntaxError, StackerTypeError
from stacker.lang import generation
from stacker.lang.arguments import integer_argument
from stacker.lang.scope import ScopedVariables
from stacker.lang.text import plain_text

if TYPE_CHECKING:
    from stacker.data_type import stack_data
    from stacker.engine.core import StackerCore


def _body_scope(word: str, block: object, parent: StackerCore) -> ScopedVariables:
    """Returns the scope the loop body ``block`` is bound to; a value that is not a block is refused by name."""
    if not isinstance(block, type(parent)):
        raise StackerTypeError(f"`{word}` expects a code block as the body, got {plain_text(block)}")
    return block.variables


def _loop(body: object, parent: StackerCore, stack: stack_data[object]) -> None:
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
    trusted = None  # (the body's unit, once an iteration ran it to its end: see stacker.engine.inline)
    while True:
        try:
            trusted = parent._run_block(body, stack, trusted)
        except BreakException:
            break


def check_times_count(n_times: object) -> None:
    """Refuses a count of `times` that is not a number.

    A symbol is let through: the caller reports it as a type error, like
    any symbol where a value is needed. Anything else that is not a number
    is the block and the count written the wrong way round. The word and a
    compiled `times` both check the count here.

    Args:
        n_times: The value in the count's place.

    Raises:
        StackerSyntaxError: The value is neither a number nor a symbol.
    """
    if not isinstance(n_times, (int, float, Symbol)):
        raise StackerSyntaxError(
            f"`times` expects a number of repetitions on top, got {plain_text(n_times)}: "
            "write `{body} n times`"
        )


def _times(
    n_times: int,
    block: StackerCore | object,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Executes a block of code a specified number of times.

    Raises:
        StackerSyntaxError: If ``n_times`` is not a number, which is what
            the block and the count written the wrong way round gives.
    """
    check_times_count(n_times)
    count = 0
    trusted = None
    while count < n_times:  # a comparison, not range(): non-integer counts keep working
        try:
            trusted = parent._run_block(block, stack, trusted)
        except BreakException:
            return
        count += 1


def _do(
    start_value: int,
    end_value: int,
    symbol: str,
    block: StackerCore,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    # Each iteration runs in a scope of its own holding the loop variable,
    # a child of the body's own scope: a lambda or block kept from one
    # iteration sees that iteration's value, and a name the body is first
    # to set goes to the body's scope (see loop_scope)
    values = do_range(start_value, end_value)
    body_scope = _body_scope("do", block, parent)
    trusted = None
    for i in values:
        try:
            trusted = parent._run_bound(block, ScopedVariables.loop_scope(body_scope, {symbol: i}), stack, trusted)
        except BreakException:
            break


def do_range(start_value: object, end_value: object) -> range:
    """The integers a `do` runs over, first to last inclusive; the two bounds are checked as integers, first one first.

    The word and a compiled `do` both take their range here.

    Args:
        start_value: The first value, as written.
        end_value: The last value, as written.

    Raises:
        StackerTypeError: A bound is not an integer (a symbol is reported by the caller).
    """
    return range(integer_argument("do", start_value), integer_argument("do", end_value) + 1)


def _while(
    condition: StackerCore,
    body: StackerCore,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Executes a block of code while a condition block is true.

    Raises:
        StackerSyntaxError: If ``condition`` is not a code block (a plain
            value would test the same every time, looping for ever or never).
    """
    if not isinstance(condition, type(parent)):
        raise StackerSyntaxError(f"`while` expects a condition block, got {condition}")
    # each block's unit is trusted only while the other block changed nothing in the process
    trusted_condition = trusted_body = None
    while True:
        epoch = generation.epoch
        trusted_condition = parent._run_block(condition, stack, trusted_condition)
        if generation.epoch != epoch:
            trusted_body = None
        if not parent._condition_left(stack, "while"):
            break
        epoch = generation.epoch
        try:
            trusted_body = parent._run_block(body, stack, trusted_body)
        except BreakException:
            break
        if generation.epoch != epoch:
            trusted_condition = None


def _dolist(
    symbol: str,
    lst: list[object],
    block: StackerCore,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    # Each iteration runs in a scope of its own holding the loop variable,
    # a child of the body's own scope (see _do)
    body_scope = _body_scope("dolist", block, parent)
    trusted = None
    for i in lst:
        try:
            trusted = parent._run_bound(block, ScopedVariables.loop_scope(body_scope, {symbol: i}), stack, trusted)
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
