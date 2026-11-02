"""The guards of the compile tier, pinned as a matrix: what makes a unit stale, and what becomes of it.

A compiled block (a ``Unit``) keeps what its names resolved to, and three guards say when that has gone stale: the
word tables' generation (``OperatorManager.generation``), the bindings' generation (``generation.bindings``) and the
scope check ``ScopedVariables.hides_any``. Whatever the guards do, a program must leave what the interpreter leaves.
Each test here therefore asserts two things:

- the result: every program is run on a pair of interpreters (``Twin``), one that never compiles and one that
  compiles a block on its first run, and the two are compared step by step (the stack, what was printed, the error and
  the trace of the error). The test also says what the result is, so two interpreters agreeing on a wrong answer pass
  nothing
- the unit's fate, which depends on when the guard fails:

  - before the unit runs (the tables changed since it was made, or a variable hides a word it took): the unit is
    forgotten, the block counts its runs again and no drop is counted (``_unit is None``, ``_runs == 0``, ``_drops``
    as it was); the interpreter runs that run, and the block is compiled again once it reaches the threshold
  - in the middle of a run (a word that ran changed the tables or bound a name): the interpreter finishes the run
    and the drop is counted (``_drops``, ``_unit is None``), once however many calls of the unit are running; after
    ``GIVE_UP`` drops the block is left to the interpreter (``compiler.UNCOMPILABLE``)
  - the units the compiler made are recorded, so a unit that was forgotten or dropped can still be looked at, and so
    can what the unit that replaced it took the names for

Every test compiles on the first run (``THRESHOLD`` = 1, set by the ``twin`` fixture of this directory's conftest;
the harness itself is ``compile_helpers.py``), whatever state the session runs in except the parity tests at the end, which set the threshold they name. ``VERIFY`` is left as the session has
it: in the ``eager`` state every resolved instruction also re-resolves its name first, so a guard that lets a stale
one through fails there loudly. Run the file in each state: ``STACKER_TEST_COMPILE=off|default|eager``.

Sections:

 1. the writers of the word tables, between two runs, inside the block's own run and inside a function it calls
 2. a variable that hides a word, a literal or an undefined name the unit took
 3. one block under different heads and in different function scopes
 4. each kind of step runs as the interpreter does
 5. re-entrancy: a unit running again inside its own run, and dropped from the inside
 6. off, default and eager leave the same results

and, last, the harness itself: a compiler that gets a program wrong, or a guard that is missing, does not pass unseen.
What the neighbouring ``test_compiler.py`` covers is not repeated here: the same block under two names for the `do`
variable, a token list changed in place, a block of another interpreter, a list literal whose template failed to build.
"""

from typing import NamedTuple

import pytest

from stacker.engine import compiler, inline
from stacker.engine.compiler import (
    BAD,
    BAD_LIST,
    BLOCK,
    CALL,
    CONST,
    DO,
    DOLIST,
    FAST1,
    FAST2,
    IF,
    IFELSE,
    LIST,
    LIT,
    LOOP,
    MACRO,
    NAME,
    SET,
    TIMES,
    UNDEF,
    VAR,
    WHILE,
    WORD,
)
from stacker.engine.core import StackerCore
from stacker.engine.data_type import Symbol, stack_data
from stacker.engine.smacro import StackerMacro
from test.engine.compile_helpers import (
    DEFAULT_THRESHOLD,
    Outcome,
    Side,
    assert_compiled,
    assert_dropped,
    assert_given_up,
    assert_kept,
    assert_rewarmed,
    fails,
    lines,
    ok,
    register_host_words,
    resolved_as,
    steps,
    undefined,
)

# ---------------------------------------------------------------------------
# 1. The writers of the word tables
# ---------------------------------------------------------------------------


class Writer(NamedTuple):
    """One way to write the word tables, and a word whose meaning it changes.

    Attributes:
        id: The writer, for the test's name.
        given: The value the block is given on the stack.
        use: The block's code: its first step is ``word``, which takes ``given``.
        change: Code that writes the table: Stacker source, or a plugin word that calls the host's method.
        word: The word ``use`` names and ``change`` affects.
        before: What the block leaves before the change.
        after: What it leaves after it.
        resolved: What ``word`` is taken for before the change and after it.
        rewrites: Whether running ``change`` again writes a table again (a word taken away once is not taken twice).
        setup: Code that runs first.
    """

    id: str
    given: str
    use: str
    change: str
    word: str
    before: Outcome
    after: Outcome
    resolved: tuple[str, str]
    rewrites: bool
    setup: str = ""

    @property
    def program(self):
        """The program that runs the block ``blk`` on what ``given`` pushes."""
        return f"{self.given} blk eval"


DEFINE_F = "{x} {x 100 +} :f defun"
DEFINE_M = "{} {{100 +}} :m defmacro"

WRITERS = [
    Writer("defun", given="5", use="f", change=DEFINE_F, word="f",
           before=undefined("f", 5), after=ok(105), resolved=(UNDEF, CALL), rewrites=True),
    Writer("defun-over-a-function", given="5", setup="{x} {x 1 +} :f defun", use="f", change=DEFINE_F, word="f",
           before=ok(6), after=ok(105), resolved=(CALL, CALL), rewrites=True),
    Writer("defmacro", given="5", use="m", change=DEFINE_M, word="m",
           before=undefined("m", 5), after=ok(105), resolved=(UNDEF, MACRO), rewrites=True),
    Writer("defmacro-over-a-variable", given="5", setup="7 :m set", use="m", change=DEFINE_M, word="m",
           before=ok(5, 7), after=ok(105), resolved=(VAR, MACRO), rewrites=True),
    Writer("defmacro-over-a-function", given="5", setup="{x} {x 1 +} :m defun", use="m", change=DEFINE_M, word="m",
           before=ok(6), after=ok(105), resolved=(CALL, MACRO), rewrites=True),
    Writer("alias", given="5", use="inc", change="{100 +} {inc} alias", word="inc",
           before=undefined("inc", 5), after=ok(105), resolved=(UNDEF, MACRO), rewrites=True),
    Writer("register_sfunction", given="5", use="hf", change="reg-hf", word="hf",
           before=undefined("hf", 5), after=ok(105), resolved=(UNDEF, WORD), rewrites=True),
    Writer("register_plugin", given="5", use="pw", change="reg-pw", word="pw",
           before=undefined("pw", 5), after=ok(105), resolved=(UNDEF, WORD), rewrites=True),
    Writer("register_macro", given="5", use="hm", change="reg-hm", word="hm",
           before=undefined("hm", 5), after=ok(105), resolved=(UNDEF, MACRO), rewrites=True),
    Writer("register_plugin-over-a-plugin", given="3", use="triple", change="redefine-triple", word="triple",
           before=ok(9), after=ok(30), resolved=(WORD, WORD), rewrites=True),
    Writer("defun-over-a-plugin", given="3", use="triple", change="{x} {x 100 +} :triple defun", word="triple",
           before=ok(9), after=ok(103), resolved=(WORD, CALL), rewrites=True),
    Writer("defun-over-a-built-in", given="1 2", use="+", change='{a b} {"mine"} :+ defun', word="+",
           before=ok(3), after=ok("mine"), resolved=(FAST2, CALL), rewrites=True),
    Writer("register_operator", given="7", use="dup", change="redefine-dup", word="dup",
           before=ok(7, 7), after=ok(7, 100), resolved=(WORD, WORD), rewrites=True),
    Writer("disable_plugin", given="3", use="triple", change='"triple" disable_plugin', word="triple",
           before=ok(9), after=undefined("triple", 3), resolved=(WORD, UNDEF), rewrites=False),
    Writer("disable_all_plugins", given="3", use="triple", change="disable_all_plugins", word="triple",
           before=ok(9), after=undefined("triple", 3), resolved=(WORD, UNDEF), rewrites=False),
]
REWRITERS = [writer for writer in WRITERS if writer.rewrites]
every_writer = pytest.mark.parametrize("writer", WRITERS, ids=lambda writer: writer.id)


@every_writer
def test_a_write_between_two_runs_makes_the_unit_stale_and_the_next_run_compiles_it_anew(twin, writer):
    twin.do(register_host_words)
    twin.run(writer.setup)
    blk = twin.block("{" + writer.use + "}")

    assert twin.run(writer.program) == writer.before
    stale = blk._unit
    assert resolved_as(stale, writer.word) == writer.resolved[0]

    assert twin.run(writer.change) == ok()
    assert twin.run(writer.program) == writer.after  # (stale when it starts: the interpreter runs this one)
    assert_rewarmed(blk)

    assert twin.run(writer.program) == writer.after
    assert blk._unit is not stale
    assert resolved_as(blk._unit, writer.word) == writer.resolved[1]
    assert blk._drops == 0


def first_run_with_a_write_in_it(twin, writer, blk):
    """Runs a block whose run makes ``writer``'s change: its unit is dropped right after the word that wrote."""
    assert twin.run(writer.program) == writer.after  # (the change is seen by the rest of the very run that made it)
    (stale,) = twin.units(blk)
    assert resolved_as(stale, writer.word) == writer.resolved[0]
    assert_dropped(blk)


