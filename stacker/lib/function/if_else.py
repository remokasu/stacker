from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def _if(condition: Stacker | bool, blockstack: Stacker | Any, parent: Stacker) -> None:
    """Executes a block of code if a condition is true.
    {block}
    {condition}
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
    true_block: Stacker | Any,
    false_block: Stacker | Any,
    parent: Stacker,
) -> None:
    """Executes a block of code if a condition is true, otherwise executes another block of code.
    {true block}
    {false block}
    {condition}
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


def _iferror(
    try_block: Stacker | Any,
    catch_block: Stacker | Any,
    parent: Stacker,
):
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
