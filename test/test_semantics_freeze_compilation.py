"""Semantics-freeze tests for what an optimization of the evaluation loop must keep.

These tests pin the *observed* behavior of the current interpreter where a
program changes what a name means, which scope a name lives in, or what an
error reports, while code that has already run is running again: a word
shadowed or redefined in the middle of a loop, a function redefined while it
runs, a block handed to another interpreter, a copy of an interpreter, the
text and the trace and the stack of an error. Expected values were captured
by running each program against the unmodified interpreter; they are frozen
observations, not derived from first principles. If one of these tests fails
after an optimization, the optimization changed the language.

Loops come in three sizes (``SHORT_LOOP``, ``LONG_LOOP`` and ``EARLY_LOOP``):
a short one whose expectation can be read at a glance; one whose body runs
thousands of times on each side of the change; and one that changes on its
second iteration and then runs thousands more. The change is therefore tried
before, in the middle of, and long after a block has started to run often,
whatever the engine does with a block that runs often.

A frozen observation is not a specification. A few observations below look
like defects (the tests say "Looks wrong"); they are pinned as they are, so
that an optimization cannot change them by accident, and when one is
corrected on purpose its test is rewritten to pin the fixed behavior and the
change is recorded in the CHANGELOG.

Sections:

 1. a variable named after a word (built-in or control), made mid-loop
 2. a plugin re-registers words from inside a loop body
 3. a function is redefined while a call of it is running
 4. a macro or a function takes the name of a variable or a word, mid-loop
 5. `:y set` in a function body: where the write goes
 6. `disable_plugin` / `disable_all_plugins` mid-loop
 7. `include` / `require` mid-loop
 8. closures made per iteration, and by loops with no scope of their own
 9. `break`
10. the "stack" entry of `try`
11. the message for too few values, per category of word
12. the recursion limit, exactly at the limit
13. the trace after an error
14. the order `vars` lists the variables in
15. the warning for a global named after a built-in word
16. a block made by one interpreter, run by another
17. `Stacker.copy()` of an interpreter that has run a loop and a function
18. a symbol where `times` or `do` needs a number
19. host-registered words under names that are not bare words
20. a reserved word met after an `echo`
21. what a control word, `set` and a function call show while they run: the body `times` leaves on the stack
    while it reads its count, the name `set` refuses before it takes the value, the trace of each body, a `break`
    in a `while` condition, a control word re-registered and restored mid-loop
"""

import itertools
import logging
from collections.abc import Callable, Iterable

import pytest

