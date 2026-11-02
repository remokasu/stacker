"""The harness the tests of the compile tier share: outcomes, a pair of interpreters, the units made, and the fates of a block.

A compiled block (a ``Unit``) keeps what its names resolved to; whatever the compile tier does, a program must leave
what the interpreter leaves. ``Twin`` runs every program on two interpreters, one that never compiles and one that
compiles a block on its first run, and compares what they leave step by step (the stack, what was printed, the error
and the trace of the error). ``Compilations`` records every unit the compiler makes, so a test can look at a unit
that was dropped and at the one that replaced it. The ``assert_*`` functions say what became of a block's unit.
"""

import contextlib
import io
from typing import NamedTuple

from stacker import Stacker
from stacker.engine import compiler
from stacker.engine.core import StackerCore, TokenList
from stacker.engine.data_type import stack_data
from stacker.engine.slambda import StackerLambda
from stacker.engine.smacro import StackerMacro
from stacker.error import StackerError

#: The threshold the compiler is made with, which the parity tests (section 6) run under as "default"
DEFAULT_THRESHOLD = 8

# ---------------------------------------------------------------------------
# The harness
# ---------------------------------------------------------------------------


class Outcome(NamedTuple):
    """What a program leaves behind: the values on its stack, what it printed and the error that stopped it."""

    stack: list
    out: str
    error: tuple[str, str] | None


def ok(*stack, out=""):
    """The outcome of a program that finishes with ``stack`` (and printed ``out``)."""
    return Outcome(list(stack), out, None)


def fails(kind, message, *stack, out=""):
    """The outcome of a program that stops with the error ``kind`` (the class name) saying ``message``."""
    return Outcome(list(stack), out, (kind, message))


def undefined(name, *stack, out=""):
    """The outcome of a program that stops at the undefined word ``name``."""
    return fails("UndefinedSymbolError", f"`{name}` is not defined.", *stack, out=out)


def lines(*values):
    """The text printed by echoing each of ``values`` in turn."""
    return "".join(f"{value}\n" for value in values)


def shown(value):
    """``value`` with each block and lambda replaced by its text: a block of one interpreter equals no other's.

    Args:
        value: A value from a stack.

    Returns:
        The value, with blocks and lambdas inside lists and dictionaries replaced as well.
    """
    if isinstance(value, (StackerCore, StackerLambda)):
        return str(value)
    if isinstance(value, list):
        return [shown(item) for item in value]
    if isinstance(value, dict):
        return {key: shown(item) for key, item in value.items()}
    return value


class Side:
    """One interpreter, and what the programs it runs leave behind."""

    def __init__(self, compiles):
        self.stacker = Stacker(compile=compiles)

    def observe(self, source):
        """Runs ``source`` on a stack of its own and reports what it left.

        Args:
            source: Stacker source.

        Returns:
            The outcome, and the text of the trace the interpreter keeps for an error.
        """
        stack = stack_data()
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            try:
                self.stacker.eval(source, stack)
                error = None
            except StackerError as caught:
                error = (type(caught).__name__, str(caught))
        trace = [str(token) for token in self.stacker.get_trace_copy()]
        return Outcome(shown(list(stack)), printed.getvalue(), error), trace


class Compilations:
    """Every unit the compiler makes, in order, with the interpreter and the token list it was made for.

    A block forgets a unit it drops. The record keeps it, so a test can ask what the stale unit had resolved a name
    as and what the unit that replaced it resolved it as.
    """

    def __init__(self, monkeypatch):
        self.made: list[tuple[object, TokenList, object]] = []
        compile_block = compiler.compile_block

        def recording(core, tokens, entries):
            unit = compile_block(core, tokens, entries)
            self.made.append((core.operator_manager, tokens, unit))
            return unit

        monkeypatch.setattr(compiler, "compile_block", recording)

    def of(self, tokens):
        """The units made for ``tokens``, the first one first."""
        return [unit for _, made_for, unit in self.made if made_for is tokens]

    def by(self, stacker):
        """The units made for blocks that ran on ``stacker`` (not the blocks the compiler failed on)."""
        manager = stacker.operator_manager
        return [unit for made_by, _, unit in self.made if made_by is manager and isinstance(unit, compiler.Unit)]


