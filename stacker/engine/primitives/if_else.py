"""The condition words' Python entries: `if`, `ifelse`, `cond`, `iferror`, `try` and `throw`.

Each entry puts its arguments back on the stack and hands the word to the
machine, which holds the one implementation; a wrapper registered over a
word, or a subclass, reaches it here. `throw` raises on its own, and the
stack's restoring after a caught error is written here for the machine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.data_type import Symbol
from stacker.error import StackerTypeError, UserError
from stacker.lang.text import plain_text

if TYPE_CHECKING:
    from stacker.data_type import stack_data
    from stacker.engine.core import StackerCore


def _if(
    condition: StackerCore | bool,
    blockstack: StackerCore | object,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if a condition is true.
    {condition}
    {block}
    if
    """
    stack.append(condition)
    stack.append(blockstack)
    parent._run_built_in("if", stack)


def _if_else(
    condition: StackerCore | bool,
    true_block: StackerCore | object,
    false_block: StackerCore | object,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if a condition is true, otherwise executes another block of code.
    {condition}
    {true block}
    {false block}
    ifelse
    """
    stack.append(condition)
    stack.append(true_block)
    stack.append(false_block)
    parent._run_built_in("ifelse", stack)


def _cond(pairs: list[tuple[object, object]], parent: StackerCore, stack: stack_data[object]) -> None:
    """Evaluates condition-result pairs in order, executing the first matching result.
    {c1} {r1} {c2} {r2} ... n cond
    """
    for condition, result in pairs:
        stack.append(condition)
        stack.append(result)
    stack.append(len(pairs))
    parent._run_built_in("cond", stack)


def _put_back(stack: stack_data[object], saved: list[object]) -> list[object]:
    """Returns the stack to ``saved`` (what it held when the word began) and returns what it held at the failure.

    Values the failing block pushed are dropped and values it took are
    back; what the block changed in place (an array, a dictionary, a
    variable) stays changed.
    """
    partial = list(stack)
    stack.clear()
    stack.extend(saved)
    return partial


def _iferror(
    try_block: StackerCore | object,
    catch_block: StackerCore | object,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if an error occurs.
    {try block}
    {catch block}
    iferror

    The stack is as it was when `iferror` began before the catch block
    runs: what the try block pushed is dropped and what it took is back.
    """
    stack.append(try_block)
    stack.append(catch_block)
    parent._run_built_in("iferror", stack)


def _throw(kind: object, message: object) -> None:
    """``kind message throw``: raises an error of the program's own kind with ``message`` as its text."""
    if isinstance(kind, Symbol):
        kind = kind.name
    if not isinstance(kind, str) or kind == "" or not isinstance(message, str):
        raise StackerTypeError(
            "`throw` expects a kind (a string or a symbol) and a message (a string), "
            f"got {plain_text(kind)} and {plain_text(message)}"
        )
    raise UserError(str(kind), str(message))


def _try(
    try_block: StackerCore | object,
    handler: StackerCore | object,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """``{try} {handler} try``: runs ``try_block``; on an error, pushes the error as a dictionary and runs ``handler``.

    The stack is as it was when `try` began before the dictionary is
    pushed. The dictionary has the keys ``"kind"`` (a `throw` kind, or the
    class name of a built-in error), ``"message"`` and ``"stack"`` (what
    the stack held at the failure, for looking into). What is caught is
    what `iferror` catches: every error, but not `break` or an exit.
    """
    stack.append(try_block)
    stack.append(handler)
    parent._run_built_in("try", stack)


condition_operators = {
    "cond": {
        "func": _cond,
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Evaluates condition-result pairs in order. {c1} {r1} ... n cond",
    },
    "if": {
        "func": _if,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Executes a block of code if a condition is true.",
    },
    "ifelse": {
        "func": _if_else,
        "arg_count": 3,
        "push_result_to_stack": False,
        "desc": (
            "Executes a block of code if a condition is true, "
            "otherwise executes another block of code."
        ),
    },
    "iferror": {
        "func": _iferror,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "{try} {catch} iferror: if the first block raises an error, puts the stack back as it was and runs the catch block",
    },
    "try": {
        "func": _try,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "{try} {handler} try: if the first block raises an error, puts the stack back as it was and runs the handler with the error on top as a dictionary ('kind', 'message', 'stack')",
    },
    "throw": {
        "func": _throw,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "kind message throw: raises an error of your own kind (a string or a symbol) with a message",
    },
}
