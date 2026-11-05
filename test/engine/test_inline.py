"""The control words run with their literal bodies in place (``stacker.engine.inline``): what only that path can get wrong.

The shapes every control word must keep (the stack when it fails, a break, a closure per iteration, the trace) are
in ``test_compiler_guards.py``, against the interpreter. Here are the points where the inlined path has its own
machinery: the copy of the body per iteration, a count that is a variable gone since the block was compiled, the
worth of a unit, and the shapes where the copying, the trace and the recursion limit are easiest to get wrong: a
recursion through the same literal bodies, a huge range, what `dolist` iterates, a lambda as a condition, a `try`
around a failing loop, a body that clears the stack.
"""

import itertools

import pytest

from stacker import Stacker
from stacker.data_type import stack_data
from stacker.engine import compiler, copier, machine
from stacker.engine import core as _core
from stacker.engine.compiler import (
    BLOCK,
    CALL,
    CONST,
    DO,
    DOLIST,
    FAST2,
    IF,
    TIMES,
    VAR,
    WORD,
)
from stacker.lang import recursion
from test.engine.compile_helpers import assert_compiled, lines, ok, steps


def test_a_do_loop_binds_one_copy_of_its_body_again_and_again_as_the_interpreter_does(twin, monkeypatch):
    if _core._UNSHARED_REFCOUNT is None:
        pytest.skip("no exact reference counts to reuse a copy by")
    copies = []
    original = copier.shallow_copy
    # (a counter, not a spy: a spy keeps the last copy it saw, and a copy something holds is never reused)
    monkeypatch.setattr(copier, "shallow_copy", lambda core: copies.append(1) or original(core))
    blk = twin.block("{1 1000 :i {i drop} do}")
    copies.clear()
    assert twin.run("blk eval") == ok()
    # (two interpreters ran the loop: a copy or two each, not one per iteration)
    assert len(copies) <= 6
    assert steps(assert_compiled(blk)) == [CONST, CONST, CONST, DO]


def test_a_times_whose_vanished_count_variable_hid_a_word_that_rebinds_times_runs_times_as_it_is_then(twin):
    twin.run("{} {7 :times global} :n defun 3 :n set")
    blk = twin.block("{{1} n times}")
    assert twin.run("blk eval") == ok(1, 1, 1)
    assert steps(assert_compiled(blk)) == [TIMES]
    twin.do(lambda stacker: stacker.variables.pop("n"))
    # `n` is the function now: it makes `times` a variable, and the `times` after it pushes that variable's value
    assert twin.run("blk eval") == ok("{1}", 7)


