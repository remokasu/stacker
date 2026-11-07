"""A macro whose body is one block literal expands once per set of arguments, and the kept expansion is what a fresh one is.

Every program here runs with the expansions kept and with them never kept, and
must leave the same values, of the same types, or the same error. The traps are
the ways a kept expansion could go stale: the scope it is run in, the tables of
the interpreter it is run by, the identity of its arguments, the blocks it holds.
"""

import copy
import os
import tempfile

import pytest

from stacker import Stacker
from stacker.engine import machine
from stacker.engine.core import StackerCore
from stacker.lang import recursion
from stacker.lang.smacro import StackerMacro, template_only


@pytest.fixture(autouse=True)
def kept_expansions(monkeypatch):
    """These tests set the states themselves; the session's state (``STACKER_TEST_MEMO``) is put aside."""
    monkeypatch.setattr(machine, "MEMO_ENABLED", True)
    monkeypatch.setattr(machine, "MEMO_SHADOW", False)


def outcome(code, enabled=True, shadow=False, stacker=None):
    """What ``code`` leaves: the values with their types, or the error with its message."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(machine, "MEMO_ENABLED", enabled)
        patch.setattr(machine, "MEMO_SHADOW", shadow)
        if stacker is None:
            stacker = Stacker()
        try:
            stacker.process_expression(code)
        except Exception as error:  # noqa: BLE001 - the error is the outcome
            return ("error", type(error).__name__, str(error)), stacker
        return ("values", [(type(value).__name__, repr(value)) for value in stacker.stack]), stacker


def both(code):
    """The outcomes with the expansions kept and never kept, which must agree."""
    kept, stacker = outcome(code, enabled=True)
    fresh, _ = outcome(code, enabled=False)
    assert kept == fresh
    return kept, stacker


def hits(stacker, name):
    return stacker.macros[name].memo_hits


# ---------------------------------------------------------------------------
# Which macros keep expansions
# ---------------------------------------------------------------------------


def test_a_body_of_one_block_literal_keeps_expansions_and_any_other_body_does_not():
    stacker = Stacker()
    stacker.process_expression("{x} {{x x +}} :twice defmacro")
    stacker.process_expression("{c a b} { {c} eval {a} {b} ifelse } :my-if defmacro")
    stacker.process_expression("{} {gensym} :fresh defmacro")
    stacker.process_expression("{} {{1} {2}} :two defmacro")
    assert stacker.macros["twice"].expansions == {}
    assert stacker.macros["my-if"].expansions is None
    assert stacker.macros["fresh"].expansions is None
    assert stacker.macros["two"].expansions is None
    assert template_only(object()) is False


def test_alias_and_the_words_it_makes_keep_expansions():
    _, stacker = both("{over drop} :over2 alias 1 2 over2 over2 over2")
    assert hits(stacker, "over2") == 2
    assert stacker.macros["alias"].expansions is not None


def test_a_macro_that_runs_code_at_expansion_time_expands_every_time():
    kept, stacker = both(
        "{c a b} { {c} eval {a} {b} ifelse } :my-if defmacro 0 :acc set "
        "1 1000 :i { {i 2 % 1 ==} {acc 1 +} {acc 2 +} my-if :acc set } do acc"
    )
    assert kept == ("values", [("int", "1500")])
    assert hits(stacker, "my-if") == 0


def test_macroexpand_always_expands_anew_and_keeps_nothing():
    _, stacker = both("{x} {{x x +}} :tw defmacro 3 :tw macroexpand drop 3 :tw macroexpand")
    assert stacker.macros["tw"].expansions == {}
    assert hits(stacker, "tw") == 0


# ---------------------------------------------------------------------------
# The key: identity, not equality
# ---------------------------------------------------------------------------


def test_equal_arguments_of_other_types_are_other_expansions():
    kept, _ = both("{x} {{x x +}} :twice defmacro 1 twice 1.0 twice true twice")
    assert kept == ("values", [("int", "2"), ("float", "2.0"), ("int", "2")])


def test_the_same_object_hits_and_a_new_one_misses():
    # A string made by `+` is a new object on every implementation; equal ints need not be
    _, stacker = both('{x} {{x x +}} :twice defmacro "a" :a set a twice a twice a twice "b" :b set b "c" + twice b "c" + twice')
    assert hits(stacker, "twice") == 2


def test_a_list_argument_is_never_keyed():
    _, stacker = both("{l} {{l len}} :ln defmacro [1 2] :l set l ln l ln")
    assert hits(stacker, "ln") == 0
    assert stacker.macros["ln"].expansions == {}


def test_a_symbol_and_a_block_are_keyed_by_identity():
    _, stacker = both(
        "{s} {{s eval}} :call defmacro {} {7} :seven defun :seven :s set s call s call "
        "{b} {{b eval}} :run defmacro {8} :blk set blk run blk run"
    )
    assert hits(stacker, "call") == 1
    assert hits(stacker, "run") == 1


def test_an_identity_is_not_reused_for_another_object(monkeypatch):
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 1000 :a set a inc")
    (key, entry), = stacker.macros["inc"].expansions.items()
    stale = (("gone",), entry[1], entry[2])  # the entry of an object that is gone, under the same key
    stacker.macros["inc"].expansions[key] = stale
    monkeypatch.setattr(machine, "_memo_key", lambda macro, stack: (key, (stack[-1],)))
    stacker.process_expression("2000 inc")
    assert list(stacker.stack) == [1001, 2001]
    assert hits(stacker, "inc") == 0


# ---------------------------------------------------------------------------
# The traps: scope, tables, blocks, re-entry, depth
# ---------------------------------------------------------------------------


def test_the_kept_expansion_runs_in_the_scope_it_is_called_from():
    kept, stacker = both("{} {{y}} :gety defmacro {y} {gety} :h defun 1 h 2 h")
    assert kept == ("values", [("int", "1"), ("int", "2")])
    assert hits(stacker, "gety") == 1


def test_a_variable_the_kept_expansion_sets_is_the_callers():
    kept, _ = both("{v} {{v :out set}} :put defmacro {} {1 put out} :f defun f f 2 put out")
    assert kept == ("values", [("int", "1"), ("int", "1"), ("int", "2")])


def test_the_generated_code_can_call_a_function_that_calls_the_macro_again():
    kept, stacker = both("{} {{n 1 - :n set n 0 > {f} {} ifelse}} :step defmacro {} {step} :f defun 3 :n set f n")
    assert kept == ("values", [("int", "0")])
    assert hits(stacker, "step") == 2


def test_a_loop_and_a_recursive_function_in_the_generated_code():
    kept, _ = both(
        "{} {{0 :s set 1 10 :i {s i + :s set} do s}} :sum10 defmacro sum10 sum10 "
        "{} {{ {k} {k 0 == {1} {k 1 - fact k *} ifelse} :fact defun 5 fact }} :mkfact defmacro mkfact mkfact"
    )
    assert kept == ("values", [("int", "55"), ("int", "55"), ("int", "120"), ("int", "120")])


def test_a_lambda_made_by_the_kept_expansion_reads_names_where_it_runs():
    kept, stacker = both(
        "{} {{ {x} {x y +} lambda }} :mkadd defmacro 1 :y set mkadd :f set 2 :y set mkadd :g set "
        "{} {100 :y set mkadd} :h defun h :k set 10 f eval 10 g eval 10 k eval"
    )
    assert kept == ("values", [("int", "110"), ("int", "110"), ("int", "110")])  # `y` is read when the lambda runs
    assert hits(stacker, "mkadd") == 2


def test_the_kept_expansion_pushes_a_new_block_each_time_as_a_fresh_expansion_does():
    stacker = Stacker()
    stacker.process_expression("{} {{ {1} }} :mk defmacro mk mk mk")
    first, second, third = stacker.stack
    assert hits(stacker, "mk") == 2
    assert first == second == third
    assert first is not second and second is not third and first is not third
    (entry,) = stacker.macros["mk"].expansions.values()
    (literal,) = entry[1]
    assert all(block is not literal for block in (first, second, third))  # the kept block itself is never pushed


def test_the_kept_expansion_holds_no_callers_scope():
    stacker = Stacker()
    stacker.process_expression("{v} {{ {v 1 +} eval {2} }} :mk defmacro {} {5 mk} :f defun f f f")
    assert hits(stacker, "mk") == 2
    (entry,) = stacker.macros["mk"].expansions.values()
    tokens = entry[1]
    literals = [token for token in tokens if isinstance(token, StackerCore)]
    assert len(literals) == 2
    assert all(literal.variables is machine._KEPT for literal in literals)
    assert all(literal._bound_cache is None for literal in literals)  # the pushes cached no copy, which would hold f's scope


def test_a_kept_macro_called_with_too_few_arguments_fails_as_before_and_takes_nothing():
    results = []
    for enabled in (True, False):
        _, stacker = outcome("{a b} {{a b +}} :add2 defmacro 1 2 add2 1 2 add2 clear 7", enabled=enabled)
        result, _ = outcome("add2", enabled=enabled, stacker=stacker)
        results.append((result, list(stacker.stack), hits(stacker, "add2")))
    kept, fresh = results
    assert kept[0] == ("error", "StackUnderflowError", "Operator `add2` requires 2 arguments.")
    assert kept[:2] == fresh[:2]  # the same error, and the stack as the fresh path leaves it
    assert kept[2] == 1 and fresh[2] == 0


def test_a_macro_of_no_arguments_is_keyed_by_nothing_and_hits():
    _, stacker = both("{} {{1 2 +}} :three defmacro three three three")
    assert hits(stacker, "three") == 2
    assert list(stacker.macros["three"].expansions) == [()]


def test_a_hit_inside_a_macro_body_runs_on_a_core_that_is_no_expander(monkeypatch):
    cores = []
    kept = machine._kept_expansion

    def spy(frame, name, macro, entry, stack):
        child = kept(frame, name, macro, entry, stack)
        cores.append((frame.template, child.core))
        return child

    monkeypatch.setattr(machine, "_kept_expansion", spy)
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro {y} { 3 inc :z set {y z +} } :addz defmacro 10 addz 10 addz")
    assert list(stacker.stack) == [14, 14]
    (template, core), = [(t, c) for t, c in cores if t._interp_scope is not None]  # the hit met inside addz's body
    assert core._interp_scope is None and core._interp_name is None and not core._interp_params
    assert core.parent is template
    root = core
    while root.parent is not None:
        root = root.parent
    assert root is stacker


def test_a_kept_expansion_used_from_an_included_file_and_then_from_the_parent():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "child.stk")
        with open(path, "w", encoding="utf-8") as file:
            file.write("{x} {{x y +}} :addy defmacro 1 :y set 5 addy drop\n")
        kept, stacker = both(f'"{path}" include 2 :y set 5 addy')
    assert kept == ("values", [("int", "7")])
    assert hits(stacker, "addy") == 1


def test_a_function_defined_in_the_parent_after_the_include_is_seen_by_the_kept_expansion():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "child.stk")
        with open(path, "w", encoding="utf-8") as file:
            file.write("{} {{ {bar} eval }} :callbar defmacro {} {1} :bar defun callbar drop\n")
        kept, stacker = both(f'"{path}" include {{}} {{42}} :bar defun callbar')
    assert kept == ("values", [("int", "42")])
    assert hits(stacker, "callbar") == 1


def test_the_recursion_limit_is_reached_at_the_same_depth():
    limit = recursion.get_limit()
    recursion.set_limit(40)
    try:
        results = []
        for enabled in (True, False):
            stacker = Stacker()
            stacker.process_expression("{} {{rec}} :rec defmacro")
            result, _ = outcome("rec", enabled=enabled, stacker=stacker)
            results.append(result)
    finally:
        recursion.set_limit(limit)
    kept, fresh = results
    assert kept[:2] == ("error", "StackerRecursionError")
    assert kept == fresh


def test_an_error_in_the_kept_expansion_names_the_macro():
    kept, _ = both("{} {{nothing-here}} :m defmacro {m} {} iferror m")
    assert kept == ("error", "UndefinedSymbolError", "`nothing-here` is not defined. (in code generated by macro 'm')")


def test_an_error_while_expanding_keeps_nothing():
    kept, stacker = both("{x} {{:x set}} :bad defmacro 1 bad")
    assert kept[:2] == ("error", "StackerSyntaxError")
    assert stacker.macros["bad"].expansions == {}


def test_a_macro_called_inside_a_macro_body_during_expansion():
    kept, stacker = both("{x} {{x 1 +}} :inc defmacro {y} { 3 inc :z set {y z +} } :addz defmacro 10 addz 10 addz")
    assert kept == ("values", [("int", "14"), ("int", "14")])
    assert hits(stacker, "inc") == 1


# ---------------------------------------------------------------------------
# The table: redefinition, copy, eviction, giving up
# ---------------------------------------------------------------------------


def test_a_redefinition_starts_with_nothing_kept():
    kept, stacker = both("{x} {{x 2 *}} :tw defmacro 3 tw 3 tw {x} {{x 10 *}} :tw defmacro 3 tw 3 tw")
    assert kept == ("values", [("int", "6"), ("int", "6"), ("int", "30"), ("int", "30")])
    assert hits(stacker, "tw") == 1


def test_a_copy_of_the_interpreter_starts_with_nothing_kept():
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 1 inc 1 inc")
    twin = stacker.copy()
    assert twin.macros["inc"].expansions == {}
    assert twin.macros["inc"].memo_hits == 0
    twin.process_expression("5 inc 5 inc")
    assert list(twin.stack)[-2:] == [6, 6]
    assert twin.macros["inc"].memo_hits == 1
    assert stacker.macros["inc"].memo_hits == 1


def test_a_macro_whose_body_runs_code_copies_with_no_table():
    stacker = Stacker()
    stacker.process_expression("{} {gensym} :fresh defmacro")
    assert copy.deepcopy(stacker.macros["fresh"]).expansions is None


def test_the_state_a_macro_is_copied_or_pickled_with_has_nothing_kept():
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 1 inc 1 inc")
    macro = stacker.macros["inc"]
    assert macro.expansions and macro.memo_hits == 1
    state = macro.__getstate__()  # what pickle and deepcopy both take
    assert state["expansions"] == {} and state["memo_hits"] == 0 and state["memo_misses"] == 0
    assert macro.expansions and macro.memo_hits == 1  # the macro itself is untouched


def test_the_table_holds_at_most_memo_max_entries_and_the_oldest_goes_first():
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro")
    objects = [float(i) for i in range(machine.MEMO_MAX + 3)]
    for value in objects:
        stacker.push(value)
        stacker.process_expression("inc")
    table = stacker.macros["inc"].expansions
    assert len(table) == machine.MEMO_MAX
    assert [entry[0][0] for entry in table.values()] == objects[3:]
    assert list(stacker.stack) == [value + 1 for value in objects]


def test_a_macro_given_a_new_object_every_time_gives_up(monkeypatch):
    monkeypatch.setattr(machine, "MEMO_GIVE_UP", 5)
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 1000 :k set")
    for _ in range(5):
        stacker.process_expression("k 1 + :k set k inc drop")
    assert stacker.macros["inc"].expansions is not None
    stacker.process_expression("k 1 + :k set k inc drop")
    assert stacker.macros["inc"].expansions is None
    stacker.process_expression("3 inc 3 inc")
    assert list(stacker.stack) == [4, 4]
    assert stacker.macros["inc"].memo_hits == 0


def test_a_use_resets_the_misses_in_a_row(monkeypatch):
    monkeypatch.setattr(machine, "MEMO_GIVE_UP", 3)
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 1000 :k set")
    for _ in range(4):
        stacker.process_expression("k 1 + :k set k inc drop 3 inc drop")
    assert stacker.macros["inc"].expansions is not None


# ---------------------------------------------------------------------------
# The oracle: a kept expansion is what a fresh one is
# ---------------------------------------------------------------------------


def test_the_kept_expansion_matches_macroexpand_strictly():
    stacker = Stacker()
    stacker.process_expression('{a b s} {{a {b 1 +} "t" [1 2] :s}} :m defmacro {5} :blk set 3 blk :nm m drop')
    (entry,) = stacker.macros["m"].expansions.values()
    args, kept, bracket = entry
    stacker.process_expression("3 blk :nm :m macroexpand")
    fresh = stacker.stack[-1]
    assert fresh.bracket_type == bracket
    assert machine._same_expansion(fresh.tokens, kept, args)
    assert isinstance(kept[1], StackerCore) and kept[1] is not fresh.tokens[1]  # the block the template made is its own
    assert kept[1].tokens[0] is args[1]  # the block argument stands as itself


def test_the_strict_comparison_tells_a_type_a_value_an_argument_and_a_block_apart():
    same = machine._same_expansion
    block = StackerCore()
    other = StackerCore()
    assert same([1, "s"], [1, "s"], ())
    assert not same([1], [1.0], ())
    assert not same([1], [True], ())
    assert not same([1, 2], [1], ())
    assert not same([block], [other], (block,))  # an argument must stand as itself
    assert not same([block], [block], ())  # a block the template made must be another object
    assert same([block], [other], ())


def test_shadow_mode_checks_every_use_and_reports_a_stale_entry(monkeypatch):
    monkeypatch.setattr(machine, "MEMO_SHADOW", True)
    stacker = Stacker()
    stacker.process_expression("{x} {{x 1 +}} :inc defmacro 5 :a set a inc a inc")
    assert list(stacker.stack) == [6, 6]
    assert stacker.macros["inc"].memo_hits == 1
    (key, entry), = stacker.macros["inc"].expansions.items()
    stacker.macros["inc"].expansions[key] = (entry[0], [2, "+"], entry[2])  # not what the template makes
    with pytest.raises(machine.ExpansionMismatch):
        stacker.process_expression("a inc")


def test_a_registered_macro_that_is_not_a_stacker_macro_is_left_alone():
    class Foreign:
        name = "f"
        args = ()
        arg_count = 0

    stacker = Stacker()
    body = Stacker()
    body.process_expression("{{1}}")
    foreign = Foreign()
    foreign.body = body.stack[-1]
    stacker.register_macro("f", foreign)
    stacker.process_expression("f f")
    assert list(stacker.stack) == [1, 1]
    assert not isinstance(foreign, StackerMacro)
