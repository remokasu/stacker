"""Compiles a block that runs often into resolved instructions, and runs them as the interpreter would.

A block's token list (``TokenList``) is shared by every copy of the block
that runs: each run is counted on it, and at the ``THRESHOLD``-th run the
list is compiled (``compile_block``). Compiling resolves each token once, the way
``StackerCore._evaluate`` resolves it on every run: a value, a list
template, a block literal, a macro, a variable, a word (built-in,
function or plugin, looked up as ``_lookup_word`` does; a function written
in Stacker is a call of its own), a literal spelled as a name, an
undefined name. The result is a ``Unit``: the instructions
(data: kind, position, name and value; a block literal is named by its
position alone). The machine (``stacker.engine.machine``) does for each
instruction exactly what it does for the token, through the interpreter's
own functions, on the real stack and the real scope: what a run leaves
behind, and what an error finds, is what the interpreter would have left.

Some steps do the interpreter's work more directly, under conditions that
make the result the same: a regular word on plain values is called
without the word runner (FAST1, FAST2), a function written in Stacker is
called without it (CALL), and a word with the tokens it reads written
right before it is one step (``_fuse``: a symbol and `set`, a control
word and its literal bodies, run by the machine as its own activations).
A unit's steps are therefore not one per token; a fused step stands at
its word's position.

What a unit resolved can go stale, and two guards catch that:

- the interpreter's word tables changed since the unit was compiled
  (``OperatorManager.generation``): the unit is dropped and the
  interpreter runs the block
- the names the unit took for words (and for literals and undefined
  names) must not be variables now: no scope the block runs in may hold
  one. This is checked when the unit starts (only the innermost scope
  when the scopes above it are the ones checked last time and nothing has
  changed since) and again after any instruction that ran a word. A
  variable the unit took for one may have vanished since; its
  instruction then looks the name up the general way

Both are told by one process-wide counter, ``generation.epoch``, which
every change of a word table or of a scope's names advances: after a
word, the unit compares it once and looks at the two guards only when it
moved. A loop running the same unit again, in a scope of the same shape,
right after an iteration that passed the entry checks admits it without
them (the machine's ``_loop_next``).

A guard that fails when the unit starts sends the block back to counting
its runs; one that fails in the middle lets the interpreter finish the
block and counts a drop. A block whose unit was dropped ``GIVE_UP`` times
that way is left to the interpreter for good. The interpreter also runs
the block when the unit belongs to another interpreter (a token list a
host hands to a second interpreter); a token list changed in place forgets
its unit (``TokenList._changed``).

Compiling never changes a program's result. A failure inside the compiler
itself leaves the block to the interpreter and is logged at DEBUG; a
failure of the host (``RecursionError``, ``MemoryError``) is retried on
a later run.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple

from stacker.data_type import Array, String, Symbol

# core imports this module: its names are read at call time only
from stacker.engine import core as _core
from stacker.engine import inline
from stacker.engine.sfunction import StackerFunction
from stacker.syntax.token_rules import cached_literal_eval

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore, TokenList
    from stacker.lang.scope import ScopedVariables

_LOGGER = logging.getLogger("stacker")

#: The run of a block on which it is compiled; None compiles nothing (tests set it)
THRESHOLD: int | None = 8
#: Whether every resolved instruction first re-resolves its name and checks the unit's answer (tests set it)
VERIFY = False
#: How many times a block's unit may be dropped in mid-run before the block is left to the interpreter
GIVE_UP = 3
#: Whether a block whose unit holds no fast word, fused step or direct call (or holds a macro expansion that
#: outweighs them) is left to the interpreter instead. Off: on the machine a unit's steps run with less around
#: them than the walk of the classification does, so every block that runs often is compiled (tests set it)
ONLY_WORTHWHILE = False

#: Set by the machine: rewrites a unit's steps, in place, when the unit is made (the kinds the machine runs
#: a word's step by are decided once there, not at every step). None leaves the steps as compiled
REWRITE = None
#: The unit of a block that is left to the interpreter for good
UNCOMPILABLE = object()

# The kinds of instruction. CONST, LIST, BLOCK and BAD come from the token's
# classification alone; the others are what a dynamic name resolved to
CONST = "CONST"  # push the value (a number, a string, a symbol) as it is
LIST = "LIST"  # build the list literal from its template and push it
BAD_LIST = "BAD_LIST"  # a list literal whose template failed to build: build it here, as the interpreter does
BLOCK = "BLOCK"  # push the block literal (the token itself) bound to the scope the block runs in
BAD = "BAD"  # a token that does not parse: raise its message here
MACRO = "MACRO"  # expand the macro of that name
VAR = "VAR"  # push the variable of that name (or, gone or not yet made, look the name up the general way)
WORD = "WORD"  # run the built-in word, function or plugin of that name, looked up once
CALL = "CALL"  # call the function of that name (a word whose entry holds a function written in Stacker)
FAST1 = "FAST1"  # run the regular word of one argument directly when the argument is a plain value
FAST2 = "FAST2"  # run the regular word of two arguments directly when both are plain values
SET = "SET"  # bind the variable a symbol names to the value under it: a symbol and `set` (or `=`) fused
# a control word with its literal bodies, run by stacker.engine.inline; the value holds the word's lookup and the
# bodies' positions
DO = "DO"
DOLIST = "DOLIST"
LOOP = "LOOP"
WHILE = "WHILE"
IF = "IF"
IFELSE = "IFELSE"
TIMES = "TIMES"  # `{body} n times` with the count a number literal or a variable: the value holds them too
LIT = "LIT"  # push the literal the name spells (the name is not a variable)
NAME = "NAME"  # look the name up the general way, every time

CONTROL = frozenset({DO, DOLIST, LOOP, WHILE, IF, IFELSE, TIMES})
#: The kinds made of several tokens; their value starts with the lookup of the word that ends them
FUSED = CONTROL | {SET}
RESOLVED = frozenset({MACRO, VAR, WORD, CALL, FAST1, FAST2, LIT}) | FUSED  # what a dynamic name can resolve to
NOT_VARIABLES = frozenset({WORD, CALL, FAST1, FAST2, LIT}) | FUSED  # the kinds that hold only while no variable has the name
WORDS = frozenset({WORD, CALL, FAST1, FAST2})  # the kinds that hold a word's lookup, (kind, entry), as their value
#: The kinds that do less than the interpreter does for the same tokens; a unit without one gains nothing
WORTHWHILE = frozenset({CALL, FAST1, FAST2}) | FUSED
#: The kinds whose work dwarfs what a unit saves around them: a unit with one gains nothing either (to be
#: reconsidered when expansions are shared between runs, since the expansion would then be compiled too)
OVERWHELMING = frozenset({MACRO})
#: The control words that are inlined with their literal bodies: the word, its kind, and how many bodies it takes
#: right before it (the last tokens before the word must all be block literals)
_CONTROL_WORDS = {
    "do": (DO, 1),
    "dolist": (DOLIST, 1),
    "loop": (LOOP, 1),
    "while": (WHILE, 2),
    "if": (IF, 1),
    "ifelse": (IFELSE, 2),
}
_KIND_OF_CONTROL = {kind: word for word, (kind, _) in _CONTROL_WORDS.items()}
_KIND_OF_CONTROL[TIMES] = "times"

#: The category of the words that take their arguments as values and leave at most one result (``_exec_regular``).
#: The category names are the operator manager's (``_DISPATCH_ORDER``), as the core's dispatch spells them
REGULAR = "regular"
#: The category of the words run by a handler of the core's own (``_PRIORITY_HANDLERS``)
_PRIORITY = "priority"
#: The words that bind a variable from a symbol and a value (a cheap sieve before the handler is compared)
_SET_WORDS = frozenset({"set", "="})
#: The types ``_pop_arg`` hands to a word unchanged: a FAST step takes them from the stack itself. A value of another
#: type goes through the word runner: a block is evaluated there, a Symbol reported, a lambda refused...
_PLAIN = frozenset({int, float, bool, complex, str, list, tuple, dict, type(None), Array})
#: ...except a String, which ``_pop_arg`` hands as the ``str`` it holds: a FAST step takes it too, unwrapped the same
#: way, on a path of its own, so that the plain values pay nothing for it
_DIRECT = _PLAIN | {String}


def _handler_of(kind: str) -> object:
    """The interpreter's handler a fused instruction of ``kind`` stands for (looked up when asked: core loads after this module)."""
    if kind == SET:
        return _core.StackerCore._prio_set
    return _core.StackerCore._PRIORITY_HANDLERS[_KIND_OF_CONTROL[kind]]