def test_a_block_whose_unit_would_do_nothing_faster_is_left_to_the_interpreter(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", True)
    stacker = Stacker()
    stacker.process_expression("[] array :a set {x} {x} :f defun")
    stacker.process_expression("{} {{1 +}} :inc defmacro")
    worthless = next(iter(stacker.eval("{a dup drop}")))  # a variable and two stack words: the runner runs them anyway
    expanding = next(iter(stacker.eval("{inc 2 *}")))  # a fast word next to a macro expansion, which outweighs it
    worthwhile = next(iter(stacker.eval("{1 +}")))  # a fast word
    called = next(iter(stacker.eval("{f}")))  # a call
    for block in (worthless, expanding, worthwhile, called):
        stacker.register_parameter("blk", block)
        stacker.eval("3 blk eval")
    assert worthless.tokens._unit is compiler.UNCOMPILABLE
    assert expanding.tokens._unit is compiler.UNCOMPILABLE
    assert steps(worthwhile.tokens._unit) == [CONST, FAST2]
    assert steps(called.tokens._unit) == [CALL]


def test_the_token_list_an_expansion_builds_is_not_counted_but_a_loop_body_written_inside_it_is(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro {} {{1 3 :i {i 2 *} do}} :triple-loop defmacro")
    built = next(iter(stacker.eval("{5} :inc macroexpand")))
    assert built.tokens._unit is compiler.UNCOMPILABLE  # (made for one run: never counted, never compiled)
    assert list(stacker.eval("2 inc")) == [3]
    expansion = next(iter(stacker.eval(":triple-loop macroexpand")))
    assert list(stacker.eval("triple-loop")) == [2, 4, 6]
    body = next(token for token in expansion.tokens if isinstance(token, _core.StackerCore))
    assert body.tokens._unit is None  # (the generated loop body runs as often as the program says: counted as any other)
    stacker.eval("triple-loop")
    assert body.tokens._unit is None  # (each expansion builds its own copy of the body; this one ran once)


def test_a_block_left_to_the_interpreter_follows_every_later_change_of_its_words(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", True)
    stacker = Stacker()
    block = next(iter(stacker.eval("{dup}")))
    stacker.register_parameter("blk", block)
    assert list(stacker.eval("3 blk eval")) == [3, 3]
    assert block.tokens._unit is compiler.UNCOMPILABLE
    stacker.process_expression("{x} {x 100 +} :dup defun")
    assert list(stacker.eval("3 blk eval")) == [103]  # (the interpreter reads the word as it is now)
    stacker.process_expression("99 :dup set")
    assert list(stacker.eval("3 blk eval")) == [3, 99]


@pytest.mark.parametrize(
    ("program", "kinds"),
    [
        pytest.param("{n} {n 0 == {0} {n 1 - rec} ifelse} :rec defun 5 rec", [CONST, CALL], id="through-ifelse"),
        pytest.param("{n} {n 0 != {n 1 - rec} if n} :rec defun 5 rec", [CONST, CALL], id="through-if"),
        pytest.param("{n} {n 0 != {1 1 :i {n 1 - rec} do} if n} :rec defun 3 rec", [CONST, CALL], id="through-do"),
        pytest.param("{n} {n 0 != {[1] :i {n 1 - rec} dolist} if n} :rec defun 3 rec", [CONST, CALL], id="through-dolist"),
        pytest.param("{n} {n 0 != {{n 1 - rec} 1 times} if n} :rec defun 3 rec", [CONST, CALL], id="through-times"),
    ],
)
def test_a_function_recursing_through_the_same_literal_bodies_runs_as_the_interpreter_does(twin, program, kinds):
    definition, _, call = program.partition(" defun ")
    twin.run(definition + " defun")
    blk = twin.block("{" + call + "}")
    for _ in range(2):
        twin.run("blk eval")
    assert steps(assert_compiled(blk)) == kinds


def test_a_do_over_a_huge_range_that_breaks_early_does_not_build_the_range(twin):
    blk = twin.block("{1 100000000000000000000 :i {i 3 == {break} if i} do}")
    for _ in range(2):
        assert twin.run("blk eval") == ok(1, 2)
    assert steps(assert_compiled(blk)) == [CONST, CONST, CONST, DO]


@pytest.mark.parametrize(
    ("items", "left"),
    [
        pytest.param('"ab"', ["a", "b"], id="a-string-gives-its-characters"),
        pytest.param("[1 2]", [1, 2], id="a-list"),
        pytest.param("[1 2] array", [1, 2], id="an-array"),
        pytest.param("1 3 seq", [1, 2, 3], id="a-sequence-a-word-made"),
    ],
)
def test_a_dolist_over_what_the_interpreter_iterates_runs_as_it_does(twin, items, left):
    blk = twin.block("{" + items + " :k {k} dolist}")
    for _ in range(2):
        assert twin.run("blk eval") == ok(*left)
    assert steps(assert_compiled(blk))[-1] == DOLIST


def test_a_lambda_as_the_condition_of_an_if_runs_as_the_interpreter_does(twin):
    twin.run("{} {true} lambda :t set")
    blk = twin.block("{t {1} if}")
    for _ in range(2):
        twin.run("blk eval")
    assert steps(assert_compiled(blk)) == [VAR, IF]


def test_a_try_around_an_inlined_loop_that_fails_records_the_stack_as_the_interpreter_does(twin):
    blk = twin.block('{5 {1 3 :i {i 2 == {foo} if i} do} {"stack" get} try}')
    for _ in range(2):
        assert twin.run("blk eval") == ok(5, [5, 1])
    assert steps(assert_compiled(blk)) == [CONST, BLOCK, BLOCK, WORD]


def test_a_body_that_clears_the_stack_runs_as_the_interpreter_does(twin):
    blk = twin.block("{1 2 3 1 2 :i {clear i} do}")
    for _ in range(2):
        assert twin.run("blk eval") == ok(2)
    assert steps(assert_compiled(blk)) == [CONST, CONST, CONST, CONST, CONST, CONST, DO]


@pytest.mark.parametrize("word", ["if", "do", "dolist", "times", "loop", "while"])
def test_the_recursion_limit_is_met_at_the_same_depth_through_an_inlined_control_word(twin, word):
    # (the limit counts every activation: the call, the arm of `if`, a loop and its body; 30 levels fit in 400
    # through each of these, 300 do not. The call is not in tail position, or no depth would be used)
    limit, depth = recursion.get_limit(), recursion.get_depth()
    recursion.set_limit(400)
    try:
        bodies = {  # (every level leaves a 0 and drops the one its call left: the call is not in tail position)
            "if": "{n 1 - deep drop} if",
            "do": "{1 1 :i {n 1 - deep drop} do} if",
            "dolist": "{[1] :i {n 1 - deep drop} dolist} if",
            "times": "{{n 1 - deep drop} 1 times} if",
            "loop": "{{n 1 - deep drop break} loop} if",
            "while": "{{true} {n 1 - deep drop break} while} if",
        }
        twin.run("{n} {n 0 != " + bodies[word] + " 0} :deep defun")
        for _ in range(3):
            assert twin.run("30 deep") == ok(0)
        outcome = twin.run("300 deep")
        assert outcome.error is not None and outcome.error[0] == "StackerRecursionError"
        assert "Maximum recursion depth (400) exceeded in function `deep`" in outcome.error[1]
        assert recursion.get_depth() == depth
    finally:
        recursion.set_limit(limit)


# --- a loop admits its body's unit without the entry checks once an iteration passed them ---


def _admissions(monkeypatch):
    """Records, per run of a unit, whether it was admitted without the entry checks, with the block's tokens."""
    seen = []
    monkeypatch.setattr(machine, "_admissions", seen)  # (the machine appends to it, on every path a unit is entered by)
    return seen


def _blocks(tokens):
    """The token lists of the literal blocks written directly in ``tokens``, in order."""
    return [token.tokens for token in tokens if isinstance(token, _core.StackerCore)]


def _runs_of(flags):
    """``flags`` with each run of equal values folded into one."""
    return [flag for flag, _ in itertools.groupby(flags)]


@pytest.mark.parametrize(
    ("program", "block", "left"),
    [
        pytest.param("{1 5 :i {acc i + :acc set} do acc}", 0, ok(15), id="do"),
        pytest.param("{[1 2 3 4] :i {acc i + :acc set} dolist acc}", 0, ok(10), id="dolist"),
        pytest.param("{{acc 1 + :acc set} 5 times acc}", 0, ok(5), id="times"),
        pytest.param("{{acc 1 + :acc set acc 5 == {break} if} loop acc}", 0, ok(5), id="loop"),
        pytest.param("{{acc 5 <} {acc 1 + :acc set} while acc}", 1, ok(5), id="while-body"),
        pytest.param("{{acc 5 <} {acc 1 + :acc set} while acc}", 0, ok(5), id="while-condition"),
    ],
)
def test_a_loop_body_is_admitted_without_the_entry_checks_after_its_first_iteration(twin, monkeypatch, program, block, left):
    seen = _admissions(monkeypatch)
    twin.run("0 :acc set")  # (a name the block itself would create makes its unit drop at the `set`)
    blk = twin.block(program)
    body = _blocks(blk)[block]
    assert twin.run("blk eval") == left
    flags = [admitted for tokens, admitted in seen if tokens is body]
    assert _runs_of(flags) == [False, True], flags


def test_a_body_that_drops_its_unit_in_mid_run_is_checked_again_on_the_next_iteration(twin, monkeypatch):
    seen = _admissions(monkeypatch)
    blk = twin.block("{1 6 :i {i 3 == {{a b} {a b -} :+ defun} if 1 2 + echo} do}")
    body = _blocks(blk)[0]
    # the third iteration replaces `+`: the rest of that iteration and the later ones use the new one
    assert twin.run("blk eval") == ok(out=lines(3, 3, -1, -1, -1, -1))
    flags = [admitted for tokens, admitted in seen if tokens is body]
    assert _runs_of(flags) == [False, True, False, True], flags


#: (setup, the loop as a block, what it leaves): loops whose trusted iterations must still follow what the loop changes
TRUSTED_LOOP_PROGRAMS = [
    pytest.param("", "{1 6 :i {i 3 == {9 :echo set} if i echo} do}", ok(3, 9, 4, 9, 5, 9, 6, 9, out=lines(1, 2)), id="a-variable-hides-a-word-from-the-third-iteration"),
    pytest.param("", "{1 4 :dup {dup} do}", ok(1, 2, 3, 4), id="the-loop-variable-is-a-word-of-the-body"),
    pytest.param("", "{[1 2 3] :echo {echo} dolist}", ok(1, 2, 3), id="the-dolist-variable-is-a-word-of-the-body"),
    pytest.param("0 :n set", "{{n 1 + :n set n 3 == {{a b} {a b *} :- defun} if n 6 <} {5 2 - echo} while}", ok(out=lines(3, 3, 10, 10, 10)), id="the-condition-replaces-a-word-of-the-body"),
    pytest.param("6 :n set", "{{n 1 - :n set n 0 >} {n 3 == {{a b} {a b * -1 *} :- defun} if 5 2 - echo} while}", ok(out=lines(3, 3, -10)), id="the-body-replaces-a-word-of-the-condition"),
    pytest.param("0 :n set", "{{n 1 + :n set n 5 == {9 :dup set} if 1 2 dup} 8 times}", ok(*[1, 2, 2] * 4, *[1, 2, 9] * 4), id="a-times-body-hides-a-word-it-uses-after-from-the-fifth-iteration"),
    pytest.param("", "{1 100 :i {i 5 == {break} if i} do}", ok(1, 2, 3, 4), id="break-after-trusted-iterations"),
    pytest.param("{} {9 :echo global} :g defun", "{1 6 :i {i 3 == {g} if i echo} do}", ok(3, 9, 4, 9, 5, 9, 6, 9, out=lines(1, 2)), id="a-function-called-by-the-body-hides-a-word-globally"),
    pytest.param("", "{[1 2 3 4 5 6] :i {i 4 == {9 :echo set} if i echo} dolist}", ok(4, 9, 5, 9, 6, 9, out=lines(1, 2, 3)), id="a-dolist-body-hides-a-word-from-the-fourth-iteration"),
    pytest.param("0 :n set", "{{n 1 + :n set n 4 == {9 :echo set} if n echo n 6 == {break} if} loop}", ok(4, 9, 5, 9, 6, 9, out=lines(1, 2, 3)), id="a-loop-body-hides-a-word-from-the-fourth-iteration"),
    pytest.param("", "{1 6 :i {i 3 == {{} {{5}} :+ defmacro} if 1 2 + echo} do}", ok(1, 2, 1, 2, 1, 2, 1, 2, out=lines(3, 3, 5, 5, 5, 5)), id="a-branch-of-the-body-makes-a-word-a-macro"),
    pytest.param(
        "{n} {n 0 == {{a b} {a b *} :+ defun 0} {1 2 :i {n 1 - rec drop 1 2 + echo} do n} ifelse} :rec defun",
        "{2 rec}",
        ok(2, out=lines(2, 2, 2, 2, 2, 2)),
        id="an-inner-activation-of-the-same-loop-replaces-a-word-the-outer-one-uses-after",
    ),
]


@pytest.mark.parametrize(("setup", "program", "left"), TRUSTED_LOOP_PROGRAMS)
def test_a_trusted_iteration_still_follows_what_the_loop_itself_changes(twin, setup, program, left):
    if setup:
        twin.run(setup)
    twin.block(program)
    assert twin.run("blk eval") == left  # (once: what the loop changes stays changed for a second run)


@pytest.mark.parametrize(("setup", "program", "left"), TRUSTED_LOOP_PROGRAMS)
def test_the_loop_word_itself_trusts_its_body_as_an_inlined_loop_does(twin, setup, program, left):
    if setup:
        twin.run(setup)
    # (the loop at the top level: the word runs it, not a compiled block. The recursion row's loop is inside
    # the function either way; it is kept so that the two tables stay one)
    assert twin.run(program[1:-1]) == left


def test_a_unit_of_another_interpreter_is_refused_even_when_admitted(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)
    first, second = Stacker(), Stacker()
    first.eval("{1 2 +} :blk set")
    first.eval("blk eval")
    block = first.variables["blk"]
    unit = block.tokens._unit
    assert type(unit) is compiler.Unit
    stack = stack_data()
    # a loop of `second` could hold this unit as trusted (the run before left it in the tokens): the interpreter
    # check is the one made even then
    frame = machine.Frame(machine.TOP, None)
    frame.template = frame.core = second
    frame.scope = second.variables
    frame.stack = stack
    assert machine._admit(frame, block.tokens, unit, True) is False
    assert frame.resolved is False
    assert list(stack) == []


@pytest.mark.parametrize(
    "program",
    [
        pytest.param("1 5 :i {acc i + :acc set} do acc", id="do"),
        pytest.param("[1 2 3 4] :i {acc i + :acc set} dolist acc", id="dolist"),
        pytest.param("{acc 1 + :acc set} 5 times acc", id="times"),
        pytest.param("{acc 1 + :acc set acc 5 == {break} if} loop acc", id="loop"),
        pytest.param("{acc 5 <} {acc 1 + :acc set} while acc", id="while"),
    ],
)
def test_the_loop_word_itself_admits_its_bodies_after_their_first_iteration(twin, monkeypatch, program):
    seen = _admissions(monkeypatch)
    twin.run("0 :acc set")
    twin.run(program)  # (at the top level, so the only units run are the loop's bodies)
    by_body = {}
    for tokens, admitted in seen:
        by_body.setdefault(id(tokens), []).append(admitted)
    repeated = [flags for flags in by_body.values() if len(flags) > 1]  # (a `{break}` branch runs once)
    assert repeated and all(_runs_of(flags) == [False, True] for flags in repeated), by_body


def test_a_loop_run_again_inside_its_own_body_by_a_recursive_call_checks_its_first_iteration_each_time(twin, monkeypatch):
    seen = _admissions(monkeypatch)
    twin.run("{n} {n 0 == {0} {1 2 :i {n 1 - rec drop} do n} ifelse} :rec defun")
    twin.block("{3 rec}")
    assert twin.run("blk eval") == ok(3)
    body = _blocks(_blocks(twin.body("rec"))[1])[0]  # the `do` body inside the ifelse's second branch
    flags = [admitted for tokens, admitted in seen if tokens is body]
    # seven activations of the loop (n = 3, 2, 2, 1, 1, 1, 1), each checking its first iteration and trusting its
    # second; the outermost one compiled the body in its first iteration (not recorded) and checks its second too.
    # The runs nest in a fixed order, so the record is fixed: innermost first
    checked, trusted = False, True
    assert flags == [checked, checked, checked, trusted, trusted, checked, trusted] * 2, flags