def second_run_with_a_write_in_it(twin, writer, blk):
    """Runs the block again: it is compiled anew, with the word taken for what it is now."""
    twin.run(writer.program)
    _, recompiled = twin.units(blk)
    assert resolved_as(recompiled, writer.word) == writer.resolved[1]
    if writer.rewrites:  # it writes again, and the new unit is dropped as the first was
        assert_dropped(blk, times=2)
    else:  # there is nothing left to write, so the new unit stays
        assert_kept(blk, recompiled, drops=1)


@every_writer
def test_a_write_inside_the_blocks_own_run_drops_its_unit_after_the_word_that_wrote(twin, writer):
    twin.do(register_host_words)
    twin.run(writer.setup)
    blk = twin.block("{" + writer.change + " " + writer.use + "}")
    first_run_with_a_write_in_it(twin, writer, blk)
    second_run_with_a_write_in_it(twin, writer, blk)


@every_writer
def test_a_write_inside_a_function_the_block_calls_drops_the_units_of_the_function_and_of_the_block(twin, writer):
    twin.do(register_host_words)
    twin.run(writer.setup)
    twin.run("{} {" + writer.change + "} :change defun")
    blk = twin.block("{change " + writer.use + "}")
    first_run_with_a_write_in_it(twin, writer, blk)
    assert_dropped(twin.body("change"))  # (the body that wrote is dropped too)
    second_run_with_a_write_in_it(twin, writer, blk)


@pytest.mark.parametrize("writer", REWRITERS, ids=lambda writer: writer.id)
def test_a_block_that_writes_a_table_on_every_run_is_given_up_after_that_many_drops(twin, writer):
    twin.do(register_host_words)
    twin.run(writer.setup)
    blk = twin.block("{" + writer.change + " " + writer.use + "}")
    for run in range(1, compiler.GIVE_UP + 1):
        assert twin.run(writer.program) == writer.after
        assert blk._drops == run
    assert_given_up(blk)
    assert twin.run(writer.program) == writer.after  # (the interpreter runs it from now on)
    assert_given_up(blk)
    assert len(twin.units(blk)) == compiler.GIVE_UP  # (one unit for each drop, none after)


def test_after_a_unit_is_forgotten_the_block_runs_the_threshold_number_of_times_before_it_is_compiled_again(
    twin, monkeypatch
):
    monkeypatch.setattr(compiler, "THRESHOLD", 3)
    blk = twin.block("{1 +}")
    for _ in range(3):
        assert twin.run("10 blk eval") == ok(11)
    unit = blk._unit
    assert isinstance(unit, compiler.Unit)

    twin.run("{x} {x} :g defun")  # a write: the unit is stale
    assert twin.run("10 blk eval") == ok(11)
    assert_rewarmed(blk)
    for _ in range(2):  # (two more runs by the interpreter)
        assert twin.run("10 blk eval") == ok(11)
        assert blk._unit is None
    assert twin.run("10 blk eval") == ok(11)
    assert isinstance(blk._unit, compiler.Unit)
    assert blk._unit is not unit


def test_after_a_drop_in_mid_run_the_block_runs_the_threshold_number_of_times_before_it_is_compiled_again(
    twin, monkeypatch
):
    monkeypatch.setattr(compiler, "THRESHOLD", 3)
    blk = twin.block("{{x} {x} :g defun 1 +}")  # (it writes a table on every run)
    for run in range(1, 7):
        assert twin.run("10 blk eval") == ok(11)
        compiled = len(twin.units(blk))
        # compiled on the third run and dropped in it; the runs after it count from 0, so the sixth compiles it again
        assert compiled == {1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2}[run]
    assert blk._drops == 2


# ---------------------------------------------------------------------------
# 2. A variable that hides a word the unit took
# ---------------------------------------------------------------------------

#: The ways to make the variable ``dup`` between two runs of a block: in the global scope, by a word and by the host
MAKING_A_GLOBAL_BETWEEN_RUNS = [
    pytest.param(lambda twin: twin.run("99 :dup set"), id="set"),
    pytest.param(lambda twin: twin.run("99 :dup global"), id="global"),
    pytest.param(lambda twin: twin.do(lambda stacker: stacker.register_parameter("dup", 99)), id="register_parameter"),
]


@pytest.mark.parametrize("make", MAKING_A_GLOBAL_BETWEEN_RUNS)
def test_a_variable_made_between_two_runs_under_the_name_of_a_word_hides_it_from_the_next_run_on(twin, make):
    blk = twin.block("{7 dup}")
    assert twin.run("blk eval") == ok(7, 7)
    stale = blk._unit
    assert resolved_as(stale, "dup") == WORD

    make(twin)
    assert twin.run("blk eval") == ok(7, 99)  # (the variable wins over the word)
    assert_rewarmed(blk)  # (found by the check at the unit's start: the interpreter ran this one)

    assert twin.run("blk eval") == ok(7, 99)
    assert blk._unit is not stale
    assert resolved_as(blk._unit, "dup") == VAR
    assert blk._drops == 0


def test_a_global_a_called_function_makes_hides_the_word_for_the_rest_of_the_run(twin):
    twin.run("{} {99 :dup global} :mk defun")
    blk = twin.block("{5 mk dup}")

    assert twin.run("blk eval") == ok(5, 99)  # (`dup` was a word when the unit was made; `mk` made the variable)
    (stale,) = twin.units(blk)
    assert resolved_as(stale, "dup") == WORD
    assert_dropped(blk)

    assert twin.run("blk eval") == ok(5, 99)  # (the variable is there now, and `mk` makes no new name)
    recompiled = twin.units(blk)[1]
    assert resolved_as(recompiled, "dup") == VAR
    assert_kept(blk, recompiled, drops=1)


def test_a_variable_a_nested_block_makes_hides_the_word_for_the_rest_of_the_run(twin):
    blk = twin.block("{5 {99 :dup set} eval dup}")
    assert twin.run("blk eval") == ok(5, 99)
    assert resolved_as(twin.units(blk)[0], "dup") == WORD
    assert_dropped(blk)


def test_a_variable_a_loop_body_sets_hides_the_word_from_its_next_step_and_the_body_is_compiled_again(twin):
    """The first iteration makes the variable (in the scope the body was written in, as a loop's body does)."""
    body = twin.block("{i :dup set dup}", "body")

    assert twin.run("1 3 :i body do") == ok(1, 2, 3)
    first, second = twin.units(body)
    assert resolved_as(first, "dup") == WORD  # (the unit of the first iteration took the word)
    assert resolved_as(second, "dup") == VAR  # (the unit of the second sees the variable)
    assert_kept(body, second, drops=1)  # (and keeps it for the third)

    assert twin.run("1 3 :i body do") == ok(1, 2, 3)  # (the variable is there from the start)
    assert_kept(body, second, drops=1)


def test_a_local_a_function_sets_under_the_name_of_a_word_drops_its_body_on_every_call_until_it_is_given_up(twin):
    """The call's scope is new, so the name is first bound in the middle of the unit, on every call."""
    twin.run("{x} {x :dup set dup} :f defun")
    body = twin.body("f")
    for call in range(1, compiler.GIVE_UP + 1):
        assert twin.run(f"{call} f") == ok(call)  # (`dup` is the local, and so it is pushed)
        assert body._drops == call
        assert body._unit is None or call == compiler.GIVE_UP
    assert_given_up(body)
    assert twin.run("9 f") == ok(9)
    assert_given_up(body)
    assert len(twin.units(body)) == compiler.GIVE_UP


def test_a_variable_that_defines_an_undefined_name_between_two_runs_is_read_by_the_next_run(twin):
    blk = twin.block("{nosuch}")
    assert twin.run("blk eval") == undefined("nosuch")
    assert resolved_as(blk._unit, "nosuch") == UNDEF

    twin.run("5 :nosuch set")
    assert twin.run("blk eval") == ok(5)
    assert_rewarmed(blk)
    assert twin.run("blk eval") == ok(5)
    assert resolved_as(blk._unit, "nosuch") == VAR


def test_a_variable_that_defines_an_undefined_name_inside_the_run_is_read_by_the_rest_of_it(twin):
    blk = twin.block("{5 :nosuch set nosuch}")
    assert twin.run("blk eval") == ok(5)
    assert resolved_as(twin.units(blk)[0], "nosuch") == UNDEF
    assert_dropped(blk)


def test_a_variable_named_like_a_literal_a_block_spells_as_a_name_hides_the_literal(twin):
    """Only a block of raw tokens holds a literal as a name; the variable ``3`` is a host's doing."""
    blk = twin.raw_block(["3", "4"], "raw")
    assert twin.run("raw eval") == ok(3, 4)
    assert steps(blk._unit) == [LIT, LIT]

    twin.do(lambda stacker: stacker.register_parameter("3", 99))
    assert twin.run("raw eval") == ok(99, 4)
    assert_rewarmed(blk)


def test_a_variable_named_like_a_word_the_unit_never_took_for_one_leaves_the_unit_alone(twin):
    """The unit holds the symbol ``:dup`` as a value and `eval` as the word; ``dup`` is not among the names it took."""
    blk = twin.block("{5 :dup eval}")
    assert twin.run("blk eval") == ok(5, 5)
    unit = blk._unit

    twin.run("99 :dup set")
    assert twin.run("blk eval") == ok(5, 99)  # (the symbol is run as the name `dup` is now: the variable)
    assert_kept(blk, unit)


