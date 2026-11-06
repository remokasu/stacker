"""Runs Stacker code as a stack machine: one loop, and a return stack of its own.

The interpreter used to run a block by calling a Python function for it,
and a function call, a loop body, a condition or a `try` body by calling
another one inside it: every level of a Stacker program was a level of the
host's call stack, and the host's limit on that stack was the limit on
how deep a Stacker recursion could go. Here the levels are *activations*
kept by this module, and the one function ``run`` works through them in a
loop. A function call, a block run by `if`, `eval` or a loop, a `try`:
each pushes an activation and the loop goes on with it; when it ends, the
loop picks up the one below. The host's stack does not grow.

An activation is either a code activation, which walks a list of
instructions, or a control activation, which has no instructions of its
own but a continuation: it pushes a child (a loop body, a condition, the
handler of a `try`) and decides what to do when the child ends. The kinds:

- ``TOP``: the tokens the machine was entered with (an expression typed at
  the prompt, an included file's expression, a block a Python word runs)
- ``BLOCK``: a block run where it stands, on the caller's stack: the arm of
  `if`, a loop's body, a condition, `eval`
- ``CALL``: the body of a function or a lambda, on a new stack of its own
- ``TRANSIENT``: a name run as `eval` runs a symbol: a one-token list
- ``CATCHER``: the body of `try` / `iferror` when it is a block: a BLOCK that
  catches the errors raised inside it itself (the handler then runs where
  the word was)
- ``LOOP``: `do` `dolist` `times` `while` `loop`, running their body again
  and again (the body is a child; the loop variable's scope is made here)
- ``COND``: `if` `ifelse` `cond` while a condition block runs
- ``TRY``: `try` `iferror` while the body or the handler runs
- ``COLLECT``: `collect`, gathering what its child leaves on a fresh stack

What a program leaves behind is what the interpreter left: the stack, the
output, the error and its message, the trace, the warnings. The words
read their arguments through the same functions (``_do_arguments``,
``_condition_left``, ``_name_of`` ...) and errors are reworded by the same
ones (``_report_underflow``, ``_reword_type_error``,
``_reraise_type_error``). Only the machinery between them changed.

Two instruction streams are walked: the *generic* one, the tokens'
classification, resolving every name as it comes (``StackerCore._evaluate``
did this), and the *resolved* one, the unit the compiler made of a block
that ran often (``stacker.engine.compiler``), with its guards: when a
guard fails in mid-run the activation goes on with the generic stream from
the next token, in place, as the interpreter used to finish such a block.

A core is handed to a Python word (``_run_word``) only when the word reads
the running scope or position (the categories in ``NEEDS_VIEW``); a word
that takes values and gives values gets the block's own core, whose
tables are the same. For a call or a loop iteration, the core with the
activation's scope is made the first time such a word needs it, not for
every call, as before.

Errors are caught in one place. The activations are taken down one by
one, each applying what the function that used to run it applied: a
function call leaves the recursion guard and renames the host's depth
error, a block hands its trace to the one that ran it, a `try` body
catches, a loop body catches `break`, a word rewords an underflow or a
type error as its own. A `break` is caught by the innermost loop whose
body is running; one that reaches the bottom leaves the machine, for the
entry point to report.

The machine is re-entered where a Python word runs Stacker code (a
plugin, a word re-registered in Python, ``_pop_arg`` evaluating a block in
a value's place, a macro expansion): that nested run keeps the host's
depth for as long as the word runs, and no longer.
"""

from __future__ import annotations

from itertools import islice
from typing import TYPE_CHECKING

from stacker.data_type import Symbol, stack_data

# core imports this module: its names are read at call time only
from stacker.engine import compiler, copier, inline
from stacker.engine import core as _core
from stacker.engine import include as _include_module
from stacker.engine.compiler import (
    _PLAIN,
    BAD,
    BAD_LIST,
    CONST,
    CONTROL,
    DO,
    DOLIST,
    FAST1,
    FAST2,
    IF,
    IFELSE,
    LIST,
    LIT,
    MACRO,
    RESOLVED,
    SET,
    TIMES,
    UNDEF,
    VAR,
    WORD,
)
from stacker.engine.compiler import (
    BLOCK as R_BLOCK,
)
from stacker.engine.compiler import (
    CALL as R_CALL,
)
from stacker.engine.primitives import if_else, loop
from stacker.engine.primitives.hof import hof_operators
from stacker.engine.primitives.include import include_operators
from stacker.engine.sfunction import StackerFunction
from stacker.engine.slambda import LAMBDA_NAME, StackerLambda
from stacker.error import (
    BreakException,
    MacroExpansionError,
    NoValueProducedError,
    ResultCountError,
    StackerError,
    StackerRecursionError,
    StackerSyntaxError,
    StackerTypeError,
    StackUnderflowError,
    attach_macro_context,
    error_kind,
)
from stacker.lang import generation, recursion
from stacker.lang.arguments import integer_argument
from stacker.lang.scope import ScopedVariables
from stacker.syntax.parser import parse_expression
from stacker.syntax.token_rules import cached_literal_eval

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore

# The kinds of activation. The code kinds walk instructions; the control
# kinds have a continuation
TOP = 0
BLOCK = 1
CALL = 2
TRANSIENT = 3
ELEMENT = 4  # a block run for one element of `map` / `filter`, on a stack of its own
MACRO_RUN = 5  # the expansion of a macro, run where the macro was called
EXPAND = 6  # a macro's body, run on its expander for the expansion
CATCHER = 7  # the body of `try` / `iferror` as a block: a BLOCK that catches the errors raised inside it itself
LOOP = 10
COND = 11
TRY = 12
COLLECT = 13
MAP = 14  # `map` / `filter`: one child per element
REDUCE = 15  # `reduce` / `fold`: one child per element, with the accumulator
INCLUDE = 16  # `include` / `require`: one child per expression of the file
ARGS = 17  # a word with a block in a value's place: the block runs first, its value takes its place

#: The phases of a control activation: not started yet, or which child is running
START = -1
BODY = 0
CONDITION = 1
HANDLER = 2

#: The operator categories whose words read the running core (its scope, its position, its trace) and so
#: must be handed the core bound to the activation's scope; the others take values and give values and are
#: handed the block's own core, whose tables are the same (``_run_word`` and the executors in core.py)
NEEDS_VIEW = frozenset({"priority", "system", "settings", "hof", "transform", "aggregate"})

#: The words the machine runs itself, as long as each is the built-in: its entry holds the original
#: function (``None`` for the words that have none) and the interpreter's handler for it is the original
_ORIGINAL_FUNCS: dict[str, object] = {
    **inline.ORIGINALS,
    "cond": if_else.condition_operators["cond"]["func"],
    "try": if_else.condition_operators["try"]["func"],
    "iferror": if_else.condition_operators["iferror"]["func"],
    "set": None,
    "=": None,
    "global": None,
    "eval": None,
    "collect": None,
    "apply": None,
    "break": None,
    "macroexpand": None,
    "include": include_operators["include"]["func"],
    "require": include_operators["require"]["func"],
    "throw": if_else.condition_operators["throw"]["func"],
    "exit-code": None,
}
#: The categories whose words take their arguments as values (``_pop_arg``): a block in a value's place runs first
_TAKES_VALUES = frozenset({"regular", "stack", "system", "file", "plugin"})
#: The places, from the top of the stack, where these priority words read a value: a block there runs first.
#: ``"arg"`` is read as ``_pop_arg`` reads (one value), ``"eval"`` as ``_pop_and_eval`` (nothing is VOID, many spill)
_ARG_PLACES: dict[str, tuple[tuple[int, str], ...]] = {
    "do": ((-3, "arg"), (-4, "arg")),  # below the body and the name: the last value, then the first
    "dolist": ((-3, "arg"),),
    "times": ((-1, "eval"),),
    "cond": ((-1, "arg"),),
    "apply": ((-2, "eval"),),
    "throw": ((-1, "arg"), (-2, "arg")),
    "exit-code": ((-1, "arg"),),
}
#: The higher-order words the machine runs itself, with the original function of each entry
_HOF_FUNCS: dict[str, object] = {name: hof_operators[name]["func"] for name in ("map", "filter", "reduce", "fold")}

_MISSING = object()
#: A list the tests set to record every admission of a unit: ``(tokens, admitted)``, admitted being True when
#: the unit was taken on trust without the checks made on entry. None outside the tests
_admissions: list | None = None
# The core's classification kinds and helpers, bound into this module's globals by ``_bind_core`` at the first
# run: core.py is still being imported when this module is, so they cannot be imported above
K_VALUE = K_BLOCK_VALUE = K_STRING = K_DYNAMIC = K_LIST = K_SYMBOL = K_BLOCK = -1
WORD_FUNCTION = WORD_PLUGIN = ""
TokenList = StackerCore = None  # type: ignore[assignment]
HOST_ERRORS: tuple = ()
VOID = None
_bound = False


def _bind_core() -> None:
    """Copies the core's constants into this module's globals (once)."""
    global K_VALUE, K_BLOCK_VALUE, K_STRING, K_DYNAMIC, K_LIST, K_SYMBOL, K_BLOCK, WORD_FUNCTION, WORD_PLUGIN
    global TokenList, StackerCore, HOST_ERRORS, VOID, _bound
    K_VALUE, K_BLOCK_VALUE, K_STRING, K_DYNAMIC = _core.K_VALUE, _core.K_BLOCK_VALUE, _core.K_STRING, _core.K_DYNAMIC
    K_LIST, K_SYMBOL, K_BLOCK = _core.K_LIST, _core.K_SYMBOL, _core.K_BLOCK
    WORD_FUNCTION, WORD_PLUGIN = _core.WORD_FUNCTION, _core.WORD_PLUGIN
    TokenList, StackerCore = _core.TokenList, _core.StackerCore
    HOST_ERRORS, VOID = _core._HOST_ERRORS, _core.VOID
    _bound = True


#: Returned by the code activations when they ran to their end
_ENDED = object()


#: How many values a fused control word needs on the stack besides its literal bodies (``inline``'s checks)
_NEEDED = {DO: 3, DOLIST: 2, IF: 1, IFELSE: 1, compiler.LOOP: 0, compiler.WHILE: 0}


class _Arm:
    """A block literal fused with the control word that runs it (``compiler._fuse``): run in the scope of the block around it."""

    __slots__ = ("block", "scope")

    def __init__(self, block: StackerCore, scope: ScopedVariables) -> None:
        self.block = block
        self.scope = scope


#: name -> (the original function of its entry, the interpreter's own handler), filled when first needed (core loads
#: after this module)
_ORIGINALS: dict[str, tuple[object, object]] = {}


def _is_builtin(core: StackerCore, name: str, entry: dict) -> bool:
    """Whether ``name``, a priority word with ``entry``, is the built-in the machine knows how to run."""
    if not _ORIGINALS:
        handlers = _core.StackerCore._PRIORITY_HANDLERS
        _ORIGINALS.update({word: (func, handlers[word]) for word, func in _ORIGINAL_FUNCS.items()})
    func, handler = _ORIGINALS[name]
    return entry["func"] is func and core._PRIORITY_HANDLERS.get(name) is handler


#: The activation whose code or continuation is running, or None outside the machine. ``recursion._depth`` is its
#: depth, written with it when the machine switches activations; the arms of `if` it runs in place are counted by
#: whoever reads the depth from outside (``recursion.get_depth``, a machine started inside a Python word). Both
#: hold wherever a Python word can run; between a child's end and the next switch they are still the child's
_current: Frame | None = None


