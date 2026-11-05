"""Pins what the words do when they are reached from Python rather than from Stacker code.

A control word's function can be wrapped and registered again under its
name; a subclass can give a word a handler of its own; a word whose entry
has no function can be registered over; a function or lambda value can be
called from Python; a script can be included through the interpreter's
methods; and a higher-order word can be wrapped too. None of these paths
is in the golden cases, so what they leave (the stack, the error, the trace,
the depth they count) is pinned here, before the Python side of each word
is rewritten.
"""

from __future__ import annotations

import contextlib
import io
import logging
from typing import ClassVar, NamedTuple

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.error import StackerError, include_location_of
from stacker.lang import recursion


class Outcome(NamedTuple):
    """What a program left: its stack as text, the error that stopped it (kind, message) or None, the trace."""

    stack: list[str]
    error: tuple[str, str] | None
    trace: list[object]


def outcome(program: str, stacker: Stacker | None = None) -> Outcome:
    """Runs ``program`` on ``stacker`` (a fresh interpreter when None) and returns what it left."""
    if stacker is None:  # (not `or`: an interpreter with no tokens of its own is falsy)
        stacker = Stacker()
    try:
        stacker.process_expression(program)
    except Exception as error:  # noqa: BLE001 -- a host error (ZeroDivisionError) is an outcome too
        return Outcome([str(v) for v in stacker.stack], (type(error).__name__, str(error)), list(stacker.trace))
    return Outcome([str(v) for v in stacker.stack], None, list(stacker.trace))


def ok(*stack: object, trace: list[object]) -> Outcome:
    return Outcome([str(v) for v in stack], None, trace)


def fails(kind: str, message: str, trace: list[object], *stack: object) -> Outcome:
    return Outcome([str(v) for v in stack], (kind, message), trace)


def wrap(stacker: Stacker, category: str, word: str) -> list[int]:
    """Registers ``word`` again as a wrapper that calls the built-in function; returns the list the calls are counted in."""
    entry = stacker.operator_manager.operators[category][word]
    original = entry["func"]
    calls: list[int] = []

    def wrapper(*taken):
        calls.append(len(taken))
        return original(*taken)

    stacker.register_operator(word, wrapper, entry["arg_count"], entry["push_result_to_stack"], "wrapped")
    return calls


@pytest.fixture
def limit():
    """Sets the recursion limit for a test and puts the default back."""

    def set_limit(value: int) -> None:
        recursion.set_limit(value)

    yield set_limit
    recursion.set_limit(recursion.DEFAULT_RECURSION_LIMIT)


# ---------------------------------------------------------------------------
# A. A control word wrapped and registered again runs its built-in function from Python
# ---------------------------------------------------------------------------

WRAPPED_RUNS = {
    "if": ("1 true {2} if 3 false {4} if", ok(1, 2, 3, trace=["1", "true", "{2}", "if", "3", "false", "{4}", "if"]), [4, 4]),
    "ifelse": ("true {1} {2} ifelse false {3} {4} ifelse", ok(1, 4, trace=["true", "{1}", "{2}", "ifelse", "false", "{3}", "{4}", "ifelse"]), [5, 5]),
    "cond": ("5 {false} {1} {true} {2} 2 cond", ok(5, 2, trace=["5", "{false}", "{1}", "{true}", "{2}", "2", "cond"]), [3]),
    "try": ('{1 0 /} {dup "kind" get} try', ok({"kind": "ZeroDivisionError", "message": "division by zero", "stack": []}, "ZeroDivisionError", trace=[1, 0, "/"]), [4]),
    "iferror": ('{1 0 /} {"caught"} iferror', ok("caught", trace=[1, 0, "/"]), [4]),
    "loop": ("0 {1 + dup 3 == {break} if} loop", ok(3, trace=["0", "{1 + dup 3 == {break} if}", "loop"]), [3]),
    "while": ("0 {dup 3 <} {1 +} while", ok(3, trace=["0", "{dup 3 <}", "{1 +}", "while"]), [4]),
    "times": ("0 {1 +} 3 times", ok(3, trace=["0", "{1 +}", "3", "times"]), [4]),
    "do": ("0 1 3 :i {i +} do", ok(6, trace=["0", "1", "3", ":i", "{i +}", "do"]), [6]),
    "dolist": ("0 [1 2 3] :x {x +} dolist", ok(6, trace=["0", "[1 2 3]", ":x", "{x +}", "dolist"]), [5]),
}