def test_a_unit_that_took_no_name_for_a_word_is_not_dropped_by_the_variables_a_step_makes(twin):
    """Its steps are values and a macro call: there is nothing a variable could hide, whatever the macro binds."""
    twin.run("{} {{99 :made global}} :mk defmacro")
    blk = twin.block("{3 mk 4}")

    assert twin.run("blk eval") == ok(3, 4)
    unit = blk._unit
    assert steps(unit) == [CONST, MACRO, CONST]
    assert twin.run("made") == ok(99)  # (the macro made the variable)
    assert twin.run("blk eval") == ok(3, 4)
    assert_kept(blk, unit)


@pytest.mark.parametrize("make", MAKING_A_GLOBAL_BETWEEN_RUNS)
def test_a_variable_made_in_the_scope_above_between_two_calls_hides_the_word_from_the_next_call(twin, make):
    """The body runs in a new scope under the same parent each time; the name appears in that parent in between."""
    twin.run("{x} {x dup} :f defun")
    body = twin.body("f")

    assert twin.run("5 f") == ok(5, 5)
    stale = body._unit
    assert resolved_as(stale, "dup") == WORD

    make(twin)
    assert twin.run("5 f") == ok(5, 99)
    assert_rewarmed(body)
    assert twin.run("5 f") == ok(5, 99)
    assert body._unit is not stale
    assert resolved_as(body._unit, "dup") == VAR


@pytest.mark.parametrize("make", MAKING_A_GLOBAL_BETWEEN_RUNS)
def test_a_variable_made_in_the_scope_above_between_two_loops_hides_the_word_from_the_next_loop(twin, make):
    """Each round runs in a new loop scope under the same parent; the name appears in that parent in between."""
    body = twin.block("{7 dup}", "body")

    assert twin.run("1 2 :i body do") == ok(7, 7, 7, 7)
    stale = body._unit
    assert resolved_as(stale, "dup") == WORD

    make(twin)
    assert twin.run("1 2 :i body do") == ok(7, 99, 7, 99)
    first, second = twin.units(body)  # (the first round found the variable and forgot the unit, no drop counted;
    assert first is stale  #  the second round compiled the body anew, with the variable in view, and keeps it)
    assert resolved_as(second, "dup") == VAR
    assert_kept(body, second)


def test_calls_and_rounds_in_new_scopes_under_the_same_parent_keep_the_unit(twin):
    """Nothing hides a word and no name is bound anywhere in between: the unit is not forgotten for the new scopes."""
    twin.run("{x} {x dup drop} :f defun")
    body = twin.body("f")
    loop_body = twin.block("{7 dup drop}", "loop_body")

    for call in range(1, 6):
        assert twin.run(f"{call} f") == ok(call)
    assert twin.run("1 5 :i loop_body do") == ok(7, 7, 7, 7, 7)
    for tokens in (body, loop_body):
        (unit,) = twin.units(tokens)  # (made once, on the first run, and run by every call and every round)
        assert_kept(tokens, unit)


# ---------------------------------------------------------------------------
# 3. One block under different heads and in different function scopes
# ---------------------------------------------------------------------------

#: (the loop, with the name of its variable left open; what it leaves when the name is `i`; what it leaves when it
#: is `dup`). The block ``{7 dup +}`` adds 7 to itself, or to the loop's value when the loop's variable is `dup`.
#: (`do` is left to test_compiler.py, which runs the same block under `:i` and `:dup`; the loops with a scope of their
#: own that it does not run are here, and the loop scopes of `do` are in the tests that follow)
HEADS = [
    pytest.param("[1 2 3] {name} body dolist", ok(14, 14, 14), ok(8, 9, 10), id="dolist"),
    pytest.param("[1 2 3] 0 {name} :x body reduce", ok(14), ok(21), id="reduce"),
]


@pytest.mark.parametrize(("head", "plain", "shadowing"), HEADS)
def test_a_block_compiled_under_a_head_that_leaves_a_word_alone_is_forgotten_under_one_that_names_it(
    twin, head, plain, shadowing
):
    body = twin.block("{7 dup +}", "body")

    assert twin.run(head.format(name=":i")) == plain
    stale = body._unit
    assert resolved_as(stale, "dup") == WORD
    assert_kept(body, stale)

    assert twin.run(head.format(name=":dup")) == shadowing  # (the loop's variable hides `dup` from its first step)
    first, second = twin.units(body)
    assert first is stale
    assert resolved_as(second, "dup") == VAR  # (compiled again on the second iteration, in the scope that has it)
    assert_kept(body, second)  # (forgotten at the start of the first iteration: no drop counted)

    assert twin.run(head.format(name=":i")) == plain  # (the variable is gone: `dup` is the word again, nothing dropped)
    assert_kept(body, second)


@pytest.mark.parametrize(("head", "plain", "shadowing"), HEADS)
def test_a_block_compiled_under_a_head_that_named_a_word_finds_the_word_again_under_one_that_does_not(
    twin, head, plain, shadowing
):
    body = twin.block("{7 dup +}", "body")

    assert twin.run(head.format(name=":dup")) == shadowing
    unit = body._unit
    assert resolved_as(unit, "dup") == VAR
    assert_kept(body, unit)

    assert twin.run(head.format(name=":i")) == plain  # (the step for the variable finds none and looks the name up)
    assert_kept(body, unit)


#: How a function or a lambda is made of a body, with a parameter named `a` and with one named `dup`, and how each is
#: called with 1
CALLABLES = [
    pytest.param("{a} body :f defun {dup} body :g defun", "1 f", "1 g", id="function"),
    pytest.param("{a} body lambda :f set {dup} body lambda :g set", "1 f eval", "1 g eval", id="lambda"),
]


@pytest.mark.parametrize(("define", "call_a", "call_dup"), CALLABLES)
def test_a_body_shared_by_two_callables_is_forgotten_in_the_call_whose_parameter_is_named_like_the_word(
    twin, define, call_a, call_dup
):
    body = twin.block("{7 dup +}", "body")
    twin.run(define)

    assert twin.run(call_a) == ok(14)
    first = body._unit
    assert resolved_as(first, "dup") == WORD

    assert twin.run(call_dup) == ok(8)  # (`dup` is the argument)
    assert_rewarmed(body)

    assert twin.run(call_dup) == ok(8)
    second = body._unit
    assert resolved_as(second, "dup") == VAR

    assert twin.run(call_a) == ok(14)  # (the parameter `a` leaves `dup` the word: found again by the variable's step)
    assert_kept(body, second)


#: Blocks written in a body that two functions share: one is run by `eval`, the other by a loop (whose scope is a
#: child of the call's, so the name that hides `dup` is in the middle of the chain)
NESTED_BLOCKS = [
    pytest.param("{7 {dup +} eval}", ok(14), ok(8), id="eval"),
    pytest.param("{7 1 2 :k {dup +} do}", ok(28), ok(9), id="do-in-the-middle-of-the-chain"),
]


@pytest.mark.parametrize(("outer_source", "with_a", "with_dup"), NESTED_BLOCKS)
def test_a_block_written_in_a_shared_body_is_forgotten_in_the_scope_of_the_call_that_binds_the_word(
    twin, outer_source, with_a, with_dup
):
    outer = twin.block(outer_source, "outer")
    inner = next(token for token in outer if isinstance(token, StackerCore)).tokens
    twin.run("{a} outer :f defun {dup} outer :g defun")

    assert twin.run("1 f") == with_a
    first = inner._unit
    assert resolved_as(first, "dup") == WORD
    shared_body = assert_compiled(outer)

    assert twin.run("1 g") == with_dup  # (this call's scope binds `dup`, the block runs in a child of it)
    assert twin.units(inner)[0] is first
    assert inner._unit is not first  # (forgotten when it started under the call that binds `dup` ...)
    assert inner._drops == 0
    for later in twin.units(inner)[1:]:  # (... and, when the call runs it again, compiled with the variable in view)
        assert resolved_as(later, "dup") == VAR
    assert_kept(outer, shared_body)  # (the body itself names no such word: it keeps its unit through both calls)


@pytest.mark.parametrize(("outer_source", "with_a", "with_dup"), NESTED_BLOCKS)
def test_a_block_written_in_a_shared_body_compiled_where_the_word_is_bound_finds_the_word_where_it_is_not(
    twin, outer_source, with_a, with_dup
):
    outer = twin.block(outer_source, "outer")
    inner = next(token for token in outer if isinstance(token, StackerCore)).tokens
    twin.run("{a} outer :f defun {dup} outer :g defun")

    assert twin.run("1 g") == with_dup
    unit = inner._unit
    assert resolved_as(unit, "dup") == VAR

    assert twin.run("1 f") == with_a
    assert twin.run("1 g") == with_dup
    assert_kept(inner, unit)


#: A body that two functions share: it makes a lambda out of a block literal and calls it at once, so the lambda's call
#: runs in a child of the scope of the function's call. The two calls have parents of their own (one binds `dup`) and
#: no name is bound anywhere between one call and the other
LAMBDA_IN_A_SHARED_BODY = "{{} {7 dup +} lambda eval}"


