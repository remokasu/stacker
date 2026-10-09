from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.operators.block_exec import run_block

if TYPE_CHECKING:
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


def _resolve_condition(condition: object, parent: Stacker, stack: stack_data[object]) -> object:
    """Evaluate a condition block on ``stack`` or resolve a variable name."""
    if isinstance(condition, type(parent)):
        parent.evaluate(condition.tokens, stack=stack)
        return stack.pop()
    if isinstance(condition, str) and condition in parent.variables:
        return parent.variables[condition]
    return condition


def _if(
    condition: Stacker | bool,
    blockstack: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if a condition is true.
    {condition}
    {block}
    if
    """
    if _resolve_condition(condition, parent, stack):
        run_block(blockstack, parent, stack)


def _if_else(
    condition: Stacker | bool,
    true_block: Stacker | object,
    false_block: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if a condition is true, otherwise executes another block of code.
    {condition}
    {true block}
    {false block}
    ifelse
    """
    if _resolve_condition(condition, parent, stack):
        run_block(true_block, parent, stack)
    else:
        run_block(false_block, parent, stack)


def _cond(pairs: list[tuple[object, object]], parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates condition-result pairs in order, executing the first matching result.
    {c1} {r1} {c2} {r2} ... n cond
    """
    for condition, result in pairs:
        if isinstance(condition, type(parent)):
            parent.evaluate(condition.tokens, stack=stack)
            cond_val = stack.pop()
        else:
            cond_val = condition
        if cond_val:
            run_block(result, parent, stack)
            return


def _iferror(
    try_block: Stacker | object,
    catch_block: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if an error occurs.
    {try block}
    {catch block}
    iferror
    """
    try:
        run_block(try_block, parent, stack)
    # Deliberately Exception, not BaseException: control-flow signals such as
    # BreakException derive from BaseException so they pass through iferror
    # (a break inside the try block must exit the enclosing loop, not run the
    # catch block). The broad catch itself is intentional: iferror is the
    # language's user-facing generic try/catch construct, so it must catch
    # every runtime error, unlike internal error handling.
    except Exception as _:  # noqa: BLE001
        run_block(catch_block, parent, stack)


condition_operators = {
    "cond": {
        "func": (lambda pairs, parent, stack: _cond(pairs, parent, stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Evaluates condition-result pairs in order. {c1} {r1} ... n cond",
    },
    "if": {
        "func": (
            lambda condition, blockstack, parent, stack: _if(
                condition, blockstack, parent, stack
            )
        ),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code if a condition is true.",
    },
    "ifelse": {
        "func": (
            lambda condition, true_block, false_block, parent, stack: _if_else(
                condition, true_block, false_block, parent, stack
            )
        ),
        "arg_count": 3,
        "push_result_to_stack": False,
        "desc": (
            "Executes a block of code if a condition is true, "
            "otherwise executes another block of code."
        ),
    },
    "iferror": {
        "func": (
            lambda try_block, catch_block, parent, stack: _iferror(
                try_block, catch_block, parent, stack
            )
        ),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code if an error occurs.",
    },
}