@pytest.mark.parametrize("word", WRAPPED_RUNS)
def test_a_wrapped_control_word_leaves_what_the_built_in_leaves_and_is_called_once_per_use(word):
    program, expected, calls_expected = WRAPPED_RUNS[word]
    stacker = Stacker()
    calls = wrap(stacker, "priority", word)
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)
    assert calls == calls_expected


WRAPPED_BREAKS = {
    "loop": ("{break} loop 9", ok(9, trace=["{break}", "loop", "9"])),
    "while": ("{true} {break} while 9", ok(9, trace=["{true}", "{break}", "while", "9"])),
    "times": ("0 {1 + break} 3 times 9", ok(1, 9, trace=["0", "{1 + break}", "3", "times", "9"])),
    "do": ("1 3 :i {i i 2 == {break} if} do 9", ok(1, 2, 9, trace=["1", "3", ":i", "{i i 2 == {break} if}", "do", "9"])),
    "dolist": ("[1 2 3] :x {x x 2 == {break} if} dolist 9", ok(1, 2, 9, trace=["[1 2 3]", ":x", "{x x 2 == {break} if}", "dolist", "9"])),
}


@pytest.mark.parametrize("word", WRAPPED_BREAKS)
def test_a_break_inside_a_wrapped_loop_word_ends_that_loop(word):
    program, expected = WRAPPED_BREAKS[word]
    stacker = Stacker()
    wrap(stacker, "priority", word)
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)


WRAPPED_ERRORS = {
    "if": ("true {1 0 /} if", fails("ZeroDivisionError", "division by zero", [1, 0, "/"])),
    "ifelse": ("false {1} {nosuchword} ifelse", fails("UndefinedSymbolError", "`nosuchword` is not defined.", ["nosuchword"])),
    "cond": ("{true} {1 0 /} 1 cond", fails("ZeroDivisionError", "division by zero", [1, 0, "/"])),
    "loop": ("{1 0 /} loop", fails("ZeroDivisionError", "division by zero", [1, 0, "/"])),
    "while": ("{true} {1 0 /} while", fails("ZeroDivisionError", "division by zero", [1, 0, "/"])),
    "times": ("{1 0 /} 2 times", fails("ZeroDivisionError", "division by zero", [1, 0, "/"])),
    "do": ("1 2 :i {i 0 /} do", fails("ZeroDivisionError", "division by zero", ["i", 0, "/"])),
    "dolist": ("[1] :x {x 0 /} dolist", fails("ZeroDivisionError", "division by zero", ["x", 0, "/"])),
}


@pytest.mark.parametrize("word", WRAPPED_ERRORS)
def test_an_error_inside_a_wrapped_control_word_keeps_its_kind_message_and_trace(word):
    program, expected = WRAPPED_ERRORS[word]
    stacker = Stacker()
    wrap(stacker, "priority", word)
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)


# ---------------------------------------------------------------------------
# A2. The depth a recursion through a wrapped word counts
# ---------------------------------------------------------------------------

LIMIT = 60
TOO_DEEP = f"Maximum recursion depth ({LIMIT}) exceeded in function `f`"

