"""The loop words' Python entries: `loop`, `times`, `do`, `while` and `dolist`.

Each entry puts its arguments back on the stack and hands the word to the
machine, which holds the one implementation; a wrapper registered over a
word, or a subclass, reaches it here. The checks the machine shares with a
compiled loop (the count of `times`, the bounds of `do`, the body's scope)
are written here too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.data_type import Symbol
from stacker.engine import core as _core
from stacker.error import StackerSyntaxError, StackerTypeError
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
    """Runs ``body`` on ``stack`` again and again until a ``break``.

    The loop is the machine's: this function puts the body back and hands
    the word over, like every entry in this module.

    Args:
        body: Code block to repeat.
        parent: Interpreter evaluating the loop.
        stack: Evaluation stack the loop was invoked on.

    Raises:
        StackerSyntaxError: If ``body`` is not a code block (a bare value
            would otherwise be pushed forever).
    """
    stack.append(body)
    parent._run_built_in("loop", stack)


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
    """Runs ``block`` ``n_times`` times.

    The count was read for this call already, so it goes back wrapped, for
    the machine to read as it is (a block it left is not run again).

    Raises:
        StackerSyntaxError: If ``n_times`` is not a number, which is what
            the block and the count written the wrong way round gives.
    """
    stack.append(block)
    stack.append(_core.Taken(n_times))
    parent._run_built_in("times", stack)


def _do(
    start_value: int,
    end_value: int,
    symbol: str,
    block: StackerCore,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Runs ``block`` once for each integer from ``start_value`` to ``end_value``, bound to ``symbol``.

    The bounds were read for this call already, so they go back wrapped,
    for the machine to read as they are (a block one left is not run
    again). The machine makes each iteration's scope, a child of the
    body's own holding the loop variable (see ``loop_scope``).
    """
    stack.append(_core.Taken(start_value))
    stack.append(_core.Taken(end_value))
    stack.append(Symbol(symbol))
    stack.append(block)
    parent._run_built_in("do", stack)


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
    stack.append(condition)
    stack.append(body)
    parent._run_built_in("while", stack)


def _dolist(
    symbol: str,
    lst: list[object],
    block: StackerCore,
    parent: StackerCore,
    stack: stack_data[object],
) -> None:
    """Runs ``block`` once for each item of ``lst``, bound to ``symbol``.

    The items were read for this call already, so they go back wrapped, for
    the machine to read as they are; the machine makes each iteration's
    scope (see ``_do``).
    """
    stack.append(_core.Taken(lst))
    stack.append(Symbol(symbol))
    stack.append(block)
    parent._run_built_in("dolist", stack)


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
