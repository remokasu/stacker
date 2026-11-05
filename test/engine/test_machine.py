"""The machine runs Stacker code without the host's call stack growing with the program's depth.

A Stacker recursion is as deep as the machine's own return stack lets it
be, whatever the host's limit on its call stack: a function calling itself
through any of the constructs below goes a thousand levels deep in a host
that could not nest a tenth of that. A Python word that runs a block is
the one place the machine is entered again; a program made of built-in
words alone enters it once per expression.
"""

import gc
import os
import subprocess
import sys
import textwrap
import time

import pytest

from stacker import Stacker
from stacker.engine import compiler, machine, recursion
from stacker.engine.data_type import stack_data
from stacker.error import (
    NoValueProducedError,
    ResultCountError,
    StackerRecursionError,
    include_location_of,
)

#: Runs enough for a block to be compiled in any state of the tier (the threshold is 8 by default)
WARM_RUNS = 12

#: How deep the recursions below go: far past any host limit the tests run under
DEEP = 600

#: A recursion through each construct the machine runs itself: `rec` counts down ``n`` and leaves 0
CONSTRUCTS = {
    "call": "{n} {n 0 == {0} {n 1 - rec} ifelse} :rec defun",
    "lambda": "{n} {n 0 == {0} {n 1 - lam eval} ifelse} lambda :lam set {n} {n lam eval} :rec defun",
    "mutual": "{n} {n 0 == {0} {n 1 - rec} ifelse} :other defun {n} {n other} :rec defun",
    "if-arm": "{n} {n 0 == {0} if n 0 == not {n 1 - rec} if} :rec defun",
    "cond": "{n} {{n 0 ==} {0} {true} {n 1 - rec} 2 cond} :rec defun",
    "eval-block": "{n} {n 0 == {0} {{n 1 - rec} eval} ifelse} :rec defun",
    "eval-symbol": "{n} {n 0 == {0} {n 1 - :rec eval} ifelse} :rec defun",
    "apply": "{n} {n 0 == {0} {{n 1 -} {rec} apply} ifelse} :rec defun",
    "do-body": "{n} {n 0 == {0} {1 1 :i {n 1 - rec} do} ifelse} :rec defun",
    "dolist-body": "{n} {n 0 == {0} {[1] :i {n 1 - rec} dolist} ifelse} :rec defun",
    "times-body": "{n} {n 0 == {0} {{n 1 - rec} 1 times} ifelse} :rec defun",
    "loop-body": "{n} {n 0 == {0} {{n 1 - rec break} loop} ifelse} :rec defun",
    "while-body": "{n} {n 0 == {0} {true {dup} {drop n 1 - rec false} while drop} ifelse} :rec defun",
    "while-condition": "{n} {n 0 == {0} {{n 1 - rec false} {} while} ifelse} :rec defun",
    "try-body": "{n} {n 0 == {0} {{n 1 - rec} {} try} ifelse} :rec defun",
    "try-handler": '{n} {n 0 == {0} {{"x" "boom" throw} {drop n 1 - rec} try} ifelse} :rec defun',
    "iferror-body": "{n} {n 0 == {0} {{n 1 - rec} {} iferror} ifelse} :rec defun",
    "collect": "{n} {n 0 == {0} {{n 1 - rec} collect expand} ifelse} :rec defun",
    "map-body": "{n} {n 0 == {0} {[1] {drop n 1 - rec} map car} ifelse} :rec defun",
    "filter-body": "{n} {n 0 == {0} {[1] {drop n 1 - rec 0 ==} filter len 1 -} ifelse} :rec defun",
    "reduce-body": "{n} {n 0 == {0} {[1] 0 :a :x {n 1 - rec} reduce} ifelse} :rec defun",
    "macro": "{m} {{m}} :run defmacro {n} {n 0 == {0} {n 1 - :rec run} ifelse} :rec defun",
    "arg-block": "{n} {n 0 == {0} {{n 1 - rec} 0 +} ifelse} :rec defun",
    "times-count-block": "{n} {n 0 == {0} {{} {n 1 - rec} times 0} ifelse} :rec defun",
    "apply-args-block": "{n} {n 0 == {0} {{n 1 - rec} {} apply} ifelse} :rec defun",
}