#: A function recursing through a control word, and the deepest call that runs under the limit: with the word
#: built in, with the word wrapped, and with `if`, `ifelse` and `times` all wrapped. None: a tail call, any depth
DEPTHS = {
    "ifelse": ("{n} {n 0 == {0} {n 1 - f} ifelse} :f defun", None, 59, 59),
    "if": ("{n} {n 0 > {n 1 - f} if} :f defun", None, 59, 59),
    "times": ("{n} {n 0 > {{n 1 - f} 1 times} if} :f defun", 14, 29, 59),
    "eval": ("{n} {n 0 > {{n 1 - f} eval} if} :f defun", None, 29, 29),
}


def deepest(make, upper: int = LIMIT + 10) -> int:
    """The deepest ``n`` for which ``n f`` runs on the interpreter ``make`` returns, searched up to ``upper``."""
    low, high = 0, upper
    while low < high:
        middle = (low + high + 1) // 2
        try:
            make().process_expression(f"{middle} f")
        except StackerError:
            high = middle - 1
        else:
            low = middle
    return low


@pytest.mark.parametrize("word", DEPTHS)
def test_the_depth_a_recursion_through_a_wrapped_control_word_counts(word, limit):
    definition, built_in, wrapped, all_wrapped = DEPTHS[word]
    wrapped_word = "if" if word == "eval" else word

    def make(*words: str) -> Stacker:
        stacker = Stacker()
        for name in words:
            wrap(stacker, "priority", name)
        stacker.process_expression(definition)
        return stacker

    limit(LIMIT)
    if built_in is None:
        make().process_expression("4000 f")  # a tail call: the depth does not grow
    else:
        assert deepest(make) == built_in
    assert deepest(lambda: make(wrapped_word)) == wrapped
    assert deepest(lambda: make("if", "ifelse", "times")) == all_wrapped
    too_deep = make(wrapped_word)
    with pytest.raises(StackerError, match=TOO_DEEP.replace("(", r"\(").replace(")", r"\)")):
        too_deep.process_expression(f"{wrapped + 1} f")


# ---------------------------------------------------------------------------
# B. A subclass with a handler of its own for a word
# ---------------------------------------------------------------------------


class _Mine(Stacker):
    """An interpreter whose `if` pushes what it was given instead of choosing."""

    def _my_if(self, op, stack):
        true_block = stack.pop()
        condition = stack.pop()
        stack.append(("mine", str(condition), str(true_block)))

    _PRIORITY_HANDLERS: ClassVar[dict] = {**StackerCore._PRIORITY_HANDLERS, "if": _my_if}


@pytest.mark.parametrize(
    "program, expected",
    [
        ("true {1} if", ok(("mine", "True", "{1}"), trace=["true", "{1}", "if"])),
        ("{true {1} if} eval", ok(("mine", "True", "{1}"), trace=["{true {1} if}", "eval"])),
        ("0 {true {1} if drop 1 +} 20 times", ok(20, trace=["0", "{true {1} if drop 1 +}", "20", "times"])),
        ("1 20 :i {true {i} if} do", ok(*[("mine", "True", "{i}")] * 20, trace=["1", "20", ":i", "{true {i} if}", "do"])),
    ],
    ids=["at the top", "in a block", "hot", "in a loop"],
)
def test_a_subclass_handler_runs_in_place_of_the_built_in_everywhere(program, expected):
    assert outcome(program, _Mine()) == expected


# ---------------------------------------------------------------------------
# C. A word whose entry has no function keeps its meaning when registered over
# ---------------------------------------------------------------------------

NO_FUNCTION = {
    "eval": ("{1 2 +} eval", ok(3, trace=["{1 2 +}", "eval"])),
    "collect": ("{1 2} collect", ok([1, 2], trace=["{1 2}", "collect"])),
    "apply": ("[1 2] {+} apply", ok(3, trace=["[1 2]", "{+}", "apply"])),
    "macroexpand": ("{} {1} :m defmacro :m macroexpand", ok(1, trace=["{}", "{1}", ":m", "defmacro", ":m", "macroexpand"])),
    "break": ("{break} loop 9", ok(9, trace=["break"])),
    "global": ("5 :g global g", ok(5, trace=["5", ":g", "global", "g"])),
    "=": ("5 :x = x", ok(5, trace=["5", ":x", "=", "x"])),
    "set": ("5 :x set x", ok(5, trace=["5", ":x", "set", "x"])),
}


