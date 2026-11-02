"""Tests for the counters that tell a compiled block when what it resolved may have gone stale."""

import pytest

from stacker import Stacker
from stacker.engine import generation
from stacker.engine.scope import ScopedVariables


@pytest.fixture
def stacker():
    return Stacker()


def words_advanced_by(stacker, action):
    before = stacker.operator_manager.generation
    action()
    return stacker.operator_manager.generation - before


def bindings_advanced_by(action):
    before = generation.bindings
    action()
    return generation.bindings - before


def epoch_advanced_by(action):
    before = generation.epoch
    action()
    return generation.epoch - before


# --- the word tables (one generation per interpreter) ---


@pytest.mark.parametrize(
    "define",
    [
        pytest.param(lambda s: s.eval("{x} {x} :f defun"), id="defun"),
        pytest.param(lambda s: s.eval("{} {{1}} :m defmacro"), id="defmacro"),
        pytest.param(lambda s: s.eval("{1 +} {inc} alias"), id="alias"),
        pytest.param(lambda s: s.register_sfunction("g", lambda x: x, 1), id="register_sfunction"),
        pytest.param(lambda s: s.register_plugin("p", lambda x: x), id="register_plugin"),
        pytest.param(lambda s: s.register_operator("dup", lambda x: x, 1, True), id="register_operator"),
    ],
)
def test_defining_or_replacing_a_word_advances_the_words_once_and_the_bindings_not_at_all(stacker, define):
    before = generation.bindings
    assert words_advanced_by(stacker, lambda: define(stacker)) == 1
    assert generation.bindings == before


def test_redefining_a_function_advances_the_words(stacker):
    stacker.eval("{x} {x} :f defun")
    assert words_advanced_by(stacker, lambda: stacker.eval("{x} {x 1 +} :f defun")) == 1


def test_disabling_a_plugin_advances_the_words_only_when_it_was_there(stacker, capsys):
    stacker.register_plugin("p", lambda x: x)
    assert words_advanced_by(stacker, lambda: stacker.eval('"p" disable_plugin')) == 1
    assert words_advanced_by(stacker, lambda: stacker.eval('"p" disable_plugin')) == 0


def test_disabling_all_plugins_advances_the_words_only_when_there_were_any(stacker):
    assert words_advanced_by(stacker, lambda: stacker.eval("disable_all_plugins")) == 0
    stacker.register_plugin("p", lambda x: x)
    assert words_advanced_by(stacker, lambda: stacker.eval("disable_all_plugins")) == 1


def test_replacing_a_word_that_does_not_exist_registers_nothing_and_advances_nothing(stacker):
    assert words_advanced_by(stacker, lambda: stacker.register_operator("no-such-word", lambda: 1, 0, False)) == 0
    assert "no-such-word" not in stacker.operator_manager.dispatch_table


def test_each_interpreter_counts_its_own_words(stacker):
    other = Stacker()
    assert words_advanced_by(stacker, lambda: other.eval("{x} {x} :f defun")) == 0


def test_running_code_that_defines_nothing_new_advances_neither_counter(stacker):
    stacker.eval("{x} {x 1 +} :inc defun 0 :acc set")
    program = "1 100 :i {acc inc :acc set i 2 % 0 == {acc} {acc 1 -} ifelse drop} do acc"
    words, bindings, epoch = stacker.operator_manager.generation, generation.bindings, generation.epoch
    stacker.eval(program)
    assert (stacker.operator_manager.generation, generation.bindings, generation.epoch) == (words, bindings, epoch)


# --- the epoch (one counter for the process, moved by both kinds of change) ---


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda s: s.eval("{x} {x} :f defun"), id="a-word-of-this-interpreter"),
        pytest.param(lambda s: s.other.eval("{x} {x} :f defun"), id="a-word-of-another-interpreter"),
        pytest.param(lambda s: s.eval("1 :fresh set"), id="a-new-variable"),
        pytest.param(lambda s: s.variables.pop("gone"), id="a-variable-removed"),
    ],
)
def test_the_epoch_advances_with_the_words_of_any_interpreter_and_with_the_bindings(stacker, change):
    stacker.other = Stacker()  # (made before the count: an interpreter's birth moves the epoch too)
    stacker.eval("1 :gone set")
    assert epoch_advanced_by(lambda: change(stacker)) == 1