class Frame:
    """One activation: what it runs, where, and what to do when it ends or an error passes it.

    Slots, every one written when the activation is made: an activation's
    fields are read and written some forty times while it runs, and a slot
    is read or written in a third of the time a dictionary entry takes.
    """

    __slots__ = (
        "arms",  # the arms of `if` / `ifelse` this activation is inside, innermost last (tuples), or None
        "core",  # the core handed to Python words: the template when it is bound to ``scope``, else made on demand
        "depth",  # how many activations are below this one
        "entries",  # the classification of ``tokens``
        "epoch",  # generation.epoch as last compared by this resolved activation
        "index",  # the position of the instruction that pushed the running child (for the guard on return)
        "interp",  # the macro expansion scope whose names block literals interpolate, or None
        "it",  # the iterator over the instructions (code activations)
        "kind",  # TOP, BLOCK, CALL, TRANSIENT, LOOP, COND, TRY, COLLECT
        "name",  # a CALL's name for the recursion guard
        "owner",  # for a control activation, the nearest code activation below: where its trace goes (None: itself)
        "parent",  # the activation below (None for the bottom)
        "resolved",  # whether ``it`` walks a unit's steps (True) or the classification (False)
        "scope",  # the scope names are read in
        "stack",  # the stack values are pushed on
        "state",  # kind-specific: a LOOP's state, a TRY's saved stack, a COLLECT's stack, a CALL's result flag
        "tail",  # the CALL activation that ends when this one ends: what a tail call replaces (None for a call: itself)
        "tailpos",  # whether the steps being walked are the last of ``tail``'s body (an arm run in place may not be)
        "template",  # the core whose tokens run (its tables, position and class)
        "tokens",  # the token list being run (its trace value and, for a TokenList, its unit)
        "trace",  # the trace value of this activation (mirrored into ``core.trace`` when there is a core)
        "unit",  # the unit being walked, or None
        "unit_before",  # the unit the tokens had when the activation began (what a loop may trust next time)
        "word",  # the word of the parent that pushed this activation, for the rewording of its errors
    )

    def __init__(self, kind: int, parent: Frame | None, name: str | None = None) -> None:
        """Makes an activation above ``parent``, one level deeper (the arms ``parent`` runs in place count too).

        Args:
            kind: The activation's kind.
            parent: The activation below, or None at the bottom (the depth then goes on from the running activation's).
            name: For a CALL, the function's name, reported when the depth exceeds the limit.

        Raises:
            StackerRecursionError: The return stack would be deeper than the limit (``recursion.set_limit``).
        """
        self.kind = kind
        self.parent = parent
        # a code activation is its own owner (kept as None: a reference to itself would keep it alive until
        # the cyclic collector ran, and a loop iteration's bound copy is reused only once nothing holds it)
        if parent is None:
            depth = recursion._depth + _arms_running()  # (the depth of the machine this one runs inside, if any)
            self.owner = None
        else:
            depth = parent.depth + 1
            arms = parent.arms
            if arms:
                depth += len(arms)
            if depth > recursion._limit:
                raise _depth_error(kind, parent, name)
            self.owner = None if kind < LOOP else _owner(parent)
        self.depth = depth
        # (``it``, ``unit`` and ``epoch`` are written by whatever starts the activation on its stream, before
        # anything reads them: _admit, _start, _enter_code, _finish, _loop_next and _splice_arm)
        self.arms = None
        self.core = None
        self.entries = None
        self.index = -1
        self.interp = None
        self.name = None
        self.resolved = False
        self.scope = None
        self.stack = None
        self.state = None
        self.tail = None
        self.tailpos = True
        self.template = None
        self.tokens = None
        self.trace = None
        self.unit_before = None
        self.word = None


def _arms_running() -> int:
    """The arms of `if` the running activation runs in place: in the depth, but not in ``recursion._depth``."""
    current = _current
    return len(current.arms) if current is not None and current.arms else 0


recursion._arms = _arms_running


def _depth_error(kind: int, parent: Frame, name: str | None) -> StackerRecursionError:
    """The error for an activation that would exceed the limit: named after the nearest call or macro, or the word that ran the block."""
    if kind == CALL and name is not None:
        return StackerRecursionError(name, recursion.get_limit(), "function")
    if kind == EXPAND and name is not None:
        return StackerRecursionError(name, recursion.get_limit(), "macro")
    word = None
    frame = parent
    while frame is not None:
        if frame.kind == CALL:
            return StackerRecursionError(frame.name, recursion.get_limit(), "function")
        if frame.kind == EXPAND or frame.kind == MACRO_RUN:
            return StackerRecursionError(frame.name, recursion.get_limit(), "macro")
        if word is None and frame.word is not None:
            word = frame.word  # (the nearest word that ran a block, when no call or macro is on the way)
        frame = frame.parent
    return StackerRecursionError(word if word is not None else "eval", recursion.get_limit(), "word")


#: The kinds of loop, for ``_loop_next``'s fast way round
L_DO, L_TIMES, L_WHILE, L_LOOP = 0, 1, 2, 3


class _LoopState:
    """What a running loop remembers between two runs of its body."""

    __slots__ = ("body", "body_frame", "body_scope", "condition", "condition_frame", "count", "epoch", "kind", "limit", "name", "phase", "trusted", "trusted_condition", "values", "word", "wrap_args")

    def __init__(self, word: str) -> None:
        self.word = word
        self.kind = L_DO if word == "do" or word == "dolist" else L_TIMES if word == "times" else L_WHILE if word == "while" else L_LOOP
        self.body_frame: Frame | None = None  # the body's activation, run again on every iteration
        self.condition_frame: Frame | None = None  # `while`: the condition's
        self.body: object = None
        self.body_scope: ScopedVariables | None = None
        self.name: str | None = None
        self.values = None  # the iterator of `do` / `dolist`
        self.count = 0  # `times`: how often the body ran
        self.limit: object = None  # `times`: the count asked for
        self.condition: object = None  # `while`
        self.phase = START
        self.trusted: compiler.Unit | None = None
        self.trusted_condition: compiler.Unit | None = None
        self.epoch = 0
        self.wrap_args: list | None = None  # the arguments ``_reraise_type_error`` shows for `do` / `dolist` / `times`


def _owner(frame: Frame) -> Frame:
    """The code activation ``frame`` is or belongs to."""
    owner = frame.owner
    return frame if owner is None else owner


def _write_trace(frame: Frame, value: object) -> None:
    """Sets the trace of the code activation ``frame`` (or, for a control activation, of the one it runs in)."""
    frame = _owner(frame)
    frame.trace = value
    core = frame.core
    if core is not None:
        core.trace = value


def _view(frame: Frame) -> StackerCore:
    """The core a Python word is handed for ``frame``: made on first demand for a call or a loop iteration."""
    core = frame.core
    if core is not None:
        return core
    template = frame.template
    if frame.kind == CALL:
        core = copier.shallow_copy(template)
        core.variables = frame.scope
        core.stack = frame.stack
    else:
        # (a bound copy, with a stack of its own: no word reads the running core's ``stack``, the words that
        # take the stack are handed it)
        core = template._bound_to(frame.scope)
    core.trace = frame.trace
    frame.core = core
    return core


class _Poison:
    """Stands in for the scope or the stack of a core handed to a word that must not read them (``compiler.VERIFY``)."""

    __slots__ = ("what",)

    def __init__(self, what: str) -> None:
        self.what = what

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"a word of a category that takes values read the running core's {self.what} ({name})")

    def __getitem__(self, key: object) -> object:
        raise AssertionError(f"a word of a category that takes values read the running core's {self.what}")

    def __len__(self) -> int:
        raise AssertionError(f"a word of a category that takes values read the running core's {self.what}")

    def __iter__(self) -> object:
        raise AssertionError(f"a word of a category that takes values read the running core's {self.what}")

    def __contains__(self, key: object) -> bool:
        raise AssertionError(f"a word of a category that takes values read the running core's {self.what}")


def _poisoned(frame: Frame) -> StackerCore:
    """A copy of the activation's template whose scope and stack fail when read: what a word that takes values is handed under VERIFY.

    A word of such a category that read the running core's scope or stack
    would, outside the tests, read the template's (the wrong ones): here
    it fails instead, so the category table (``NEEDS_VIEW``) is checked by
    every test that runs in the eager state.
    """
    template = frame.template
    core = type(template).__new__(type(template))  # (not a copy the engine makes: the tests count those)
    core.__dict__.update(template.__dict__)
    core.variables = _Poison("scope")
    core.stack = _Poison("stack")
    return core


def _core_for(frame: Frame, kind: str) -> StackerCore:
    """The core to run a word of category ``kind`` on."""
    core = frame.core
    if core is not None:
        return core
    if kind in NEEDS_VIEW:
        return _view(frame)
    if compiler.VERIFY:
        return _poisoned(frame)
    return frame.template


def _reworded(core: StackerCore, word: str, error: BaseException) -> BaseException:
    """The error ``word``'s runner would have let out for ``error`` raised while the word ran (``_run_word``)."""
    try:
        if isinstance(error, IndexError):
            core._report_underflow(word, error)
        elif isinstance(error, TypeError):
            _core._reword_type_error(word, error)
    except (StackerError, IndexError, TypeError) as replacement:  # the reworded error, or the same one raised again
        return replacement
    return error


def _rewrapped(word: str, args: list, error: BaseException) -> BaseException:
    """The error the loop and higher-order words let out for ``error`` from their body (``_reraise_type_error``)."""
    if not isinstance(error, (TypeError, AttributeError)):
        return error
    try:
        _core._reraise_type_error(word, args, error)
    except (StackerError, TypeError, AttributeError) as replacement:  # the reworded error, or the same one raised again
        return replacement
    return error


def _host_depth_error(name: str, error: RecursionError) -> StackerRecursionError:
    """The named error a call reports when the host ran out of depth inside it (``StackerFunction.run``)."""
    replacement = StackerRecursionError(name, recursion.get_limit(), depth=recursion.get_depth())
    replacement.__cause__ = None
    replacement.__suppress_context__ = True
    return replacement