@pytest.fixture
def deep_limit():
    """The recursion guard taken off for the recursions here, and put back after."""
    before = recursion.get_limit()
    recursion.set_limit(recursion.NO_LIMIT)
    yield
    recursion.set_limit(before)


@pytest.mark.parametrize("construct", CONSTRUCTS)
def test_a_recursion_through_each_construct_is_as_deep_as_the_guard_allows_whatever_the_host_allows(deep_limit, construct):
    program = f"{CONSTRUCTS[construct]} {DEEP} rec"
    code = textwrap.dedent(
        f"""
        import sys
        from stacker import Stacker
        from stacker.engine import recursion
        recursion.set_limit(recursion.NO_LIMIT)
        s = Stacker()
        print(list(s.eval({program!r})))
        """
    )
    # a host limit too low for even a tenth of the recursion the old way: the machine does not use it
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    result = subprocess.run([sys.executable, "-X", "frozen_modules=off", "-c", f"import sys; sys.setrecursionlimit(120)\n{code}"], capture_output=True, text=True, env=env, timeout=120, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[0]"


@pytest.mark.parametrize("state", ["off", "eager"])
def test_the_recursion_is_as_deep_in_both_streams(deep_limit, monkeypatch, state):
    if state == "off":
        monkeypatch.setattr(compiler, "THRESHOLD", None)
    else:
        monkeypatch.setattr(compiler, "THRESHOLD", 1)
        monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)
    s = Stacker()
    assert list(s.eval(f"{CONSTRUCTS['call']} {DEEP} rec")) == [0]


def test_the_guard_still_stops_a_recursion_by_name_at_its_limit():
    before = recursion.get_limit()
    recursion.set_limit(50)
    try:
        s = Stacker()
        with pytest.raises(StackerRecursionError, match=r"Maximum recursion depth \(50\) exceeded in function `rec`"):
            s.eval("{n} {n 0 == {0} {n 1 - rec 1 +} ifelse} :rec defun 1000 rec")  # (not a tail call)
        assert recursion.get_depth() == 0
    finally:
        recursion.set_limit(before)


def test_a_tail_call_takes_no_depth_and_the_values_left_before_it_come_out_under_the_result():
    before = recursion.get_limit()
    recursion.set_limit(10)
    try:
        s = Stacker()
        assert list(s.eval("{n} {n 0 == {0} {n 1 - rec} ifelse} :rec defun 100000 rec")) == [0]
        assert list(s.eval("{n} {n n 0 > {n 1 - h} {} ifelse} :h defun 3 h")) == [3, 2, 1, 0]
        assert list(s.eval("{n} {n 0 == {0} {n 1 - :rec eval} ifelse} :rec defun 50000 rec")) == [0]
        assert list(s.eval("{x} {x 0 == {0} {x 1 - lam eval} ifelse} lambda :lam set 50000 lam eval")) == [0]
        assert list(s.eval("{n} {n 0 == {0} {{n 1 -} {rec} apply} ifelse} :rec defun 50000 rec")) == [0]
        with pytest.raises(StackerRecursionError):  # not in tail position: the depth is used
            s.eval("{n} {n 0 == {0} {n 1 - rec 1 +} ifelse} :rec defun 100 rec")
        assert recursion.get_depth() == 0
    finally:
        recursion.set_limit(before)


def test_a_call_leaves_no_cycle_so_its_activation_goes_with_the_last_reference():
    s = Stacker()
    s.eval("{n} {n 1 +} :inc defun 0 {inc} 10 times drop")
    s.eval("{n} {n n 0 > {n 1 - h} {} ifelse} :h defun 3 h clear")
    gc.disable()  # (from here on, only reference counting frees anything)
    try:
        before = sum(isinstance(o, machine.Frame) for o in gc.get_objects())
        s.eval("0 {inc} 3000 times drop 30 h clear {x} {x 1 +} lambda :f set 0 {f eval} 1000 times drop")
        assert sum(isinstance(o, machine.Frame) for o in gc.get_objects()) == before
    finally:
        gc.enable()