def test_the_epoch_advances_by_exactly_the_sum_of_the_two_counters(stacker):
    words, bindings, epoch = stacker.operator_manager.generation, generation.bindings, generation.epoch
    stacker.eval("{x} {x} :f defun 1 :fresh set 2 :fresh set")
    assert (stacker.operator_manager.generation - words, generation.bindings - bindings) == (1, 1)
    assert generation.epoch - epoch == 2


# --- the names an existing scope holds (one counter for the process) ---


def test_every_writer_of_a_scope_counts_the_names_it_adds_or_removes_and_nothing_else():
    scope = ScopedVariables(local_vars={"a": 1})
    assert bindings_advanced_by(lambda: scope.__setitem__("a", 2)) == 0
    assert bindings_advanced_by(lambda: scope.__setitem__("b", 1)) == 1
    assert bindings_advanced_by(lambda: scope.bind("c", 1)) == 1
    assert bindings_advanced_by(lambda: scope.bind("c", 2)) == 0
    assert bindings_advanced_by(lambda: scope.set_global("d", 1)) == 1
    assert bindings_advanced_by(lambda: scope.set_global("d", 2)) == 0
    assert bindings_advanced_by(lambda: scope.update({"a": 3, "b": 3})) == 0
    assert bindings_advanced_by(lambda: scope.update([("a", 4), ("e", 4)])) == 1
    assert bindings_advanced_by(lambda: scope.__delitem__("e")) == 1
    before = generation.bindings
    with pytest.raises(KeyError):
        del scope["e"]
    assert generation.bindings == before
    assert bindings_advanced_by(lambda: scope.pop("d")) == 1
    assert bindings_advanced_by(lambda: scope.pop("d")) == 0


def test_a_transparent_scope_counts_a_new_name_once_in_the_parent():
    parent = ScopedVariables()
    loop = ScopedVariables.loop_scope(parent, {"i": 1})
    assert bindings_advanced_by(lambda: loop.__setitem__("tmp", 1)) == 1
    assert "tmp" in parent.own_bindings()


def test_a_new_variable_advances_the_bindings_and_setting_it_again_does_not(stacker):
    assert bindings_advanced_by(lambda: stacker.eval("1 :x set")) == 1
    assert bindings_advanced_by(lambda: stacker.eval("2 :x set")) == 0


def test_a_new_global_advances_the_bindings_once(stacker):
    stacker.eval("{} {1 :g global} :make defun")
    assert bindings_advanced_by(lambda: stacker.eval("make")) == 1
    assert bindings_advanced_by(lambda: stacker.eval("make")) == 0


def test_a_parameter_registered_from_the_host_advances_the_bindings(stacker):
    assert bindings_advanced_by(lambda: stacker.register_parameter("answer", 42)) == 1


def test_a_variable_first_set_in_a_loop_body_advances_the_bindings_once(stacker):
    assert bindings_advanced_by(lambda: stacker.eval("1 3 :i {i :tmp set} do")) == 1


def test_a_local_set_in_a_call_advances_the_bindings_on_every_call(stacker):
    stacker.eval("{x} {x 2 * :t set t} :f defun")
    assert bindings_advanced_by(lambda: stacker.eval("1 f drop 2 f drop")) == 2


def test_removing_a_variable_advances_the_bindings_only_when_it_was_there(stacker):
    stacker.eval("1 :x set")
    assert bindings_advanced_by(lambda: stacker.variables.pop("x")) == 1
    assert bindings_advanced_by(lambda: stacker.variables.pop("x")) == 0


@pytest.mark.parametrize(
    ("setup", "program"),
    [
        pytest.param("{x y} {x y +} :add defun", "1 2 add drop", id="a function call's arguments"),
        pytest.param("{x} {x} lambda :same set", "1 same eval drop", id="a lambda call's arguments"),
        pytest.param("{a} {{a a +}} :twice defmacro", "3 twice drop", id="a macro expansion's arguments"),
        pytest.param("0 :acc set", "1 5 :i {acc i + :acc set} do", id="a loop variable"),
        pytest.param("", "[1 2 3] 0 :acc :x {acc x +} reduce drop", id="the names reduce binds"),
    ],
)
def test_names_a_fresh_scope_is_born_with_do_not_advance_the_bindings(stacker, setup, program):
    stacker.eval(setup)
    assert bindings_advanced_by(lambda: stacker.eval(program)) == 0


def test_a_calls_arguments_keep_their_order(stacker, capsys):
    stacker.eval("{first second third} {vars} :show defun 1 2 3 show")
    listed = [line.split(" = ")[0].strip() for line in capsys.readouterr().out.splitlines()]
    assert [name for name in listed if name in ("first", "second", "third")] == ["first", "second", "third"]