def make_two_functions_around_a_lambda(twin):
    """Returns the token list of the lambda's body, and defines `f` (parameter `a`) and `g` (parameter `dup`)."""
    outer = twin.block(LAMBDA_IN_A_SHARED_BODY, "outer")
    lambda_body = [token for token in outer if isinstance(token, StackerCore)][1].tokens
    twin.run("{a} outer :f defun {dup} outer :g defun")
    return lambda_body


def test_a_block_run_under_another_parent_scope_that_binds_the_word_is_checked_afresh(twin):
    lambda_body = make_two_functions_around_a_lambda(twin)

    assert twin.run("1 f") == ok(14)
    first = lambda_body._unit
    assert resolved_as(first, "dup") == WORD

    assert twin.run("1 g") == ok(8)  # (the name is in the scope in the middle of the chain, which is new)
    assert twin.units(lambda_body) == [first]
    assert_rewarmed(lambda_body)


def test_a_block_compiled_under_a_parent_scope_that_binds_the_word_finds_the_word_under_another(twin):
    lambda_body = make_two_functions_around_a_lambda(twin)

    assert twin.run("1 g") == ok(8)
    unit = lambda_body._unit
    assert resolved_as(unit, "dup") == VAR

    assert twin.run("1 f") == ok(14)  # (the variable's step finds none and looks the name up)
    assert twin.run("1 g") == ok(8)
    assert_kept(lambda_body, unit)


# ---------------------------------------------------------------------------
# 4. Each kind of step runs as the interpreter does
# ---------------------------------------------------------------------------


#: (program, the kinds its block compiles to): a regular word of one or two arguments is a FAST step, which runs the
#: word directly when its arguments are plain values and through the word runner otherwise; both ways must leave
#: what the interpreter leaves, so the programs cover plain values, the values the runner converts or evaluates (a
#: String, a block, a Symbol), a stack too short, a host error, an error of the word's own, and a word with no result
FAST_PROGRAMS = [
    pytest.param("1 2 +", [CONST, CONST, FAST2], id="two-plain-values"),
    pytest.param("true false +", [CONST, CONST, FAST2], id="booleans-are-plain"),
    pytest.param("[1] [2] +", [LIST, LIST, FAST2], id="lists-are-plain"),
    pytest.param('"a" "b" +', [CONST, CONST, FAST2], id="strings-go-through-the-runner"),
    pytest.param('"a" 2 *', [CONST, CONST, FAST2], id="a-string-and-a-number"),
    pytest.param("{1} 2 +", [BLOCK, CONST, FAST2], id="a-block-argument-is-evaluated"),
    pytest.param("{} 2 +", [BLOCK, CONST, FAST2], id="a-block-argument-that-leaves-nothing"),
    pytest.param(":x 1 +", [CONST, CONST, FAST2], id="a-symbol-is-reported-as-one"),
    pytest.param("1 +", [CONST, FAST2], id="too-few-values"),
    pytest.param("+", [FAST2], id="no-values"),
    pytest.param('1 "a" +', [CONST, CONST, FAST2], id="a-host-type-error"),
    pytest.param("-1 sqrt", [CONST, FAST1], id="a-host-value-error"),
    pytest.param("[1 2] 5 nth", [LIST, CONST, WORD], id="a-priority-word-is-not-fast"),
    pytest.param("2.25 sqrt", [CONST, FAST1], id="one-plain-value"),
    pytest.param("-3 abs", [CONST, FAST1], id="one-negative-value"),
    pytest.param('"a" str', [CONST, FAST1], id="one-string-through-the-runner"),
    pytest.param("{4} sqrt", [BLOCK, FAST1], id="one-block-argument"),
    pytest.param("sqrt", [FAST1], id="one-argument-missing"),
    pytest.param(":x neg", [CONST, FAST1], id="one-symbol"),
    pytest.param("7 echo", [CONST, FAST1], id="a-word-with-no-result"),
    pytest.param('"s" echo', [CONST, FAST1], id="a-word-with-no-result-on-a-string"),
    pytest.param("[1 2 3] 1 + ", [LIST, CONST, FAST2], id="a-list-and-a-number"),
    pytest.param("null 1 +", [CONST, CONST, FAST2], id="null-is-plain"),
    pytest.param("true 1 +", [CONST, CONST, FAST2], id="a-boolean-under-a-number"),
    pytest.param("1 true +", [CONST, CONST, FAST2], id="a-boolean-over-a-number"),
    pytest.param("2 {1} +", [CONST, BLOCK, FAST2], id="a-block-on-top"),
    pytest.param("1 :x +", [CONST, CONST, FAST2], id="a-symbol-on-top"),
    pytest.param('1 "2" +', [CONST, CONST, FAST2], id="a-string-on-top"),
    pytest.param('"12" 3 *', [CONST, CONST, FAST2], id="a-string-of-digits-is-text"),
    pytest.param("9 1 2 +", [CONST, CONST, CONST, FAST2], id="a-value-under-the-arguments-stays"),
    pytest.param("[[1] [2]] [3] +", [LIST, LIST, FAST2], id="nested-lists"),
    pytest.param("[1 2] array [3] array +", [LIST, WORD, LIST, WORD, FAST2], id="arrays-go-through-the-runner"),
    pytest.param("[1 2] array 1 +", [LIST, WORD, CONST, FAST2], id="an-array-and-a-number"),
    pytest.param("3 2 1 - -", [CONST, CONST, CONST, FAST2, FAST2], id="two-fast-words-in-a-row"),
]


def test_a_fast_word_runs_directly_on_plain_values_and_through_the_runner_otherwise(twin, monkeypatch):
    blk = twin.block("{+}")
    compiled_tables = twin.compiled.stacker.operator_manager
    runs = []  # the words the runner ran for the compiling side (the interpreter side always runs `+` through it)
    original = StackerCore._run_word

    def recording(core, token, kind, op, stack):
        if core.operator_manager is compiled_tables:
            runs.append(token)
        return original(core, token, kind, op, stack)

    monkeypatch.setattr(StackerCore, "_run_word", recording)
    for given, runs_the_runner in (("1 2", False), ('"a" "b"', True), ("{1} 2", True), (":x 1", True), ("1", True)):
        runs.clear()
        twin.run(f"{given} blk eval")
        assert ("+" in runs) is runs_the_runner, given
    assert steps(assert_compiled(blk)) == [FAST2]


def test_one_fast_step_run_on_values_of_changing_types_leaves_what_the_interpreter_leaves(twin):
    blk = twin.block("{+}")
    for given in ("1 2", '"a" "b"', "{1} 2", "2 {1}", "1.5 2", "[1] [2]", ":x 1", "true 1", "1"):
        twin.run(f"{given} blk eval")
    assert steps(assert_compiled(blk)) == [FAST2]


@pytest.mark.parametrize(("program", "kinds"), FAST_PROGRAMS)
def test_a_regular_word_runs_as_the_interpreter_does_whatever_its_arguments_are(twin, program, kinds):
    blk = twin.block("{" + program + "}")
    for _ in range(2):
        twin.run("blk eval")  # (the twin compares the result, the output, the error and the trace)
    assert steps(assert_compiled(blk)) == kinds


#: (program, the kinds its block compiles to on the first run, the kinds on the second): a symbol and `set` fuse
#: into SET, which must bind, refuse and fail as `set` does, and leave the same stack when it fails. A name the
#: set makes is undefined, or a word, when the block is first compiled; the binding drops that unit (the step
#: after it took the name for something else), and the second run compiles the block with the variable
SET_PROGRAMS = [
    pytest.param("5 :x set x", [CONST, SET, UNDEF], [CONST, SET, VAR], id="binds-and-reads-back"),
    pytest.param("5 :x = x", [CONST, SET, UNDEF], [CONST, SET, VAR], id="the-equals-spelling"),
    pytest.param("5 :true set", [CONST, SET], [CONST, SET], id="a-literal-as-the-name"),
    pytest.param("5 :help set", [CONST, SET], [CONST, SET], id="a-repl-command-as-the-name"),
    pytest.param(":x set", [SET], [SET], id="no-value-to-take"),
    pytest.param("5 :dup set dup", [CONST, SET, WORD], [CONST, SET, VAR], id="a-word-hidden-by-the-set-before-it"),
    pytest.param(
        "1 :+ set 2 3 +", [CONST, SET, CONST, CONST, FAST2], [CONST, SET, CONST, CONST, VAR],
        id="an-arithmetic-word-hidden-by-the-set",
    ),
    pytest.param(
        "5 :set set 7 :y set", [CONST, SET, CONST, SET], [CONST, CONST, VAR, CONST, CONST, VAR],
        id="set-itself-hidden-mid-block",
    ),
    pytest.param('5 "x" set', [CONST, CONST, WORD], [CONST, CONST, WORD], id="a-string-is-not-a-name"),
    pytest.param("5 {x} set x", [CONST, BLOCK, WORD, UNDEF], [CONST, BLOCK, WORD, VAR], id="a-quoted-name-is-read-by-the-word"),
    pytest.param(
        "[] :items set 1 :items get", [LIST, SET, CONST, CONST, WORD], [LIST, SET, CONST, CONST, WORD],
        id="a-list-bound-and-indexed",
    ),
    pytest.param("{1 2} :b set b", [BLOCK, SET, UNDEF], [BLOCK, SET, VAR], id="a-block-as-the-value-stays-a-block"),
    pytest.param('"s" :s set s', [CONST, SET, UNDEF], [CONST, SET, VAR], id="a-string-as-the-value"),
    pytest.param(":a :b set b", [CONST, SET, UNDEF], [CONST, SET, VAR], id="a-symbol-as-the-value"),
    pytest.param(
        "0 :outer set 1 2 :i {i :outer set} do outer", [CONST, SET, CONST, CONST, CONST, DO, UNDEF],
        [CONST, SET, CONST, CONST, CONST, DO, VAR], id="an-outer-variable-updated-from-a-loop",
    ),
]