def test_a_run_of_tail_calls_that_leave_values_takes_time_in_proportion_to_its_length():
    s = Stacker()
    s.eval("{n m} {n n m < {n 1 + m h} {} ifelse} :h defun 0 10 h clear")

    def timed(n):
        start = time.perf_counter()
        assert len(s.eval(f"0 {n} h")) == n + 1
        s.eval("clear")
        return time.perf_counter() - start

    small = min(timed(2000) for _ in range(3))
    large = timed(32000)
    assert large < small * 64  # (16 times the length: linear is about 16 times the time, quadratic about 256)


def test_the_depth_a_python_word_reads_counts_the_arms_run_in_place():
    s = Stacker()
    seen = []

    def probe():
        seen.append(recursion.get_depth())
        return 0

    s.register_sfunction("probe", probe, 0, push_result_to_stack=True)
    s.eval("{} {probe drop} :f defun")
    program = "probe drop {probe drop} eval {} {true {true {probe drop} if} if} :g defun g f 1 1 :i {probe drop} do"
    s.eval(program)  # (the first run: the arms are activations in the generic stream)
    first, seen[:] = list(seen), []
    for _ in range(WARM_RUNS):
        s.eval(program)  # (warmed up: the arms of `if` are run in place, counted by the reader)
    assert seen[-len(first):] == first == [0, 1, 3, 1, 2]


def test_the_hosts_depth_error_inside_a_call_through_a_python_word_is_renamed_as_the_calls():
    s = Stacker()

    def twice(block):
        s.evaluate(block.tokens, stack_data())  # a Python word running a block: the host's own depth is used here
        return 2

    s.register_sfunction("twice", twice, 1, push_result_to_stack=True)
    with pytest.raises(StackerRecursionError, match=r"exceeded in function `r` at \d+ calls, before the limit"):
        s.eval("{} {{r} twice drop} :r defun r")
    assert recursion.get_depth() == 0


def test_an_element_whose_call_ends_in_a_tail_call_leaves_the_next_element_a_sound_activation():
    # (the element's activation is kept for the next element; a tail call replaces it, so the next element
    # must not be run on the replaced one, left in the middle of an arm)
    s = Stacker()
    s.eval("{n} {n 2 >} :big defun")
    for _ in range(3):
        assert list(s.eval("1 20 seq {x} {x 5 > {x big} {false} ifelse} lambda filter")) == [list(range(6, 21))]
        assert list(s.eval("1 12 seq {x} {x 5 > {x big} {x 0 >} ifelse} lambda map")) == [[True] * 12]
        s.eval("clear")


@pytest.mark.parametrize(
    "program, expected",
    [
        pytest.param("{x} {x 1 +} lambda {99} iferror", [99], id="a-lambda-body-short-of-arguments-is-caught"),
        pytest.param("{x y} {x y +} lambda {96} iferror", [96], id="a-lambda-body-of-two-is-caught"),
        pytest.param('{1 0 /} {x} {x "kind" get} lambda try', ["ZeroDivisionError"], id="a-lambda-handler-is-called-on-the-error"),
        pytest.param("{1 0 /} 5 iferror", [5], id="a-value-as-handler-is-pushed"),
        pytest.param("{{1 0 /} {drop 1} try 0 /} {drop 2} try", [2], id="a-try-inside-a-try"),
        pytest.param("1 5 :i {{i 3 == {break} if} {drop 9} try i} do", [1, 2], id="break-passes-through-the-body"),
        pytest.param('{"x" "boom" throw} {"kind" get} try', ["x"], id="the-error-record-is-the-handlers"),
    ],
)
def test_the_body_of_try_catches_for_itself_as_the_control_activation_did(program, expected):
    s = Stacker()
    for _ in range(WARM_RUNS):  # (compiled or not, the same)
        assert list(s.eval(program)) == expected
        s.eval("clear")