def run(core: StackerCore, tokens: list[object], stack: stack_data[object], *, trace: bool = True, trusted: compiler.Unit | None = None, word: str | None = None) -> None:
    """Runs ``tokens`` on ``stack`` in ``core``'s scope, to their end.

    The one way Stacker code is run. The interpreter's ``_evaluate`` calls
    it, and so, through that, does every Python word that runs a block.

    The two instruction streams are walked here, in one function: the
    activation's scope, stack, template and iterator are local variables
    while it runs, saved on the activation when a child is pushed and read
    back when the child ends. Switching activations costs no host call.

    Args:
        core: The core whose scope, tables and trace the tokens run with.
        tokens: The tokens (a block's ``TokenList``, or a list built for the occasion).
        stack: The stack to run on.
        trace: Whether ``core.trace`` becomes ``tokens`` first (not read when ``word`` is given).
        trusted: A unit of ``tokens`` that ran them to their end just before, for a loop running them again
            (not read when ``word`` is given).
        word: One of the machine's own words to run once on ``stack`` instead of ``tokens`` (the bridge a control
            word's Python function crosses when it is called from Python: ``StackerCore._run_built_in``).

    Raises:
        BreakException: A `break` with no loop around it inside these tokens.
        Exception: Whatever the code raised, reworded as the words it passed would have.
    """
    global _current
    if not _bound:
        _bind_core()
    depth0 = recursion._depth
    current0 = _current
    including = core._includes.stack
    including0 = len(including)
    frame = Frame(TOP, None)
    frame.template = core
    frame.core = core
    frame.scope = core.variables
    frame.stack = stack
    missing = _MISSING
    plain = _PLAIN
    host_errors = HOST_ERRORS
    void = VOID
    verify = compiler.VERIFY  # (set before a run, by the tests)
    # the word tables of the generic stream are the interpreter's, shared by every block of it: read once,
    # and again only for a block of another interpreter (its dispatch table is rebuilt when a word is
    # registered: read each time). A unit's guards read the unit's own manager, the one it was resolved against
    manager = core.operator_manager
    macros = core.macros
    sfunctions = core.sfunctions
    plugins = core.plugins
    try:
        if word is None:
            _enter_code(frame, tokens, trusted, trace)
        else:
            # nothing of its own to walk: the word's activation runs, and when it ends this one is over
            # (``epoch`` stays unset, read only while ``resolved`` is true; the entry passed is the one
            # registered under the word, which these words' handlers do not read)
            frame.tokens = tokens
            frame.entries = []
            frame.resolved = False
            frame.unit = None
            frame.it = iter(())
            child = _MACHINE_WORDS[word](frame, word, manager.dispatch_table[word][1], stack)
            if child is None:
                return
            frame = child
        while True:
            # ``frame`` is always the activation whose code or continuation is running, so an error raised
            # below is taken down from it
            try:
                while True:
                    _current = frame  # (the depth is written once per switch of activation: a Python word may read it)
                    recursion._depth = frame.depth
                    if frame.kind >= LOOP:
                        frame = _continue(frame)
                        continue
                    template = frame.template
                    scope = frame.scope
                    stack = frame.stack
                    child = None
                    if frame.resolved:
                        # --- the resolved stream: a unit's steps, with its guards (as compiler.run had them).
                        # The iterator, the unit, its tokens and the epoch are registers here: an arm of `if`
                        # whose unit can run now is run in place by swapping them (the parent's are put aside
                        # on ``arms``), so the arm costs no activation
                        it = frame.it
                        unit = frame.unit
                        tokens = frame.tokens
                        epoch = frame.epoch
                        arms = frame.arms
                        tailpos = frame.tailpos
                        spliced = False
                        while True:
                            for kind, index, name, value in it:
                                if verify:
                                    if kind in RESOLVED:
                                        compiler._check(_view(frame), kind, name, value)
                                    elif kind == PYWORD or kind == TWORD or kind == VWORD:
                                        compiler._check(_view(frame), WORD, name, (value[0], value[1]))
                                    elif kind == MWORD:
                                        compiler._check(_view(frame), WORD, name, ("priority", value[1]))
                                        if not _is_builtin(_view(frame), name, value[1]):
                                            raise AssertionError(f"compiled `{name}` as the machine's own, but it is not the built-in now")
                                if kind == FAST2:
                                    # a regular word on two plain values: popped and called here, as _exec_regular
                                    # would, with the same wrapping of a host error; anything else goes through the
                                    # word runner
                                    entry = value[1]
                                    if len(stack) >= 2 and type(stack[-1]) in plain and type(stack[-2]) in plain:
                                        second = stack.pop()
                                        first = stack.pop()
                                        try:
                                            result = entry["func"](first, second)
                                        except host_errors as error:
                                            _core._host_error_as_the_words(name, [first, second], error)
                                        if entry["push_result_to_stack"] and result is not void:
                                            stack.append(result)
                                    elif (stack and isinstance(stack[-1], StackerCore)) or (len(stack) > 1 and isinstance(stack[-2], StackerCore)):
                                        if arms:
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                        frame.epoch = epoch
                                        frame.index = index
                                        child = _word(frame, name, value[0], entry)
                                        if child is not None:
                                            break
                                    else:
                                        _core_for(frame, value[0])._run_word(name, value[0], entry, stack)
                                elif kind == FAST1:
                                    entry = value[1]
                                    if stack and type(stack[-1]) in plain:
                                        first = stack.pop()
                                        try:
                                            result = entry["func"](first)
                                        except host_errors as error:
                                            _core._host_error_as_the_words(name, [first], error)
                                        if entry["push_result_to_stack"] and result is not void:
                                            stack.append(result)
                                    elif stack and isinstance(stack[-1], StackerCore):
                                        if arms:
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                        frame.epoch = epoch
                                        frame.index = index
                                        child = _word(frame, name, value[0], entry)
                                        if child is not None:
                                            break
                                    else:
                                        _core_for(frame, value[0])._run_word(name, value[0], entry, stack)
                                elif kind == CONST or kind == LIT:
                                    stack.append(value)
                                    continue
                                elif kind == VAR:
                                    found = scope.get(name, missing)
                                    if found is not missing:
                                        stack.append(found)
                                        continue
                                    # gone: the name means what it means now
                                    if arms:
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                    frame.epoch = epoch
                                    frame.index = index
                                    child = _push_transient(frame, [name], None, False)
                                    break
                                elif kind == TWORD:
                                    # a Python word that reads nothing of the running core (what the eager state's poisoned
                                    # core checks): run on the template, whichever core the activation has
                                    wkind, entry = value
                                    (_poisoned(frame) if verify else template)._run_word(name, wkind, entry, stack)
                                elif kind == VWORD:
                                    # a Python word that reads the running core: run on its view, made on first demand
                                    wkind, entry = value
                                    wcore = frame.core
                                    if wcore is None:
                                        wcore = _view(frame)
                                    wcore._run_word(name, wkind, entry, stack)
                                    wcore = None  # (not kept: a loop iteration's bound copy is reused only while nothing else holds it)
                                elif kind == PYWORD:
                                    # a Python word that takes values: it pushes no activation, unless a block stands where
                                    # it reads a value
                                    wkind, entry, count = value
                                    if (
                                        stack
                                        and (
                                            isinstance(stack[-1], StackerCore)
                                            or (count > 1 and len(stack) > 1 and isinstance(stack[-2], StackerCore))
                                            or (count > 2 and _block_among(stack, count))
                                        )
                                    ):
                                        if arms:
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                        frame.epoch = epoch
                                        frame.index = index
                                        child = _word(frame, name, wkind, entry)
                                        if child is not None:
                                            break
                                    else:
                                        wcore = frame.core
                                        if wcore is None:
                                            wcore = _view(frame) if wkind in NEEDS_VIEW else (_poisoned(frame) if verify else template)
                                        wcore._run_word(name, wkind, entry, stack)
                                        wcore = None  # (not kept: a loop iteration's bound copy is reused only while nothing else holds it)
                                elif kind == MWORD:
                                    # a built-in the machine runs itself (eval, set, if, try, ...), as _word would run it
                                    if arms:
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                    frame.epoch = epoch
                                    frame.index = index
                                    handler, entry = value
                                    try:
                                        child = handler(frame, name, entry, stack)
                                    except IndexError as error:
                                        template._report_underflow(name, error)
                                    except TypeError as error:
                                        _core._reword_type_error(name, error)
                                    if child is not None:
                                        break
                                elif kind == R_CALL or kind == WORD:
                                    # a priority word (maybe one the machine runs itself), or the function's own
                                    # call without the general word runner in between
                                    if arms:
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                    frame.epoch = epoch
                                    frame.index = index
                                    child = _word(frame, name, value[0], value[1])
                                    if child is not None:
                                        break
                                elif kind == SET:
                                    # the symbol and `set` as one step: the name is checked first and the value taken
                                    # after, as _prio_set does; with nothing to take, the word runner reports the shortage
                                    lookup, symbol = value
                                    if stack:
                                        bound = template._name_of(symbol, "set")
                                        template._set_variable(bound, stack.pop(), scope)  # (as _pop_and_resolve takes the value)
                                    else:
                                        stack.append(symbol)
                                        if arms:
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                        frame.epoch = epoch
                                        frame.index = index
                                        child = _word(frame, name, lookup[0], lookup[1])
                                        if child is not None:
                                            break
                                elif kind == R_BLOCK:
                                    stack.append(tokens[index]._bound_to(scope))
                                    continue
                                elif kind == LIST:
                                    stack.append(template._build_list(value, scope))
                                    continue
                                elif kind == MACRO:
                                    if arms:
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                    frame.epoch = epoch
                                    frame.index = index
                                    child = _expand(frame, name, stack, True)
                                    break
                                elif kind == UNDEF:
                                    raise _core._name_not_found(name)
                                elif kind == BAD:
                                    raise StackerSyntaxError(value)
                                elif kind == BAD_LIST:
                                    stack.append(template._build_list(_core._compile_list_template(name), scope))
                                    continue
                                elif kind in CONTROL:
                                    handled = False
                                    if (kind == IF or kind == IFELSE) and stack:
                                        condition = stack.pop()
                                        if not isinstance(condition, StackerCore):
                                            # a value decides at once: the chosen arm runs in place of the word
                                            handled = True
                                            if condition:
                                                arm = tokens[value[1]]
                                            elif kind == IFELSE:
                                                arm = tokens[value[2]]
                                            else:
                                                arm = None
                                            if arm is not None:
                                                arm_tokens = arm.tokens
                                                arm_unit = arm_tokens._unit
                                                if (
                                                    arm_unit is not None
                                                    and arm_unit is not compiler.UNCOMPILABLE
                                                    and _guards_pass(arm_unit, arm_tokens, scope, template.operator_manager, False)
                                                ):
                                                    # in place: the registers swap, the parent's are put aside
                                                    if arms is None:
                                                        arms = frame.arms = []
                                                    if frame.depth + len(arms) + 1 > recursion._limit:
                                                        raise _depth_error(BLOCK, frame, None)
                                                    arms.append((it, unit, tokens, epoch, name, index, tailpos))
                                                    tailpos = tailpos and index == len(tokens) - 1
                                                    it = iter(arm_unit.steps)
                                                    unit = arm_unit
                                                    tokens = arm_tokens
                                                    epoch = generation.epoch
                                                    frame.trace = tokens
                                                    tcore = frame.core
                                                    if tcore is not None:
                                                        tcore.trace = tokens
                                                        tcore = None
                                                    spliced = True
                                                    break
                                                if arms:
                                                    frame.it = it
                                                    frame.unit = unit
                                                    frame.tokens = tokens
                                                    frame.tailpos = tailpos
                                                frame.epoch = epoch
                                                frame.index = index
                                                child = _push_block(frame, name, arm, scope, stack, None, _in_tail_position(frame))
                                                break
                                        else:
                                            stack.append(condition)  # (the general path takes it again)
                                    if not handled:
                                        if arms:
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                        frame.epoch = epoch
                                        frame.index = index
                                        child = _fused(frame, kind, name, value)
                                        if child is not None:
                                            break
                                else:  # NAME: a raw block, which only a hand-built token list holds
                                    if arms:
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                    frame.epoch = epoch
                                    frame.index = index
                                    child = _push_transient(frame, [name], None, False)
                                    break
                                # a word ran: the world may have changed. One comparison says whether anything did,
                                # anywhere in the process; only then are the two things that matter here looked at
                                if generation.epoch != epoch:
                                    if unit.manager.generation != unit.words or scope.hides_any(unit.not_variables):
                                        frame.it = it
                                        frame.unit = unit
                                        frame.tokens = tokens
                                        frame.tailpos = tailpos
                                        _finish(frame, index)
                                        child = frame  # (the same activation, on the generic stream now)
                                        break
                                    epoch = generation.epoch
                            else:
                                # the steps ran out
                                if arms:
                                    # an arm of `if` ran out: the parent's registers come back, and the guard after
                                    # the word is made as after any word
                                    it, unit, tokens, epoch, _arm_word, index, tailpos = arms.pop()
                                    frame.it = it  # (written back: the activation may be entered again before another write)
                                    frame.unit = unit
                                    frame.tokens = tokens
                                    frame.tailpos = tailpos
                                    frame.trace = tokens
                                    tcore = frame.core
                                    if tcore is not None:
                                        tcore.trace = tokens
                                        tcore = None
                                    if generation.epoch != epoch:
                                        if unit.manager.generation != unit.words or scope.hides_any(unit.not_variables):
                                            frame.it = it
                                            frame.unit = unit
                                            frame.tokens = tokens
                                            frame.tailpos = tailpos
                                            _finish(frame, index)
                                            child = frame
                                            break
                                        epoch = generation.epoch
                                    continue
                                frame.epoch = epoch
                            if spliced:
                                spliced = False
                                continue  # the arm's steps
                            break
                        if child is frame:
                            continue  # (the generic stream takes over, in this activation)
                    else:
                        # --- the generic stream: the tokens' classification, each name resolved as it comes
                        # (as StackerCore._evaluate had it)
                        if template.operator_manager is not manager:
                            manager = template.operator_manager
                            macros = template.macros
                            sfunctions = template.sfunctions
                            plugins = template.plugins
                        for index, (kind, token, payload) in frame.it:
                            if kind == K_VALUE:
                                stack.append(token)
                                continue
                            if kind == K_BLOCK_VALUE:
                                interp = frame.interp
                                if interp is not None:
                                    stack.append(frame.core._interpolate(token, interp))
                                else:
                                    # The block object is shared by every evaluation of this token list; what is
                                    # pushed is the block bound to the scope it is pushed from, so a lambda or a
                                    # `map` body made here keeps this scope (closure)
                                    stack.append(token._bound_to(scope))
                                continue
                            if kind == K_STRING:
                                stack.append(payload)  # a string literal is never a name
                                continue
                            # Macros take precedence over variables and operators
                            if token in macros:
                                frame.index = index
                                child = _expand(frame, token, stack, True)
                                break
                            elif kind == K_DYNAMIC:
                                if (found := scope.get(token, missing)) is not missing:
                                    # A variable reference pushes the value, whatever it is: a lambda is a value too
                                    stack.append(found)
                                elif token in sfunctions:
                                    frame.index = index  # (the position: a call made by the last token is a tail call)
                                    child = _word(frame, token, WORD_FUNCTION, sfunctions[token])
                                    if child is not None:
                                        break
                                elif token in plugins:
                                    if _block_among(stack, plugins[token]["arg_count"]):
                                        frame.index = index
                                        child = _word(frame, token, WORD_PLUGIN, plugins[token])
                                        if child is not None:
                                            break
                                    else:
                                        _core_for(frame, WORD_PLUGIN)._run_word(token, WORD_PLUGIN, plugins[token], stack)
                                elif (entry := manager.dispatch_table.get(token)) is not None:
                                    wkind = entry[0]
                                    if (
                                        (wkind == "priority" and (token in _MACHINE_WORDS or token in _ARG_PLACES))
                                        or wkind == "hof"
                                        or (
                                            wkind in _TAKES_VALUES
                                            and (count := entry[1]["arg_count"]) > 0
                                            and stack
                                            and (
                                                isinstance(stack[-1], StackerCore)
                                                or (count > 1 and len(stack) > 1 and isinstance(stack[-2], StackerCore))
                                                or (count > 2 and _block_among(stack, count))
                                            )
                                        )
                                    ):
                                        frame.index = index
                                        child = _word(frame, token, wkind, entry[1])
                                        if child is not None:
                                            break
                                    else:
                                        # a Python word (its category's executor): it pushes no activation
                                        wcore = frame.core
                                        if wcore is None:
                                            wcore = _view(frame) if wkind in NEEDS_VIEW else (_poisoned(frame) if verify else template)
                                        wcore._run_word(token, wkind, entry[1], stack)
                                        wcore = None  # (not kept: a loop iteration's bound copy is reused only while nothing else holds it)
                                else:
                                    # A literal (classified as a name only when the literal check was skipped or
                                    # deferred) pushes its value; any other name is undefined: an error here
                                    evaluated = cached_literal_eval(token)
                                    if isinstance(evaluated, str):
                                        raise _core._name_not_found(token)
                                    stack.append(evaluated)
                            elif kind == K_LIST:
                                if payload is None:
                                    # Malformed literal: compiled again here so the error is raised at the token
                                    payload = _core._compile_list_template(token)
                                stack.append(template._build_list(payload, scope))
                            elif kind == K_SYMBOL:
                                stack.append(payload)  # the Symbol
                            elif kind == K_BLOCK:
                                _view(frame)._substack(token, stack)
                            else:  # K_INVALID
                                raise StackerSyntaxError(payload)
                    if child is not None:
                        frame = child
                        continue
                    if not frame.resolved and frame.arms:
                        _leave_arm(frame)  # the rest of an arm of `if`, run by the generic stream, ran out
                        continue
                    # the activation ran to its end: what it leaves goes below, and the one below goes on
                    ended = frame
                    frame = ended.parent
                    ekind = ended.kind
                    if ekind == CALL:
                        caller_stack, push_result, leftovers = ended.state
                        if push_result:
                            if leftovers:
                                caller_stack.extend(leftovers)  # what the calls this one replaced had left
                            caller_stack.extend(ended.stack)  # every value the body left, in order
                    elif ekind == EXPAND:
                        frame = _expanded(ended)  # the expansion: run next, or pushed
                        continue
                    if frame is None:
                        return
                    if frame.kind == LOOP:
                        frame = _loop_next(frame, ended)  # (the body: the same activation, entered again)
                    elif frame.kind > LOOP:
                        frame = _child_ended(frame, ended)
                    elif frame.resolved and frame.index >= 0:
                        # the word that pushed the child is done: a resolved activation checks its guards now
                        index = frame.index
                        frame.index = -1
                        if generation.epoch != frame.epoch:
                            _guard_after(frame, index)
                    ended = None  # (not kept: a bound copy is reused only while nothing else holds it)
            except BreakException as signal:
                frame = _unwind(frame, signal, True)
            except Exception as error:  # noqa: BLE001 -- taken down activation by activation, see _unwind
                frame = _unwind(frame, error, False)
    finally:
        recursion._depth = depth0
        _current = current0
        del including[including0:]  # (an exit or an interrupt left files on the way)