@pytest.mark.parametrize(("program", "first", "second"), SET_PROGRAMS)
def test_a_symbol_and_set_run_as_the_interpreter_does(twin, program, first, second):
    blk = twin.block("{" + program + "}")
    for _ in range(2):
        twin.run("blk eval")
    units = twin.units(blk)
    assert (steps(units[0]), steps(units[-1])) == (first, second)


#: (program, the kinds its block compiles to): a control word with its bodies written as literals right before it
#: is one step, run with the bodies in place; it must do what the word does, in the same order, whatever is on the
#: stack: the right values, too few of them, values of the wrong kind, a condition that is a block, a body that
#: breaks, fails or leaves values, a body that is not a literal (a variable, a value made by a word)
CONTROL_PROGRAMS = [
    pytest.param("1 3 :k {k} do", [CONST, CONST, CONST, DO], id="do"),
    pytest.param("1 3 :k {k 2 == {break} if k} do", [CONST, CONST, CONST, DO], id="do-with-a-break-in-an-if"),
    pytest.param("3 1 :k {k} do", [CONST, CONST, CONST, DO], id="do-over-an-empty-range"),
    pytest.param(":k {k} do", [CONST, DO], id="do-with-too-few-values"),
    pytest.param("1 3 {k} do", [CONST, CONST, DO], id="do-without-a-symbol"),
    pytest.param("1 :x {} do", [CONST, CONST, DO], id="do-with-a-symbol-as-a-bound"),
    pytest.param('1 "3" :k {k} do', [CONST, CONST, CONST, DO], id="do-with-a-string-as-a-bound"),
    pytest.param("1 3 :help {1} do", [CONST, CONST, CONST, DO], id="do-with-a-reserved-name"),
    pytest.param("1 {2} :k {k} do", [CONST, BLOCK, CONST, DO], id="do-with-a-block-as-a-bound"),
    pytest.param("1 3 :k {k foo} do", [CONST, CONST, CONST, DO], id="do-whose-body-fails"),
    pytest.param("1 3 :k {{k}} do {eval} map", [CONST, CONST, CONST, DO, BLOCK, WORD], id="do-making-closures"),
    pytest.param("{k} :b set 1 3 :k b do", [BLOCK, SET, CONST, CONST, CONST, VAR, WORD], id="do-with-a-body-in-a-variable"),
    # (a loop admits its body's unit without the entry checks after an iteration passed them: what the loop
    # itself changes must still be followed)
    pytest.param("1 6 :i {i 3 == {{a b} {a b *} :- defun} if 5 2 - echo} do", [CONST, CONST, CONST, DO], id="do-whose-body-replaces-a-word-of-its-own-in-mid-loop"),
    pytest.param("1 6 :i {i 3 == {9 :echo set} if i echo} do", [CONST, CONST, CONST, DO], id="do-whose-body-hides-a-word-of-its-own-in-mid-loop"),
    pytest.param("1 4 :dup {dup} do", [CONST, CONST, CONST, DO], id="do-whose-variable-is-a-word-of-the-body"),
    pytest.param("[1 2 3] :echo {echo} dolist", [LIST, CONST, DOLIST], id="dolist-whose-variable-is-a-word-of-the-body"),
    pytest.param("0 :n set {n 1 + :n set n 3 == {{a b} {a b *} :- defun} if n 6 <} {5 2 - echo} while", [CONST, SET, WHILE], id="while-whose-condition-replaces-a-word-of-the-body"),
    pytest.param("6 :n set {n 1 - :n set n 0 >} {n 3 == {{a b} {a b * -1 *} :- defun} if 5 2 - echo} while", [CONST, SET, WHILE], id="while-whose-body-replaces-a-word-of-the-condition"),
    pytest.param("0 :n set {n 1 + :n set n 5 == {9 :dup set} if 1 2 dup} 8 times", [CONST, SET, TIMES], id="times-whose-body-hides-a-word-it-uses-after-from-the-fifth-iteration"),
    pytest.param("1 100 :i {i 5 == {break} if i} do", [CONST, CONST, CONST, DO], id="do-breaking-after-trusted-iterations"),
    pytest.param("[1 2 3 4 5 6] :i {i 4 == {9 :echo set} if i echo} dolist", [LIST, CONST, DOLIST], id="dolist-whose-body-hides-a-word-from-the-fourth-iteration"),
    pytest.param("0 :n set {n 1 + :n set n 4 == {9 :echo set} if n echo n 6 == {break} if} loop", [CONST, SET, LOOP], id="loop-whose-body-hides-a-word-from-the-fourth-iteration"),
    pytest.param("1 6 :i {i 3 == {{} {{5}} :+ defmacro} if 1 2 + echo} do", [CONST, CONST, CONST, DO], id="do-whose-body-makes-a-word-a-macro-in-mid-loop"),
    pytest.param("[1 2] :k {k} dolist", [LIST, CONST, DOLIST], id="dolist"),
    pytest.param("[1 2 3] :k {k 2 == {break} if k} dolist", [LIST, CONST, DOLIST], id="dolist-with-a-break"),
    pytest.param("5 :k {k} dolist", [CONST, CONST, DOLIST], id="dolist-over-a-number"),
    pytest.param("{k} dolist", [DOLIST], id="dolist-with-too-few-values"),
    pytest.param('"ab" :k {k} dolist', [CONST, CONST, DOLIST], id="dolist-over-a-string"),
    pytest.param("0 :c set {c 1 + :c set c 3 == {break} if} loop c", [CONST, SET, LOOP, VAR], id="loop"),
    pytest.param("0 :c set {c 1 + :c set} {c 3 <} while", [CONST, SET, WHILE], id="while-with-blocks-reversed"),
    pytest.param("0 :c set {c 3 <} {c 1 + :c set} while c", [CONST, SET, WHILE, VAR], id="while"),
    pytest.param("0 :c set {c 3 <} {c 1 + :c set 7} while", [CONST, SET, WHILE], id="while-whose-body-leaves-values"),
    pytest.param("{} {1} while", [WHILE], id="while-whose-condition-leaves-nothing"),
    pytest.param("{foo} {1} while", [WHILE], id="while-whose-condition-fails"),
    pytest.param("0 :c set {c 1 + :c set c 2 == {break} if true} {1} while", [CONST, SET, WHILE], id="while-whose-condition-breaks"),
    pytest.param("true {1} if", [CONST, IF], id="if"),
    pytest.param("false {1} if", [CONST, IF], id="if-not-taken"),
    pytest.param("{1} if", [IF], id="if-with-too-few-values"),
    pytest.param("{true} {1} if", [BLOCK, IF], id="if-with-a-block-condition"),
    pytest.param("{} {1} if", [BLOCK, IF], id="if-whose-condition-leaves-nothing"),
    pytest.param(":x {1} if", [CONST, IF], id="if-with-a-symbol-condition"),
    pytest.param('"" {1} if', [CONST, IF], id="if-with-an-empty-string-condition"),
    pytest.param("true {foo} if", [CONST, IF], id="if-whose-body-fails"),
    pytest.param("true {1} {2} ifelse", [CONST, IFELSE], id="ifelse"),
    pytest.param("false {1} {2} ifelse", [CONST, IFELSE], id="ifelse-not-taken"),
    pytest.param("{1} {2} ifelse", [IFELSE], id="ifelse-with-too-few-values"),
    pytest.param("{false} {1} {foo} ifelse", [BLOCK, IFELSE], id="ifelse-whose-taken-branch-fails"),
    pytest.param("true {1} 2 ifelse", [CONST, BLOCK, CONST, WORD], id="ifelse-with-a-value-as-a-branch"),
    pytest.param("true 1 {2} ifelse", [CONST, CONST, BLOCK, WORD], id="ifelse-with-a-value-as-the-other-branch"),
    pytest.param("{1} 3 times", [TIMES], id="times"),
    pytest.param("{1} 0 times", [TIMES], id="times-zero"),
    pytest.param("{1} -1 times", [TIMES], id="times-negative"),
    pytest.param("{1} 2.5 times", [TIMES], id="times-fractional"),
    pytest.param("{1} true times", [TIMES], id="times-boolean"),
    pytest.param("3 :n set {1} n times", [CONST, SET, TIMES], id="times-with-a-variable-count"),
    pytest.param("{2} :n set {1} n times", [BLOCK, SET, TIMES], id="times-with-a-variable-holding-a-block"),
    pytest.param(":s :n set {1} n times", [CONST, SET, TIMES], id="times-with-a-variable-holding-a-symbol"),
    pytest.param('"3" :n set {1} n times', [CONST, SET, TIMES], id="times-with-a-variable-holding-a-string"),
    pytest.param("{1} :n times", [BLOCK, CONST, WORD], id="times-with-a-symbol-count-is-not-inlined"),
    pytest.param("{1} {2} times", [BLOCK, BLOCK, WORD], id="times-with-a-block-count-is-not-inlined"),
    pytest.param("{1} {} times", [BLOCK, BLOCK, WORD], id="times-with-an-empty-block-count"),
    pytest.param("{1} depth times", [BLOCK, WORD, WORD], id="times-with-a-word-between-is-not-inlined"),
    pytest.param("{1} nosuch times", [BLOCK, UNDEF, WORD], id="times-with-an-undefined-count"),
    pytest.param("{break 1} 3 times", [TIMES], id="times-with-a-break"),
    pytest.param("{foo} 2 times", [TIMES], id="times-whose-body-fails"),
    pytest.param("1 2 :k {k {k} :j {j} do} do", [CONST, CONST, CONST, DO], id="nested-do"),
    pytest.param("true {true {1} if} if", [CONST, IF], id="nested-if"),
]