def test_a_try_whose_body_is_a_block_is_one_activation(mocker):
    s = Stacker()
    before = recursion.get_limit()
    recursion.set_limit(2)  # the expression's activation and the body's
    try:
        assert list(s.eval("{{1 0 /} {drop 3} try} eval")) == [3]
    finally:
        recursion.set_limit(before)
    interrupting = mocker.patch.object(machine._core.StackerCore, "_run_word", side_effect=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):  # (an interrupt is not an error the body takes)
        s.eval("{1 dup} {drop 0} try")
    assert interrupting.called and recursion.get_depth() == 0


def test_a_block_eval_runs_in_place_behaves_as_an_activation_of_its_own():
    s = Stacker()
    before = recursion.get_limit()
    recursion.set_limit(30)
    try:
        for _ in range(WARM_RUNS):
            with pytest.raises(StackerRecursionError):  # the recursion through `eval` stops at the limit
                s.eval("{b eval 1 +} :b set b eval")
            assert recursion.get_depth() == 0 and len(s.stack) == 0
            assert list(s.eval("0 1 10 :i {{i 4 == {break} if} eval i +} do")) == [6]  # `break` inside the block leaves the loop
            with pytest.raises(ZeroDivisionError):
                s.eval("1 {2 {3 0 /} eval} eval")
            assert list(s.get_trace_copy()) == [3, 0, "/"]  # the innermost block's tokens, as an activation leaves them
            assert list(s.eval("{n} {n 0 == {0} {{n 1 - rec} eval} ifelse} :rec defun 200 rec")) == [0]  # a tail call through `eval`
            s.eval("clear")
    finally:
        recursion.set_limit(before)