@pytest.mark.parametrize("word", NO_FUNCTION)
def test_a_word_without_a_function_runs_its_handler_whatever_is_registered_under_it(word):
    program, expected = NO_FUNCTION[word]
    stacker = Stacker()
    stacker.register_operator(word, lambda *taken: taken[-1].append("mine"), 1, False, "mine")
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)


# ---------------------------------------------------------------------------
# D. A function or lambda value called from Python
# ---------------------------------------------------------------------------


def test_a_function_value_called_from_python_returns_every_value_its_body_left():
    stacker = Stacker()
    stacker.process_expression("{x} {x 2 * x 3 *} :f defun")
    function = stacker.sfunctions["f"]["func"]
    assert function.run([3]) == [6, 9]
    assert function(3) == [6, 9]
    with pytest.raises(StackerError, match="The function `f` takes 1 arguments, got 2"):
        function.run([1, 2])


def test_an_error_in_a_function_called_from_python_is_the_bodys_own():
    stacker = Stacker()
    stacker.process_expression("{x} {x 0 /} :g defun")
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        stacker.sfunctions["g"]["func"](1)


def test_a_recursion_started_from_python_counts_against_the_limit(limit):
    stacker = Stacker()
    stacker.process_expression("{n} {n 0 == {0} {n 1 - h} ifelse} :h defun")
    limit(30)
    assert stacker.sfunctions["h"]["func"](20) == [0]
    assert stacker.sfunctions["h"]["func"](100) == [0]  # (a tail call: the depth does not grow)
    stacker.process_expression("{n} {n 0 == {0} {n 1 - k 1 +} ifelse} :k defun")
    assert stacker.sfunctions["k"]["func"](14) == [14]  # (two levels of depth per call)
    with pytest.raises(StackerError, match=r"Maximum recursion depth \(30\) exceeded in function `k`"):
        stacker.sfunctions["k"]["func"](15)


def test_a_lambda_value_called_from_python():
    stacker = Stacker()
    stacker.process_expression("{a b} {a b +} lambda")
    add = stacker.stack.pop()
    assert add(1, 2) == [3]
    with pytest.raises(StackerError, match="The lambda takes 2 arguments, got 1"):
        add(1)
    stacker.process_expression("{a} {a 0 /} lambda")
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        stacker.stack.pop()(1)


# ---------------------------------------------------------------------------
# E. A script included through the interpreter's methods, and through the words
# ---------------------------------------------------------------------------