def _is_builtin_control(core: StackerCore, name: str, lookup: tuple) -> bool:
    """Whether the word ``name``, looked up as ``lookup``, is the built-in control word run by the interpreter's own handler."""
    return (
        lookup[0] == _PRIORITY
        and lookup[1]["func"] is inline.ORIGINALS[name]
        and core._PRIORITY_HANDLERS.get(name) is _core.StackerCore._PRIORITY_HANDLERS[name]
    )


class Instruction(NamedTuple):
    """One step of a unit: what to do, where its last token was, and what doing it needs.

    Most steps stand for one token; a fused step (``_fuse``) stands for a
    word and the tokens it reads, and takes the word's position.
    """

    kind: str
    index: int
    name: str | None
    value: object


class Unit:
    """A compiled block: its instructions and what they were resolved against."""

    __slots__ = ("instructions", "manager", "not_variables", "seen_epoch", "seen_parent", "steps", "words")

    def __init__(self, instructions: list[Instruction], core: StackerCore) -> None:
        #: the instructions, readable as data (tests and tools look at them)...
        self.instructions = instructions
        #: ...and the same as plain tuples, which the run loop unpacks fastest
        self.steps = [tuple(instruction) for instruction in instructions]
        if REWRITE is not None:
            REWRITE(self.steps, core)
        #: the names resolved as not being variables: no scope the block runs in may hold one
        self.not_variables = frozenset(i.name for i in instructions if i.kind in NOT_VARIABLES)
        #: the interpreter whose tables the names were resolved against, and its tables' generation then
        self.manager = core.operator_manager
        self.words = self.manager.generation
        #: the scope above the one the block last ran in, and generation.epoch when its
        #: chain was checked. The scope is held strongly on purpose: ``is`` against it is
        #: what the fast path rests on, and a scope that died and was replaced at the same
        #: address would pass for the one that was checked
        self.seen_parent: ScopedVariables | None = None
        self.seen_epoch = -1


