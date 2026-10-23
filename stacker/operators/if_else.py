from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, UserError, error_kind
from stacker.util.disp import plain_text

if TYPE_CHECKING:
    from stacker.stacker import Stacker
    from stacker.util.stack_data import stack_data


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
    if parent._condition_of(condition, stack, "if"):
        parent._run_block(blockstack, stack)


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
    if parent._condition_of(condition, stack, "ifelse"):
        parent._run_block(true_block, stack)
    else:
        parent._run_block(false_block, stack)


def _cond(pairs: list[tuple[object, object]], parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates condition-result pairs in order, executing the first matching result.
    {c1} {r1} {c2} {r2} ... n cond
    """
    for condition, result in pairs:
        if parent._condition_of(condition, stack, "cond"):
            parent._run_block(result, stack)
            return


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
    try_block: Stacker | object,
    catch_block: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """Executes a block of code if an error occurs.
    {try block}
    {catch block}
    iferror

    The stack is as it was when `iferror` began before the catch block
    runs: what the try block pushed is dropped and what it took is back.
    """
    saved = list(stack)
    try:
        parent._run_block(try_block, stack)
    # Deliberately Exception, not BaseException: control-flow signals such as
    # BreakException derive from BaseException so they pass through iferror
    # (a break inside the try block must exit the enclosing loop, not run the
    # catch block). The broad catch itself is intentional: iferror is the
    # language's user-facing generic try/catch construct, so it must catch
    # every runtime error, unlike internal error handling.
    except Exception as _:  # noqa: BLE001
        _put_back(stack, saved)
        parent._run_block(catch_block, stack)


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
    try_block: Stacker | object,
    handler: Stacker | object,
    parent: Stacker,
    stack: stack_data[object],
) -> None:
    """``{try} {handler} try``: runs ``try_block``; on an error, pushes the error as a dictionary and runs ``handler``.

    The stack is as it was when `try` began before the dictionary is
    pushed. The dictionary has the keys ``"kind"`` (a `throw` kind, or the
    class name of a built-in error), ``"message"`` and ``"stack"`` (what
    the stack held at the failure, for looking into). What is caught is
    what `iferror` catches: every error, but not `break` or an exit.
    """
    saved = list(stack)
    try:
        parent._run_block(try_block, stack)
    except Exception as error:  # noqa: BLE001 -- the language's try/catch, see _iferror
        partial = _put_back(stack, saved)
        stack.append({"kind": error_kind(error), "message": str(error), "stack": partial})
        parent._run_block(handler, stack)


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