@pytest.fixture
def scripts(tmp_path):
    (tmp_path / "lib.stk").write_text('{x} {x 1 +} :inc defun\n"lib-ran" echo\n', encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.stk").write_text('"../lib.stk" include\n', encoding="utf-8")
    (tmp_path / "bad.stk").write_text('1 2\n"a" 0 /\n', encoding="utf-8")
    (tmp_path / "nested_err.stk").write_text(f'1\n"{tmp_path / "bad.stk"}" include\n', encoding="utf-8")
    (tmp_path / "brk.stk").write_text("break\n", encoding="utf-8")
    (tmp_path / "left.stk").write_text("1 2 3\n", encoding="utf-8")
    (tmp_path / "self.stk").write_text(f'"{tmp_path / "self.stk"}" include\n', encoding="utf-8")
    return tmp_path


@pytest.fixture(params=["method", "word"])
def include(request):
    """Includes a file by the interpreter's method, or by the word: both must agree."""

    def include_file(stacker: Stacker, path, once: bool = False) -> None:
        if request.param == "method":
            (stacker.require if once else stacker.include)(str(path))
        else:
            stacker.process_expression(f'"{path}" {"require" if once else "include"}')

    return include_file


def test_an_included_file_defines_its_words_here_and_prints_as_it_runs(scripts, include):
    stacker = Stacker()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        include(stacker, scripts / "lib.stk")
        stacker.process_expression("5 inc")
    assert (list(stacker.stack), out.getvalue()) == ([6], "lib-ran\n")


def test_require_runs_a_file_once_and_include_runs_it_again(scripts, include):
    stacker = Stacker()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        include(stacker, scripts / "lib.stk", once=True)
        include(stacker, scripts / "lib.stk", once=True)
        include(stacker, scripts / "lib.stk")
    assert out.getvalue() == "lib-ran\nlib-ran\n"


def test_a_relative_include_resolves_against_the_including_file(scripts, include):
    stacker = Stacker()
    with contextlib.redirect_stdout(io.StringIO()):
        include(stacker, scripts / "sub" / "deep.stk")
    stacker.process_expression("1 inc")
    assert list(stacker.stack) == [2]


def test_a_file_including_itself_is_circular(scripts, include):
    path = scripts / "self.stk"
    with pytest.raises(StackerError) as caught:
        include(Stacker(), path)
    error = caught.value
    assert (type(error).__name__, str(error)) == ("IncludeError", f"Circular include detected: {path}")
    assert include_location_of(error) == ((str(path), 1, f'"{path}" include'), [])


def test_an_error_inside_an_included_file_carries_the_innermost_position(scripts, include):
    stacker = Stacker()
    with pytest.raises(StackerError) as caught:
        include(stacker, scripts / "nested_err.stk")
    error = caught.value
    assert (type(error).__name__, str(error)) == ("StackerTypeError", "`/` cannot use 'a' and 0 together")
    (file, line, source), frames = include_location_of(error)
    assert (file, line, source) == (str(scripts / "bad.stk"), 2, '"a" 0 /')
    assert frames == [(str(scripts / "nested_err.stk"), 2)]
    assert (list(stacker.trace), list(stacker.stack)) == (['"a"', "0", "/"], [])


def test_a_break_at_the_top_of_an_included_file_is_a_syntax_error_with_the_files_position(scripts, include):
    with pytest.raises(StackerError) as caught:
        include(Stacker(), scripts / "brk.stk")
    error = caught.value
    assert (type(error).__name__, str(error)) == ("StackerSyntaxError", "`break` can only be used inside a loop")
    assert include_location_of(error) is not None


def test_the_values_an_included_file_leaves_are_dropped_and_named(scripts, include, caplog):
    stacker = Stacker()
    with caplog.at_level(logging.WARNING):
        include(stacker, scripts / "left.stk")
    assert list(stacker.stack) == []
    assert [record.getMessage() for record in caplog.records] == ["3 values left on the stack at the end of left.stk: 1, 2, 3"]


def test_a_missing_file_is_reported_by_the_name_written(scripts, include):
    with pytest.raises(StackerError) as caught:
        include(Stacker(), scripts / "missing.stk")
    assert str(caught.value).startswith(f"File {scripts / 'missing.stk'} not found. Tried: ")


@pytest.mark.parametrize("word", ["include", "require"])
def test_the_word_refuses_a_path_that_is_not_a_string(word):
    assert outcome(f"5 {word}") == fails(
        "StackerTypeError", f'`{word}` expects the file path as a string, e.g. "lib.stk" {word}; got 5', ["5", word]
    )


# ---------------------------------------------------------------------------
# F. A higher-order word wrapped and registered again
# ---------------------------------------------------------------------------

WRAPPED_HOF = {
    "map": ("[1 2 3] {2 *} map", ok([2, 4, 6], trace=["[1 2 3]", "{2 *}", "map"]), [2]),
    "filter": ("[1 2 3] {1 >} filter", ok([2, 3], trace=["[1 2 3]", "{1 >}", "filter"]), [2]),
    "reduce": ("[1 2 3] 0 :acc :x {acc x +} reduce", ok(6, trace=["[1 2 3]", "0", ":acc", ":x", "{acc x +}", "reduce"]), [3]),
    "fold": ("[1 2 3] 10 :acc :x {acc x -} fold", ok(4, trace=["[1 2 3]", "10", ":acc", ":x", "{acc x -}", "fold"]), [3]),
    "zip": ("[1 2] [3 4] zip", ok([[1, 3], [2, 4]], trace=["[1 2]", "[3 4]", "zip"]), [2]),
}


@pytest.mark.parametrize("word", WRAPPED_HOF)
def test_a_wrapped_higher_order_word_leaves_what_the_built_in_leaves_and_is_called_once(word):
    program, expected, calls_expected = WRAPPED_HOF[word]
    stacker = Stacker()
    calls = wrap(stacker, "hof", word)
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)
    assert calls == calls_expected