class Twin:
    """The same programs on two interpreters: one never compiles, the other compiles a block on its first run.

    ``run`` runs a program on both and fails when they differ in anything they leave behind, so a test only says
    once what the program should do. Blocks, functions and words are made on both in the same way; the token lists
    a test looks at belong to the compiling one.
    """

    def __init__(self, compilations):
        self.reference = Side(compiles=False)
        self.compiled = Side(compiles=True)
        self.compilations = compilations

    def run(self, source):
        """Runs ``source`` on both interpreters and checks the compiling one did what the other did.

        Args:
            source: Stacker source.

        Returns:
            The outcome (the two are equal).
        """
        expected, expected_trace = self.reference.observe(source)
        actual, actual_trace = self.compiled.observe(source)
        assert not self.compilations.by(self.reference.stacker), "the interpreter that must not compile did"
        assert actual == expected, f"`{source}`: compiled {actual}, interpreted {expected}"
        if actual.error is not None:
            assert actual_trace == expected_trace, (
                f"`{source}`: compiled trace {actual_trace}, interpreted {expected_trace}"
            )
        return actual

    def do(self, action):
        """Applies a host action (a call on the interpreter) to both interpreters.

        Args:
            action: A function of one interpreter.
        """
        action(self.reference.stacker)
        action(self.compiled.stacker)

    def _bind(self, name, make):
        """Binds the block ``make`` returns for each interpreter to the variable ``name`` on that interpreter.

        Returns:
            The token list of the compiling interpreter's block.
        """
        blocks = {}
        for side in (self.reference, self.compiled):
            blocks[side] = make(side.stacker)
            side.stacker.register_parameter(name, blocks[side])
        return blocks[self.compiled].tokens

    def block(self, source, name="blk"):
        """Makes the block ``source`` denotes on both interpreters and binds it to the variable ``name``.

        Args:
            source: A block literal.
            name: The variable that holds it.

        Returns:
            The token list of the compiling interpreter's block.
        """
        return self._bind(name, lambda stacker: next(iter(stacker.eval(source))))

    def raw_block(self, tokens, name):
        """Makes a block of raw tokens, as a host builds one, on both interpreters and binds it to ``name``.

        A block literal turns its literals into values when it is made, so only a block made this way holds a
        literal spelled as a name (``"3"``) or a block that is still text (``"{1 2}"``).

        Args:
            tokens: The block's tokens.
            name: The variable that holds it.

        Returns:
            The token list of the compiling interpreter's block.
        """
        return self._bind(name, lambda stacker: stacker._block_of(list(tokens)))

    def body(self, word):
        """The token list of the body of the function ``word`` on the compiling interpreter."""
        return self.compiled.stacker.sfunctions[word]["func"].blockstack.tokens

    def units(self, tokens):
        """The units the compiler made for ``tokens`` so far, the first one first."""
        return self.compilations.of(tokens)


def steps(unit):
    """The kinds of the steps of ``unit``, in order."""
    return [step.kind for step in unit.instructions]


def resolved_as(unit, name):
    """The kind of the one step of ``unit`` that names ``name``: what the unit took the name for."""
    (kind,) = [step.kind for step in unit.instructions if step.name == name]
    return kind


def assert_dropped(tokens, times=1):
    """Fails unless the block's unit was dropped in mid-run ``times`` times and the block has none now."""
    assert tokens._unit is None
    assert tokens._drops == times


def assert_rewarmed(tokens, drops=0):
    """Fails unless the unit was forgotten when it was about to start, which counts no drop: the block runs by the
    interpreter and counts its runs again (``drops`` is how many mid-run drops it had before)."""
    assert tokens._unit is None
    assert tokens._runs == 0
    assert tokens._drops == drops


def assert_kept(tokens, unit, drops=0):
    """Fails unless ``unit`` is still the block's unit, dropped ``drops`` times before it."""
    assert tokens._unit is unit
    assert tokens._drops == drops


def assert_compiled(tokens, drops=0):
    """Fails unless the block has a unit, dropped ``drops`` times before it; returns the unit."""
    assert isinstance(tokens._unit, compiler.Unit)
    assert tokens._drops == drops
    return tokens._unit


def assert_given_up(tokens):
    """Fails unless the block was dropped so often that it is left to the interpreter for good."""
    assert tokens._unit is compiler.UNCOMPILABLE
    assert tokens._drops >= compiler.GIVE_UP


def register_host_words(stacker):
    """Registers the plugin words the scenarios use on ``stacker``.

    ``triple`` is a plain plugin word. The others take the interpreter (``pass_core``) and write a word table with
    the host's own method, which is how a program reaches ``register_sfunction``, ``register_plugin``,
    ``register_macro`` and ``register_operator``.

    Args:
        stacker: The interpreter.
    """
    macro_body = next(iter(stacker.eval("{{100 +}}")))

    def register_function(core):
        core.register_sfunction("hf", lambda a: a + 100, 1, True, "adds 100")

    def register_plugin_word(core):
        core.register_plugin("pw", lambda a: a + 100, True, False, "adds 100")

    def register_macro_word(core):
        core.register_macro("hm", StackerMacro("hm", [], macro_body))

    def redefine_triple(core):
        core.register_plugin("triple", lambda a: a * 10, True, False, "multiplies by ten")

    def redefine_dup(core):
        core.register_operator("dup", lambda stack: stack.append(100), 0, False, "pushes 100")

    words = {
        "reg-hf": register_function,
        "reg-pw": register_plugin_word,
        "reg-hm": register_macro_word,
        "redefine-triple": redefine_triple,
        "redefine-dup": redefine_dup,
    }
    for name, word in words.items():
        stacker.register_plugin(name, word, push_result_to_stack=False, pass_core=True, desc=name)
    stacker.register_plugin("triple", lambda a: a * 3, True, False, "triples")