@pytest.mark.parametrize(("program", "kinds"), CONTROL_PROGRAMS)
def test_a_control_word_with_literal_bodies_runs_as_the_interpreter_does(twin, program, kinds):
    blk = twin.block("{" + program + "}")
    for _ in range(2):
        twin.run("blk eval")
    assert steps(twin.units(blk)[-1]) == kinds


def test_a_times_whose_variable_count_vanishes_between_two_runs_leaves_the_count_to_the_word(twin):
    twin.run("3 :n set")
    blk = twin.block("{{1} n times}")
    assert twin.run("blk eval") == ok(1, 1, 1)
    assert steps(assert_compiled(blk)) == [TIMES]
    twin.do(lambda stacker: stacker.variables.pop("n"))
    assert twin.run("blk eval") == undefined("n", "{1}")  # (the body is pushed first, as the word reads its count after)


def test_a_control_word_re_registered_is_not_inlined_and_the_word_registered_runs(twin):
    twin.do(register_host_words)
    blk = twin.block("{true {1} if}")
    assert twin.run("blk eval") == ok(1)
    twin.do(lambda stacker: stacker.register_operator("if", lambda *taken: taken[-1].append("mine"), 2, False, ""))
    assert twin.run("blk eval") == ok("mine")  # (the unit was stale: the interpreter ran this one)
    assert twin.run("blk eval") == ok("mine")
    assert steps(assert_compiled(blk)) == [CONST, BLOCK, WORD]
    twin.do(lambda stacker: stacker.register_operator("if", inline.ORIGINALS["if"], 2, False, ""))
    assert twin.run("blk eval") == ok(1)
    assert twin.run("blk eval") == ok(1)
    assert steps(assert_compiled(blk)) == [CONST, IF]  # (the built-in again: inlined again)


def test_a_control_word_hidden_by_a_variable_mid_block_leaves_its_later_uses_to_the_interpreter(twin):
    blk = twin.block("{true {1} if 99 :if global true {2} if}")
    assert twin.run("blk eval") == ok(1, True, "{2}", 99)
    assert_dropped(blk)


#: (program, the kinds): a call of a function written in Stacker, with every kind of argument, and what the
#: stack holds when the call fails
CALL_PROGRAMS = [
    pytest.param("{x} {x} :f defun 1 f", [CONST, CALL], id="a-plain-argument"),
    pytest.param("{x} {x} :f defun {1} f", [BLOCK, CALL], id="a-block-argument-stays-raw"),
    pytest.param('{x} {x} :f defun "s" f', [CONST, CALL], id="a-string-argument"),
    pytest.param("{x} {x} :f defun :s f", [CONST, CALL], id="a-symbol-argument"),
    pytest.param("{x y} {x y +} :f defun 9 1 2 f", [CONST, CONST, CONST, CALL], id="a-value-under-the-arguments-stays"),
    pytest.param("{x} {x foo} :f defun 9 1 f", [CONST, CONST, CALL], id="a-call-that-fails"),
    pytest.param("{x} {x drop drop} :f defun 9 1 f", [CONST, CONST, CALL], id="a-body-that-pops-past-its-stack"),
    pytest.param("{x} {} :f defun 1 f", [CONST, CALL], id="a-body-that-leaves-nothing"),
    pytest.param("{x} {x x} :f defun 1 f", [CONST, CALL], id="a-body-that-leaves-two-values"),
    pytest.param("{x} {x} :f defun f", [CALL], id="a-call-without-its-argument"),
]


@pytest.mark.parametrize(("program", "kinds"), CALL_PROGRAMS)
def test_a_call_of_a_function_runs_as_the_interpreter_does(twin, program, kinds):
    definition, _, call = program.partition(" defun ")
    twin.run(definition + " defun")
    blk = twin.block("{" + call + "}")
    for _ in range(2):
        twin.run("blk eval")
    assert steps(assert_compiled(blk)) == kinds


def test_a_host_error_no_word_wraps_reaches_the_program_from_a_fast_step_as_from_the_interpreter(twin):
    # a division by zero is not among the errors the word runner wraps: it reaches the program as it is
    blk = twin.block("{1 0 /}")
    for side in (twin.reference, twin.compiled):
        with pytest.raises(ZeroDivisionError):
            side.stacker.eval("blk eval")
    assert steps(assert_compiled(blk)) == [CONST, CONST, FAST2]


def test_a_block_with_every_kind_of_step_that_can_finish_compiles_to_them_and_runs_as_the_interpreter_does(twin):
    twin.run("{x} {x 1 +} :f defun {a} {{a a +}} :twice defmacro 7 :v set")
    twin.do(register_host_words)
    blk = twin.block('{true 1 "two" :three [v 2] {9} v f 3 twice 4 triple drop}')

    assert twin.run("blk eval") == ok(True, 1, "two", Symbol("three"), [7, 2], "{9}", 8, 6)
    assert steps(blk._unit) == [CONST, CONST, CONST, CONST, LIST, BLOCK, VAR, CALL, CONST, MACRO, CONST, WORD, WORD]
    assert_compiled(blk)


def test_a_literal_spelled_as_a_name_and_a_block_still_text_run_as_the_interpreter_does(twin):
    """No program text makes these two steps: a block literal turns its literals into values when it is made."""
    blk = twin.raw_block(["3", "{1 2}", "4"], "raw")
    assert twin.run("raw eval raw eval") == ok(3, "{1 2}", 4, 3, "{1 2}", 4)
    assert steps(blk._unit) == [LIT, NAME, LIT]
    assert_compiled(blk)


def test_a_list_literal_is_built_from_the_variables_as_they_are_on_every_run(twin):
    twin.run("1 :x set")
    blk = twin.block("{[x 2 [x 3]]}")
    assert twin.run("blk eval blk eval") == ok([1, 2, [1, 3]], [1, 2, [1, 3]])
    unit = assert_compiled(blk)
    assert steps(unit) == [LIST]

    twin.run("9 :x set")
    assert twin.run("blk eval") == ok([9, 2, [9, 3]])
    assert_kept(blk, unit)


def test_a_list_literal_makes_a_list_of_its_own_on_every_run(twin):
    blk = twin.block("{[1 [2 3]]}")
    stack = stack_data()
    twin.compiled.stacker.eval("blk eval blk eval", stack)
    first, second = stack
    assert first == second
    assert first is not second
    assert first[1] is not second[1]
    assert steps(assert_compiled(blk)) == [LIST]


def test_a_block_pushed_by_a_compiled_loop_body_keeps_the_scope_of_its_iteration(twin):
    twin.run("[] array :fs set")
    body = twin.block("{{i} fs append!}", "body")
    assert twin.run("1 3 :i body do fs {eval} map") == ok([1, 2, 3])
    assert steps(assert_compiled(body)) == [BLOCK, VAR, WORD]


def test_a_block_pushed_by_a_compiled_function_body_keeps_the_scope_of_its_call(twin):
    twin.run("{n} {{n}} :mk defun")
    assert twin.run("1 mk 2 mk 3 mk 3 listn {eval} map") == ok([1, 2, 3])
    assert steps(assert_compiled(twin.body("mk"))) == [BLOCK]


def test_a_macro_called_in_a_compiled_block_expands_where_the_call_stands(twin):
    twin.run("{a} {{a a +}} :twice defmacro")
    blk = twin.block("{3 twice 4 twice}")
    assert twin.run("blk eval") == ok(6, 8)
    assert steps(assert_compiled(blk)) == [CONST, MACRO, CONST, MACRO]