def _enter_code(frame: Frame, tokens: list[object], trusted: compiler.Unit | None, write_trace: bool) -> None:
    """Prepares the code activation ``frame`` to walk ``tokens``: by the block's unit when it has (or now gets) one, else by the classification."""
    frame.tokens = tokens
    if write_trace:  # (a code activation is its own owner)
        frame.trace = tokens
        core = frame.core
        if core is not None:
            core.trace = tokens
    template = frame.template
    if isinstance(tokens, TokenList):
        unit = tokens._unit
        frame.unit_before = unit
        if template._compiles and template._interp_scope is None:
            if unit is None and compiler.THRESHOLD is not None:
                runs = tokens._runs + 1
                tokens._runs = runs
                if runs >= compiler.THRESHOLD:
                    unit = compiler.compile_block(_view(frame), tokens, tokens.classification())
            if unit is not None and unit is not compiler.UNCOMPILABLE and _admit(frame, tokens, unit, unit is trusted):
                return
        frame.entries = entries = tokens.classification()
        core = frame.core
        frame.interp = core._interp_scope if core is not None and tokens is core.tokens else None
    else:
        frame.entries = entries = _core._classify_tokens(tokens)
        frame.interp = None
    frame.resolved = False
    frame.unit = None
    frame.it = enumerate(entries)


def _start(child: Frame, template: StackerCore, tokens: list[object], trusted: compiler.Unit | None) -> None:
    """Starts the activation ``child`` on a block's own token list (its trace is already written).

    The lean form of ``_enter_code`` for the pushes made most: a unit that
    is there is admitted through the guards; a block counted often enough
    is compiled; anything else walks the classification.
    """
    # (a unit that is there is run without asking whether ``template`` compiles or is a macro expander, as
    # ``_enter_code`` asks: the blocks pushed here are values and bodies, never an expander, and a unit of a
    # non-compiling interpreter cannot exist. The guards refuse a unit of another interpreter either way)
    unit = tokens._unit
    if unit is None:
        if compiler.THRESHOLD is not None and template._compiles and template._interp_scope is None:
            runs = tokens._runs + 1
            tokens._runs = runs
            if runs >= compiler.THRESHOLD:
                unit = compiler.compile_block(_view(child), tokens, tokens.classification())
                if unit is not None and unit is not compiler.UNCOMPILABLE and _admit(child, tokens, unit, False):
                    return
    elif unit is not compiler.UNCOMPILABLE and _admit(child, tokens, unit, unit is trusted):
        return
    entries = tokens.classification()
    child.entries = entries
    child.resolved = False
    child.unit = None
    child.it = enumerate(entries)


def _guards_pass(unit: compiler.Unit, tokens: list[object], scope: ScopedVariables, manager: object, admitted: bool) -> bool:
    """Whether the unit may run now in ``scope`` (the checks made on entry, ``compiler.run``'s); a stale unit is rewarmed."""
    if _admissions is not None:
        _admissions.append((tokens, admitted))
    if manager is not unit.manager:
        return False  # another interpreter's block: its words are not this one's
    if admitted:
        return True
    if manager.generation != unit.words:
        compiler._rewarm(tokens, unit)
        return False
    names = unit.not_variables
    if names:
        epoch = generation.epoch
        # the scope's own attributes are read here, not through its methods: this runs on every entry
        if scope._parent is unit.seen_parent and epoch == unit.seen_epoch:
            if not scope._local.keys().isdisjoint(names):
                compiler._rewarm(tokens, unit)
                return False
        else:
            if scope.hides_any(names):
                compiler._rewarm(tokens, unit)
                return False
            unit.seen_parent = scope._parent
            unit.seen_epoch = epoch
    return True


def _splice_arm(frame: Frame, block: StackerCore, word: str, index: int) -> bool:
    """Runs the arm ``block`` of ``word`` (the step at ``index``) inside ``frame`` itself, when its unit can run now.

    The arm runs in the scope and on the stack ``frame`` runs in, so no
    activation is made for it: the activation's iterator, unit, tokens and
    trace are put aside and the arm's take their place, until the arm's
    steps run out (``_leave_arm``). An error inside the arm is reworded as
    the word's, as it would be in an activation of its own, and leaves the
    arm's tokens as the trace, as the innermost failing block's.

    Returns:
        True when the arm was spliced in; False when it has no unit that can run now (then it is pushed).
    """
    tokens = block.tokens
    unit = tokens._unit
    if unit is None or unit is compiler.UNCOMPILABLE or not block._compiles:
        return False
    if not _guards_pass(unit, tokens, frame.scope, block.operator_manager, False):
        return False
    arms = frame.arms
    if arms is None:
        frame.arms = arms = []
    if frame.depth + len(arms) + 1 > recursion._limit:
        raise _depth_error(BLOCK, frame, None)
    arms.append((frame.it, frame.unit, frame.tokens, frame.epoch, word, index, frame.tailpos))
    frame.tailpos = frame.tailpos and index == len(frame.tokens) - 1
    frame.it = iter(unit.steps)
    frame.unit = unit
    frame.tokens = tokens
    frame.entries = None
    frame.epoch = generation.epoch
    frame.resolved = True
    frame.trace = tokens
    core = frame.core
    if core is not None:
        core.trace = tokens
    return True


def _leave_arm(frame: Frame) -> None:
    """The spliced arm's steps ran out: ``frame`` goes on after the word, with its guards checked as after any word."""
    it, unit, tokens, epoch, _word, index, tailpos = frame.arms.pop()
    frame.tailpos = tailpos
    frame.it = it
    frame.unit = unit
    frame.tokens = tokens
    frame.entries = None
    frame.epoch = epoch
    frame.resolved = True  # (an arm is spliced in by a resolved activation only)
    frame.trace = tokens
    core = frame.core
    if core is not None:
        core.trace = tokens
    frame.index = -1
    _guard_after(frame, index)


def _admit(frame: Frame, tokens: list[object], unit: compiler.Unit, admitted: bool) -> bool:
    """Starts ``frame`` on the unit's steps when the guards made on entry pass (``compiler.run``'s), else says no.

    The guards are those of ``_guards_pass``, written out here: this runs
    for every call and every block pushed, and a call costs.
    """
    manager = frame.template.operator_manager
    if _admissions is not None:
        _admissions.append((tokens, admitted))
    if manager is not unit.manager:
        return False  # another interpreter's block: its words are not this one's
    if not admitted:
        if manager.generation != unit.words:
            compiler._rewarm(tokens, unit)
            return False
        names = unit.not_variables
        if names:
            scope = frame.scope
            epoch = generation.epoch
            # the scope's own attributes are read here, not through its methods: this runs on every entry
            if scope._parent is unit.seen_parent and epoch == unit.seen_epoch:
                if not scope._local.keys().isdisjoint(names):
                    compiler._rewarm(tokens, unit)
                    return False
            else:
                if scope.hides_any(names):
                    compiler._rewarm(tokens, unit)
                    return False
                unit.seen_parent = scope._parent
                unit.seen_epoch = epoch
    frame.unit = unit
    frame.epoch = generation.epoch
    frame.resolved = True
    frame.it = iter(unit.steps)
    return True


def _finish(frame: Frame, index: int) -> None:
    """Drops the unit ``frame`` walks, in mid-run, and goes on with the generic stream from the token after ``index``."""
    tokens = frame.tokens
    unit = frame.unit
    if tokens._unit is unit:
        tokens._drops += 1
        tokens._runs = 0
        tokens._unit = compiler.UNCOMPILABLE if tokens._drops >= compiler.GIVE_UP else None
    frame.unit = None
    frame.resolved = False
    frame.index = -1  # (set for the word that just ran: there is no guard to make after it now)
    if frame.entries is None:
        frame.entries = tokens.classification()
    frame.it = enumerate(islice(frame.entries, index + 1, None), index + 1)


def _guard_after(frame: Frame, index: int) -> bool:
    """The check a resolved activation makes after a word ran; True when the unit was dropped and the stream switched."""
    epoch = generation.epoch
    if epoch == frame.epoch:
        return False
    unit = frame.unit
    if frame.template.operator_manager.generation != unit.words or frame.scope.hides_any(unit.not_variables):
        _finish(frame, index)
        return True
    frame.epoch = epoch  # a scope changed shape without hiding a name, or another interpreter's tables moved
    return False


# ---------------------------------------------------------------------------
# Pushing activations
# ---------------------------------------------------------------------------


def _in_tail_position(frame: Frame) -> Frame | None:
    """The call that ends with the step ``frame`` is on (``frame.index``), when that step is the last of what ends it; else None."""
    if frame.kind < LOOP and frame.tailpos and frame.index == len(frame.tokens) - 1:  # (a control activation has no step)
        return frame if frame.kind == CALL else frame.tail  # (a call is its own tail: it keeps no reference to itself)
    return None


def _push_block(frame: Frame, word: str | None, block: StackerCore, scope: ScopedVariables, stack: stack_data[object], trusted: compiler.Unit | None = None, tail: Frame | None = None) -> Frame:
    """Pushes the block ``block`` to run on ``stack`` in ``scope`` (its own scope, or a loop iteration's child of it).

    Args:
        frame: The activation pushing it.
        word: The word that runs it, for the rewording of its errors, or None.
        block: The block.
        scope: The scope it runs in.
        stack: The stack it runs on.
        trusted: A unit of its tokens a loop may admit without the entry checks.
        tail: The call that ends when this block ends (an arm or an `eval` in tail position), or None.
    """
    child = Frame(BLOCK, frame)
    child.tail = tail
    if word is not None:
        child.word = word
    child.template = block
    child.scope = scope
    child.stack = stack
    tokens = block.tokens
    child.tokens = tokens
    child.trace = tokens
    if block.variables is scope:
        child.core = block
        block.trace = tokens
    if trusted is not None:
        child.unit_before = tokens._unit  # (a loop's body: what the next iteration may trust)
    _start(child, block, tokens, trusted)
    return child


def _push_transient(frame: Frame, tokens: list[object], word: str | None, write_trace: bool, stack: stack_data[object] | None = None, tail: Frame | None = None) -> Frame:
    """Pushes a short list of tokens to run as ``frame`` itself would run them (a symbol's name, a name looked up again)."""
    owner = _owner(frame)  # a control activation runs a symbol as the code activation it belongs to would
    child = Frame(TRANSIENT, frame)
    child.tail = tail
    child.word = word
    child.template = owner.template
    child.scope = owner.scope
    child.stack = owner.stack if stack is None else stack
    child.core = owner.core
    if write_trace:
        _write_trace(owner, tokens)  # the symbol's name becomes the running block's trace, and stays
    child.trace = owner.trace
    _enter_code(child, tokens, None, False)
    return child