def test_the_steps_of_a_unit_carry_the_machines_kinds(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    s = Stacker()
    s.eval("{} {1} :f defun")
    s.eval('{"a" dup len drop {} eval f [1] {2 *} map clear} :blk set')
    s.eval("blk eval")  # (compiled on this run: the threshold is one)
    block = next(iter(s.eval("blk")))
    kinds = {step[2]: step[0] for step in block.tokens._unit.steps if step[2] is not None}
    assert kinds["len"] == machine.VWORD  # (an aggregate word reads the running core)
    assert kinds["dup"] == machine.TWORD and kinds["clear"] == machine.TWORD  # (a stack word works the stack itself)
    # a word of a category that takes values, with values to take: the step looks for a block among them first
    entry = s.operator_manager.dispatch_table["pick"]
    steps = [(compiler.WORD, 0, "pick", entry)]
    machine._rewrite_steps(steps, s)
    assert steps[0][0] == machine.PYWORD and steps[0][3][2] == entry[1]["arg_count"] == 1
    assert kinds["eval"] == machine.MWORD and kinds["map"] == compiler.WORD and kinds["f"] == compiler.CALL


def test_a_word_redefined_after_its_unit_was_made_runs_as_redefined():
    s = Stacker()
    program = "-3 abs"
    for _ in range(WARM_RUNS):
        assert list(s.eval(program)) == [3]
        s.eval("clear")
    s.eval("{x} {x 100 *} :abs defun")
    assert list(s.eval(program)) == [-300]


def test_an_activation_entered_again_has_the_bodys_tokens_as_its_trace():
    s = Stacker()
    program = "1 5 :i {{i 2 == {1 0 /} {1} ifelse} {drop 0} try drop 10 i 3 - / drop} do"
    for _ in range(WARM_RUNS):
        with pytest.raises(ZeroDivisionError):
            s.eval(program)
        assert list(s.get_trace_copy())[-1] == "drop"  # the body's tokens, not the inner block's the `try` caught
        s.eval("clear")
    reducing = "[1 2 3 4 5] 0 :a :x {{x 2 == {1 0 /} {1} ifelse} {drop 0} try drop 10 x 3 - / drop a x +} reduce"
    for _ in range(WARM_RUNS):
        with pytest.raises(ZeroDivisionError):
            s.eval(reducing)
        assert list(s.get_trace_copy())[-1] == "+"
        s.eval("clear")


def test_map_and_reduce_leave_no_cycle_of_activations():
    s = Stacker()
    programs = ["1 5 seq {2 *} map drop", "1 5 seq {x} {x 2 *} lambda map drop", "1 5 seq 0 :a :x {a x +} reduce drop", "1 5 seq {2 >} filter drop"]
    for program in programs:
        s.eval(program)
    gc.disable()
    try:
        before = sum(isinstance(o, machine.Frame) for o in gc.get_objects())
        for program in programs:
            for _ in range(20):
                s.eval(program)
        assert sum(isinstance(o, machine.Frame) for o in gc.get_objects()) == before
    finally:
        gc.enable()


def test_a_program_of_built_in_words_enters_the_machine_once_per_expression(monkeypatch):
    entries = []
    original = machine.run

    def counting(core, tokens, stack, **kwargs):
        entries.append(tokens)
        return original(core, tokens, stack, **kwargs)

    s = Stacker()  # (made before the count: loading the prelude enters the machine too)
    monkeypatch.setattr(machine, "run", counting)
    programs = [
        "{n} {n 0 == {0} {n 1 - rec} ifelse} :rec defun",
        "20 rec",
        "0 :acc set 1 100 :i {acc i + :acc set} do",
        "[1 2 3] :x {x acc + :acc set} dolist",
        "{acc 1 + :acc set} 3 times",
        "{acc 200 <} {acc 1 + :acc set} while",
        "{acc 1 + :acc set acc 300 > {break} if} loop",
        "{1 0 /} {drop} try {1 0 /} {} iferror",
        "{1 2 3} collect [1 2] {+} apply {7} eval :acc eval",
        "[1 2 3] {2 *} map [1 2 3] {1 >} filter [1 2 3] 0 :a :x {a x +} reduce",
        "{a} {a a +} :twice defmacro 3 twice {x} {{x x *}} :sq defmacro 4 sq",
        "{1 2 +} {4} + {3} 1 swap drop {1} {2} :i {} do {} {2} times",
        "true {1} {2} ifelse {false} {3} {true} {4} 2 cond",
        "3 :x set 4 :y global",
    ]
    for program in programs:
        entries.clear()
        s.process_expression(program)
        assert len(entries) == 1, (program, len(entries))


def test_a_python_word_that_runs_a_block_enters_the_machine_again_and_the_guard_is_kept(monkeypatch):
    entries = []
    original = machine.run

    def counting(core, tokens, stack, **kwargs):
        entries.append(tokens)
        return original(core, tokens, stack, **kwargs)

    s = Stacker()  # (made before the count: loading the prelude enters the machine too)

    def twice(block):
        s.evaluate(block.tokens, stack_data())  # a Python word running a block: the one way the machine is re-entered
        return 2

    s.register_sfunction("twice", twice, 1, push_result_to_stack=True)  # (a function takes its block raw)
    monkeypatch.setattr(machine, "run", counting)
    assert list(s.eval("{1 2 +} twice")) == [2]
    assert len(entries) == 1 + 1
    assert recursion.get_depth() == 0
    entries.clear()
    assert list(s.eval("[1 2 3] {2 *} map [1 2 3] 0 :a :x {a x +} reduce")) == [[2, 4, 6], 6]  # (the machine's own)
    assert len(entries) == 1


def test_a_recursion_that_goes_through_no_function_stops_at_the_limit_named_after_the_word():
    s = Stacker()
    with pytest.raises(StackerRecursionError, match=r"Maximum recursion depth \(100000\) exceeded in word `eval`"):
        s.eval("{b eval 1 +} :b set b eval")
    assert recursion.get_depth() == 0


def test_an_error_leaves_the_guard_where_the_run_began():
    s = Stacker()
    s.eval("{n} {n 0 == {1 0 /} {n 1 - f} ifelse} :f defun")
    with pytest.raises(ZeroDivisionError):
        s.eval("10 f")
    assert recursion.get_depth() == 0
    s.eval("{10 f} {drop} try")
    assert recursion.get_depth() == 0


def test_a_break_leaves_the_calls_it_passes():
    s = Stacker()
    assert list(s.eval("{} {break} :b defun 1 5 :i {i 3 == {b} if i} do")) == [1, 2]
    assert recursion.get_depth() == 0


def test_an_activation_of_another_interpreter_is_refused_at_the_door(monkeypatch):
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)
    first, second = Stacker(), Stacker()
    first.eval("{1 2 +} :blk set")
    first.eval("blk eval")
    block = first.variables["blk"]
    unit = block.tokens._unit
    assert type(unit) is compiler.Unit
    frame = machine.Frame(machine.TOP, None)
    frame.template = frame.core = second
    frame.scope = second.variables
    frame.stack = stack_data()
    assert machine._admit(frame, block.tokens, unit, True) is False


