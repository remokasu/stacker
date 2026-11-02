"""Runs the control words of a compiled block with their literal bodies, without pushing the bodies.

A block that writes ``{body} do`` (or `dolist`, `loop`, `while`, `if`,
`ifelse`) with the body as a literal right before the word compiles to
one instruction (``stacker.engine.compiler``), run by the function of the
same name here. Each function does what the word's handler does, in the
same order and through the same code: the arguments are read by the
core's own readers (``_do_arguments``, ``_condition_of`` ...), the range
and the count are checked by the word's own checks (``loop.do_range``),
and the body is bound to the scope the block runs in by ``_bound_to``,
exactly as pushing the literal would have bound it. Only the pushing and
the taking back of the body are skipped, and the body's unit is run
directly instead of through ``_evaluate``.

A stack too short for the word's other arguments is left to the word
itself: the bodies are pushed and the word runner is called, so the error
and the stack it leaves are the interpreter's.

These functions run outside the word runner's own catches (a stack that
ran out, a host type error reworded in the word's name), so they must
never let a bare IndexError or TypeError out: the stack is checked before
anything is popped, and a value the word has to judge is handed to the
word. Every function takes the core of the compiled block, its tokens,
the word's lookup ``(kind, entry)`` (used when the word itself has to
run), the positions of the literal bodies and the stack.

A loop admits its body's unit without the checks made on entry once an
iteration has entered through them and run to its end (``run_body``
returns the unit to trust so, the loop hands it back): between two
iterations only the body's own words run, and one that changed a word
table or hid a name under a variable made the unit drop itself right
after. The scope of each iteration has the shape of the last (the loop
variable alone, or the same scope again), so a name hidden by it would
have been found on the first entry. In ``while`` two blocks alternate,
and each trusts its unit only while the other left the epoch alone. The
loop words themselves trust their bodies the same way, through the
core's ``_run_block`` and ``_run_bound`` and the ``trusted`` argument of
``_evaluate``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# core imports compiler, which imports this module: core's names are read at call time only
from stacker.engine import compiler, generation
from stacker.engine import core as _core
from stacker.engine.scope import ScopedVariables
from stacker.error import BreakException
from stacker.operators import if_else, loop

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore, TokenList
    from stacker.engine.data_type import stack_data

#: The types a count of `times` is run on here; the word itself looks at any other
COUNTS = frozenset({int, float, bool})
#: The function each control word's entry holds when it is the built-in: a word re-registered under the name
#: holds another, and is not inlined
ORIGINALS = {
    "do": loop.loop_operators["do"]["func"],
    "dolist": loop.loop_operators["dolist"]["func"],
    "loop": loop.loop_operators["loop"]["func"],
    "while": loop.loop_operators["while"]["func"],
    "times": loop.loop_operators["times"]["func"],
    "if": if_else.condition_operators["if"]["func"],
    "ifelse": if_else.condition_operators["ifelse"]["func"],
}


def run_body(
    core: StackerCore, body: StackerCore, stack: stack_data[object], trusted: compiler.Unit | None = None
) -> compiler.Unit | None:
    """Runs the bound block ``body`` on ``stack`` by its unit when it has one, else by the interpreter.

    Args:
        core: The core of the compiled block (its trace is set to the body's on an error, as the handlers do).
        body: The body, bound to the scope it runs in.
        stack: The stack.
        trusted: The unit this call returned last time, for a loop running the body again: it is admitted
            without the checks made on entry (see the module's docstring).

    Returns:
        The body's unit when it ran the body to its end through the checks (or as ``trusted``): what the
        next iteration may trust. None when the interpreter ran the body, or the unit dropped itself in mid-run.
    """
    try:
        tokens = body.tokens  # (a block's tokens are always a TokenList, which counts its runs and keeps its unit)
        unit = tokens._unit
        if type(unit) is compiler.Unit and body._interp_scope is None:
            body.trace = tokens
            if compiler.run(unit, body, tokens, stack, unit is trusted):
                return unit if tokens._unit is unit else None  # (dropped in mid-run: the interpreter finished it)
        body._evaluate(tokens, stack)
        return None
    except Exception:
        core.trace = body.trace  # the tokens of the innermost failing block, for diagnostics
        raise


def _fall_back(
    core: StackerCore, tokens: TokenList, indexes: tuple[int, ...], name: str, lookup: tuple, stack: stack_data[object]
) -> None:
    """Pushes the literal bodies and runs the word itself: the stack is too short for its other arguments."""
    for index in indexes:
        stack.append(tokens[index]._bound_to(core.variables))
    core._run_word(name, lookup[0], lookup[1], stack)


def do(core: StackerCore, tokens: TokenList, lookup: tuple, body_index: int, stack: stack_data[object]) -> None:
    """``first last :name {body} do``: runs the body once per integer, each run in a scope of its own."""
    if len(stack) < 3:
        _fall_back(core, tokens, (body_index,), "do", lookup, stack)
        return
    start_value, end_value, name = core._do_arguments(stack)
    try:
        values = loop.do_range(start_value, end_value)
    except (TypeError, AttributeError) as error:
        _core._reraise_type_error("do", [start_value, end_value], error)
    body = tokens[body_index]._bound_to(core.variables)
    body_scope = body.variables
    trusted = None
    for i in values:
        # (the iteration's copy is not kept in a name here: with nothing else holding it, the next
        # iteration's _bound_to binds the same copy again instead of making one, as _run_bound lets it)
        try:
            trusted = run_body(core, body._bound_to(ScopedVariables.loop_scope(body_scope, {name: i})), stack, trusted)
        except BreakException:
            break


def dolist(core: StackerCore, tokens: TokenList, lookup: tuple, body_index: int, stack: stack_data[object]) -> None:
    """``items :name {body} dolist``: runs the body once per item, each run in a scope of its own."""
    if len(stack) < 2:
        _fall_back(core, tokens, (body_index,), "dolist", lookup, stack)
        return
    items, name = core._dolist_arguments(stack)
    body = tokens[body_index]._bound_to(core.variables)
    body_scope = body.variables
    trusted = None
    try:
        for i in items:
            try:
                trusted = run_body(core, body._bound_to(ScopedVariables.loop_scope(body_scope, {name: i})), stack, trusted)
            except BreakException:
                break
    except (TypeError, AttributeError) as error:
        _core._reraise_type_error("dolist", [items], error)


def loop_(core: StackerCore, tokens: TokenList, lookup: tuple, body_index: int, stack: stack_data[object]) -> None:
    """``{body} loop``: runs the body until it breaks (``lookup`` is unused: the word reads nothing else)."""
    body = tokens[body_index]._bound_to(core.variables)
    trusted = None
    while True:
        try:
            trusted = run_body(core, body, stack, trusted)
        except BreakException:
            break


def while_(
    core: StackerCore, tokens: TokenList, lookup: tuple, condition_index: int, body_index: int, stack: stack_data[object]
) -> None:
    """``{condition} {body} while``: runs the body while the condition block leaves a true value (``lookup`` unused)."""
    condition = tokens[condition_index]._bound_to(core.variables)
    body = tokens[body_index]._bound_to(core.variables)
    # each block's unit is trusted only while the other block changed nothing in the process
    trusted_condition = trusted_body = None
    while True:
        epoch = generation.epoch
        trusted_condition = run_body(core, condition, stack, trusted_condition)
        if generation.epoch != epoch:
            trusted_body = None
        if not core._condition_left(stack, "while"):  # (a break in the condition leaves the loop around the while)
            break
        epoch = generation.epoch
        try:
            trusted_body = run_body(core, body, stack, trusted_body)
        except BreakException:
            break
        if generation.epoch != epoch:
            trusted_condition = None


def times(
    core: StackerCore,
    tokens: TokenList,
    lookup: tuple,
    body_index: int,
    count_kind: str,
    count_name: str | None,
    count_value: object,
    stack: stack_data[object],
) -> None:
    """``{body} n times``: runs the body ``n`` times, ``n`` a number literal or a variable's value.

    The word reads its count before it takes the body, running a block
    there for its value; so when the count is not a number (a variable
    holding a block or a symbol, a variable that is gone) the body is
    pushed, the count is pushed or looked up as the interpreter would, and
    the word itself runs.
    """
    if count_kind == compiler.CONST:
        count = count_value
    else:
        count = core.variables.get(count_name, _core._MISSING)
        if count is _core._MISSING:
            # the name means what it means now, and so does `times` after it (what the name runs may
            # change the word tables or the bindings, as the interpreter would notice between the two)
            stack.append(tokens[body_index]._bound_to(core.variables))
            core._evaluate([count_name, "times"], stack, trace=False)
            return
    if type(count) not in COUNTS:
        stack.append(tokens[body_index]._bound_to(core.variables))
        stack.append(count)
        core._run_word("times", lookup[0], lookup[1], stack)
        return
    body = tokens[body_index]._bound_to(core.variables)
    done = 0
    trusted = None
    while done < count:  # a comparison, not range(): non-integer counts keep working, as for the word
        try:
            trusted = run_body(core, body, stack, trusted)
        except BreakException:
            return
        done += 1


def if_(core: StackerCore, tokens: TokenList, lookup: tuple, body_index: int, stack: stack_data[object]) -> None:
    """``condition {body} if``: runs the body when the condition (a value, or a block run for one) is true."""
    if not stack:
        _fall_back(core, tokens, (body_index,), "if", lookup, stack)
        return
    condition = stack.pop()
    if core._condition_of(condition, stack, "if"):
        run_body(core, tokens[body_index]._bound_to(core.variables), stack)


def ifelse(
    core: StackerCore, tokens: TokenList, lookup: tuple, true_index: int, false_index: int, stack: stack_data[object]
) -> None:
    """``condition {true} {false} ifelse``: runs one body or the other."""
    if not stack:
        _fall_back(core, tokens, (true_index, false_index), "ifelse", lookup, stack)
        return
    condition = stack.pop()
    chosen = true_index if core._condition_of(condition, stack, "ifelse") else false_index
    run_body(core, tokens[chosen]._bound_to(core.variables), stack)