def _push_call(frame: Frame, word: str | None, name: str, body: StackerCore, params: list[str], args: list[object], stack: stack_data[object], push_result: bool, tail: Frame | None = None) -> Frame:
    """Pushes the body of a function or a lambda, called with ``args``, whose results go to ``stack`` when it ends.

    A call made by the last step of a call's body (or of an arm, an `eval`
    or an `apply` in that position) is a tail call: the activation that
    ends with it is replaced instead of grown, so the return stack does not
    deepen, and what that activation had left on its stack goes to the
    caller under the results when the new call ends.

    Args:
        frame: The activation making the call.
        word: The word the call is reworded as (the function's name, or `eval` for a lambda), or None.
        name: The name the recursion guard reports.
        body: The function's or lambda's body.
        params: Its parameter names.
        args: The arguments, in parameter order.
        stack: The caller's stack, where the results go.
        push_result: Whether the results go there at all.
        tail: The call this one replaces, when the caller has decided it is a tail call; None to decide here.

    Returns:
        The call's activation, ready to run.
    """
    if len(args) != len(params):
        what = "The lambda" if name == LAMBDA_NAME else f"The function `{name}`"
        raise StackerTypeError(f"{what} takes {len(params)} arguments, got {len(args)}")
    if tail is None and frame.kind < LOOP and frame.tailpos and frame.index == len(frame.tokens) - 1:
        tail = frame if frame.kind == CALL else frame.tail  # (a call is its own tail; a control activation has no step)
    if tail is not None and push_result:
        # a tail call: the activation ``tail`` (and anything above it) ends here, replaced by the new call
        caller_stack, _push, leftovers = tail.state
        rest = leftovers or []  # (the replaced call's own list: grown in place, so a run of tail calls is linear)
        rest.extend(tail.stack)
        child = Frame(CALL, tail.parent, name)
        child.state = (caller_stack, True, rest or None)
    else:
        child = Frame(CALL, frame, name)
        child.state = (stack, push_result, None)
    child.word = word
    child.name = name
    child.template = body
    # The arguments are the new scope's names from its birth
    child.scope = body.variables.create_child_scope(dict(zip(params, args)))
    child.stack = stack_data()  # each call has a stack of its own
    tokens = body.tokens
    child.tokens = tokens
    child.trace = tokens
    _start(child, body, tokens, None)
    return child


def _push_code(frame: Frame, word: str | None, code: object, stack: stack_data[object], tail: Frame | None = None) -> Frame | None:
    """Runs ``code`` on ``stack`` as `eval` and every word that runs a block do.

    A block is pushed as an activation, a lambda is called with its
    arguments from ``stack``, a symbol is run as its name, and any other
    value is pushed on ``stack`` as it is.

    Args:
        frame: The activation running the word.
        word: The word, for the rewording of errors, or None.
        code: The block, lambda, symbol or value.
        stack: The stack to run on.
        tail: The call that ends when this code ends (the word stood last in that call), or None.

    Returns:
        The pushed activation, or None when the value was pushed and there is nothing to run.
    """
    if isinstance(code, StackerCore):
        return _push_block(frame, word, code, code.variables, stack, None, tail)
    if isinstance(code, StackerLambda):
        return _call_lambda(frame, word, code, stack, tail)
    if isinstance(code, Symbol):
        return _push_transient(frame, [code.name], word, True, stack, tail)
    stack.append(code)
    return None


def _call_lambda(frame: Frame, word: str | None, fn: StackerLambda, stack: stack_data[object], tail: Frame | None = None) -> Frame:
    """Calls the lambda ``fn`` with arguments popped from ``stack``; every value its body leaves is pushed there.

    Args:
        frame: The activation running the word.
        word: The word, for the rewording of errors, or None.
        fn: The lambda.
        stack: The stack the arguments are on and the results go to.
        tail: The call the lambda replaces when the word that runs it stood last in that call, or None.
    """
    args: list[object] = []
    try:
        for _ in range(fn.arg_count):
            args.insert(0, stack.pop())  # parameters are binding forms: a block is bound raw
    except IndexError:
        raise StackUnderflowError("lambda", fn.arg_count) from None
    return _push_call(frame, word, LAMBDA_NAME, fn.blockstack, fn.args, args, stack, True, tail)


# ---------------------------------------------------------------------------
# Words: the ones the machine runs itself, and the rest through the word runner
# ---------------------------------------------------------------------------


def _word(frame: Frame, name: str, kind: str, entry: dict) -> Frame | None:
    """Runs the word ``name`` looked up as ``kind`` / ``entry``: by the machine when it is a built-in it knows, else by the word runner.

    Returns:
        The activation the word pushed, or None when the word is done.
    """
    stack = frame.stack
    template = frame.template
    if kind == WORD_FUNCTION and isinstance(entry["func"], StackerFunction):
        func = entry["func"]
        try:
            args: list[object] = []
            for _ in range(entry["arg_count"]):
                # Parameters are binding forms: block arguments bind raw (code is data)
                args.insert(0, stack.pop())
        except IndexError as error:
            template._report_underflow(name, error)
        return _push_call(frame, name, func.name, func.blockstack, func.args, args, stack, entry["push_result_to_stack"])
    if kind in _TAKES_VALUES or kind == WORD_PLUGIN:
        if _block_among(stack, entry["arg_count"]):
            return _args(frame, name, tuple((-i - 1, "arg") for i in range(entry["arg_count"])), kind, entry)
        _core_for(frame, kind)._run_word(name, kind, entry, stack)
        return None
    if kind == "priority":
        places = _ARG_PLACES.get(name)
        if places is not None and _is_builtin(template, name, entry) and _block_at(stack, places):
            return _args(frame, name, places, kind, entry)
    if kind == "hof" and name in _HOF_FUNCS and entry["func"] is _HOF_FUNCS[name] and template._CATEGORY_EXECUTORS["hof"] is _core.StackerCore._exec_hof:
        try:
            return _hof(frame, name, stack)
        except IndexError as error:
            template._report_underflow(name, error)
        except TypeError as error:
            _core._reword_type_error(name, error)
    if kind == "priority" and name in _MACHINE_WORDS and _is_builtin(template, name, entry):
        try:
            return _MACHINE_WORDS[name](frame, name, entry, stack)
        except IndexError as error:
            template._report_underflow(name, error)
        except TypeError as error:
            _core._reword_type_error(name, error)
    _core_for(frame, kind)._run_word(name, kind, entry, stack)
    return None