ONE_VALUE = "`{word}` needs one value from the block for each element, but it left 2"
WRAPPED_HOF_CASES = {
    "map two values": ("map", "[1 2] {dup} map", fails("ResultCountError", ONE_VALUE.format(word="map"), ["[1 2]", "{dup}", "map"])),
    "map no value": ("map", "[1 2] {drop} map", fails("NoValueProducedError", "The block passed to `map` must leave a value on the stack. Use `dolist` for side-effect-only iteration.", ["[1 2]", "{drop}", "map"])),
    "map error": ("map", "[1 2] {0 /} map", fails("ZeroDivisionError", "division by zero", ["[1 2]", "{0 /}", "map"])),
    "map symbol": ("map", "{x} {x 10 *} :ten defun [1 2] :ten map", ok([10, 20], trace=["{x}", "{x 10 *}", ":ten", "defun", "[1 2]", ":ten", "map"])),
    "map lambda": ("map", "[1 2] {x} {x 1 +} lambda map", ok([2, 3], trace=["[1 2]", "{x}", "{x 1 +}", "lambda", "map"])),
    "map array": ("map", "[1 2] array {2 *} map", ok([2, 4], trace=["[1 2]", "array", "{2 *}", "map"])),
    "map over a block": ("map", "{a b} {1} map", fails("ResultCountError", ONE_VALUE.format(word="map"), ["{a b}", "{1}", "map"])),
    "filter error": ("filter", "[1 2] {0 /} filter", fails("ZeroDivisionError", "division by zero", ["[1 2]", "{0 /}", "filter"])),
    "reduce two values": ("reduce", "[1 2] 0 :a :x {a x} reduce", fails("ResultCountError", ONE_VALUE.format(word="reduce"), ["[1 2]", "0", ":a", ":x", "{a x}", "reduce"])),
    "reduce undefined symbol": ("reduce", "[1 2] 0 :a :x :foo reduce", fails("UndefinedSymbolError", "`foo` is not defined.", ["foo"])),
    "zip not a sequence": ("zip", "[1 2] 3 zip", fails("StackerTypeError", "`zip` expects a list, an array, a string or a block, got 3", ["[1 2]", "3", "zip"])),
    "zip array": ("zip", "[1 2] array [3 4] zip", ok([[1, 3], [2, 4]], trace=["[1 2]", "array", "[3 4]", "zip"])),
}


@pytest.mark.parametrize("case", WRAPPED_HOF_CASES)
def test_a_wrapped_higher_order_word_fails_and_succeeds_as_the_built_in_does(case):
    word, program, expected = WRAPPED_HOF_CASES[case]
    stacker = Stacker()
    wrap(stacker, "hof", word)
    assert outcome(program, stacker) == expected
    assert outcome(program)[:2] == expected[:2]  # (the built-in's trace may be the innermost block's: not compared)
