"""Shadowing rule: only kernel words are protected.

A bare name written right before a binding form is a name, unless it is a
kernel word (a Python-side operator); then it executes as that operator and
shadowing requires an explicit `$name` / `{name}`.
"""

import pytest

from stacker.error import StackerError, StackerSyntaxError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


def test_undefined_name_is_a_symbol():
    assert run("5 x set x") == [5]


def test_user_variable_can_be_rebound_by_bare_name():
    assert run("5 x set 6 x set x") == [6]


def test_user_function_can_be_redefined_by_bare_name():
    assert run("{a} {a 1 +} f defun", "{a} {a 10 +} f defun", "1 f") == [11]


def test_user_macro_can_be_redefined_by_bare_name():
    assert run("{} {{1}} m defmacro", "{} {{2}} m defmacro", "m") == [2]


def test_bare_kernel_word_before_set_executes_as_operator():
    # `dup` runs, then `set` sees a number where a name is expected.
    with pytest.raises(StackerSyntaxError):
        run("3 dup set")


def test_bare_kernel_word_before_defun_executes_as_operator():
    stacker = Stacker()
    with pytest.raises(StackerError):
        stacker.eval("{a} {a} max defun")
    assert "max" not in stacker.sfunctions


def test_kernel_word_can_be_shadowed_with_explicit_quote():
    assert run("3 $dup set dup") == [3]
    assert run("4 {dup} set dup") == [4]


def test_macro_shadowing_a_kernel_word_wins_at_lookahead_position_too():
    # `dup` is a macro now; at the lookahead position it still expands.
    assert run("{} {{$k}} $dup defmacro", "3 dup set k") == [3]


def test_do_loop_variable_named_like_a_constant_is_unaffected():
    assert run("0 1 3 e {e +} do") == [6]


def test_dolist_loop_variable_named_like_a_kernel_word_is_unaffected():
    assert run("0 [1 2 3] max {max +} dolist") == [6]


def test_symbolic_operator_shadowing_still_requires_quote():
    # Frozen semantics: `99 $+ set +` pushes 99.
    assert run("99 $+ set +") == [99]


def test_bare_kernel_word_before_assign_executes_as_operator():
    with pytest.raises(StackerSyntaxError):
        run("3 dup =")


def test_bare_kernel_word_before_global_executes_as_operator():
    with pytest.raises(StackerSyntaxError):
        run("3 dup global")


def test_kernel_word_can_be_assigned_and_made_global_with_explicit_quote():
    assert run("3 $dup = dup") == [3]
    assert run("4 {dup} global dup") == [4]


def test_do_loop_variable_named_like_a_kernel_word_is_readable_in_body():
    assert run("0 1 3 dup {dup +} do") == [6]


def test_overriding_a_kernel_word_with_register_operator_keeps_it_protected():
    stacker = Stacker()
    stacker.register_operator("abs", lambda a: 42, 1, True, "replaced abs")
    # The lookahead check still treats `abs` as a kernel word: it executes
    # (now returning 42) instead of being taken as the name to bind.
    with pytest.raises(StackerSyntaxError, match="42"):
        stacker.eval("3 abs set", stack=stacker.stack)
    assert "abs" not in stacker.variables


def test_plugin_registered_after_a_function_body_was_classified_is_protected():
    stacker = Stacker()
    stacker.eval("{} {7 foo set foo} f defun", stack=stacker.stack)
    assert list(stacker.eval("f", stack=stacker.stack)) == [7]
    stacker.register_plugin("foo", lambda a: a * 2, True, False, "double")
    # Same cached function body: `foo` is now a kernel word and runs as an
    # operator, so `set` receives 14 instead of a name.
    with pytest.raises(StackerSyntaxError, match="14"):
        stacker.eval("f", stack=stacker.stack)


class TestLiteralsAreNeverNames:
    """`5 3 set 3` used to bind a variable named `3`, and `3 {5} set` one
    keyed by the integer 5."""

    @pytest.mark.parametrize(
        "expression",
        ["5 3 set", "3 {5} set", "{a} {a} 7 defun", "5 True set", "5 None set"],
        ids=["number-set", "quoted-number", "number-defun", "True", "None"],
    )
    def test_literal_in_a_name_position_is_a_syntax_error(self, expression):
        with pytest.raises(StackerSyntaxError):
            run(expression)

    @pytest.mark.parametrize(("name", "value"), [("{x}", 5), ("{$x}", 5)], ids=["bare", "dollar"])
    def test_one_token_blocks_holding_a_name_are_names(self, name, value):
        assert run(f"{value} {name} set x") == [value]

    def test_one_token_block_holding_a_string_is_not_a_name(self):
        # A string literal is data wherever it is written (1.16.0).
        with pytest.raises(StackerSyntaxError):
            run('5 {"x"} set')

    def test_multi_token_block_is_not_a_name(self):
        with pytest.raises(StackerSyntaxError):
            run("5 {x y} set")


class TestEveryNameTakingWordReadsBareNames:
    """Bare names right before `macroexpand`, and the two names before the
    block of `reduce` / `fold`, used to be looked up as variables."""

    def test_bare_macro_name_before_macroexpand(self):
        (block,) = run("{} {{1}} m defmacro", "m macroexpand")
        assert list(block.tokens) == [1]

    @pytest.mark.parametrize("word", ["reduce", "fold"])
    def test_both_names_before_the_block_are_names_even_when_variables_exist(self, word):
        assert run("9 x set 9 acc set", f"[1 2 3] 0 acc x {{acc x +}} {word}") == [6]

    @pytest.mark.parametrize("word", ["reduce", "fold"])
    def test_dollar_names_still_work(self, word):
        assert run(f"[1 2 3] 0 $acc $x {{acc x +}} {word}") == [6]

    @pytest.mark.parametrize("word", ["set", "=", "global", "defun", "defmacro", "macroexpand", "do"])
    def test_string_literal_reading_like_a_binding_word_is_not_a_binding_word(self, word):
        # `{x "set"}`: the literal "set" must not turn the `x` before it into a name.
        assert run("5 x set", f'{{x "{word}"}} eval') == [5, word]