#: The errors a step that cannot run raises: (the class name, the message)
COLON_ALONE = ("StackerSyntaxError", "`:` is not a symbol: `:` must be followed by a name")
COLON_AND_NUMBER = ("StackerSyntaxError", "`:1` is not a symbol: `:` must be followed by a name")
DOLLAR_NAME = ("StackerSyntaxError", "`$x` is not a symbol: a symbol is written `:x` (`$` is no longer used)")
BLOCK_IN_LIST = (
    "StackerSyntaxError",
    "a code block cannot be written inside a list literal; use {x} 1 listn, or [:x] for a symbol",
)
REPL_COMMAND = ("ReservedWordError", "`help` is a REPL command: type it alone at the REPL's prompt")


def register_macro_under(token):
    """A host action that registers a macro, expanding to the code ``{9}``, under ``token`` (any text, even ``:s``)."""

    def register(stacker):
        body = next(iter(stacker.eval("{{9}}")))
        stacker.register_macro(token, StackerMacro(token, [], body))

    return register


#: Tokens that are no name, with what a block ``{TOKEN 2}`` leaves while no macro has that text. Each would be a
#: symbol, a list or an error: the interpreter looks a macro up before it reads the token's kind
TOKENS_A_MACRO_CAN_TAKE = {
    ":s": ok(Symbol("s"), 2),
    "[1 2]": ok([1, 2], 2),
    ":": fails(*COLON_ALONE),
    "$x": fails(*DOLLAR_NAME),
}
tokens_a_macro_can_take = pytest.mark.parametrize(
    "token", list(TOKENS_A_MACRO_CAN_TAKE), ids=["a-symbol", "a-list", "a-colon-alone", "a-dollar-name"]
)


@tokens_a_macro_can_take
def test_a_macro_registered_under_a_token_that_is_no_name_is_expanded_where_the_token_stands(twin, token):
    twin.do(register_macro_under(token))
    blk = twin.block("{1 " + token + " 2}")
    assert twin.run("blk eval") == ok(1, 9, 2)
    assert steps(assert_compiled(blk)) == [CONST, MACRO, CONST]


@tokens_a_macro_can_take
def test_a_macro_registered_under_such_a_token_after_the_unit_was_made_takes_the_token_from_then_on(twin, token):
    """The unit holds the token as a value (or as the error it is) in its first step; only the generation is stale."""
    blk = twin.block("{" + token + " 2}")
    assert twin.run("blk eval") == TOKENS_A_MACRO_CAN_TAKE[token]
    stale = blk._unit

    twin.do(register_macro_under(token))
    assert twin.run("blk eval") == ok(9, 2)
    assert_rewarmed(blk)
    assert twin.run("blk eval") == ok(9, 2)
    assert blk._unit is not stale
    assert steps(blk._unit) == [MACRO, CONST]


#: (the step's text, its kind, the error it raises). A step that cannot run raises at its own position
FAILING_STEPS = [
    pytest.param("nosuch", UNDEF, ("UndefinedSymbolError", "`nosuch` is not defined."), id="an-undefined-name"),
    pytest.param("help", UNDEF, REPL_COMMAND, id="a-repl-command"),
    pytest.param(":", BAD, COLON_ALONE, id="a-colon-alone"),
    pytest.param(":1", BAD, COLON_AND_NUMBER, id="a-colon-and-a-number"),
    pytest.param("$x", BAD, DOLLAR_NAME, id="a-dollar-name"),
    pytest.param("[{1}]", BAD_LIST, BLOCK_IN_LIST, id="a-block-in-a-list"),
    pytest.param("[1 :]", BAD_LIST, COLON_ALONE, id="a-colon-in-a-list"),
]


@pytest.mark.parametrize(("step", "kind", "error"), FAILING_STEPS)
def test_a_step_that_cannot_run_raises_at_its_own_position_after_the_output_before_it(twin, step, kind, error):
    blk = twin.block('{"a" echo ' + step + ' "b" echo}')
    for _ in range(2):  # (an error does not drop the unit: the second run fails the same way)
        assert twin.run("blk eval") == fails(*error, out="a\n")  # "a" is printed, "b" is not
    assert steps(assert_compiled(blk)) == [CONST, FAST1, kind, CONST, FAST1]  # (`echo` is a regular word)


def test_a_string_token_with_a_bad_escape_in_a_block_of_raw_tokens_raises_at_its_own_position(twin):
    """A block literal refuses the escape when it is made; a block a host builds fails where the token stands."""
    blk = twin.raw_block(['"a"', '"\\q"', '"b"'], "raw")
    bad_escape = ("StackerSyntaxError", "unknown escape `\\q` in a string; write `\\\\` for a backslash")
    for _ in range(2):
        assert twin.run("raw eval") == fails(*bad_escape, "a")  # ("a" was pushed, "b" never is)
    assert steps(assert_compiled(blk)) == [CONST, BAD, CONST]


#: A body that stops its loop on the third round, for each loop word. ``BREAK`` is `break`, or `stop`, a word that does
LOOPS_THAT_BREAK = [
    pytest.param("{i 3 == {BREAK} if i}", "1 5 :i body do", id="do"),
    pytest.param("{i 3 == {BREAK} if i}", "[1 2 3 4 5] :i body dolist", id="dolist"),
    pytest.param("{n 1 + :n set n 3 == {BREAK} if n}", "0 :n set body 10 times", id="times"),
    pytest.param("{n 1 + :n set n 3 == {BREAK} if n}", "0 :n set {true} body while", id="while"),
    pytest.param("{n 1 + :n set n 3 == {BREAK} if n}", "0 :n set body loop", id="loop"),
]


@pytest.mark.parametrize(("body_source", "loop"), LOOPS_THAT_BREAK)
def test_break_in_a_compiled_loop_body_leaves_the_loop_and_the_unit_alone(twin, body_source, loop):
    body = twin.block(body_source.replace("BREAK", "break"), "body")
    assert twin.run(loop) == ok(1, 2)
    unit = assert_compiled(body)
    assert twin.run(loop) == ok(1, 2)  # (the second run, on the same unit)
    assert_kept(body, unit)


@pytest.mark.parametrize(("body_source", "loop"), LOOPS_THAT_BREAK)
def test_break_in_a_compiled_function_called_from_a_loop_leaves_the_loop_and_both_units_alone(twin, body_source, loop):
    twin.run("{} {break} :stop defun")
    body = twin.block(body_source.replace("BREAK", "stop"), "body")
    assert twin.run(loop) == ok(1, 2)
    unit, stop_unit = assert_compiled(body), assert_compiled(twin.body("stop"))
    assert twin.run(loop) == ok(1, 2)  # (the second run, on the same unit)
    assert_kept(body, unit)
    assert_kept(twin.body("stop"), stop_unit)


#: (a block that fails, the error `try` reports, what the failed block had printed, the stack it held when it failed)
FAILING_BLOCKS = [
    pytest.param("{1 2 nosuch 3}", "UndefinedSymbolError", "`nosuch` is not defined.", "", [1, 2], id="undefined-name"),
    pytest.param("{1 drop drop 3}", "DropError", "Stack is empty", "", [], id="stack-underflow"),
    pytest.param('{"a" echo 1 0 / "b" echo}', "ZeroDivisionError", "division by zero", "a\n", [], id="host-error"),
    pytest.param(
        "{[1 2] 5 nth}",
        "StackerIndexError",
        "`nth` index 5 is out of range for a length of 2",
        "",
        [[1, 2]],
        id="index",
    ),
]


@pytest.mark.parametrize(("source", "kind", "message", "printed", "held"), FAILING_BLOCKS)
def test_try_around_a_compiled_block_that_fails_reports_what_the_stack_held_at_the_failure(
    twin, source, kind, message, printed, held
):
    risky = twin.block(source, "risky")
    caught = {"kind": kind, "message": message, "stack": held}
    for _ in range(2):  # (an error does not drop the unit: the second run fails the same way)
        assert twin.run("risky {} try") == ok(caught, out=printed)
    assert_compiled(risky)


def test_try_around_a_compiled_block_in_a_loop_catches_the_failing_round_and_the_others_go_on(twin):
    body = twin.block("{{i 3 == {nosuch} if i} {drop 0} try}", "body")
    risky = next(token for token in body if isinstance(token, StackerCore)).tokens
    assert twin.run("1 5 :i body do") == ok(1, 2, 0, 4, 5)  # (round 3 is caught, its handler leaves 0)
    assert_compiled(body)
    assert_compiled(risky)


@pytest.mark.parametrize(
    ("definition", "word"),
    [pytest.param(DEFINE_F, "f", id="a-function"), pytest.param(DEFINE_M, "m", id="a-macro")],
)
def test_eval_of_a_symbol_in_a_compiled_block_runs_the_name_as_it_means_when_the_step_runs(twin, definition, word):
    blk = twin.block("{5 :" + word + " eval}")
    assert twin.run("blk eval") == undefined(word, 5)  # (the symbol is a value to the unit; `eval` looks it up)
    assert steps(blk._unit) == [CONST, CONST, WORD]

    twin.run(definition)
    assert twin.run("blk eval") == ok(105)
    assert_rewarmed(blk)  # (the word tables changed: the unit is stale, though it took no name for the word)
    assert twin.run("blk eval") == ok(105)
    assert steps(assert_compiled(blk)) == [CONST, CONST, WORD]


# ---------------------------------------------------------------------------
# 5. Re-entrancy: a unit running again inside its own run, and dropped from the inside
# ---------------------------------------------------------------------------