def _set(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> None:
    """`set` / `=`: ``value :name set``."""
    symbol = stack.pop()
    bound = frame.template._name_of(symbol, "set")  # (`=` speaks as `set` does)
    frame.template._set_variable(bound, stack.pop(), frame.scope)


def _global(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> None:
    """`global`: ``value :name global``, always in the root scope."""
    symbol = stack.pop()
    bound = frame.template._name_of(symbol, "global")
    value = stack.pop()  # blocks bind raw (code is data)
    scope = frame.scope
    if bound not in scope.root().own_bindings():
        frame.template._warn_builtin_redefinition(bound)  # a new global hides a word of its name everywhere
    scope.set_global(bound, value)


def _break(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> None:
    """`break`: the signal the innermost loop whose body is running catches (``_unwind``)."""
    raise BreakException()


def _eval(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`eval`: runs the top value as code, never as text."""
    expression = stack.pop()
    if isinstance(expression, str) and not isinstance(expression, Symbol):
        raise StackerTypeError(
            f"`eval` expects a code block, a symbol or a lambda, got the string {str(expression)!r}. "
            "A string is text, not code: turn it into a block with `parse` first, "
            'e.g. "3 4 +" parse eval'
        )
    if isinstance(expression, StackerCore):  # (the usual case: pushed here, without _push_code's other cases)
        if expression.variables is frame.scope and frame.resolved and frame.index >= 0 and _splice_arm(frame, expression, "eval", frame.index):
            frame.index = -1  # in place, as an arm of `if`: the guard after the word is made when the block is left
            return frame
        return _push_block(frame, "eval", expression, expression.variables, stack, None, _in_tail_position(frame))
    return _push_code(frame, "eval", expression, stack, _in_tail_position(frame))


def _apply(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`apply`: ``{args} func apply`` pushes the arguments, then runs the function."""
    template = frame.template
    func = stack.pop()
    args_list = template._pop_and_eval(stack)
    if args_list is _core.VOID:
        pass  # an empty argument block: the function is applied to nothing
    elif isinstance(args_list, (list, tuple)):
        for arg in args_list:
            stack.append(arg)
    elif isinstance(args_list, _core.StackerCore):
        for tok in args_list.tokens:
            stack.append(_core.token_to_value(tok))
    else:
        stack.append(args_list)
    if not isinstance(func, (_core.StackerCore, StackerLambda, Symbol)):
        raise StackerTypeError(template._function_spec_message("apply", func))
    return _push_code(frame, "apply", func, stack, _in_tail_position(frame))


def _collect(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame:
    """`collect`: runs the code on an empty stack, in this scope, and pushes what it left as one list."""
    code = stack.pop()
    if not isinstance(code, (_core.StackerCore, Symbol, StackerLambda)):
        raise StackerTypeError(f"`collect` expects a code block, a symbol or a lambda, got {_core.plain_text(code)}")
    control = Frame(COLLECT, frame)
    control.word = "collect"
    control.stack = stack
    control.state = [START, code, stack_data()]
    return control


def _if(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`if`: ``condition {body} if``."""
    true_block = stack.pop()
    condition = stack.pop()
    return _conditional(frame, "if", stack, condition, true_block, None)


def _ifelse(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`ifelse`: ``condition {true} {false} ifelse``."""
    false_block = stack.pop()
    true_block = stack.pop()
    condition = stack.pop()
    return _conditional(frame, "ifelse", stack, condition, true_block, false_block)


def _cond(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`cond`: ``{c1} {r1} ... n cond``, the first true condition's result runs."""
    template = frame.template
    n = integer_argument("cond", template._pop_arg(stack, "cond"))
    if n < 0:
        stack.append(n)
        raise _core.ValidationError(f"`cond` expects a count of 0 or more, got {n}")
    if len(stack) < 2 * n:
        have = len(stack)
        stack.append(n)
        raise StackUnderflowError(
            "cond", 2 * n,
            f"`cond` needs {2 * n} values below the count ({n} pairs of a condition and a result), "
            f"but the stack has {have}.",
        )
    pairs = []
    for _ in range(n):
        result = stack.pop()
        condition = stack.pop()
        pairs.insert(0, (condition, result))
    if not pairs:
        return None
    first_condition, first_result = pairs[0]
    return _conditional(frame, "cond", stack, first_condition, first_result, None, rest_pairs=pairs[1:])


def _conditional(frame: Frame, word: str, stack: stack_data[object], condition: object, chosen: object, otherwise: object, rest_pairs: list | None = None) -> Frame | None:
    """Makes the activation that tests ``condition`` (a block is run for its value) and runs the arm it chooses; `cond` tries its pairs in turn.

    A condition that is a value decides at once, without an activation.

    Args:
        frame: The activation running the word.
        word: `if`, `ifelse` or `cond`.
        stack: The stack.
        condition: The first condition, a block or a value.
        chosen: What runs when it holds.
        otherwise: What runs when it does not (`ifelse`), or None.
        rest_pairs: The remaining (condition, result) pairs of `cond`, or None.

    Returns:
        The activation to go on with, or None when nothing is left to run.
    """
    if not isinstance(condition, StackerCore) and not rest_pairs:
        if condition:
            return _arm(frame, word, chosen)
        if otherwise is not None:
            return _arm(frame, word, otherwise)
        return None
    control = Frame(COND, frame)
    control.word = word
    control.stack = stack
    # state: the phase, the condition, the arm when true, the arm when false (`ifelse`), the remaining pairs (`cond`)
    control.state = [START, condition, chosen, otherwise, rest_pairs if rest_pairs is not None else []]
    return control


def _test(control: Frame) -> Frame | None:
    """Runs or reads the condition of the COND activation ``control``: a block is pushed, a value decides now."""
    state = control.state
    condition = state[1]
    if isinstance(condition, StackerCore):
        state[0] = CONDITION
        return _push_block(control, None, condition, condition.variables, control.stack)
    return _decide(control, condition)


def _decide(control: Frame, truth: object) -> Frame | None:
    """Chooses the arm of the COND activation ``control`` for ``truth`` and runs it in place of the activation."""
    _phase, _condition, chosen, otherwise, rest = control.state
    parent = control.parent
    word = control.word
    if truth:
        return _arm(parent, word, chosen)
    if word == "ifelse":
        return _arm(parent, word, otherwise)
    if word == "cond" and rest:
        condition, result = rest[0]
        control.state = [START, condition, result, None, rest[1:]]
        return _test(control)
    return _resume(parent)


def _arm(parent: Frame, word: str, code: object) -> Frame | None:
    """Runs the chosen arm ``code`` for the word ``word`` of ``parent``; a value is pushed and the parent resumes."""
    tail = _in_tail_position(parent)
    if type(code) is _Arm:
        if code.scope is parent.scope and parent.index >= 0 and _splice_arm(parent, code.block, word, parent.index):
            parent.index = -1  # (the guard after the word is made when the arm is left)
            return parent
        return _push_block(parent, word, code.block, code.scope, parent.stack, None, tail)
    child = _push_code(parent, word, code, parent.stack, tail)
    return child if child is not None else _resume(parent)


def _try(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame:
    """`try` / `iferror`: ``{body} {handler} try``; the stack is as it was when the word began before the handler runs."""
    handler = stack.pop()
    try_block = stack.pop()
    if isinstance(try_block, StackerCore):
        # the body catches for itself: one activation, whose word is the try's (an error it does not take is reworded
        # as the word's, as the control activation's would be). state: the stack as it was, the handler
        child = _push_block(frame, name, try_block, try_block.variables, stack)
        child.kind = CATCHER
        child.state = (list(stack), handler)
        return child
    control = Frame(TRY, frame)
    control.word = name
    control.stack = stack
    control.state = [START, list(stack), try_block, handler]  # (the body, a lambda or a value, is pushed by the continuation: under the try, so that it catches)
    return control


def _loop_word(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`do` `dolist` `times` `while` `loop`: reads the word's arguments as its handler does and starts the loop."""
    template = frame.template
    state = _LoopState(name)
    if name == "do":
        body = stack.pop()
        start_value, end_value, var = template._do_arguments(stack)
        state.wrap_args = [start_value, end_value]
        try:
            state.values = iter(loop.do_range(start_value, end_value))
            state.body_scope = loop._body_scope("do", body, template)
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error("do", state.wrap_args, error)
        state.body = body
        state.name = var
    elif name == "dolist":
        body = stack.pop()
        items, var = template._dolist_arguments(stack)
        state.wrap_args = [items]
        try:
            state.body_scope = loop._body_scope("dolist", body, template)
            state.values = iter(items)
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error("dolist", state.wrap_args, error)
        state.body = body
        state.name = var
    elif name == "times":
        n_times = template._times_count(stack)
        body = stack.pop()
        state.wrap_args = [n_times]
        try:
            loop.check_times_count(n_times)
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error("times", state.wrap_args, error)
        state.body = body
        state.limit = n_times
    elif name == "while":
        body = stack.pop()
        condition = stack.pop()
        if not isinstance(condition, type(template)):
            raise StackerSyntaxError(f"`while` expects a condition block, got {condition}")
        state.body = body
        state.condition = condition
    else:  # loop
        body = stack.pop()
        if not isinstance(body, type(template)):
            raise StackerSyntaxError(f"`loop` expects a code block, got {body}")
        state.body = body
    control = Frame(LOOP, frame)
    control.word = name
    control.stack = stack
    control.state = state
    return control


def _macroexpand(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame:
    """`macroexpand`: pushes a macro's expansion instead of running it."""
    macro = frame.template._name_of(stack.pop(), "macroexpand")
    if macro not in frame.template.macros:
        raise StackerSyntaxError(f"`macroexpand` expects a macro name, `{macro}` is not a macro")
    return _expand(frame, macro, stack, False)


def _expand(frame: Frame, name: str, stack: stack_data[object], evaluate: bool) -> Frame:
    """Starts the expansion of the macro ``name`` called from ``frame``.

    The body runs on a throwaway core, in a child scope of the caller's
    where the arguments are bound and assignments stay local, with its own
    stack; ``_expanded`` takes the one value it leaves. The recursion guard
    counts the expansion until the expansion's run is over.

    Args:
        frame: The activation that met the macro.
        name: The macro's name (known to be in the tables).
        stack: The caller's stack.
        evaluate: Whether to run the expansion (`macroexpand` pushes it instead).

    Returns:
        The expansion's activation.
    """
    template = frame.template
    macro = template.macros[name]
    args: list[object] = []
    for _ in range(macro.arg_count):
        try:
            args.insert(0, stack.pop())  # blocks stay raw, symbols stay symbols
        except IndexError:
            raise StackUnderflowError(name, macro.arg_count) from None
    parent = _view(frame)  # the expander's parent: where it reads its position and its root
    scope = frame.scope.create_child_scope(dict(zip(macro.args, args)))
    scope._write_barrier = True
    expander = type(parent)(parent=parent)
    expander.tokens = macro.body.tokens  # shared, read-only
    expander.bracket_type = macro.body.bracket_type
    expander.variables = scope
    expander._interp_scope = scope
    expander._interp_name = name
    expander._interp_params = frozenset(macro.args)
    child = Frame(EXPAND, frame, name)
    child.name = name
    child.template = expander
    child.core = expander
    child.scope = scope
    child.stack = stack_data()
    child.state = (stack, evaluate)
    _enter_code(child, expander.tokens, None, True)
    return child


def _expanded(ended: Frame) -> Frame:
    """The macro's body ran: the one value it left is the expansion, run where the macro was called or pushed there.

    Args:
        ended: The EXPAND activation, done.

    Returns:
        The expansion's run (a MACRO_RUN activation), or the caller's activation when the expansion is pushed.

    Raises:
        NoValueProducedError: The body left nothing.
        MacroExpansionError: The body left more than one value.
    """
    caller, evaluate = ended.state
    name = ended.name
    parent = ended.parent
    expansion_stack = ended.stack
    if len(expansion_stack) == 0:
        raise NoValueProducedError(name, f"Macro `{name}` left no value to use as its expansion.")
    if len(expansion_stack) > 1:
        raise MacroExpansionError(name, len(expansion_stack))
    result = expansion_stack.pop()
    # The expansion runs where the macro was called, as if written there
    scope = _owner(parent).scope
    if isinstance(result, StackerCore):
        result = result._bound_to(scope)
    elif isinstance(result, StackerLambda):
        result.blockstack = result.blockstack._bound_to(scope)
    if not evaluate or not isinstance(result, StackerCore):
        caller.append(result)
        return _resume(parent)
    child = Frame(MACRO_RUN, parent)
    child.name = name
    child.template = result
    child.core = result
    child.scope = result.variables
    child.stack = caller
    _enter_code(child, result.tokens, None, True)
    return child


def _hof(frame: Frame, name: str, stack: stack_data[object]) -> Frame:
    """`map` / `filter` / `reduce` / `fold`: reads the word's arguments as its executor does and starts the run over the elements."""
    template = frame.template
    if name == "map" or name == "filter":
        body = stack.pop()
        items_arg = stack.pop()
        spec = _function_spec(frame, body, name)
        items = template._data_items(items_arg, name)
        try:
            it = iter(items)
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error(name, [items], error)
        control = Frame(MAP, frame)
        control.word = name
        control.stack = stack
        # state: the spec, the elements, the elements for the message, the source (for the container pushed),
        # the results, the element on the way, the stack the element's run leaves its value on, the element's
        # activation (made once, entered again for every element), how the function is named in an error
        kind = spec[0]
        who = "the block" if kind == "block" else ("the lambda" if kind == "lambda" else f"`{spec[2]}`")
        control.state = [spec, it, items, items_arg, [], None, None, None, who]
        return control
    body = stack.pop()
    symbol_x = stack.pop()  # Second variable name (element)
    symbol_acc = stack.pop()  # First variable name (accumulator)
    init = stack.pop()
    fold_args = stack.pop()
    if isinstance(body, Symbol):
        body = _view(frame)._block_of([body.name])
    if not isinstance(body, StackerCore):
        raise StackerTypeError(f"`{name}` expects a code block as the function, got {_core.plain_text(body)}")
    name_acc = template._name_of(symbol_acc, name)
    name_x = template._name_of(symbol_x, name)
    items = template._data_items(fold_args, name)
    try:
        it = iter(items)
    except (TypeError, AttributeError) as error:
        _core._reraise_type_error(name, [init, items], error)
    control = Frame(REDUCE, frame)
    control.word = name
    control.stack = stack
    # state: the body, the two names, the elements, the accumulator, the arguments for the message, the step's
    # activation (made once, entered again for every step)
    control.state = [body, name_acc, name_x, it, init, [init, items], None]
    return control


def _function_spec(frame: Frame, spec: object, word: str) -> tuple:
    """What `map` / `filter` run for each element (``StackerCore._resolve_function_spec``), as a kind and its payload.

    Returns:
        ``("block", block)``: the block, run with the element on a stack of its own;
        ``("lambda", fn)``: the lambda, called on the element;
        ``("function", func, name)``: a function written in Stacker, called on the element;
        ``("host", func, name)``: a host word of one argument, called directly.
    """
    template = frame.template
    if isinstance(spec, StackerCore):
        return ("block", spec)
    if isinstance(spec, StackerLambda):
        if spec.arg_count != 1:
            raise StackerTypeError(f"`{word}` expects a lambda of one parameter, got one of {spec.arg_count}")
        return ("lambda", spec)
    if isinstance(spec, Symbol):
        name = spec.name
        if name not in template.macros and frame.scope.get(name, _MISSING) is _MISSING:
            sfunc = template.sfunctions.get(name)
            if sfunc is not None and sfunc["arg_count"] == 1 and sfunc["push_result_to_stack"]:
                func = sfunc["func"]
                if isinstance(func, StackerFunction):
                    return ("function", func, name)
                return ("host", func, name)
            host = template.plugins.get(name)
            if host is None:
                entry = template.operator_manager.dispatch_table.get(name)
                if entry is not None and entry[0] == "regular":
                    host = entry[1]
            if host is not None and host["arg_count"] == 1 and host["push_result_to_stack"]:
                return ("host", host["func"], name)
        return ("block", _view(frame)._block_of([name]))
    raise StackerTypeError(template._function_spec_message(word, spec))


def _map_next(control: Frame, ended: Frame | None) -> Frame:
    """An element's run ended (None: the run starts): takes its value and runs the next element, or pushes the result."""
    state = control.state
    spec, it, _items, items_arg, results, element, result_stack, child, who = state
    word = control.word
    if ended is not None:
        value = result_stack[0] if len(result_stack) == 1 else _core.StackerCore._one_result(result_stack, word, who)
        if word == "map":
            results.append(value)
        elif value:
            results.append(element)
    while True:
        try:
            element = next(it)
        except StopIteration:
            state[7] = None  # (the element's activation points back at this one: let go, as a loop lets its body go)
            parent = control.parent
            if isinstance(items_arg, StackerCore):
                _view(_owner(parent))._push_like(items_arg, results, control.stack)
            elif isinstance(items_arg, tuple):
                control.stack.append(tuple(results))
            else:
                control.stack.append(results)
            return _resume(parent)
        kind = spec[0]
        if kind == "host":
            func, name = spec[1], spec[2]
            template = _owner(control).template
            # The element is prepared as `_run_word` would (a block is evaluated, a String literal is
            # unwrapped), and a type error names the word, as `_run_word` would
            try:
                value = func(template._pop_arg(stack_data([element]), name))
            except (TypeError, AttributeError) as error:
                _core._reraise_type_error(name, [element], error)
            if word == "map":
                results.append(value)
            elif value:
                results.append(element)
            continue
        state[5] = element
        if kind == "block":
            body = spec[1]
            if child is None:
                child = state[7] = Frame(ELEMENT, control)
                child.template = body
                child.core = body
                child.scope = body.variables
                child.stack = result_stack = state[6] = stack_data()
            else:
                result_stack.clear()  # (the element's stack, used again: what the last element left was taken)
            result_stack.append(element)  # the element is pushed as a value, never spliced into the tokens
            if ended is not None and _reenter(child, body):
                return child
            _enter_code(child, body.tokens, None, True)
            return child
        if result_stack is None:
            result_stack = state[6] = stack_data()
        else:
            result_stack.clear()
        results_of_call = result_stack
        if kind == "lambda":
            fn = spec[1]
            body, params, name = fn.blockstack, fn.args, LAMBDA_NAME
        else:
            func = spec[1]
            body, params, name = func.blockstack, func.args, func.name
        if child is None or ended is not child:
            # the first element, or the last element's call ended with a tail call that replaced its activation
            # (what ended is the replacement): the element gets an activation of its own
            child = state[7] = _push_call(control, None, name, body, params, [element], results_of_call, True)
            child.unit_before = body.tokens._unit  # (what the next element may be admitted on without the checks)
            return child
        # the call's activation, entered again for this element: what _push_call sets for a call is set anew
        child.state = (results_of_call, True, None)
        child.scope = body.variables.create_child_scope({params[0]: element})
        child.stack.clear()  # (the call's own stack, used again: what the last call left went to the results)
        child.core = None
        if not _reenter(child, body):
            tokens = body.tokens
            child.trace = tokens
            child.unit_before = tokens._unit
            _start(child, body, tokens, None)
        return child


def _reduce_next(control: Frame, ended: Frame | None) -> Frame:
    """A step's run ended (None: the run starts): takes the new accumulator and runs the next step, or pushes the result."""
    state = control.state
    body, name_acc, name_x, it, acc, _wrap_args, child = state
    if ended is not None:
        acc = state[4] = _core.StackerCore._one_result(ended.stack, control.word, "the block")
    try:
        x = next(it)
    except StopIteration:
        state[6] = None  # (the step's activation points back at this one: let go)
        control.stack.append(acc)
        return _resume(control.parent)
    # Each step runs in a loop scope holding the two names, a child of the body's own scope: a name the body
    # is first to set goes to that scope (see loop_scope)
    scope = ScopedVariables.loop_scope(body.variables, {name_acc: acc, name_x: x})
    if child is None:
        child = state[6] = _push_block(control, None, body, scope, stack_data())
        child.unit_before = body.tokens._unit  # (what the next step may be admitted on without the checks)
        return child
    # the step's activation, entered again (as _push_block sets it, for the new scope)
    child.scope = scope
    child.stack.clear()  # (the step's stack, used again: the accumulator it left was taken)
    child.core = None
    if not _reenter(child, body):
        tokens = body.tokens
        child.trace = tokens
        child.unit_before = tokens._unit
        _start(child, body, tokens, None)
    return child


def _block_among(stack: stack_data[object], count: int) -> bool:
    """Whether a block stands among the top ``count`` values of ``stack`` (the values a word is about to take)."""
    n = len(stack)
    count = min(count, n)
    for i in range(1, count + 1):
        if isinstance(stack[-i], StackerCore):
            return True
    return False


def _block_at(stack: stack_data[object], places: tuple[tuple[int, str], ...]) -> bool:
    """Whether a block stands at one of ``places`` (offsets from the top) of ``stack``."""
    n = len(stack)
    for place, _mode in places:
        if -place <= n and isinstance(stack[place], StackerCore):
            return True
    return False


def _args(frame: Frame, name: str, places: tuple[tuple[int, str], ...], kind: str, entry: object) -> Frame:
    """Starts the word ``name`` whose values include a block: each block runs first, where it stands (``_pop_arg``).

    A block in a value's place is run on its own stack and the one value it
    leaves takes its place (``"arg"``), or, where the word reads with
    ``_pop_and_eval`` (``"eval"``), what it leaves spills there and nothing
    becomes VOID. The blocks run in the order the word would have taken
    them, top first. Then the word runs as written, finding values.

    Args:
        frame: The activation running the word.
        name: The word.
        places: Where it reads values, in reading order.
        kind: The word's kind, or a fused instruction's kind.
        entry: The word's entry, or the fused instruction's value.

    Returns:
        The control activation.
    """
    control = Frame(ARGS, frame)
    control.word = name
    control.stack = frame.stack
    # state: the places, how many were looked at, the word's kind and entry, the place whose block is running
    control.state = [places, 0, kind, entry, None]
    return control


def _args_next(control: Frame, ended: Frame | None) -> Frame | None:
    """A block in a value's place ran (None: the word starts): its value takes its place; the next block runs, or the word.

    The values above the block, which the word pops before reading it, are
    taken off while it runs and put back after (an error inside it then
    finds the stack as the word would have left it); its value goes back
    wrapped (``Taken``), so that the word reads it as it is.
    """
    state = control.state
    places, looked, kind, entry, aside = state
    stack = control.stack
    word = control.word
    if ended is not None:
        sub = ended.stack
        mode = places[looked - 1][1]
        if mode == "arg":
            if not sub:
                raise NoValueProducedError(word, f"The block passed to `{word}` left nothing on the stack.")
            if len(sub) > 1:
                shown = " ".join(_core.plain_text(v) for v in sub)
                sub.clear()  # (so that running the same block again starts clean)
                raise ResultCountError(
                    f"The block passed to `{word}` left {len(shown.split())} values on the stack ({shown}); an argument must be one value"
                )
            stack.append(_core.Taken(sub.pop()))
        elif sub:
            # what the block left spills where it stood, as `_pop_and_eval` spills it; the word reads the top one
            top = sub.pop()
            stack.extend(sub)
            sub.clear()
            stack.append(_core.Taken(top))
        else:
            stack.append(_core.Taken(VOID))  # the word sees that the block left nothing
        stack.extend(reversed(aside))
    n = len(stack)
    while looked < len(places):
        offset = places[looked][0]
        looked += 1
        if -offset > n:
            break  # too few values: the word itself reports it
        block = stack[offset]
        if isinstance(block, StackerCore):
            state[1] = looked
            state[4] = aside = [stack.pop() for _ in range(-offset - 1)]  # what the word pops before this value
            stack.pop()
            child = Frame(ELEMENT, control)
            child.template = block
            child.core = block
            child.scope = block.variables
            child.stack = block.stack  # (the block's own stack, as `_pop_arg` runs it)
            _enter_code(child, block.tokens, None, True)
            return child
    # every block ran: the word runs as written
    parent = control.parent
    if kind in CONTROL:
        child = _fused(parent, kind, word, entry)
    else:
        child = _word(parent, word, kind, entry)
    return child if child is not None else _resume(parent)


def _include(frame: Frame, name: str, entry: dict, stack: stack_data[object]) -> Frame | None:
    """`include` / `require`: starts running the file, expression by expression, by the rule of ``start_include``."""
    filename = stack.pop()
    if not isinstance(filename, str):
        raise StackerTypeError(
            f'`{name}` expects the file path as a string, e.g. "lib.stk" {name}; got {_core.plain_text(filename)}'
        )
    # the view is where relative paths resolve from, and the runner's parent
    started = _include_module.start_include(_view(frame), filename, name == "require")
    if started is None:
        return None
    control = Frame(INCLUDE, frame)  # (made before the file is marked as running: a depth error here leaves no mark)
    started.begin()
    control.word = name
    control.stack = stack_data()  # the file starts with an empty stack; what it leaves there is dropped
    control.state = started
    return control


def _include_next(control: Frame, ended: Frame | None) -> Frame:
    """An expression of the included file ran (None: the file starts): the next one runs, or the file is done."""
    started = control.state
    try:
        expression = next(started.expressions)
    except StopIteration:
        started.stop()
        started.end(control.stack)
        return _resume(control.parent)
    tokens = parse_expression(expression)
    runner = started.runner
    child = Frame(BLOCK, control)  # (an error inside it hands its trace to the including code, as `evaluate` did)
    child.template = runner
    child.core = runner
    child.scope = runner.variables
    child.stack = control.stack
    _enter_code(child, tokens, None, True)
    return child


#: The machine's own kinds of word step, decided once when a unit is made (``_rewrite_steps``): a WORD step the
#: compiler made is kept for a function written in Python, a word of higher order and a built-in that may find a
#: block where it reads a value (through ``_word`` every time)
TWORD = "TWORD"  # a Python word run on the template, never looking for a block in a value's place: value (category, entry)
VWORD = "VWORD"  # a Python word that reads the running core (``NEEDS_VIEW``), no block to look for: value (category, entry)
PYWORD = "PYWORD"  # a Python word that may find a block where it reads a value: value (category, entry, values to look at)
MWORD = "MWORD"  # a built-in the machine runs itself: value (its handler, entry)


def _rewrite_steps(steps: list[tuple], core: StackerCore) -> None:
    """Gives the WORD steps of a new unit the machine's kinds, so that the run loop dispatches them without ``_word``."""
    if not _bound:
        _bind_core()
    for i, step in enumerate(steps):
        if step[0] != WORD:
            continue
        _kind, index, name, (wkind, entry) = step
        if wkind == WORD_FUNCTION or wkind == "hof":
            continue
        if wkind == "priority":
            if name in _ARG_PLACES and _is_builtin(core, name, entry):
                continue  # (a block may stand where the word reads a value: _word looks)
            if name in _MACHINE_WORDS and _is_builtin(core, name, entry):
                steps[i] = (MWORD, index, name, (_MACHINE_WORDS[name], entry))
                continue
            steps[i] = (VWORD, index, name, (wkind, entry))
            continue
        count = entry["arg_count"] if wkind in _TAKES_VALUES or wkind == WORD_PLUGIN else 0
        if count:
            steps[i] = (PYWORD, index, name, (wkind, entry, count))
        elif wkind in NEEDS_VIEW:
            steps[i] = (VWORD, index, name, (wkind, entry))
        else:
            steps[i] = (TWORD, index, name, (wkind, entry))


compiler.REWRITE = _rewrite_steps


_MACHINE_WORDS = {
    "set": _set,
    "=": _set,
    "global": _global,
    "break": _break,
    "eval": _eval,
    "apply": _apply,
    "collect": _collect,
    "if": _if,
    "ifelse": _ifelse,
    "cond": _cond,
    "try": _try,
    "iferror": _try,
    "macroexpand": _macroexpand,
    "include": _include,
    "require": _include,
    "do": _loop_word,
    "dolist": _loop_word,
    "times": _loop_word,
    "while": _loop_word,
    "loop": _loop_word,
}


def _fused(frame: Frame, kind: str, name: str, value: tuple) -> Frame | None:
    """A control word fused with its literal bodies (``compiler._fuse``): the bodies are run without being pushed.

    When the stack is too short for the word's other arguments, the bodies
    are pushed and the word runs as written, so the error is the word's.
    """
    stack = frame.stack
    scope = frame.scope
    tokens = frame.tokens
    template = frame.template
    lookup = value[0]
    if kind == TIMES:
        _lookup, body_index, count_kind, count_name, count_value = value
        if count_kind == CONST:
            count = count_value
        else:
            count = scope.get(count_name, _MISSING)
            if count is _MISSING:
                # the name means what it means now, and so does `times` after it
                stack.append(tokens[body_index]._bound_to(scope))
                return _push_transient(frame, [count_name, "times"], None, False)
        if type(count) not in inline.COUNTS:
            stack.append(tokens[body_index]._bound_to(scope))
            stack.append(count)
            return _word(frame, "times", lookup[0], lookup[1])
        state = _LoopState("times")
        state.body = tokens[body_index]
        state.body_scope = scope
        state.wrap_args = [count]
        state.limit = count
        control = Frame(LOOP, frame)
        control.word = "times"
        control.stack = stack
        control.state = state
        return control
    indexes = value[1:]
    if len(stack) < _NEEDED[kind]:
        for index in indexes:
            stack.append(tokens[index]._bound_to(scope))
        return _word(frame, name, lookup[0], lookup[1])
    if kind == IF or kind == IFELSE:
        condition = stack.pop()
        if not isinstance(condition, StackerCore):
            # a value decides at once: the chosen arm runs in place of the word, inside this activation when
            # its unit can run now, else as an activation of its own
            if condition:
                arm = tokens[indexes[0]]
            elif kind == IFELSE:
                arm = tokens[indexes[1]]
            else:
                return None
            if _splice_arm(frame, arm, name, frame.index):
                return frame
            return _push_block(frame, name, arm, scope, stack, None, _in_tail_position(frame))
        control = Frame(COND, frame)
        control.word = name
        control.stack = stack
        true_body = _Arm(tokens[indexes[0]], scope)
        false_body = _Arm(tokens[indexes[1]], scope) if kind == IFELSE else None
        control.state = [START, condition, true_body, false_body, []]
        return control
    if kind == DO or kind == DOLIST:
        places = ((-2, "arg"), (-3, "arg")) if kind == DO else ((-2, "arg"),)  # below the name: the bounds, or the items
        if _block_at(stack, places):
            return _args(frame, name, places, kind, value)
    state = _LoopState(name)
    state.body_scope = scope
    if kind == DO:
        start_value, end_value, var = template._do_arguments(stack)
        state.wrap_args = [start_value, end_value]
        try:
            state.values = iter(loop.do_range(start_value, end_value))
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error("do", state.wrap_args, error)
        state.body = tokens[indexes[0]]
        state.name = var
    elif kind == DOLIST:
        items, var = template._dolist_arguments(stack)
        state.wrap_args = [items]
        try:
            state.values = iter(items)
        except (TypeError, AttributeError) as error:
            _core._reraise_type_error("dolist", state.wrap_args, error)
        state.body = tokens[indexes[0]]
        state.name = var
    elif kind == compiler.WHILE:
        state.condition = tokens[indexes[0]]
        state.body = tokens[indexes[1]]
    else:  # LOOP
        state.body = tokens[indexes[0]]
    control = Frame(LOOP, frame)
    control.word = name
    control.stack = stack
    control.state = state
    return control


# ---------------------------------------------------------------------------
# Ending activations, and the continuations of the control activations
# ---------------------------------------------------------------------------


def _resume(frame: Frame) -> Frame:
    """Goes on with the code activation ``frame`` after a child it pushed ended: a resolved one checks its guards first."""
    if frame.resolved and frame.index >= 0:
        index = frame.index
        frame.index = -1
        if generation.epoch != frame.epoch:
            _guard_after(frame, index)
    return frame


def _child_ended(control: Frame, child: Frame | None) -> Frame | None:
    """The child of the control activation ``control`` ended (None: the activation starts): continues the word."""
    kind = control.kind
    if kind == LOOP:
        return _loop_next(control, child)
    if kind == COND:
        truth = control.parent.template._condition_left(control.stack, control.word)
        return _decide(control, truth)
    if kind == TRY:
        return _resume(control.parent)
    if kind == COLLECT:
        control.stack.append(list(control.state[2]))
        return _resume(control.parent)
    if kind == MAP:
        return _map_next(control, child)
    if kind == REDUCE:
        return _reduce_next(control, child)
    if kind == INCLUDE:
        return _include_next(control, child)
    if kind == ARGS:
        return _args_next(control, child)
    raise AssertionError(f"an activation of kind {kind} ended")


def _continue(control: Frame) -> Frame | None:
    """Starts the control activation ``control``: pushes its first child, or decides without one."""
    kind = control.kind
    if kind == LOOP:
        return _loop_next(control, None)
    state = control.state
    if kind == COND:
        return _test(control)
    if kind == TRY:
        state[0] = BODY
        child = _push_code(control, None, state[2], control.stack)
        return child if child is not None else _resume(control.parent)
    if kind == COLLECT:
        state[0] = BODY
        child = _push_code(control, None, state[1], state[2])
        return child if child is not None else _child_ended(control, control)
    if kind == MAP:
        return _map_next(control, None)
    if kind == REDUCE:
        return _reduce_next(control, None)
    if kind == INCLUDE:
        return _include_next(control, None)
    if kind == ARGS:
        return _args_next(control, None)
    raise AssertionError(f"an activation of kind {kind} has no continuation")


def _end_loop(control: Frame) -> Frame:
    """The loop ``control`` is over: its body's activations are let go (they point back at it) and the word's activation goes on."""
    state = control.state
    state.body_frame = None
    state.condition_frame = None
    return _resume(control.parent)


def _loop_next(control: Frame, ended: Frame | None) -> Frame | None:
    """A run of the loop's body (or condition) ended, or the loop starts: runs the body once more, or ends the loop.

    The body's activation is made once per loop and entered again on every
    iteration (`while` keeps one for its condition and one for its body):
    only what the iteration changes (the scope, the stream, the trace) is
    set again. A body whose unit the last iteration ran to its end is
    admitted on it again without the checks made on entry (as
    ``compiler.run`` was told ``admitted``); a body the compiler left to
    the interpreter walks its classification again. The other cases go
    through ``_start``.
    """
    state = control.state
    if ended is not None and ended is state.body_frame and state.kind <= L_TIMES:
        # the usual iteration of `do` / `dolist` / `times`: the body ran to its end on its own unit, and runs
        # again on it (the general way below is taken when anything is not so)
        unit = ended.unit_before
        if unit is not None and type(unit) is compiler.Unit and ended.tokens._unit is unit and unit.manager is state.body.operator_manager:
            if state.kind == L_DO:
                try:
                    value = next(state.values)
                except StopIteration:
                    return _end_loop(control)
                ended.scope = ScopedVariables.loop_scope(state.body_scope, {state.name: value})
                ended.core = None  # (the copy of the last iteration is let go first)
            else:
                if not (state.count < state.limit):  # a comparison, not range(): non-integer counts keep working
                    return _end_loop(control)
                state.count += 1
            state.trusted = unit
            if _admissions is not None:
                _admissions.append((ended.tokens, True))
            ended.trace = ended.tokens  # (a `try` inside the last iteration may have left its own block's)
            ended.epoch = generation.epoch
            ended.it = iter(unit.steps)
            return ended
    elif ended is not None and state.kind == L_WHILE:
        epoch = generation.epoch
        if ended is state.condition_frame:
            # the condition ran: the body runs again on its unit when it may be admitted (else the general way)
            body_frame = state.body_frame
            trusted = state.trusted if epoch == state.epoch else None
            if body_frame is not None and trusted is not None and body_frame.tokens._unit is trusted and trusted.manager is state.body.operator_manager:
                cunit = ended.unit_before
                state.trusted_condition = cunit if cunit is not None and type(cunit) is compiler.Unit and ended.tokens._unit is cunit else None
                if not control.parent.template._condition_left(control.stack, "while"):
                    return _end_loop(control)
                state.epoch = epoch
                state.phase = BODY
                if _admissions is not None:
                    _admissions.append((body_frame.tokens, True))
                body_frame.trace = body_frame.tokens
                core = body_frame.core
                if core is not None:
                    core.trace = body_frame.tokens
                body_frame.epoch = epoch
                body_frame.it = iter(trusted.steps)
                return body_frame
        elif ended is state.body_frame:
            # the body ran: the condition runs again on its unit when it may be admitted
            condition_frame = state.condition_frame
            trusted = state.trusted_condition if epoch == state.epoch else None
            if condition_frame is not None and trusted is not None and condition_frame.tokens._unit is trusted and trusted.manager is state.condition.operator_manager:
                unit = ended.unit_before
                state.trusted = unit if unit is not None and type(unit) is compiler.Unit and ended.tokens._unit is unit else None
                state.epoch = epoch
                state.phase = CONDITION
                if _admissions is not None:
                    _admissions.append((condition_frame.tokens, True))
                condition_frame.trace = condition_frame.tokens
                core = condition_frame.core
                if core is not None:
                    core.trace = condition_frame.tokens
                condition_frame.epoch = epoch
                condition_frame.it = iter(trusted.steps)
                return condition_frame
    word = state.word
    condition = False
    if ended is not None:
        if state.phase == CONDITION:
            # `while`: the condition ran; the body runs when it left a true value
            state.trusted_condition = _trusted_unit(ended)
            if generation.epoch != state.epoch:
                state.trusted = None
            if not control.parent.template._condition_left(control.stack, "while"):
                return _end_loop(control)
            state.epoch = generation.epoch
            state.phase = BODY
            body = state.body
            if not isinstance(body, StackerCore):
                child = _push_code(control, None, body, control.stack)
                if child is not None:
                    return child
                state.trusted = None  # (a value in the body's place: nothing ran)
                return _loop_next(control, None)
            scope = body.variables if state.body_scope is None else state.body_scope
            trusted = state.trusted
        else:
            if ended.kind == BLOCK:
                unit = ended.unit_before
                state.trusted = unit if unit is not None and ended.tokens._unit is unit and type(unit) is compiler.Unit else None
            else:
                state.trusted = None
            if word == "while" and generation.epoch != state.epoch:
                state.trusted_condition = None
            body = None
    else:
        body = None
    if body is None:
        while True:
            if word == "do" or word == "dolist":
                try:
                    value = next(state.values)
                except StopIteration:
                    return _end_loop(control)
                state.phase = BODY
                scope = ScopedVariables.loop_scope(state.body_scope, {state.name: value})
                body = state.body
                trusted = state.trusted
                break
            if word == "times":
                if not (state.count < state.limit):  # a comparison, not range(): non-integer counts keep working
                    return _end_loop(control)
                state.count += 1
            elif word == "while":
                state.epoch = generation.epoch
                state.phase = CONDITION
                body = state.condition
                scope = body.variables if state.body_scope is None else state.body_scope
                trusted = state.trusted_condition
                condition = True
                break
            state.phase = BODY
            body = state.body
            if not isinstance(body, StackerCore):
                child = _push_code(control, None, body, control.stack)
                if child is not None:
                    return child
                state.trusted = None  # a value in the body's place was pushed: the run is over at once
                continue
            scope = body.variables if state.body_scope is None else state.body_scope
            trusted = state.trusted
            break
    # --- the body (or the condition), entered again
    child = state.condition_frame if condition else state.body_frame
    if child is None:
        child = Frame(BLOCK, control)
        child.template = body
        child.stack = control.stack
        child.tokens = body.tokens
        if condition:
            state.condition_frame = child
        else:
            state.body_frame = child
    child.scope = scope
    tokens = body.tokens
    if body.variables is scope:
        child.core = body
        body.trace = tokens
    else:
        child.core = None  # (the copy of the last iteration is let go first)
    child.trace = tokens
    unit = tokens._unit
    child.unit_before = unit
    if unit is not None:
        if unit is trusted and unit.manager is body.operator_manager:
            # admitted: what _admit sets when it checks nothing
            if _admissions is not None:
                _admissions.append((tokens, True))
            child.unit = unit
            child.epoch = generation.epoch
            child.resolved = True
            child.it = iter(unit.steps)
            return child
        if unit is compiler.UNCOMPILABLE:
            entries = tokens.classification()
            child.entries = entries
            child.resolved = False
            child.unit = None
            child.it = enumerate(entries)
            return child
    _start(child, body, tokens, trusted)
    return child


def _reenter(child: Frame, body: StackerCore) -> bool:
    """Enters ``child`` again on the unit it ran to its end last time, when the unit is still the block's; else says no.

    What a loop does for its body between two iterations (``_loop_next``),
    for an activation `map` or `reduce` keeps for its elements: a unit that
    was there before the last run and is still there is admitted without
    the entry checks, as a loop admits a trusted unit.
    """
    unit = child.unit_before
    if unit is None or type(unit) is not compiler.Unit or body.tokens._unit is not unit or unit.manager is not body.operator_manager:
        return False
    if _admissions is not None:
        _admissions.append((body.tokens, True))
    tokens = body.tokens
    child.trace = tokens  # (a `try` inside the last run may have left its own block's)
    core = child.core
    if core is not None:
        core.trace = tokens
    child.epoch = generation.epoch
    child.it = iter(unit.steps)
    return True


def _trusted_unit(frame: Frame) -> compiler.Unit | None:
    """The unit a loop may admit next time: the one the body had before and still has, having run it to its end."""
    unit = frame.unit_before
    return unit if type(unit) is compiler.Unit and frame.tokens._unit is unit else None


# ---------------------------------------------------------------------------
# Taking activations down
# ---------------------------------------------------------------------------


def _unwind(frame: Frame, error: BaseException, is_break: bool) -> Frame | None:
    """Takes activations down from ``frame`` until one catches ``error``, applying each one's rules in turn.

    Args:
        frame: The activation that was running.
        error: The error, or the `break` signal.
        is_break: Whether ``error`` is a `break`.

    Returns:
        The activation to go on with.

    Raises:
        BaseException: ``error`` (as reworded on the way) when no activation caught it.
    """
    while True:
        kind = frame.kind
        arms = frame.arms
        if arms:
            # the arms of `if` this activation was running in place: each would have reworded the error as its
            # word's; the trace already holds the innermost arm's tokens
            if not is_break:
                for spliced in reversed(arms):
                    error = _reworded(frame.template, spliced[4], error)
            frame.tailpos = arms[0][6]
            frame.arms = None
        if kind == CALL:
            if not is_break and isinstance(error, RecursionError):
                error = _host_depth_error(frame.name, error)  # (named at the depth the call was at)
        elif kind == EXPAND:
            if not is_break and isinstance(error, StackerError):
                attach_macro_context(error, f"while expanding macro '{frame.name}'")
        elif kind == MACRO_RUN:
            if not is_break and isinstance(error, StackerError):
                attach_macro_context(error, f"in code generated by macro '{frame.name}'")
        elif kind == ARGS:
            # a value already taken must not be seen wrapped: it is unwrapped where it stands
            stack = frame.stack
            for i in range(1, min(len(stack), len(frame.state[0])) + 1):
                if type(stack[-i]) is _core.Taken:
                    stack[-i] = stack[-i].value
        elif kind == INCLUDE:
            # the error (a `break` too) is tagged with the file's position, and the file is no longer running
            frame.state.tag(error)
            frame.state.stop()
        elif kind == MAP:
            frame.state[7] = None  # (the element's activation, let go either way)
            if not is_break:
                error = _rewrapped(frame.word, [frame.state[2]], error)
        elif kind == REDUCE:
            frame.state[6] = None
            if not is_break:
                error = _rewrapped(frame.word, frame.state[5], error)
        elif kind == LOOP:
            state = frame.state
            if is_break:
                if state.phase == BODY:
                    return _end_loop(frame)  # the loop ends
            elif state.wrap_args is not None:
                error = _rewrapped(state.word, state.wrap_args, error)
            state.body_frame = None  # (the loop is over either way: its activations point back at it)
            state.condition_frame = None
        elif kind == TRY and not is_break and frame.state[0] == BODY and isinstance(error, Exception):
            state = frame.state
            partial = if_else._put_back(frame.stack, state[1])
            if frame.word == "try":
                frame.stack.append({"kind": error_kind(error), "message": str(error), "stack": partial})
            state[0] = HANDLER
            child = _push_code(frame, None, state[3], frame.stack)
            return child if child is not None else _resume(frame.parent)
        elif kind == CATCHER and not is_break and isinstance(error, Exception):
            # the body took the error: the handler runs in its place, as the word's activation's child
            saved, handler = frame.state
            parent = frame.parent
            _write_trace(parent, frame.trace)
            partial = if_else._put_back(frame.stack, saved)
            if frame.word == "try":
                frame.stack.append({"kind": error_kind(error), "message": str(error), "stack": partial})
            child = _push_code(parent, None, handler, frame.stack)
            return child if child is not None else _resume(parent)
        parent = frame.parent
        if parent is None:
            raise error
        if kind == BLOCK or kind == MACRO_RUN or kind == CATCHER:
            _write_trace(parent, frame.trace)  # the tokens of the innermost failing block, for diagnostics
        if frame.word is not None and not is_break:
            error = _reworded(_owner(frame).template, frame.word, error)
        if parent.kind < LOOP:
            parent.index = -1  # the guard after the word is not made: the word did not finish
        frame = parent