from stacker import Stacker
from stacker.constant import constants
from stacker.engine import recursion
from stacker.engine.core import StackerCore
from stacker.engine.data_type import Symbol
from stacker.error import (
    DropError,
    DupError,
    NipError,
    OverError,
    ReservedWordError,
    RotError,
    StackerRecursionError,
    StackerSyntaxError,
    StackerTypeError,
    StackUnderflowError,
    SwapError,
    UndefinedSymbolError,
)
from stacker.operators.loop import loop_operators

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: How many times a block runs in the "long" scenarios. Whatever threshold the engine uses to treat a block as hot must be
#: below HOT // 2: LONG_LOOP runs its body HOT // 2 - 1 times before the change, and the change has to meet a hot body
HOT = 3000
#: ``(iterations, the iteration a change happens on)``: a loop that reads at a glance
SHORT_LOOP = (4, 2)
#: The change comes in the middle of a loop that runs HOT times: the body is hot on both sides of it
LONG_LOOP = (HOT, HOT // 2)
#: The change comes on the second iteration of a loop that runs HOT times: before the body can be hot
EARLY_LOOP = (HOT, 2)

loop_sizes = pytest.mark.parametrize(
    ("count", "at"), [SHORT_LOOP, LONG_LOOP, EARLY_LOOP], ids=["short", "long", "long-early"]
)
change_orders = pytest.mark.parametrize(
    "change_first", [True, False], ids=["change-then-use", "use-then-change"]
)
#: Run before a scenario: no call at all, or HOT of them, so what the scenario calls has been run often
calls_before = pytest.mark.parametrize("times", [0, HOT], ids=["cold", f"after-{HOT}-calls"])


def run(program: str, stacker: Stacker | None = None) -> list[object]:
    """Runs ``program`` on a fresh interpreter's own stack, or on ``stacker``, and returns the stack.

    Args:
        program: Stacker source.
        stacker: The interpreter to run it on.
    """
    if stacker is None:  # (not `or`: an interpreter with no tokens of its own is falsy)
        stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


def shown(values: Iterable[object]) -> list[object]:
    """The values with every code block replaced by its text: a block equals nothing but a block.

    This compares text only: a block and a string of the same text compare equal, and the scope a block is bound to
    is not seen (the closure section pins scopes).

    Args:
        values: A stack, or part of one.
    """
    return [str(value) if isinstance(value, StackerCore) else value for value in values]


def fails(program: str, expected: type[Exception], stacker: Stacker | None = None) -> tuple[Stacker, Exception]:
    """Runs ``program``, which must raise an ``expected`` error, and returns the interpreter and the error.

    Args:
        program: Stacker source.
        expected: The class the error must belong to (the tests that pin the
            exact type compare ``type(error)`` themselves).
        stacker: The interpreter to run it on.
    """
    if stacker is None:
        stacker = Stacker()
    with pytest.raises(expected) as info:
        stacker.process_expression(program)
    return stacker, info.value


def mid_loop(change: str, use: str, count: int, at: int, change_first: bool = True, guard: str = "if") -> str:
    """A ``do`` loop of ``count`` iterations: ``use`` runs on every one, ``change`` on iteration ``at``.

    Args:
        change: Code that changes what a name means.
        use: Code that depends on it.
        count: How many iterations the loop has.
        at: The iteration the change happens on.
        change_first: Whether the change comes before the use in the body
            (the change is seen from iteration ``at``) or after it (from
            iteration ``at + 1``).
        guard: The word that runs ``change`` on iteration ``at``: ``if``, or
            ``ifelse`` when the change is about ``if`` itself, so that the
            guard is not what is being changed.
    """
    condition = f"i {at} == {{ {change} }}"
    changing = f"{condition} if" if guard == "if" else f"{condition} {{}} ifelse"
    body = f"{changing} {use}" if change_first else f"{use} {changing}"
    return f"1 {count} :i {{ {body} }} do"


def first_seen(at: int, change_first: bool) -> int:
    """The first iteration that sees a change made on iteration ``at``."""
    return at if change_first else at + 1


def calls_of(call: str, times: int) -> str:
    """Code that runs ``call`` (which leaves one value) ``times`` times in a loop and drops what it leaves."""
    return f"1 {times} :w {{ {call} drop }} do"


def with_loops(rows: list, also_long: Iterable[str] = ()) -> list:
    """The rows once per loop, with ``count``, ``at`` and ``change_first`` added at the end of each.

    Every row runs on the short loop in both orders (change then use, use then
    change) and on the early-change loop with the use first: the order matters
    only around the change, which the short loop has in both. The rows whose
    ids are in ``also_long`` run in both orders on the loop that changes in the
    middle of a hot loop too, which costs the most.

    Args:
        rows: ``pytest.param`` rows, each with an id.
        also_long: The ids of the rows that also run on ``LONG_LOOP``.
    """
    loops = [("short", SHORT_LOOP, True), ("short", SHORT_LOOP, False), ("long-early", EARLY_LOOP, False)]
    middle = [("long", LONG_LOOP, True), ("long", LONG_LOOP, False)]
    return [
        pytest.param(
            *row.values, count, at, change_first,
            id=f"{row.id}-{name}-{'change-then-use' if change_first else 'use-then-change'}",
        )
        for row in rows
        for name, (count, at), change_first in (loops + middle if row.id in also_long else loops)
    ]


@pytest.fixture
def word_host() -> Stacker:
    """An interpreter with a plugin word, ``triple``, and a function word registered from the host, ``hostf``."""
    stacker = Stacker()
    stacker.register_plugin("triple", lambda a: a * 3, True, False, "triple")
    stacker.register_sfunction("hostf", lambda a, b: a + b, 2, True, "adds")
    return stacker


# ---------------------------------------------------------------------------
# 1. A variable named after a word, made in the middle of a loop
# ---------------------------------------------------------------------------

#: (word, a use of it, what the use leaves as the word, what it leaves once a variable 99 hides the word, the word
#: that guards the change in the loop)
WORDS_TO_HIDE = [
    ("+", "1 2 +", [3], [1, 2, 99], "if"),
    ("sum", "[1 2 3] sum", [6], [[1, 2, 3], 99], "if"),
]
#: The same for the control words, which leave their blocks on the stack as values (`shown` compares them as text).
#: The change to `if` is guarded by an `ifelse`: see the test about the guard for what happens to an `if` guard.
#: Sections 2 and 4 build their control-word rows from this table too, so each word meets each way to take a name
CONTROL_WORDS_TO_HIDE = [
    ("if", "true {1} if", [1], [True, "{1}", 99], "ifelse"),
    ("ifelse", "true {1} {2} ifelse", [1], [True, "{1}", "{2}", 99], "if"),
    ("times", "{7} 2 times", [7, 7], ["{7}", 2, 99], "if"),
    ("while", "{false} {1} while", [], ["{false}", "{1}", 99], "if"),
    ("do", "1 2 :k {k} do", [1, 2], [1, 2, Symbol("k"), "{k}", 99], "if"),
    ("dolist", "[1 2] :k {k} dolist", [1, 2], [[1, 2], Symbol("k"), "{k}", 99], "if"),
    ("loop", "{break} loop", [], ["{break}", 99], "if"),
    ("cond", "{true} {1} 1 cond", [1], ["{true}", "{1}", 1, 99], "if"),
]
#: (how, code before the loop, code on the iteration of the change); WORD stands for the word
WAYS_TO_MAKE_THE_VARIABLE = [
    ("global", "", "99 :WORD global"),
    ("set-through-a-name", ":WORD :target set", "99 target set"),
    ("eval-of-a-block", "", "{ 99 :WORD set } eval"),
]
HIDING_FIELDS = ("before_loop", "change", "use", "as_word", "as_variable", "guard")


def hiding(words, ways) -> list:
    """The cases of ``words`` hidden by a variable made each of ``ways``."""
    return [
        pytest.param(
            before.replace("WORD", word), change.replace("WORD", word), use, as_word, as_variable, guard, id=f"{word}-{how}"
        )
        for (word, use, as_word, as_variable, guard), (how, before, change) in itertools.product(words, ways)
    ]


#: Every way to make the variable for the first two words; the control words are hidden by a `global` only (what is
#: tried with them is the word, not the way the variable is made)
HIDING = hiding(WORDS_TO_HIDE, WAYS_TO_MAKE_THE_VARIABLE) + hiding(CONTROL_WORDS_TO_HIDE, WAYS_TO_MAKE_THE_VARIABLE[:1])


@pytest.mark.parametrize(HIDING_FIELDS, HIDING)
@loop_sizes
@change_orders
def test_a_variable_named_after_a_word_made_mid_loop_shadows_it_from_the_next_use_and_after_the_loop(
    before_loop, change, use, as_word, as_variable, guard, count, at, change_first
):
    first = first_seen(at, change_first)
    program = f"{before_loop} {mid_loop(change, use, count, at, change_first, guard)} {use}"
    # (the last use, after the loop, is the variable too)
    assert shown(run(program)) == as_word * (first - 1) + as_variable * (count - first + 1) + as_variable


@loop_sizes
def test_a_variable_named_if_made_mid_loop_takes_over_the_if_of_the_loop_bodys_own_guard_too(count, at):
    # The guard is run by the very `if` the variable replaces: from the next iteration it leaves its own three
    # values (False, the block, 99) as well as the use's
    program = mid_loop("99 :if global", "true {1} if", count, at, change_first=False)
    assert shown(run(program)) == [1] * at + [True, "{1}", 99, False, "{99 :if global}", 99] * (count - at)


@pytest.mark.parametrize("change", ["99 :+ set", "{ 99 :+ set } eval"], ids=["set", "eval-of-a-block"])
@loop_sizes
def test_a_variable_made_mid_loop_inside_a_function_shadows_the_word_only_until_the_function_returns(change, count, at):
    program = "{} { " + mid_loop(change, "1 2 +", count, at) + " } :f defun f 1 2 +"
    assert run(program) == [3] * (at - 1) + [1, 2, 99] * (count - at + 1) + [3]


# ---------------------------------------------------------------------------
# 2. A plugin re-registers words from inside a loop body
# ---------------------------------------------------------------------------

#: Every control word has a plugin that re-registers it as a word that pushes a marker
MARKED_WORDS = tuple(word for word, *_ in CONTROL_WORDS_TO_HIDE)


def marking(word: str) -> Callable[[Stacker], None]:
    """A plugin function that re-registers the control word ``word`` as one that pushes ``mine-<word>``.

    Args:
        word: The control word.
    """

    def redefine(core):
        # (a control word's function is given the stack last, whatever else it is given)
        core.register_operator(word, lambda *taken: taken[-1].append(f"mine-{word}"), 2, False, "pushes a marker")

    return redefine


@pytest.fixture
def registering_host() -> Stacker:
    """An interpreter with plugin words that take the interpreter and register words when they run."""
    stacker = Stacker()

    def redefine_dup(core):
        core.register_operator("dup", lambda stack: stack.append(100), 0, False, "pushes 100")

    def redefine_plus(core):
        core.register_operator("+", lambda a, b: a * b, 2, True, "multiplies")

    def register_operator_of_a_new_name(core):
        core.register_operator("brand-new", lambda a: a * 10, 1, True, "a word the interpreter has not")

    def register_plugin_word(core):
        core.register_plugin("brand-new", lambda a: a * 10, True, False, "multiplies by ten")

    def register_function_word(core):
        core.register_sfunction("brand-new", lambda a: a * 10, 1, True, "multiplies by ten")

    plugins = {
        "redefine-dup": redefine_dup,
        "redefine-plus": redefine_plus,
        "register-operator-of-a-new-name": register_operator_of_a_new_name,
        "register-plugin-word": register_plugin_word,
        "register-function-word": register_function_word,
    }
    plugins.update({f"redefine-{word}": marking(word) for word in MARKED_WORDS})
    for name, function in plugins.items():
        stacker.register_plugin(name, function, push_result_to_stack=False, pass_core=True, desc=name)
    return stacker


def marker_rows(words: list) -> list:
    """The cases of the control words in ``words``, each re-registered by its plugin as a word that pushes a marker.

    Args:
        words: Rows of ``CONTROL_WORDS_TO_HIDE``.
    """
    return [
        pytest.param(f"redefine-{word}", use, as_word, [f"mine-{word}"], guard, id=f"plugin-{word}")
        for word, use, as_word, _as_variable, guard in words
    ]


#: (the plugin, a use of the word it redefines, what the use leaves as it was, what it leaves redefined, the guard word)
REDEFINITIONS = [
    pytest.param("redefine-dup", "7 dup", [7, 7], [7, 100], "if", id="plugin-dup"),
    pytest.param("redefine-plus", "3 4 +", [7], [12], "if", id="plugin-plus"),
    *marker_rows(CONTROL_WORDS_TO_HIDE),
]
REDEFINITION_FIELDS = ("plugin", "use", "as_it_was", "as_redefined", "guard")
#: The rows that also run on the loop that changes in the middle of a hot loop (see `with_loops`)
REDEFINITIONS_ALSO_LONG = (
    "plugin-dup", "plugin-plus", "plugin-if", "plugin-ifelse", "plugin-times", "plugin-while", "plugin-do"
)


@pytest.mark.parametrize((*REDEFINITION_FIELDS, "count", "at", "change_first"), with_loops(REDEFINITIONS, REDEFINITIONS_ALSO_LONG))
def test_a_word_redefined_by_a_plugin_mid_loop_runs_its_new_definition_from_the_next_use_and_after_the_loop(
    registering_host, plugin, use, as_it_was, as_redefined, guard, count, at, change_first
):
    first = first_seen(at, change_first)
    program = f"{mid_loop(plugin, use, count, at, change_first, guard)} {use}"
    # (the last use, after the loop, is the redefined word too)
    assert run(program, registering_host) == as_it_was * (first - 1) + as_redefined * (count - first + 1) + as_redefined


# (the function-body test runs four of the words: the others need no more to show the body is not frozen)
@pytest.mark.parametrize(
    REDEFINITION_FIELDS,
    [row for row in REDEFINITIONS if row.id in ("plugin-dup", "plugin-plus", "plugin-if", "plugin-times")],
)
@loop_sizes
def test_a_function_body_made_before_the_redefinition_runs_the_new_word(
    registering_host, plugin, use, as_it_was, as_redefined, guard, count, at
):
    program = "{} { " + use + " } :used defun " + mid_loop(plugin, "used", count, at, change_first=False, guard=guard) + " used"
    # (the function is called from the loop, the use leaving its values after it each time, and once more after the loop)
    assert run(program, registering_host) == as_it_was * at + as_redefined * (count - at) + as_redefined


@loop_sizes
def test_the_if_of_the_loop_bodys_own_guard_is_the_redefined_one_too(registering_host, count, at):
    # The guard is run by the `if` the plugin replaces: from the next iteration it leaves a marker as well as the use
    program = mid_loop("redefine-if", "true {1} if", count, at, change_first=False)
    assert run(program, registering_host) == [1] * at + ["mine-if", "mine-if"] * (count - at)


def test_register_operator_with_the_name_of_no_built_in_word_registers_nothing(registering_host):
    # Looks wrong: the call neither fails nor adds a word, so the program only finds out when it uses the name
    stacker, error = fails("register-operator-of-a-new-name 5 brand-new", UndefinedSymbolError, registering_host)
    assert (type(error), str(error), list(stacker.stack)) == (UndefinedSymbolError, "`brand-new` is not defined.", [5])


@pytest.mark.parametrize("plugin", ["register-plugin-word", "register-function-word"])
@loop_sizes
def test_a_word_registered_mid_loop_by_a_plugin_runs_from_the_next_iteration(registering_host, plugin, count, at):
    # (the word is registered after the use on iteration `at`, so it is first used on the next one)
    program = mid_loop(plugin, f"i {at} > {{ i brand-new }} if", count, at, change_first=False)
    assert run(program, registering_host) == [10 * i for i in range(at + 1, count + 1)]


# ---------------------------------------------------------------------------
# 3. A function is redefined while a call of it is running
# ---------------------------------------------------------------------------

#: f(3) replaces f by a body that multiplies by 1000; every call adds its n to the result of the next one
REDEFINES_ON_THE_WAY_DOWN = "{n} {n 0 <= {0} {n 3 == {{n} {n 1000 *} :f defun} if n 1 - f n +} ifelse} :f defun"
#: f(2) replaces f by a body that multiplies by 100, between its two calls of f
REDEFINES_BETWEEN_TWO_CALLS = "{n} {n 0 <= {0} {n 1 - f n 2 == {{n} {n 100 *} :f defun} if n 1 - f +} ifelse} :f defun"


@calls_before
def test_calls_already_running_when_a_function_is_redefined_finish_with_the_old_body(times):
    # f(5), f(4) and f(3) go on adding their n with the old body; f(2), the first call made
    # after the redefinition, runs the new one and gives 2 * 1000
    assert run(f"{REDEFINES_ON_THE_WAY_DOWN} {calls_of('1 f', times)} 5 f") == [2012]


@calls_before
def test_a_call_made_after_the_redefinition_uses_the_new_body(times):
    assert run(f"{REDEFINES_ON_THE_WAY_DOWN} {calls_of('1 f', times)} 5 f 5 f") == [2012, 5000]


@calls_before
def test_a_body_that_redefines_its_function_between_two_calls_of_it_runs_the_second_call_with_the_new_body(times):
    # f(2) calls f(1) with the old body (0), redefines f, calls f(1) with the new one (100): 100.
    # Back in f(3), its own second call, f(2), is the new body as well (200): 100 + 200
    assert run(f"{REDEFINES_BETWEEN_TWO_CALLS} {calls_of('1 f', times)} 3 f") == [300]


# ---------------------------------------------------------------------------
# 4. A macro or a function takes the name of a variable or of a word, in the middle of a loop
# ---------------------------------------------------------------------------


@loop_sizes
@change_orders
def test_a_macro_defined_mid_loop_takes_over_the_name_of_a_variable_from_the_next_use(count, at, change_first):
    first = first_seen(at, change_first)
    program = "5 :m set 0 :r set " + mid_loop("{} {{100}} :m defmacro", "r m + :r set", count, at, change_first) + " r m"
    assert run(program) == [5 * (first - 1) + 100 * (count - first + 1), 100]


def test_a_variable_hidden_by_a_macro_is_still_there_and_a_list_literal_reads_it():
    # Looks wrong: the bare `m` expands the macro while `[m]` reads the variable of the same name
    assert run("5 :m set {} {{100}} :m defmacro m [m]") == [100, [5]]


def test_a_variable_set_after_a_macro_of_the_same_name_does_not_take_the_name_back():
    # Looks wrong: as above, the macro wins the bare name and the variable is read only by a list literal
    assert run("{} {{100}} :m defmacro 5 :m set m [m]") == [100, [5]]


def macro_rows(words: list) -> list:
    """The cases of the control words in ``words``, each taken by a macro that expands to 7.

    Args:
        words: Rows of ``CONTROL_WORDS_TO_HIDE``.
    """
    rows = []
    for word, use, as_word, as_variable, guard in words:
        operands = as_variable[:-1]  # what the use pushes before the word, when the word does not run
        rows.append(pytest.param("{} {{7}} :" + word + " defmacro", use, as_word, [*operands, 7], guard, id=f"macro-{word}"))
    return rows


def function_rows(words: list) -> list:
    """The cases of the control words in ``words``, each taken by a function that takes what the use pushes and leaves "mine".

    Args:
        words: Rows of ``CONTROL_WORDS_TO_HIDE``.
    """
    rows = []
    for word, use, as_word, as_variable, guard in words:
        parameters = " ".join(f"p{i}" for i in range(len(as_variable) - 1))  # one for each value the use pushes
        definition = "{" + parameters + '} {"mine"} :' + word + " defun"
        rows.append(pytest.param(definition, use, as_word, ["mine"], guard, id=f"function-{word}"))
    return rows


#: (the code that takes the name, a use of it, what the use leaves before, what it leaves after, the guard word). Every
#: control word is taken by a macro and by a function, as section 1 hides it with a variable and section 2 has a
#: plugin redefine it
TAKEN_BY_A_DEFINITION = [
    pytest.param("{} {{7}} :+ defmacro", "1 2 +", [3], [1, 2, 7], "if", id="macro-plus"),
    pytest.param('{a b} {"mine"} :+ defun', "1 2 +", [3], ["mine"], "if", id="function-plus"),
    *macro_rows(CONTROL_WORDS_TO_HIDE),
    *function_rows(CONTROL_WORDS_TO_HIDE),
]
TAKEN_FIELDS = ("definition", "use", "as_word", "as_defined", "guard")
#: The rows that also run on the loop that changes in the middle of a hot loop (see `with_loops`)
TAKEN_ALSO_LONG = ("macro-plus", "function-plus", "macro-times", "macro-if", "function-if")


@pytest.mark.parametrize((*TAKEN_FIELDS, "count", "at", "change_first"), with_loops(TAKEN_BY_A_DEFINITION, TAKEN_ALSO_LONG))
def test_a_macro_or_function_defined_mid_loop_under_the_name_of_a_word_takes_the_name_from_the_next_use_and_after_the_loop(
    definition, use, as_word, as_defined, guard, count, at, change_first
):
    first = first_seen(at, change_first)
    program = f"{mid_loop(definition, use, count, at, change_first, guard)} {use}"
    # (the last use, after the loop, belongs to the macro or function too)
    assert shown(run(program)) == as_word * (first - 1) + as_defined * (count - first + 1) + as_defined


# ---------------------------------------------------------------------------
# 5. `:y set` in a function body: where the write goes
# ---------------------------------------------------------------------------

#: A function whose body sets y; it is defined at the global level, so its calls run in children of the global scope
SETS_Y = "{} {7 :y set y} :f defun"


@calls_before
def test_a_set_in_a_function_body_makes_a_local_when_the_name_is_nowhere_in_the_definition_chain(times):
    _, error = fails(f"{SETS_Y} {calls_of('f', times)} f drop y", UndefinedSymbolError)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`y` is not defined.")


@calls_before
def test_a_set_in_a_function_body_writes_the_variable_made_in_the_definition_chain_between_two_calls(times):
    # The calls before y existed made a local each (all gone); the one after it writes the global y,
    # which reads 0 before that call and 7 after it
    assert run(f"{SETS_Y} {calls_of('f', times)} 0 :y set y f drop y") == [0, 7]


@calls_before
def test_a_function_does_not_reach_the_local_variable_of_the_function_that_calls_it(times):
    # f is defined at the global level: its scope is a child of that, not of its caller's
    definitions = "{} {7 :y set} :f defun {} {1 :y set f y} :caller defun"
    assert run(f"{definitions} {calls_of('caller', times)} caller") == [1]


def test_neither_a_function_nor_its_caller_leaves_a_global_variable_made_by_a_set_of_a_new_name():
    program = "{} {7 :y set} :f defun {} {1 :y set f y} :caller defun caller drop y"
    _, error = fails(program, UndefinedSymbolError)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`y` is not defined.")


def test_a_function_defined_inside_a_call_writes_the_variable_of_that_call_before_a_global_one():
    program = "{} {5 :y set {} {7 :y set y} :inner defun} :outer defun outer 0 :y set inner drop y"
    assert run(program) == [0]


def test_a_function_defined_inside_a_call_that_has_no_such_variable_writes_the_global_one_once_it_exists():
    # The first inner makes a local; after the global y exists the second writes it
    program = "{} {{} {7 :y set y} :inner defun} :outer defun outer inner drop 0 :y set inner drop y"
    assert run(program) == [7]


# ---------------------------------------------------------------------------
# 6. `disable_plugin` / `disable_all_plugins` in the middle of a loop that uses a plugin word
# ---------------------------------------------------------------------------

#: (code before the loop, the disabling code run on the iteration of the change)
disabling = pytest.mark.parametrize(
    ("setup", "disable"),
    [
        ("", '"triple" disable_plugin'),
        ("", "disable_all_plugins"),
        ('{} {"triple" disable_plugin} :disable defun', "disable"),
    ],
    ids=["disable_plugin", "disable_all_plugins", "disable_plugin-in-a-function"],
)


@disabling
@loop_sizes
def test_a_plugin_word_disabled_mid_loop_is_undefined_in_the_next_iteration(word_host, setup, disable, count, at):
    program = f"{setup} {mid_loop(disable, 'i triple', count, at, change_first=False)}"
    _, error = fails(program, UndefinedSymbolError, word_host)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`triple` is not defined.")


@disabling
@loop_sizes
def test_the_stack_at_the_disabled_plugin_word_holds_the_results_so_far_and_the_failing_iterations_value(
    word_host, setup, disable, count, at
):
    program = f"{setup} {mid_loop(disable, 'i triple', count, at, change_first=False)}"
    stacker, _ = fails(program, UndefinedSymbolError, word_host)
    assert list(stacker.stack) == [3 * i for i in range(1, at + 1)] + [at + 1]


def test_a_plugin_word_disabled_between_two_calls_of_a_function_that_uses_it_is_undefined_in_the_second(word_host):
    program = '{x} {x triple} :f defun 2 f "triple" disable_plugin 3 f'
    stacker, error = fails(program, UndefinedSymbolError, word_host)
    assert (type(error), str(error), list(stacker.stack)) == (UndefinedSymbolError, "`triple` is not defined.", [6])


# ---------------------------------------------------------------------------
# 7. `include` / `require` in the middle of a loop
# ---------------------------------------------------------------------------


@pytest.fixture
def library(tmp_path) -> str:
    """A script that defines a word and a variable; returns its path as a string literal for a program."""
    path = tmp_path / "lib.stk"
    path.write_text("{x} {x 100 +} :plus100 defun\n42 :answer set\n")
    return f'"{path.as_posix()}"'


@loop_sizes
def test_a_file_included_mid_loop_gives_the_following_iterations_its_word_and_its_variable(library, count, at):
    program = mid_loop(f"{library} include", f"i {at} >= {{ i plus100 answer }} if", count, at)
    assert run(program) == [value for i in range(at, count + 1) for value in (i + 100, 42)]


@loop_sizes
def test_the_word_and_the_variable_of_a_file_included_mid_loop_are_there_after_the_loop(library, count, at):
    assert run(mid_loop(f"{library} include", "i drop", count, at) + " 5 plus100 answer") == [105, 42]


def test_a_word_is_unknown_before_the_file_that_defines_it_is_included(library):
    _, error = fails(mid_loop(f"{library} include", "i plus100", 4, 2), UndefinedSymbolError)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`plus100` is not defined.")


def test_a_file_included_in_a_function_leaves_its_word_to_everyone(library):
    program = "{} { " + mid_loop(f"{library} include", "i drop", 4, 2) + " } :f defun f 5 plus100"
    assert run(program) == [105]


def test_the_variable_of_a_file_included_in_a_function_is_gone_when_the_function_returns(library):
    program = "{} { " + mid_loop(f"{library} include", "i drop", 4, 2) + " } :f defun f answer"
    _, error = fails(program, UndefinedSymbolError)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`answer` is not defined.")


def test_a_file_required_in_a_function_binds_its_variable_in_the_global_scope(library):
    program = "{} { " + mid_loop(f"{library} require", "i drop", 4, 2) + " } :f defun f 5 plus100 answer"
    assert run(program) == [105, 42]


# ---------------------------------------------------------------------------
# 8. Closures made per iteration, and by loops with no scope of their own
# ---------------------------------------------------------------------------

closure_counts = pytest.mark.parametrize("count", [3, HOT], ids=["short", "long"])


def closures_of(body: str, count: int) -> str:
    """A ``do`` loop whose body leaves a lambda or a block each iteration, then the list of what it left."""
    return f"1 {count} :i {{ {body} }} do {count} listn"


@closure_counts
def test_lambdas_made_in_a_do_body_keep_the_variable_of_their_own_iteration(count):
    assert run(closures_of("{} {i} lambda", count) + " {eval} map") == [list(range(1, count + 1))]


@closure_counts
def test_a_lambda_made_after_the_loop_variable_was_set_in_the_body_keeps_the_value_set(count):
    # `set` finds the iteration's own i and updates it there
    program = closures_of("i 10 * :i set {} {i} lambda", count) + " {eval} map"
    assert run(program) == [[10 * i for i in range(1, count + 1)]]


@closure_counts
def test_a_block_left_by_each_iteration_keeps_the_value_the_body_set_into_the_loop_variable(count):
    program = closures_of("i 10 * :i set {i}", count) + " {eval} map"
    assert run(program) == [[10 * i for i in range(1, count + 1)]]


@closure_counts
def test_a_variable_first_set_in_the_body_is_shared_by_every_lambda_while_the_loop_variable_is_not(count):
    # k is made outside the loop's own scope and overwritten by every iteration: all the lambdas read the last
    program = closures_of("i 10 * :k set {} {k i +} lambda", count) + " {eval} map"
    assert run(program) == [[10 * count + i for i in range(1, count + 1)]]


@closure_counts
def test_each_lambda_updates_its_own_copy_of_the_loop_variable(count):
    program = closures_of("{} {i 100 + :i set i} lambda", count) + " :cells set cells {eval} map cells {eval} map"
    first = [100 + i for i in range(1, count + 1)]
    second = [200 + i for i in range(1, count + 1)]
    assert run(program) == [first, second]


#: (a loop that has no scope of its own and leaves a lambda or a block per iteration; COUNT stands for how many)
SHARED_SCOPE_LOOPS = [
    pytest.param("0 :k set {k 1 + :k set {} {k} lambda} COUNT times", id="times-lambdas"),
    pytest.param("0 :k set {k COUNT <} {k 1 + :k set {} {k} lambda} while", id="while-lambdas"),
    pytest.param("0 :k set {k 1 + :k set {} {k} lambda k COUNT == {break} if} loop", id="loop-lambdas"),
    pytest.param("0 :k set {k 1 + :k set {k}} COUNT times", id="times-blocks"),
    pytest.param("0 :k set {k COUNT <} {k 1 + :k set {k}} while", id="while-blocks"),
    pytest.param("0 :k set {k 1 + :k set {k} k COUNT == {break} if} loop", id="loop-blocks"),
]


@pytest.mark.parametrize("loop", SHARED_SCOPE_LOOPS)
@closure_counts
def test_closures_made_by_a_loop_with_no_scope_of_its_own_all_see_the_variable_as_the_loop_left_it(loop, count):
    program = loop.replace("COUNT", str(count)) + f" {count} listn {{eval}} map"
    assert run(program) == [[count] * count]


def test_lambdas_made_in_a_dolist_body_keep_the_element_of_their_own_iteration():
    assert run("[10 20 30] :x { x 1 + :x set {} {x} lambda } dolist 3 listn {eval} map") == [[11, 21, 31]]


def test_lambdas_made_by_a_function_a_loop_calls_keep_the_calls_argument_and_the_iteration():
    program = "{n} {1 3 :i { {} {n i +} lambda } do} :mk defun 100 mk 200 mk 6 listn {eval} map"
    assert run(program) == [[101, 102, 103, 201, 202, 203]]


def test_lambdas_made_in_nested_loops_see_the_outer_variable_as_the_inner_body_left_it():
    # The inner body sets the outer i (shared by the inner iterations of one outer iteration)
    program = "1 2 :i { 1 2 :j { i 10 * j + :i set {} {i j +} lambda } do } do 4 listn {eval} map"
    assert run(program) == [[113, 114, 213, 214]]


# ---------------------------------------------------------------------------
# 9. `break`
# ---------------------------------------------------------------------------

#: The body counts in n, leaves n on the stack and calls `stop` (a function that breaks) when n is 3.
#: Were the break not to leave the loop, the body ends it with an error at 10 instead of running for ever
COUNTING_BODY = '{ n ++ :n set n n 3 == { stop } if n 10 == { "Runaway" "the break did not leave the loop" throw } if }'
BREAKING_LOOPS = [
    pytest.param("1 10 :k BODY do", id="do"),
    pytest.param("[1 2 3 4 5 6 7 8 9 10] :k BODY dolist", id="dolist"),
    pytest.param("BODY 10 times", id="times"),
    pytest.param("{ n 10 < } BODY while", id="while"),
    pytest.param("BODY loop", id="loop"),
]


@pytest.mark.parametrize("loop", BREAKING_LOOPS)
def test_break_in_a_function_called_by_a_loop_body_ends_that_loop_and_keeps_what_the_iterations_left(loop):
    program = "{} {break} :stop defun 0 :n set " + loop.replace("BODY", COUNTING_BODY)
    assert run(program) == [1, 2, 3]


@pytest.mark.parametrize("last", [3, HOT - 1], ids=["short", "long"])
def test_break_in_an_if_in_the_loop_body_ends_the_loop_and_keeps_what_the_iterations_left(last):
    assert run(f"1 {HOT} :i {{ i i {last} == {{ break }} if }} do") == list(range(1, last + 1))


def test_break_in_a_function_takes_the_functions_arguments_and_results_with_it():
    # `bk` took the 3 off the stack and broke before it left anything
    assert run("{x} {x 1000 + break} :bk defun 1 5 :i { i dup 3 == { bk } if } do") == [1, 2]


def test_break_in_a_lambda_called_by_a_loop_body_ends_that_loop():
    assert run("{} {break} lambda :brk set 1 5 :i { i i 3 == { brk eval } if } do") == [1, 2, 3]


def test_break_in_a_function_with_a_loop_of_its_own_leaves_only_that_loop():
    program = "{} {1 3 :j { j 2 == { break } if j } do 99} :g defun 1 3 :i { i g } do"
    assert run(program) == [1, 1, 99, 2, 1, 99, 3, 1, 99]


def test_break_in_the_inner_of_two_loops_leaves_only_the_inner_one():
    assert run("1 3 :i { 1 3 :j { j 2 == { break } if i j } do } do") == [1, 1, 2, 1, 3, 1]


def test_break_inside_a_try_block_ends_the_enclosing_loop_without_running_the_handler():
    assert run("1 5 :i { { i i 3 == { break } if } { drop 0 } try } do") == [1, 2, 3]


@pytest.mark.parametrize(
    "program",
    ["break", "{} {break} :stop defun stop", "[1 2 3] {dup 2 == {break} if} map"],
    ids=["direct", "through-a-function", "in-a-map-body"],
)
def test_break_with_no_loop_around_it_is_a_syntax_error(program):
    _, error = fails(program, StackerSyntaxError)
    assert (type(error), str(error)) == (StackerSyntaxError, "`break` can only be used inside a loop")


def test_a_break_through_a_function_leaves_the_recursion_depth_where_it_was():
    before = recursion.get_depth()
    run("{} {break} :stop defun 1 5 :i { i i 3 == { stop } if } do")
    assert recursion.get_depth() == before


# ---------------------------------------------------------------------------
# 10. The "stack" entry of `try`
# ---------------------------------------------------------------------------

#: (code before the try, the tried block, the stack below the try, the stack the error recorded)
TRY_CASES = [
    pytest.param("", "{1 +}", [], [], id="too-few-values"),
    pytest.param("7", '{1 "a" +}', [7], [7], id="type-error"),
    pytest.param("{x} {x 1 + zzz} :f defun 7", "{10 20 f}", [7], [7, 10], id="failure-in-a-called-function"),
    pytest.param("5", "{1 2 {3 0 /} eval}", [5], [5, 1, 2], id="failure-in-a-nested-block"),
]


@pytest.mark.parametrize(("before", "block", "below", "recorded"), TRY_CASES)
def test_try_records_the_stack_at_the_failure_in_the_error_dictionary(before, block, below, recorded):
    # Looks wrong: what the failing word had already taken is not in the record. `{1 +}` records [], not [1];
    # `10 20 f` records only the 10 (f took the 20, and the 21 its body made on its own stack went with it)
    assert run(f'{before} {block} {{"stack" get}} try') == below + [recorded]


@pytest.mark.parametrize(("before", "block", "below", "recorded"), TRY_CASES)
def test_try_leaves_the_stack_as_it_was_when_it_began_once_the_handler_drops_the_error(before, block, below, recorded):
    assert run(f"{before} {block} {{drop}} try") == below


def test_try_records_the_same_stack_when_the_tried_block_has_run_thousands_of_times():
    program = f'1 {HOT} :i {{ {{ i {HOT} == {{ zzz }} if i }} {{"stack" get}} try }} do'
    assert run(program) == [*range(1, HOT), list(range(1, HOT))]


# ---------------------------------------------------------------------------
# 11. The message for too few values, per category of word
# ---------------------------------------------------------------------------

#: (program, the error's type, its full text, the stack left)
UNDERFLOWS = [
    pytest.param("1 +", StackUnderflowError, "Operator `+` requires 2 arguments.", [], id="regular-word"),
    pytest.param("+", StackUnderflowError, "Operator `+` requires 2 arguments.", [], id="regular-word-with-nothing"),
    pytest.param("neg", StackUnderflowError, "Operator `neg` requires 1 argument.", [], id="regular-word-of-one"),
    pytest.param("dup", DupError, "Stack is empty", [], id="dup"),
    pytest.param("swap", SwapError, "Stack has less than 2 elements", [], id="swap"),
    pytest.param("1 swap", SwapError, "Stack has less than 2 elements", [1], id="swap-with-one"),
    pytest.param("drop", DropError, "Stack is empty", [], id="drop"),
    pytest.param("1 over", OverError, "Stack has less than 2 elements", [1], id="over"),
    pytest.param("1 2 rot", RotError, "Stack has less than 3 elements", [1, 2], id="rot"),
    pytest.param("1 nip", NipError, "Stack has less than 2 elements", [1], id="nip"),
    pytest.param("[1 2 3] map", StackUnderflowError, "Operator `map` requires 2 arguments.", [], id="higher-order-word"),
    pytest.param("reduce", StackUnderflowError, "Operator `reduce` requires 3 arguments.", [], id="reduce"),
    pytest.param("true if", StackUnderflowError, "Operator `if` requires 2 arguments.", [], id="if"),
    pytest.param("true {1} ifelse", StackUnderflowError, "Operator `ifelse` requires 3 arguments.", [], id="ifelse"),
    pytest.param("{1} times", StackUnderflowError, "Operator `times` requires 2 arguments.", [], id="times"),
    pytest.param("{true} while", StackUnderflowError, "Operator `while` requires 2 arguments.", [], id="while"),
    pytest.param("1 2 :i do", StackUnderflowError, "Operator `do` requires 4 arguments.", [], id="do"),
    pytest.param("loop", StackUnderflowError, "Operator `loop` requires 1 argument.", [], id="loop"),
    # Looks wrong: `cond` takes a count, so it needs 1 argument, not 0
    pytest.param("cond", StackUnderflowError, "Operator `cond` requires 0 arguments.", [], id="cond"),
    # Looks wrong: "1 pairs"
    pytest.param(
        "1 cond",
        StackUnderflowError,
        "`cond` needs 2 values below the count (1 pairs of a condition and a result), but the stack has 0.",
        [1],
        id="cond-with-a-count",
    ),
    pytest.param("{x y} {x y +} :f defun 1 f", StackUnderflowError, "Function `f` requires 2 arguments.", [], id="function"),
    pytest.param("{x} {x} :f defun f", StackUnderflowError, "Function `f` requires 1 argument.", [], id="function-of-one"),
    pytest.param("triple", StackUnderflowError, "Operator `triple` requires 1 argument.", [], id="plugin-word"),
    pytest.param("1 hostf", StackUnderflowError, "Function `hostf` requires 2 arguments.", [], id="function-registered-by-the-host"),
    # Looks wrong: calling a lambda says "Operator `lambda`", and "1 arguments"
    pytest.param("{x} {x} lambda eval", StackUnderflowError, "Operator `lambda` requires 1 arguments.", [], id="lambda-of-one"),
    pytest.param("{x y} {x y +} lambda :g set 1 g eval", StackUnderflowError, "Operator `lambda` requires 2 arguments.", [], id="lambda"),
]


@pytest.mark.parametrize(("program", "error_type", "message", "left"), UNDERFLOWS)
def test_too_few_values_raise_the_error_of_the_words_kind_with_its_full_text(word_host, program, error_type, message, left):
    _, error = fails(program, error_type, word_host)
    assert (type(error), str(error)) == (error_type, message)


@pytest.mark.parametrize(("program", "error_type", "message", "left"), UNDERFLOWS)
def test_the_values_a_word_took_before_it_failed_for_want_of_more_are_gone(word_host, program, error_type, message, left):
    stacker, _ = fails(program, error_type, word_host)
    assert shown(stacker.stack) == left


def failing_on_the_last_iteration(body: str, before: str = "0", clear: str = "drop") -> str:
    """A ``do`` loop of ``HOT`` iterations that runs ``body`` on a stack that holds enough values until the last.

    The last iteration first runs ``clear``, which leaves ``body`` short of values.

    Args:
        body: Code that works on a stack with enough values and leaves the stack as it was.
        before: Code that makes the stack the body needs.
        clear: Code that empties it.
    """
    return f"{before} 1 {HOT} :i {{ i {HOT} == {{ {clear} }} if {body} }} do"


#: (program, the error's type, its full text): the word runs HOT - 1 times without trouble in the loop body, then
#: finds too few values on the last iteration
HOT_UNDERFLOWS = [
    pytest.param(failing_on_the_last_iteration("1 +"), StackUnderflowError, "Operator `+` requires 2 arguments.", id="regular-word"),
    pytest.param(failing_on_the_last_iteration("dup drop"), DupError, "Stack is empty", id="dup"),
    pytest.param(
        failing_on_the_last_iteration("swap", "0 0", "drop drop"), SwapError, "Stack has less than 2 elements", id="swap"
    ),
    pytest.param(
        failing_on_the_last_iteration("{1 +} map", "[0]"), StackUnderflowError, "Operator `map` requires 2 arguments.", id="higher-order-word"
    ),
    pytest.param(
        failing_on_the_last_iteration("f", "{x} {x} :f defun 5"), StackUnderflowError, "Function `f` requires 1 argument.", id="function"
    ),
    pytest.param(
        # (`if` takes its condition from the stack: the guard supplies one on every iteration but the last)
        f"1 {HOT} :i {{ i {HOT} < {{ true }} if {{1}} if drop }} do",
        StackUnderflowError,
        "Operator `if` requires 2 arguments.",
        id="if",
    ),
]


@pytest.mark.parametrize(("program", "error_type", "message"), HOT_UNDERFLOWS)
def test_too_few_values_in_a_loop_body_that_has_run_thousands_of_times_raise_the_same_error_and_leave_nothing(
    program, error_type, message
):
    stacker, error = fails(program, error_type)
    assert (type(error), str(error), list(stacker.stack)) == (error_type, message, [])


# ---------------------------------------------------------------------------
# 12. The recursion limit, exactly at the limit
# ---------------------------------------------------------------------------

#: The limit the recursion tests set: the depth of the return stack, every activation counted (a call, the arm of
#: an `ifelse` it runs, a macro's expansion and the run of the expansion). Each word below says the deepest level
#: that fits under it
RECURSION_LIMIT = 6


@pytest.fixture
def small_recursion_limit():
    """Sets the recursion limit to ``RECURSION_LIMIT`` for the test, then puts it and the depth counter back."""
    limit, depth = recursion.get_limit(), recursion.get_depth()
    recursion.set_limit(RECURSION_LIMIT)
    yield RECURSION_LIMIT
    recursion.set_limit(limit)
    recursion._depth = depth  # (a failing test may have left the counter raised)


#: Each word answers its depth: (the definition, the call that takes the depth, (the error's name, its kind), its
#: full text, the deepest level under the limit). A function or a lambda takes two activations a level (the call
#: and the arm of its `ifelse`): 3 levels fit in 6. A macro's expansion and the run of the expansion stand at the
#: same depth, and the arm inside the expansion one deeper: 5 levels fit, and the sixth fails as it expands
RECURSIVE_WORDS = [
    pytest.param(
        "{n} {n 1 > {n 1 - f 1 +} {1} ifelse} :f defun",
        "f",
        ("f", "function"),
        f"Maximum recursion depth ({RECURSION_LIMIT}) exceeded in function `f`",
        3,
        id="function",
    ),
    pytest.param(
        "{n} {n 1 > {n 1 - again eval 1 +} {1} ifelse} lambda :again set",
        "again eval",
        ("<lambda>", "function"),
        f"Maximum recursion depth ({RECURSION_LIMIT}) exceeded in function `<lambda>`",
        3,
        id="lambda",
    ),
    pytest.param(
        "{n} {n 1 > {{n 1 - m 1 +}} {{1}} ifelse} :m defmacro",
        "m",
        ("m", "macro"),
        f"Maximum recursion depth ({RECURSION_LIMIT}) exceeded in macro `m` (while expanding macro 'm')",
        5,
        id="macro",
    ),
]
#: The depth of the descents made before the scenario, which run inside a `do` loop (the loop and its body are two
#: activations of their own): two levels, enough to make the recursive arm hot and shallow enough to fit
WARM_UP_DEPTH = 2
#: Each descent is a few calls: this many of them are about HOT calls before the scenario
descents_before = pytest.mark.parametrize(
    "times", [0, HOT // RECURSION_LIMIT], ids=["cold", f"after-{HOT // RECURSION_LIMIT}-descents"]
)


@descents_before
@pytest.mark.parametrize(("definition", "call", "named", "message", "deepest"), RECURSIVE_WORDS)
def test_recursion_to_exactly_the_limit_succeeds(small_recursion_limit, definition, call, named, message, deepest, times):
    warm_up = calls_of(f"{WARM_UP_DEPTH} {call}", times)
    assert run(f"{definition} {warm_up} {deepest} {call}") == [deepest]


@descents_before
@pytest.mark.parametrize(("definition", "call", "named", "message", "deepest"), RECURSIVE_WORDS)
def test_recursion_one_level_past_the_limit_fails_with_the_recursion_error_and_its_message(
    small_recursion_limit, definition, call, named, message, deepest, times
):
    warm_up = calls_of(f"{WARM_UP_DEPTH} {call}", times)
    _, error = fails(f"{definition} {warm_up} {deepest + 1} {call}", StackerRecursionError)
    assert (type(error), str(error)) == (StackerRecursionError, message)


@pytest.mark.parametrize(("definition", "call", "named", "message", "deepest"), RECURSIVE_WORDS)
def test_the_recursion_error_carries_the_name_the_limit_and_the_kind(small_recursion_limit, definition, call, named, message, deepest):
    _, error = fails(f"{definition} {deepest + 1} {call}", StackerRecursionError)
    assert (error.name, error.limit, error.kind, error.depth) == (named[0], small_recursion_limit, named[1], None)


@pytest.mark.parametrize(("definition", "call", "named", "message", "deepest"), RECURSIVE_WORDS)
def test_the_depth_counter_is_back_where_it_was_after_the_failure(small_recursion_limit, definition, call, named, message, deepest):
    before = recursion.get_depth()
    fails(f"{definition} {deepest + 1} {call}", StackerRecursionError)
    assert recursion.get_depth() == before


# ---------------------------------------------------------------------------
# 13. The trace after an error
# ---------------------------------------------------------------------------


def trace_after(program: str, error_type: type[BaseException]) -> list[object]:
    """The trace (`--debug` shows its last tokens) of an interpreter on which ``program`` has failed.

    Args:
        program: Stacker source that fails.
        error_type: The exact type of the error it fails with.
    """
    stacker = Stacker()
    stacker.clear_trace()
    _, error = fails(program, error_type, stacker)
    assert type(error) is error_type
    return stacker.get_trace_copy()


#: (program, the type of the error it fails with, the trace after it): the tokens of the innermost block that failed,
#: or the program's own
TRACES = [
    pytest.param("true {foo} {1} ifelse", UndefinedSymbolError, ["foo"], id="true-branch-of-an-ifelse"),
    pytest.param("false {1} {foo} ifelse", UndefinedSymbolError, ["foo"], id="false-branch-of-an-ifelse"),
    pytest.param("true {foo} if", UndefinedSymbolError, ["foo"], id="if"),
    pytest.param("1 3 :i {foo} do", UndefinedSymbolError, ["foo"], id="do-body"),
    pytest.param("1 3 :i {1 foo 2} do", UndefinedSymbolError, [1, "foo", 2], id="do-body-of-three-tokens"),
    pytest.param("{foo} 2 times", UndefinedSymbolError, ["foo"], id="times-body"),
    pytest.param("{1 foo 2} 2 times", UndefinedSymbolError, [1, "foo", 2], id="times-body-of-three-tokens"),
    pytest.param("{true} {foo} while", UndefinedSymbolError, ["foo"], id="while-body"),
    pytest.param("{foo} {true} while", UndefinedSymbolError, ["foo"], id="while-condition"),
    pytest.param("{foo} loop", UndefinedSymbolError, ["foo"], id="loop-body"),
    pytest.param("[1 2] :x {foo} dolist", UndefinedSymbolError, ["foo"], id="dolist-body"),
    pytest.param("{true} {foo} 1 cond", UndefinedSymbolError, ["foo"], id="cond-result"),
    pytest.param("{foo} {true} 1 cond", UndefinedSymbolError, ["foo"], id="cond-condition"),
    pytest.param("{foo} eval", UndefinedSymbolError, ["foo"], id="eval-of-a-block"),
    pytest.param("{1 foo} eval", UndefinedSymbolError, [1, "foo"], id="eval-of-a-block-of-two-tokens"),
    pytest.param(":foo eval", UndefinedSymbolError, ["foo"], id="eval-of-a-symbol"),
    pytest.param("1 2 + foo", UndefinedSymbolError, ["1", "2", "+", "foo"], id="top-level"),
    # Looks wrong: a failure inside a function, a lambda or a `map` body leaves the caller's tokens as the trace,
    # not the body's, so `--debug` points at the call and not at the failing word
    pytest.param("{} {foo} :f defun f", UndefinedSymbolError, ["{}", "{foo}", ":f", "defun", "f"], id="inside-a-function"),
    pytest.param(
        "{x} {x foo} :f defun 3 f",
        UndefinedSymbolError,
        ["{x}", "{x foo}", ":f", "defun", "3", "f"],
        id="inside-a-function-with-an-argument",
    ),
    pytest.param(
        "{x} {x foo} lambda :g set 3 g eval",
        UndefinedSymbolError,
        ["{x}", "{x foo}", "lambda", ":g", "set", "3", "g", "eval"],
        id="inside-a-lambda",
    ),
    pytest.param("[1 2] {foo} map", UndefinedSymbolError, ["[1 2]", "{foo}", "map"], id="map-body"),
]


@pytest.mark.parametrize(("program", "error_type", "trace"), TRACES)
def test_the_trace_after_an_error_is_the_tokens_of_the_code_that_failed(program, error_type, trace):
    assert trace_after(program, error_type) == trace


def test_the_trace_after_an_error_in_a_loop_body_that_has_run_thousands_of_times_is_the_bodys_tokens():
    program = f"1 {HOT} :i {{ 5 i {HOT - 1} - / drop }} do"
    assert trace_after(program, ZeroDivisionError) == [5, "i", HOT - 1, "-", "/", "drop"]


def test_the_trace_of_a_program_that_succeeds_is_its_own_tokens():
    stacker = Stacker()
    stacker.process_expression("1 2 +")
    assert stacker.get_trace_copy() == ["1", "2", "+"]


def test_the_trace_after_an_error_that_a_try_caught_is_still_the_caught_blocks_tokens():
    # Looks wrong: the later failure of `foo` is at the top level, but the trace still shows the code
    # of the error that was caught
    assert trace_after("{1 0 /} {2} try 5 foo", UndefinedSymbolError) == [1, 0, "/"]


# ---------------------------------------------------------------------------
# 14. The order `vars` lists the variables in
# ---------------------------------------------------------------------------

#: The lines `vars` starts with: the constants the global scope holds from the start
CONSTANT_LINES = [f"{name} = {value}" for name, value in constants.items()]


def printed_by_vars(program: str, capsys) -> list[str]:
    """The lines ``vars`` prints at the end of ``program``."""
    run(f"{program} vars")
    return capsys.readouterr().out.splitlines()


@pytest.mark.parametrize("count", [4, HOT], ids=["short", "long"])
def test_vars_lists_the_variables_in_the_order_they_were_made_not_the_order_they_are_written(count, capsys):
    # Written c, a, b; made b (on iteration count - 2), a, c
    body = f"i {count} == {{ 3 :c set }} if i {count - 1} == {{ 2 :a set }} if i {count - 2} == {{ 1 :b set }} if"
    assert printed_by_vars(f"1 {count} :i {{ {body} }} do", capsys) == CONSTANT_LINES + ["b = 1", "a = 2", "c = 3"]


@pytest.mark.parametrize("make", ["set", "global"])
@pytest.mark.parametrize(
    ("loop", "also_listed"),
    [
        ("1 3 :i {BODY} do", []),
        ("[1 2 3] :i {BODY} dolist", []),
        ("0 :i set {i ++ :i set BODY} 3 times", ["i = 3"]),  # (the counter is made before the loop does anything)
    ],
    ids=["do", "dolist", "times"],
)
def test_vars_lists_the_variables_a_loop_made_in_the_order_it_made_them(loop, also_listed, make, capsys):
    body = f"i 3 == {{ 3 :c {make} }} if i 2 == {{ 2 :a {make} }} if i 1 == {{ 1 :b {make} }} if"
    printed = printed_by_vars(loop.replace("BODY", body), capsys)
    assert printed == CONSTANT_LINES + also_listed + ["b = 1", "a = 2", "c = 3"]


def test_vars_keeps_the_place_of_a_variable_that_is_set_again(capsys):
    program = "1 3 :i { i 1 == { 1 :b set 1 :a set } if i 2 == { 22 :b set } if } do"
    assert printed_by_vars(program, capsys) == CONSTANT_LINES + ["b = 22", "a = 1"]


def test_vars_does_not_list_the_variables_of_a_function_call_or_the_loop_variable_after_they_are_gone(capsys):
    program = "{} {1 3 :i { i :tmp set } do} :f defun f 1 2 :j { j :last set } do"
    assert printed_by_vars(program, capsys) == CONSTANT_LINES + ["last = 2"]


def test_vars_inside_a_loop_body_lists_the_iterations_variables_then_the_calls_then_the_global_ones(capsys):
    program = "{n} {1 2 :i { 5 :loc set vars } do} :f defun 7 f"
    run(program)
    assert capsys.readouterr().out.splitlines() == (
        ["i = 1", "n = 7", "loc = 5"] + CONSTANT_LINES + ["i = 2", "n = 7", "loc = 5"] + CONSTANT_LINES
    )


# ---------------------------------------------------------------------------
# 15. The warning for a global named after a built-in word, made by a `set` in a loop
# ---------------------------------------------------------------------------


def logged_by(program: str, caplog) -> list[tuple[str, str, str]]:
    """The ``(level, logger, message)`` of every record ``program`` logs at WARNING or above."""
    with caplog.at_level(logging.WARNING, logger="stacker"):
        run(program)
    return [(record.levelname, record.name, record.getMessage()) for record in caplog.records]


@pytest.mark.parametrize("count", [4, HOT], ids=["short", "long"])
def test_a_set_in_a_loop_that_makes_a_global_named_after_a_built_in_word_logs_once_not_per_iteration(count, caplog):
    logged = logged_by(f"1 {count} :i {{ i :sum set }} do", caplog)
    assert logged == [("WARNING", "stacker", "redefining built-in word 'sum'")]


@pytest.mark.parametrize(
    ("body", "messages"),
    [
        ("i :sum global", ["redefining built-in word 'sum'"]),
        ("{ i :sum set } eval", ["redefining built-in word 'sum'"]),
        ("i :sum set i :len set", ["redefining built-in word 'sum'", "redefining built-in word 'len'"]),
        ("i :alias set", ["redefining prelude word 'alias'"]),
    ],
    ids=["global", "eval-of-a-block", "two-words", "prelude-word"],
)
def test_each_global_made_in_a_loop_under_a_words_name_is_logged_once(body, messages, caplog):
    logged = logged_by(f"1 {HOT} :i {{ {body} }} do", caplog)
    assert [message for _, _, message in logged] == messages


def test_a_set_in_a_loop_inside_a_function_makes_a_local_and_logs_nothing(caplog):
    assert logged_by(f"{{}} {{1 {HOT} :i {{ i :sum set }} do}} :f defun f", caplog) == []


# ---------------------------------------------------------------------------
# 16. A block made by one interpreter, run by another
# ---------------------------------------------------------------------------


@pytest.fixture
def two_interpreters() -> tuple[Stacker, Stacker]:
    """Two interpreters that each have a variable x: 10 in the first, 20 in the second."""
    first, second = Stacker(), Stacker()
    first.process_expression("10 :x set")
    second.process_expression("20 :x set")
    return first, second


def made_by(interpreter: Stacker, code: str) -> object:
    """The one value ``code`` leaves when ``interpreter`` evaluates it (a block, a lambda), on a stack of its own."""
    return interpreter.eval(code)[-1]


def test_a_block_evaluated_by_another_interpreter_reads_the_variables_of_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    second.register_parameter("block", made_by(first, "{x 1 +}"))
    assert run("block eval", second) == [11]


def test_a_block_evaluated_by_another_interpreter_assigns_in_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    second.register_parameter("block", made_by(first, "{5 :z set}"))
    run("block eval", second)
    assert (first.variables.get("z"), "z" in second.variables) == (5, False)


def test_a_block_evaluated_by_another_interpreter_does_not_see_a_name_only_that_one_has(two_interpreters):
    first, second = two_interpreters
    second.process_expression("1 :only_second set")
    second.register_parameter("block", made_by(first, "{only_second}"))
    _, error = fails("block eval", UndefinedSymbolError, second)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`only_second` is not defined.")


def test_a_block_evaluated_by_another_interpreter_calls_the_functions_of_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    first.process_expression("{n} {n 1 +} :f defun")
    second.process_expression("{n} {n 100 +} :f defun")
    second.register_parameter("block", made_by(first, "{1 f}"))
    assert run("block eval", second) == [2]


def test_a_block_evaluated_by_another_interpreter_expands_the_macros_of_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    first.process_expression("{} {{1}} :m defmacro")
    second.process_expression("{} {{2}} :m defmacro")
    second.register_parameter("block", made_by(first, "{m}"))
    assert run("block eval", second) == [1]


def test_a_block_evaluated_by_another_interpreter_uses_the_operators_of_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    second.register_operator("+", lambda a, b: a * b, 2, True, "multiplies")
    second.register_parameter("block", made_by(first, "{3 4 +}"))
    assert run("block eval", second) == [7]


def test_a_lambda_evaluated_by_another_interpreter_reads_the_variables_of_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    second.register_parameter("lam", made_by(first, "{a} {a x +} lambda"))
    assert run("5 lam eval", second) == [15]


@pytest.mark.parametrize(
    ("program", "left"),
    [("true block if", [10]), ("1 2 :i block do", [10, 10]), ("block 2 times", [10, 10])],
    ids=["if", "do", "times"],
)
def test_a_block_run_by_any_word_of_another_interpreter_still_reads_the_one_that_made_it(two_interpreters, program, left):
    first, second = two_interpreters
    second.register_parameter("block", made_by(first, "{x}"))
    assert run(program, second) == left


def test_a_block_run_thousands_of_times_by_two_interpreters_in_turn_always_runs_in_the_one_that_made_it(two_interpreters):
    first, second = two_interpreters
    block = made_by(first, "{x 1 + :x set}")
    first.register_parameter("block", block)
    second.register_parameter("block", block)
    for interpreter in (second, first, second):
        interpreter.process_expression(f"block {HOT} times")
    assert (first.variables.get("x"), second.variables.get("x")) == (10 + 3 * HOT, 20)


# ---------------------------------------------------------------------------
# 17. `Stacker.copy()` of an interpreter that has run a loop and a function
# ---------------------------------------------------------------------------


@pytest.fixture(params=[3, HOT], ids=["after-3-iterations", f"after-{HOT}-iterations"])
def used(request) -> tuple[Stacker, int]:
    """An interpreter that has run a function in a loop of ``request.param`` iterations; and its ``total``."""
    stacker = Stacker()
    stacker.process_expression(
        "0 :total set {n} {n total + :total set total} :add defun " + f"1 {request.param} :i {{ i add drop }} do"
    )
    return stacker, request.param * (request.param + 1) // 2


def test_a_copy_runs_the_function_of_the_original_on_its_own_variable(used):
    original, total = used
    assert run("10 add", original.copy()) == [total + 10]


def test_the_function_of_a_copy_and_the_function_of_its_original_each_update_their_own_variable(used):
    original, total = used
    copy = original.copy()
    run("10 add", copy)
    run("100 add", original)
    assert (copy.variables.get("total"), original.variables.get("total")) == (total + 10, total + 100)


def test_a_variable_set_in_a_copy_does_not_appear_in_the_original_and_the_other_way_round(used):
    original, _ = used
    copy = original.copy()
    run("5 :only_in_copy set", copy)
    run("6 :only_in_original set", original)
    assert ("only_in_copy" in original.variables, "only_in_original" in copy.variables) == (False, False)


def test_a_loop_run_by_a_copy_sets_its_variables_in_the_copy_only(used):
    original, _ = used
    copy = original.copy()
    assert (run("0 :k set 1 3 :i { k i + :k set } do k", copy), "k" in original.variables) == ([6], False)


def test_a_function_redefined_in_a_copy_is_still_the_original_in_the_original(used):
    original, total = used
    copy = original.copy()
    run("{n} {n 1000 *} :add defun", copy)
    assert (run("2 add", copy), run("2 add", original)) == ([2000], [total + 2])


def test_a_lambda_and_a_macro_in_a_copy_work_on_the_copys_variables_not_the_originals():
    original = Stacker()
    original.process_expression("{} {{100}} :m defmacro 7 :q set {x} {x q +} lambda :lam set")
    copy = original.copy()
    copy.process_expression("1000 :q set")
    assert (run("1 lam eval m", copy), run("1 lam eval m", original)) == ([1001, 100], [8, 100])


def test_an_operator_registered_in_a_copy_does_not_change_the_original():
    original = Stacker()
    copy = original.copy()
    copy.register_operator("+", lambda a, b: a * b, 2, True, "multiplies")
    assert (run("3 4 +", copy), run("3 4 +", original)) == ([12], [7])


def test_a_plugin_disabled_in_a_copy_still_works_in_the_original():
    original = Stacker()
    original.register_plugin("triple", lambda a: a * 3, True, False, "triple")
    copy = original.copy()
    run('"triple" disable_plugin', copy)
    assert run("2 triple", original) == [6]


def test_the_stack_of_a_copy_starts_as_the_originals_and_then_goes_its_own_way():
    original = Stacker()
    original.process_expression("1 2 3")
    copy = original.copy()
    copy.process_expression("drop")
    assert (list(original.stack), list(copy.stack)) == ([1, 2, 3], [1, 2])


# ---------------------------------------------------------------------------
# 18. A symbol where `times` or `do` needs a number
# ---------------------------------------------------------------------------

SYMBOL_AS_A_VALUE = (
    "`{word}` cannot use the symbol `{name}` as a value. "
    "Write `{name}` for the variable's value, or `:{name} str` for its name as text."
)


@pytest.mark.parametrize(
    ("program", "word", "name"),
    [
        ("{1} :n times", "times", "n"),
        ("3 :n set {1} :n times", "times", "n"),
        ("{} {{1} :n times} :f defun 3 :n set f", "times", "n"),
        (":a 5 :i {i} do", "do", "a"),
        ("1 :b :i {i} do", "do", "b"),
        (":a :b :i {i} do", "do", "a"),
        ("1 :a set 3 :b set :a b :i {i} do", "do", "a"),
    ],
    ids=["times", "times-with-n-bound", "times-in-a-function", "do-start", "do-end", "do-both", "do-start-with-a-bound"],
)
def test_a_symbol_as_a_count_or_a_bound_is_refused_as_a_symbol_used_as_a_value(program, word, name):
    _, error = fails(program, StackerTypeError)
    assert (type(error), str(error)) == (StackerTypeError, SYMBOL_AS_A_VALUE.format(word=word, name=name))


def test_a_symbol_in_the_bodys_place_is_run_as_its_name_and_an_undefined_one_is_undefined():
    # `:n {1} times` has the count and the body the wrong way round: the block gives the count (1)
    # and the symbol is the body
    _, error = fails(":n {1} times", UndefinedSymbolError)
    assert (type(error), str(error)) == (UndefinedSymbolError, "`n` is not defined.")


def test_a_symbol_in_the_bodys_place_is_run_once_as_the_variable_it_names():
    assert run("3 :n set :n {1} times") == [3]


# ---------------------------------------------------------------------------
# 19. A macro or a function registered from the host under a name that is not a bare word
# ---------------------------------------------------------------------------


def with_macro_named(name: str) -> Stacker:
    """An interpreter with a macro, registered from the host under ``name``, that expands to 99."""
    stacker = Stacker()
    stacker.process_expression("{} {{99}} :made defmacro")
    stacker.register_macro(name, stacker.macros["made"])
    return stacker


def with_function_named(name: str) -> Stacker:
    """An interpreter with a function, registered from the host under ``name``, that leaves 99."""
    stacker = Stacker()
    stacker.register_sfunction(name, lambda: 99, 0, True, "leaves 99")
    return stacker


@pytest.mark.parametrize("name", ["[1 2]", ":x", "1"])
def test_a_macro_registered_from_the_host_under_a_name_that_is_not_a_bare_word_is_accepted(name):
    assert name in with_macro_named(name).macros


@pytest.mark.parametrize("name", ["[1 2]", ":x", "1"])
def test_a_function_registered_from_the_host_under_a_name_that_is_not_a_bare_word_is_accepted(name):
    assert name in with_function_named(name).sfunctions


#: (the macro's name, a program, the stack it leaves): the macro answers to the token as written
MACRO_NAMES = [
    pytest.param("[1 2]", "[1 2]", [99], id="list-literal"),
    pytest.param("[1 2]", "{[1 2]} eval", [99], id="list-literal-in-a-block"),
    pytest.param("[1 2]", "{} {[1 2]} :g defun g", [99], id="list-literal-in-a-function"),
    pytest.param("[1 2]", "[1 3]", [[1, 3]], id="another-list-literal"),
    pytest.param(":x", ":x", [99], id="symbol"),
    pytest.param(":x", "{:x} eval", [99], id="symbol-in-a-block"),
    pytest.param(":x", ":y", [Symbol("y")], id="another-symbol"),
    pytest.param("1", "1", [99], id="number"),
    pytest.param("1", "1 2 +", [101], id="number-in-arithmetic"),
    pytest.param("1", "2", [2], id="another-number"),
    pytest.param("1", "[1 2]", [[1, 2]], id="number-in-a-list-literal"),
    # A number inside a block is already a number when the block is made, so it is never looked up
    pytest.param("1", "{1} eval", [1], id="number-in-a-block"),
    pytest.param("1", "{} {1} :g defun g", [1], id="number-in-a-function"),
    pytest.param("1", "2 3 :i {1} do", [1, 1], id="number-in-a-loop-body"),
]


@pytest.mark.parametrize(("name", "program", "left"), MACRO_NAMES)
def test_a_macro_named_like_a_token_that_is_not_a_bare_word_answers_to_that_token(name, program, left):
    assert run(program, with_macro_named(name)) == left


#: (the function's name, a program, the stack it leaves): only a top-level number is looked up as a word
FUNCTION_NAMES = [
    pytest.param("[1 2]", "[1 2]", [[1, 2]], id="list-literal-is-built"),
    pytest.param(":x", ":x", [Symbol("x")], id="symbol-is-pushed"),
    pytest.param("1", "1", [99], id="number"),
    pytest.param("1", "1 2 +", [101], id="number-in-arithmetic"),
    pytest.param("1", "2", [2], id="another-number"),
    pytest.param("1", "[1 2]", [[1, 2]], id="number-in-a-list-literal"),
    pytest.param("1", "{1} eval", [1], id="number-in-a-block"),
    pytest.param("1", "{} {1} :g defun g", [1], id="number-in-a-function"),
    pytest.param("1", "2 3 :i {1} do", [1, 1], id="number-in-a-loop-body"),
]


@pytest.mark.parametrize(("name", "program", "left"), FUNCTION_NAMES)
def test_a_function_named_like_a_token_that_is_not_a_bare_word_is_called_only_where_the_token_is_looked_up_as_a_word(
    name, program, left
):
    assert run(program, with_function_named(name)) == left


# ---------------------------------------------------------------------------
# 20. `set` with a reserved word in the middle of a line, after an `echo`
# ---------------------------------------------------------------------------

#: (program, the word that refuses the name, the name): each is run after `"before" echo`
NAMING_RESERVED_WORDS = [
    pytest.param("5 :help set", "set", "help", id="set"),
    pytest.param("5 :about =", "set", "about", id="equals-sign"),
    pytest.param("5 :help global", "global", "help", id="global"),
    pytest.param("{} {1} :help defun", "defun", "help", id="defun"),
    pytest.param("{} {{1}} :help defmacro", "defmacro", "help", id="defmacro"),
    pytest.param("1 3 :help {1} do", "do", "help", id="do"),
    pytest.param("[1] :help {1} dolist", "dolist", "help", id="dolist"),
    pytest.param("5 {help} set", "set", "help", id="set-with-a-quoted-name"),
]


@pytest.mark.parametrize(("program", "word", "name"), NAMING_RESERVED_WORDS)
def test_naming_something_after_a_reserved_word_raises_the_reserved_word_error_with_its_message(program, word, name):
    _, error = fails(f'"before" echo {program} "after" echo', ReservedWordError)
    message = f"`{word}` cannot use `{name}` as a name: it is a reserved word, a REPL command"
    assert (type(error), str(error)) == (ReservedWordError, message)


@pytest.mark.parametrize(("program", "word", "name"), NAMING_RESERVED_WORDS)
def test_the_echo_before_a_reserved_word_is_refused_has_printed_and_the_one_after_has_not(capsys, program, word, name):
    fails(f'"before" echo {program} "after" echo', ReservedWordError)
    assert capsys.readouterr().out == "before\n"


def test_a_reserved_word_met_by_a_set_in_a_body_that_has_run_thousands_of_times_raises_after_every_echo_before_it(capsys):
    # The name is a quoted word on the last iteration only; `set` itself has run HOT - 1 times by then
    _, error = fails(f'1 {HOT} :i {{ "x" echo 5 i {HOT} == {{:help}} {{:tmp}} ifelse set }} do', ReservedWordError)
    message = "`set` cannot use `help` as a name: it is a reserved word, a REPL command"
    assert (type(error), str(error), capsys.readouterr().out) == (ReservedWordError, message, "x\n" * HOT)


def test_set_with_a_reserved_word_leaves_the_value_it_was_given_on_the_stack():
    # Looks wrong: the name is refused before the value is taken, so `5` stays (`defun` leaves its two blocks and
    # `defmacro` takes all three)
    stacker, _ = fails('"before" echo 5 :help set', ReservedWordError)
    assert list(stacker.stack) == [5]


def test_a_reserved_word_written_where_it_would_run_raises_the_reserved_word_error_after_an_echo(capsys):
    _, error = fails('"before" echo help', ReservedWordError)
    assert (type(error), str(error), capsys.readouterr().out) == (
        ReservedWordError,
        "`help` is a REPL command: type it alone at the REPL's prompt",
        "before\n",
    )


# ---------------------------------------------------------------------------
# 21. What a control word, `set` and a function call show while they run
# ---------------------------------------------------------------------------
# These pin the order in which the words take their arguments and run their bodies, from the outside: what the
# stack holds while a count is read, what `set` does before it takes the value, which tokens the trace shows, where a
# `break` goes. A faster way of running a hot body has to keep every one of them.


#: (the program that `try` runs, the stack the error recorded): `times` reads its count before it takes the body,
#: so a count that fails or leaves nothing leaves the body on the stack, where `try` records it; a count that is a
#: symbol fails after the body is taken
TIMES_COUNT_CASES = [
    pytest.param("{1} {0 0 /} times", [99, "{1}"], id="a-count-block-that-fails"),
    pytest.param("{1} {} times", [99, "{1}"], id="a-count-block-that-leaves-nothing"),
    pytest.param("{1} :n times", [99], id="a-count-that-is-a-symbol"),
]


@pytest.mark.parametrize(("tried", "recorded"), TIMES_COUNT_CASES)
def test_times_reads_its_count_before_it_takes_the_body_so_try_records_the_body_when_the_count_fails(tried, recorded):
    # 99 lies under the `try`; what the record holds beyond it is what `times` had left when it failed
    stack = run(f'99 {{{tried}}} {{"stack" get}} try')
    assert [shown(item) if isinstance(item, list) else item for item in stack] == [99, recorded]


def test_a_word_between_the_body_and_times_sees_the_body_on_the_stack():
    # `depth` counts the body: 1, so the body runs once per iteration, HOT times in all
    assert run(f"0 :c set 1 {HOT} :i {{ {{c 1 + :c set}} depth times }} do c") == [HOT]


def test_a_dup_between_the_body_and_times_makes_the_body_the_count_which_is_read_as_a_block():
    # the second copy is the count: a block that leaves nothing, refused with the body still on the stack
    stacker, error = fails(f"0 :c set 1 {HOT} :i {{ {{c 1 + :c set}} dup times }} do", StackerSyntaxError)
    assert "got a block that leaves nothing" in str(error)
    assert shown(stacker.stack) == ["{c 1 + :c set}"]


def test_set_refuses_a_literal_as_a_name_before_it_takes_the_value_even_when_set_has_run_thousands_of_times():
    stacker, error = fails(f"1 {HOT} :i {{ 5 i {HOT} == {{:true}} {{:tmp}} ifelse set }} do", StackerSyntaxError)
    assert str(error) == "`set` cannot bind `true`: it is a literal, not a variable"
    assert list(stacker.stack) == [5]


def test_set_refuses_a_repl_command_as_a_name_before_it_takes_the_value_even_when_set_has_run_thousands_of_times():
    stacker, _ = fails(f"1 {HOT} :i {{ 5 i {HOT} == {{:help}} {{:tmp}} ifelse set }} do", ReservedWordError)
    assert list(stacker.stack) == [5]


@pytest.mark.parametrize(
    ("body", "per_iteration"),
    [
        pytest.param("5 :dup set dup", [5], id="a-stack-word"),
        pytest.param("1 :+ set 2 3 +", [2, 3, 1], id="an-arithmetic-word"),
    ],
)
def test_a_variable_set_in_a_hot_body_hides_the_word_the_same_body_uses_right_after(body, per_iteration):
    assert run(f"1 {HOT} :i {{ {body} }} do") == per_iteration * HOT


def test_a_variable_named_set_made_mid_loop_turns_the_later_set_of_the_same_body_into_a_push():
    # from the iteration `set` becomes a variable, `7 :y set` pushes 7, the symbol and the variable's value
    assert run("1 3 :i { i 1 == {5 :set set} if 7 :y set } do") == [7, Symbol("y"), 5] * 3


#: (a loop body that fails on its last iteration, the type of the error, the trace after it): the tokens of the
#: innermost block that failed, which is the `{foo}` branch in every row but one, where the `while` condition
#: itself fails and the trace is the whole condition block
HOT_TRACES = [
    pytest.param(f"i {HOT} == {{foo}} if", UndefinedSymbolError, ["foo"], id="if"),
    pytest.param(f"i {HOT} == {{foo}} {{}} ifelse", UndefinedSymbolError, ["foo"], id="ifelse"),
    pytest.param(f"{{i {HOT} ==}} {{foo}} while", UndefinedSymbolError, ["foo"], id="while-body"),
    pytest.param(
        f"{{5 i {HOT - 1} - / drop false}} {{}} while",
        ZeroDivisionError,
        [5, "i", HOT - 1, "-", "/", "drop", False],
        id="while-condition",
    ),
    pytest.param(f"{{i {HOT} == {{foo}} if}} 1 times", UndefinedSymbolError, ["foo"], id="times"),
    pytest.param(f"{{i {HOT} == {{foo}} if break}} loop", UndefinedSymbolError, ["foo"], id="loop"),
    pytest.param(f"[1] :k {{i {HOT} == {{foo}} if}} dolist", UndefinedSymbolError, ["foo"], id="dolist"),
    pytest.param(f"1 1 :k {{i {HOT} == {{foo}} if}} do", UndefinedSymbolError, ["foo"], id="do"),
]


@pytest.mark.parametrize(("body", "error_type", "trace"), HOT_TRACES)
def test_the_trace_after_an_error_in_a_control_word_that_has_run_thousands_of_times_is_the_failing_blocks_tokens(
    body, error_type, trace
):
    assert trace_after(f"1 {HOT} :i {{ {body} }} do", error_type) == trace


def test_the_trace_after_an_error_in_a_function_called_thousands_of_times_is_the_callers_tokens():
    # Looks wrong, as in section 13: the trace points at the call, not at the failing word
    program = f"{{x}} {{x {HOT} == {{foo}} if}} :f defun 1 {HOT} :i {{i f}} do"
    assert trace_after(program, UndefinedSymbolError) == ["i", "f"]


def test_a_break_in_the_condition_of_a_while_leaves_the_loop_around_the_while_not_the_while():
    # i = 1: the condition holds, the body breaks out of the `while`, 100 is pushed; i = 2: the condition breaks,
    # out of the `do`
    assert run("1 3 :i { i {i 2 == {break} if true} {break} while 100 } do") == [1, 100, 2]


def test_a_control_word_re_registered_mid_loop_and_restored_later_runs_as_each_definition_says(registering_host):
    def restore_do(core):
        core.register_operator("do", loop_operators["do"]["func"], 4, False, "the loop again")

    registering_host.register_plugin("restore-do", restore_do, push_result_to_stack=False, pass_core=True, desc="")
    program = "1 6 :i { i 3 == {redefine-do} if i 5 == {restore-do} if 1 1 :k {k} do } do"
    assert run(program, registering_host) == [1, 1, "mine-do", "mine-do", 1, 1]


def test_set_re_registered_as_another_word_still_binds_the_variable():
    # `set` is run by its own handler, which does not read what was registered under the name
    stacker = Stacker()
    stacker.register_operator("set", lambda *taken: taken[-1].append("mine"), 2, False, "pushes a marker")
    assert run("5 :x set x", stacker) == [5]