# --- what the machine promises about taking activations down, pinned ---------------------------------------


def test_a_block_of_another_interpreter_is_guarded_by_its_own_tables(monkeypatch):
    """The unit of a block resolved against one interpreter's tables is checked against those, wherever it runs."""
    monkeypatch.setattr(compiler, "THRESHOLD", 1)
    monkeypatch.setattr(compiler, "ONLY_WORTHWHILE", False)
    first, second = Stacker(), Stacker()
    block = second.eval("{ {} {7} :f defun f }")[-1]
    first.variables["blk"] = block
    assert list(first.eval("blk eval")) == [7]  # (`f` is defined in the block's own interpreter as the block runs)
    assert list(first.eval("blk eval")) == [7]


def test_a_loop_lets_its_bodys_activations_go_when_it_ends():
    s = Stacker()
    s.eval("1 5 :i {i drop} do")
    s.eval("1 3 :i {1 3 :j {j drop} do} do")
    s.eval("{{1 drop} 2 times} 2 times")
    gc.disable()  # (from here on, only reference counting frees anything)
    try:
        before = sum(isinstance(o, machine.Frame) for o in gc.get_objects())  # (what other tests left for the collector)
        s.eval("1 5 :i {i drop} do 1 3 :i {1 3 :j {j drop} do} do {{1 drop} 2 times} 2 times")
        assert sum(isinstance(o, machine.Frame) for o in gc.get_objects()) == before
    finally:
        gc.enable()


@pytest.mark.parametrize(
    ("program", "kind", "message"),
    [
        pytest.param("{a b} {a b +} :f defun 1 f", "StackUnderflowError", "Function `f` requires 2 arguments.", id="underflow-in-the-callers-context"),
        pytest.param("true {1 0 /} if", "ZeroDivisionError", "division by zero", id="an-arm-passes-the-error-through"),
        pytest.param("true {+} if", "StackUnderflowError", "Operator `+` requires 2 arguments.", id="an-arm-rewords-as-the-inner-word"),
        pytest.param("1 :s :i {} do", "StackerTypeError", "`do` cannot use", id="loop-rewraps-a-symbol"),
        pytest.param(":s :n set {1} n times", "StackerTypeError", "`times` cannot use", id="times-rewraps-a-symbol"),
        pytest.param('"x" "boom" throw', "UserError", "boom", id="throw"),
        pytest.param("{{1 0 /} {} try} {} try 1 0 /", "ZeroDivisionError", "division by zero", id="a-caught-error-leaves-no-trace-in-the-guard"),
    ],
)
def test_the_rules_applied_on_the_way_down(program, kind, message):
    s = Stacker()
    with pytest.raises(Exception) as info:  # (the kind is checked below)
        s.eval(program)
    assert type(info.value).__name__ == kind
    assert message in str(info.value)
    assert recursion.get_depth() == 0