def test_a_function_that_calls_itself_runs_on_one_unit_at_every_level(twin):
    twin.run("{n} {n 2 < {n} {n 1 - fib n 2 - fib +} ifelse} :fib defun")
    body = twin.body("fib")
    assert twin.run("12 fib") == ok(144)
    (unit,) = twin.units(body)  # (made once, on the first call; every level of the recursion ran it)
    assert steps(unit) == [VAR, CONST, FAST2, IFELSE]  # (the two branches are inlined into the `ifelse`)
    assert_kept(body, unit)
    for token in body:
        if isinstance(token, StackerCore):
            assert_compiled(token.tokens)


#: f(3) replaces f by a body that multiplies by 1000, then calls it: f(2) is 2000. Every call above f(3) is still
#: running the old body and adds its n to the result of the call below it
REDEFINES_ON_THE_WAY_DOWN = "{n} {n 0 <= {0} {n 3 == {{n} {n 1000 *} :f defun} if n 1 - f n +} ifelse} :f defun"
#: f(2) replaces f by a body that multiplies by 100 between its two calls of f
REDEFINES_BETWEEN_TWO_CALLS = "{n} {n 0 <= {0} {n 1 - f n 2 == {{n} {n 100 *} :f defun} if n 1 - f +} ifelse} :f defun"


@pytest.mark.parametrize("depth", [3, 4, 5, 8])
def test_calls_still_running_a_unit_that_an_inner_call_dropped_finish_as_the_interpreter_does(twin, depth):
    twin.run(REDEFINES_ON_THE_WAY_DOWN)
    old_body = twin.body("f")

    assert twin.run(f"{depth} f") == ok(2000 + sum(range(3, depth + 1)))
    (unit,) = twin.units(old_body)  # (the old body is not called again once f is redefined)
    assert old_body._unit is not unit
    assert old_body._drops == 1  # (one change, whatever the number of calls running the unit when it was made)

    assert twin.run(f"{depth} f") == ok(depth * 1000)  # (the new body)


def test_a_call_that_redefines_its_function_between_two_calls_of_it_finishes_as_the_interpreter_does(twin):
    twin.run(REDEFINES_BETWEEN_TWO_CALLS)
    old_body = twin.body("f")
    assert twin.run("3 f") == ok(300)
    (unit,) = twin.units(old_body)
    assert old_body._unit is not unit
    assert old_body._drops == 1


def test_the_rest_of_every_call_running_a_unit_is_run_with_the_words_a_call_below_it_defined(twin):
    """f(2) defines `g`, which every call above it uses after its recursive call; the unit took `g` for undefined."""
    twin.run("{n} {n 0 <= {0} {n 2 == {{x} {x 100 +} :g defun} if n 1 - f n g +} ifelse} :f defun")
    recursive_branch = [token.tokens for token in twin.body("f") if isinstance(token, StackerCore)][1]

    assert twin.run("4 f") == ok(101 + 102 + 103 + 104)
    stale, anew, *_ = twin.units(recursive_branch)
    assert resolved_as(stale, "g") == UNDEF
    assert resolved_as(anew, "g") == CALL  # (a call made after the drop compiled the branch anew)
    assert recursive_branch._unit is not stale
    assert recursive_branch._drops == 1


def test_every_level_of_a_recursion_that_binds_a_local_named_like_a_word_finishes_as_the_interpreter_does(twin):
    """Each level binds `dup` in its own call's scope after the call below it; the unit took `dup` for the word."""
    twin.run("{n} {n 0 <= {0} {n 1 - f n :dup set dup +} ifelse} :f defun")
    body = twin.body("f")
    nested = [token.tokens for token in body if isinstance(token, StackerCore)][1]

    assert twin.run("5 f") == ok(15)
    (unit,) = twin.units(nested)
    assert resolved_as(unit, "dup") == WORD
    assert nested._unit is not unit
    assert nested._drops >= 1
    assert_compiled(body)  # (the body itself names no such word)


# ---------------------------------------------------------------------------
# 6. Off, default and eager leave the same results
# ---------------------------------------------------------------------------

#: The states a program runs in: (whether the interpreter compiles, the threshold)
STATES = {"off": (False, None), "default": (True, DEFAULT_THRESHOLD), "eager": (True, 1)}

#: (a program, what it leaves). Each runs a block more often than the default threshold, so every state meets it
PARITY_PROGRAMS = [
    pytest.param(
        "{n} {n 2 < {n} {n 1 - fib n 2 - fib +} ifelse} :fib defun 1 12 :i {i fib echo} do",
        ok(out=lines(1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144)),
        id="recursion-called-from-a-loop",
    ),
    pytest.param(
        "[] array :fs set 1 20 :i {{i} fs append!} do fs {eval} map 0 :acc :x {acc x +} reduce",
        ok(210),
        id="closures-made-by-a-loop-and-summed",
    ),
    pytest.param(
        "1 20 :i {i echo i 15 == {nosuch} if} do",
        undefined("nosuch", out=lines(*range(1, 16))),
        id="an-error-on-the-fifteenth-round",
    ),
    pytest.param(
        "{x} {x 1 +} :inc defun 1 20 :i {i 12 == {{x} {x 100 +} :inc defun} if i inc echo} do",
        ok(out=lines(*range(2, 13), *range(112, 121))),
        id="a-function-redefined-in-the-middle",
    ),
    pytest.param(
        "1 20 :i {i 12 == {99 :dup set} if 5 dup echo drop} do",
        ok(out=lines(*[5] * 11, *[99] * 9)),
        id="a-variable-that-hides-a-word-in-the-middle",
    ),
    pytest.param(
        '1 20 :i {i 12 == {"triple" disable_plugin} if i triple echo} do',
        undefined("triple", 12, out=lines(*range(3, 34, 3))),
        id="a-plugin-disabled-in-the-middle",
    ),
    pytest.param(
        "1 20 :i {{i 7 == {1 0 /} {i} ifelse} {drop -1} try echo} do",
        ok(out=lines(*range(1, 7), -1, *range(8, 21))),
        id="try-catching-one-round",
    ),
    pytest.param(
        # (the body with the macro call is left to the interpreter, as a macro expansion outweighs a unit; the
        # block that runs after each expansion is compiled)
        "{a} {{a a +}} :twice defmacro 1 20 :i {i twice {1 -} eval echo} do",
        ok(out=lines(*range(1, 40, 2))),
        id="a-macro-in-a-loop",
    ),
    pytest.param(
        "1 20 :i {i 13 == {break} if i echo} do",
        ok(out=lines(*range(1, 13))),
        id="break",
    ),
]


@pytest.mark.parametrize(("program", "expected"), PARITY_PROGRAMS)
def test_off_default_and_eager_leave_the_same_stack_output_and_error(monkeypatch, compilations, program, expected):
    outcomes, traces, compiled = {}, {}, {}
    for state, (compiles, threshold) in STATES.items():
        monkeypatch.setattr(compiler, "THRESHOLD", threshold)
        side = Side(compiles=compiles)
        register_host_words(side.stacker)
        outcomes[state], traces[state] = side.observe(program)
        compiled[state] = len(compilations.by(side.stacker))

    assert outcomes["off"] == expected
    assert outcomes["default"] == outcomes["off"]
    assert outcomes["eager"] == outcomes["off"]
    assert traces["default"] == traces["off"]
    assert traces["eager"] == traces["off"]
    assert compiled["off"] == 0
    assert compiled["default"] > 0  # (the program does meet blocks that run often)
    assert compiled["eager"] > 0


# ---------------------------------------------------------------------------
# The harness itself: a compiler that gets a program wrong, or a guard that is missing, does not pass unseen
# ---------------------------------------------------------------------------


def test_the_twin_fails_when_the_compiling_interpreter_leaves_something_else(twin, monkeypatch):
    def wrong(unit, core, tokens, stack, admitted=False):
        stack.append("not what the block pushes")
        return True

    blk = twin.block("{1 +}")
    monkeypatch.setattr(compiler, "run", wrong)
    with pytest.raises(AssertionError, match="compiled"):
        twin.run("10 blk eval")
    assert isinstance(blk._unit, compiler.Unit)  # (the block was compiled: the compiled path is what was wrong)


def test_a_stale_unit_that_runs_anyway_is_seen_by_the_twin(twin, monkeypatch):
    """The guard at the start of a unit is blinded, and the block meets a function defined after it was compiled."""
    run_unit = compiler.run

    def blind(unit, core, tokens, stack, admitted=False):
        unit.words = core.operator_manager.generation  # forgets that a table changed
        unit.not_variables = frozenset()  # and that a variable may hide a word
        return run_unit(unit, core, tokens, stack)

    blk = twin.block("{5 f}")
    twin.run("blk eval")  # (`f` is undefined: the unit took it for that)
    twin.run(DEFINE_F)
    monkeypatch.setattr(compiler, "run", blind)
    with pytest.raises(AssertionError, match="compiled"):  # (in the eager state the unit's own check says it first)
        twin.run("blk eval")
    assert isinstance(blk._unit, compiler.Unit)  # (the stale unit ran: nothing dropped it)