def resolve(core: StackerCore, name: str) -> tuple[str, object]:
    """What a dynamic name means now, in the order ``StackerCore._evaluate`` looks it up.

    Args:
        core: The core the block runs on.
        name: The token.

    Returns:
        The kind (MACRO, VAR, WORD, CALL, FAST1, FAST2 or LIT) and
        what running it needs: the word's lookup for the words, the
        literal's value for LIT, else None.
    """
    if name in core.macros:
        return MACRO, None
    if core.variables.get(name, _core._MISSING) is not _core._MISSING:
        return VAR, None
    if name in core.operator_manager.built_in_operators or name in core.sfunctions or name in core.plugins:
        lookup = core._lookup_word(name)
        kind, entry = lookup
        if kind == _core.WORD_FUNCTION and isinstance(entry["func"], StackerFunction):
            return CALL, lookup
        if kind == REGULAR:
            if entry["arg_count"] == 2:
                return FAST2, lookup
            if entry["arg_count"] == 1:
                return FAST1, lookup
        return WORD, lookup
    literal = cached_literal_eval(name)
    if isinstance(literal, str):
        # defined nowhere now: read as a variable, which looks the name up the general way when it finds none,
        # so a block that makes the variable itself (a function binding a local) keeps its unit
        return VAR, None
    return LIT, literal


def _instruction(core: StackerCore, index: int, kind: int, token: object, payload: object) -> Instruction:
    """The instruction for one classified token."""
    if kind == _core.K_VALUE:
        return Instruction(CONST, index, None, token)
    if kind == _core.K_STRING:
        return Instruction(CONST, index, None, payload)
    if kind == _core.K_BLOCK_VALUE:
        return Instruction(BLOCK, index, None, None)
    # every other kind is looked up in the macro table first, as the interpreter does
    if token in core.macros:
        return Instruction(MACRO, index, token, None)
    if kind == _core.K_SYMBOL:
        return Instruction(CONST, index, None, payload)
    if kind == _core.K_LIST:
        return Instruction(LIST if payload is not None else BAD_LIST, index, token, payload)
    if kind == _core.K_INVALID:
        return Instruction(BAD, index, None, payload)
    if kind == _core.K_DYNAMIC:
        resolved, value = resolve(core, token)
        return Instruction(resolved, index, token, value)
    return Instruction(NAME, index, token, None)  # a raw block, which only a hand-built token list holds


def _check(core: StackerCore, kind: str, name: str, value: object) -> None:
    """Fails when ``name`` no longer resolves as the unit says (VERIFY).

    A variable that vanished is allowed for: its instruction looks the name up again.

    Raises:
        AssertionError: The name resolves to another kind now, or a word to another entry; a fused step's
            word is not the built-in run by the interpreter's own handler any more.
    """
    now, now_value = resolve(core, name)
    if kind in FUSED:
        lookup = value[0]
        if now != WORD or now_value[1] is not lookup[1] or core._PRIORITY_HANDLERS.get(name) is not _handler_of(kind):
            raise AssertionError(f"compiled `{name}` into {kind}, but it is another word now")
        if kind in CONTROL and not _is_builtin_control(core, name, lookup):
            raise AssertionError(f"compiled `{name}` into {kind}, but it is not the built-in word now")
        return
    if now != kind and kind != VAR:
        raise AssertionError(f"compiled `{name}` as {kind}, but it resolves as {now} now")
    if kind in WORDS and (now_value[0] != value[0] or now_value[1] is not value[1]):
        raise AssertionError(f"compiled `{name}` as the {value[0]} it was, but it is another entry now")