def test_a_break_passes_a_try_and_is_caught_by_the_loop_around_it():
    s = Stacker()
    assert list(s.eval("1 5 :i {{i 3 == {break} if} {drop} try i} do")) == [1, 2]
    assert list(s.eval("1 5 :i {{i 3 == {break} if} {} iferror i} do")) == [1, 2]


def test_the_depth_error_inside_a_call_is_named_after_the_call():
    s = Stacker()
    # a recursion through no function reaches the limit inside the call `g`: the nearest call names the error
    s.eval("{b eval 1 +} :b set {} {b eval} :g defun")
    with pytest.raises(StackerRecursionError) as info:
        s.eval("g")
    assert (info.value.name, info.value.kind, info.value.depth) == ("g", "function", None)
    assert recursion.get_depth() == 0


def test_an_interrupt_in_mid_run_leaves_the_guard_where_the_run_began(monkeypatch):
    s = Stacker()
    s.eval("{n} {n 0 == {interrupt} {n 1 - f} ifelse} :f defun")

    def interrupt():
        raise KeyboardInterrupt

    s.register_plugin("interrupt", interrupt, push_result_to_stack=False)
    with pytest.raises(KeyboardInterrupt):
        s.eval("50 f")
    assert recursion.get_depth() == 0
    assert list(s.eval("1 2 +")) == [3]  # (the interpreter is usable afterwards)


def test_a_body_whose_iteration_caught_an_error_runs_the_next_iterations_as_before():
    s = Stacker()
    out = s.eval('0 :acc set 1 2000 :i {{i 1000 == {1 0 /} if acc i + :acc set} {drop} try} do acc')
    assert list(out) == [sum(i for i in range(1, 2001) if i != 1000)]


def test_an_included_file_runs_as_the_machines_own_activations(tmp_path, deep_limit):
    (tmp_path / "lib.stk").write_text("{n} {n 0 == {0} {n 1 - deep} ifelse} :deep defun\n600 deep\n", encoding="utf-8")
    (tmp_path / "bad.stk").write_text('"first" echo\n1 0 /\n', encoding="utf-8")
    s = Stacker()
    s.include(str(tmp_path / "lib.stk"))
    assert list(s.stack) == []  # (what a file leaves is dropped)
    assert list(s.eval("3 deep")) == [0]
    assert recursion.get_depth() == 0 and not s._includes.stack
    with pytest.raises(ZeroDivisionError) as info:
        s.include(str(tmp_path / "bad.stk"))
    (file, line, _source), _frames = include_location_of(info.value)
    assert file.endswith("bad.stk") and line == 2
    assert not s._includes.stack  # (the file is no longer running after the error)


def test_an_include_refused_at_the_limit_leaves_no_file_marked_as_running(tmp_path):
    (tmp_path / "f.stk").write_text("7", encoding="utf-8")
    before = recursion.get_limit()
    try:
        s = Stacker()
        s.eval(f'"{tmp_path / "f.stk"}" :F set')
        recursion.set_limit(2)  # the `try`, its body, and the include would be three: the include is refused
        out = s.eval("{F include} {drop} try F include 8")  # (the second include must not be taken for a circular one)
        assert list(out) == [8]  # (the include is a tail of the body, so the drop runs on the error alone)
        assert not s._includes.stack
    finally:
        recursion.set_limit(before)


def test_a_block_in_a_values_place_is_read_as_the_word_reads_it():
    s = Stacker()
    assert list(s.eval("{1 2 +} {4} + {{1 2}} {+} apply")) == [7, 3]
    assert list(s.eval('{"a"} {"b"} concat')) == ["ab"]  # (a String a block leaves is unwrapped, as _pop_arg does)
    out = s.eval("{{3} {} times} {drop depth} try")
    assert list(out) == [0]  # (the count block was taken before it ran: the record holds the stack without it)
    with pytest.raises(NoValueProducedError, match="left nothing"):
        s.eval("{} 1 +")
    with pytest.raises(ResultCountError, match="left 2 values"):
        s.eval("{1 2} 1 +")
