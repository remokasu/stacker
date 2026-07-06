from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def _if(condition: Stacker | bool, blockstack: Stacker | object, parent: Stacker) -> None:
    """Executes a block of code if a condition is true.
    {condition}
    {block}
    if
    """
    if isinstance(condition, type(parent)):
        parent.evaluate(condition.tokens, stack=parent.stack)
        condition = parent.stack.pop()
    if isinstance(condition, str):
        if condition in parent.variables:
            condition = parent.variables[condition]
    if condition:
        if isinstance(blockstack, type(parent)):
            parent.evaluate(blockstack.tokens, stack=parent.stack)
        else:  # e.g. a numeric object
            parent.stack.append(blockstack)


def _if_else(
    condition: Stacker | bool,
    true_block: Stacker | object,
    false_block: Stacker | object,
    parent: Stacker,
) -> None:
    """Executes a block of code if a condition is true, otherwise executes another block of code.
    {condition}
    {true block}
    {false block}
    ifelse
    """
    if isinstance(condition, type(parent)):
        parent.evaluate(condition.tokens, stack=parent.stack)
        condition = parent.stack.pop()
    if isinstance(condition, str):
        if condition in parent.variables:
            condition = parent.variables[condition]
    if condition:
        if isinstance(true_block, type(parent)):
            parent.evaluate(true_block.tokens, stack=parent.stack)
        else:  # e.g. a numeric object
            parent.stack.append(true_block)
    else:
        if isinstance(false_block, type(parent)):
            parent.evaluate(false_block.tokens, stack=parent.stack)
        else:
            parent.stack.append(false_block)


def _cond(pairs: list[tuple[object, object]], parent: Stacker, stack: object) -> None:
    """Evaluates condition-result pairs in order, executing the first matching result.
    {c1} {r1} {c2} {r2} ... n cond
    """
    for condition, result in pairs:
        if isinstance(condition, type(parent)):
            parent.evaluate(condition.tokens, stack=stack)  # type: ignore[arg-type]
            cond_val = stack.pop()  # type: ignore[union-attr]
        else:
            cond_val = condition
        if cond_val:
            if isinstance(result, type(parent)):
                parent.evaluate(result.tokens, stack=stack)  # type: ignore[arg-type]
            else:
                stack.append(result)  # type: ignore[union-attr]
            return


def _iferror(
    try_block: Stacker | object,
    catch_block: Stacker | object,
    parent: Stacker,
) -> None:
    """Executes a block of code if an error occurs.
    {try block}
    {catch block}
    iferror
    """
    try:
        if isinstance(try_block, type(parent)):
            parent.evaluate(try_block.tokens, stack=parent.stack)
        else:
            parent.stack.append(try_block)
    except Exception as _:
        if isinstance(catch_block, type(parent)):
            parent.evaluate(catch_block.tokens, stack=parent.stack)
        else:
            parent.stack.append(catch_block)


condition_operators = {
    "cond": {
        "func": (lambda pairs, parent, stack: _cond(pairs, parent, stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Evaluates condition-result pairs in order. {c1} {r1} ... n cond",
    },
    "if": {
        "func": (
            lambda condition, blockstack, parent: _if(condition, blockstack, parent)
        ),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code if a condition is true.",
    },
    "ifelse": {
        "func": (
            lambda condition, true_block, false_block, parent: _if_else(
                condition, true_block, false_block, parent
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
            lambda try_block, catch_block, parent: _iferror(
                try_block, catch_block, parent
            )
        ),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code if an error occurs.",
    },
}