def _fuse(core: StackerCore, instructions: list[Instruction]) -> list[Instruction]:
    """Joins the instructions that the interpreter's words read together into one.

    ``:name set`` (or ``=``): a symbol pushed and taken right back by `set`
    becomes SET, which binds the name without the push, as long as the word
    is the built-in run by the interpreter's own handler (``_prio_set``).
    ``{body} do`` and the other control words with their bodies written as
    literals right before them become one instruction run by
    ``stacker.engine.inline``, as long as the word is the built-in. The
    fused instruction stands at the word's position: what came before it
    has run when the instruction is done, so the interpreter finishing a
    run from the next token is right.

    Args:
        core: The core the block is compiled on.
        instructions: The instructions, one per token.

    Returns:
        The instructions with the fusions made.
    """
    fused: list[Instruction] = []
    for instruction in instructions:
        if instruction.kind == WORD and instruction.value[0] == _PRIORITY:
            name = instruction.name
            if (
                name in _SET_WORDS
                and core._PRIORITY_HANDLERS.get(name) is _handler_of(SET)
                and fused
                and fused[-1].kind == CONST
                and type(fused[-1].value) is Symbol
            ):
                symbol = fused.pop()
                fused.append(Instruction(SET, instruction.index, name, (instruction.value, symbol.value)))
                continue
            if name in _CONTROL_WORDS and _is_builtin_control(core, name, instruction.value):
                kind, bodies = _CONTROL_WORDS[name]
                if len(fused) >= bodies and all(step.kind == BLOCK for step in fused[-bodies:]):
                    indexes = tuple(step.index for step in fused[-bodies:])
                    del fused[-bodies:]
                    fused.append(Instruction(kind, instruction.index, name, (instruction.value, *indexes)))
                    continue
            if name == "times" and len(fused) >= 2 and _is_builtin_control(core, name, instruction.value):
                # `{body} n times`: the count must be a number literal or a variable, so that the body is
                # on the stack whenever the count turns out to be something the word has to look at
                body, count = fused[-2], fused[-1]
                if body.kind == BLOCK and (
                    (count.kind == CONST and type(count.value) in inline.COUNTS) or count.kind == VAR
                ):
                    del fused[-2:]
                    fused.append(
                        Instruction(TIMES, instruction.index, name, (instruction.value, body.index, count.kind, count.name, count.value))
                    )
                    continue
        fused.append(instruction)
    return fused


def compile_block(core: StackerCore, tokens: TokenList, entries: list[tuple[int, object, object]]) -> object:
    """Compiles ``tokens`` against ``core``'s tables and scopes, and remembers the unit on the list.

    Args:
        core: The core the block is running on.
        tokens: The block's token list.
        entries: Its classification (``tokens.classification()``).

    Returns:
        The unit; UNCOMPILABLE when the unit would gain nothing over the
        interpreter (ONLY_WORTHWHILE) or when the compiler itself failed
        (logged at DEBUG, never shown); None when the host ran out of depth
        or memory, to try again on a later run.
    """
    try:
        resolved = [_instruction(core, i, kind, token, payload) for i, (kind, token, payload) in enumerate(entries)]
        instructions = _fuse(core, resolved)
        kinds = {step.kind for step in instructions}
        if ONLY_WORTHWHILE and (kinds.isdisjoint(WORTHWHILE) or not kinds.isdisjoint(OVERWHELMING)):
            unit: object = UNCOMPILABLE  # (the interpreter does as well for these tokens, without a unit's entry cost)
        else:
            unit = Unit(instructions, core)
    except (RecursionError, MemoryError):
        unit = None
        tokens._runs = 0
    except Exception:  # a fault in the compiler must not reach the program...
        if VERIFY:  # ...except under test, where it has to be seen
            raise
        _LOGGER.debug("a block of %d tokens is left to the interpreter: its compiler failed", len(tokens), exc_info=True)
        unit = UNCOMPILABLE
    tokens._unit = unit
    return unit


def _rewarm(tokens: TokenList, unit: Unit) -> None:
    """Forgets ``unit`` before it ran: the block counts its runs again."""
    if tokens._unit is unit:
        tokens._unit = None
        tokens._runs = 0
