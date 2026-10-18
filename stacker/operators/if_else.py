from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.engine.data_type import Symbol
from stacker.error import StackerTypeError, UserError, error_kind
from stacker.operators.block_exec import resolve_condition, run_block
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
    if resolve_condition(condition, parent, stack, "if"):
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
    if resolve_condition(condition, parent, stack, "ifelse"):
        run_block(true_block, parent, stack)
    else:
        run_block(false_block, parent, stack)


def _cond(pairs: list[tuple[object, object]], parent: Stacker, stack: stack_data[object]) -> None:
    """Evaluates condition-result pairs in order, executing the first matching result.
    {c1} {r1} {c2} {r2} ... n cond
    """
    for condition, result in pairs:
        if resolve_condition(condition, parent, stack, "cond"):
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

    The dictionary has the keys ``"kind"`` (a `throw` kind, or the class
    name of a built-in error) and ``"message"``. What is caught is what
    `iferror` catches: every error, but not `break` or an exit.
    """
    try:
        run_block(try_block, parent, stack)
    except Exception as error:  # noqa: BLE001 -- the language's try/catch, see _iferror
        stack.append({"kind": error_kind(error), "message": str(error)})
        run_block(handler, parent, stack)


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
    "try": {
        "func": (lambda try_block, handler, parent, stack: _try(try_block, handler, parent, stack)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "{try} {handler} try: runs the handler with the error on the stack as a dictionary ('kind' and 'message') if the first block raises one",
    },
    "throw": {
        "func": (lambda kind, message: _throw(kind, message)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "kind message throw: raises an error of your own kind (a string or a symbol) with a message",
    },
}
