"""Rebinding a name, including a built-in word's.

A built-in word is bound like any other name, through `:name` or `{name}`:
nothing is protected, because a bare name is always a reference and so
never names anything by itself. Macros take precedence over variables and
operators when a bare name is read.
"""

import pytest

from stacker.error import StackerSyntaxError, UndefinedSymbolError
from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


def test_a_user_variable_is_rebound_through_its_symbol():
    assert run("5 :x set 6 :x set x") == [6]


def test_a_user_function_is_redefined_through_its_symbol():
    assert run("{a} {a 1 +} :f defun", "{a} {a 10 +} :f defun", "1 f") == [11]


def test_a_user_macro_is_redefined_through_its_symbol():
    assert run("{} {{1}} :m defmacro", "{} {{2}} :m defmacro", "m") == [2]


def test_a_bare_name_that_is_bound_pushes_its_value_even_before_set():
    # `x` holds 5: it pushes 5, and `set` receives a number instead of a name
    with pytest.raises(StackerSyntaxError, match="got 5"):
        run("5 :x set 6 x set")


@pytest.mark.parametrize("word", ["set", "=", "global"])
def test_a_built_in_word_before_a_binding_word_runs(word):
    # `dup` runs on 3, then the binding word sees a number where a name is expected
    with pytest.raises(StackerSyntaxError, match="got 3"):
        run(f"3 dup {word}")


def test_a_built_in_word_before_defun_runs():
    # `max` runs on the two blocks, evaluating them, so `a` is looked up
    stacker = Stacker()
    with pytest.raises(UndefinedSymbolError):
        stacker.eval("{a} {a} max defun")
    assert "max" not in stacker.sfunctions


@pytest.mark.parametrize("word", ["set", "=", "global"])
def test_a_built_in_word_is_shadowed_through_its_symbol(word):
    assert run(f"3 :dup {word} dup") == [3]
    assert run(f"4 {{dup}} {word} dup") == [4]


def test_a_symbolic_operator_is_shadowed_through_its_symbol():
    # Frozen semantics: `99 :+ set +` pushes 99.
    assert run("99 :+ set +") == [99]


def test_a_macro_named_like_a_built_in_word_wins_when_the_bare_name_is_read():
    assert run("{} {{:k}} :dup defmacro", "3 dup set k") == [3]


def test_a_loop_variable_may_be_named_like_a_constant_or_a_built_in_word():
    assert run("0 1 3 :e {e +} do") == [6]
    assert run("0 [1 2 3] :max {max +} dolist") == [6]
    assert run("0 1 3 :dup {dup +} do") == [6]


def test_an_operator_registered_from_python_is_bound_like_any_other_name():
    stacker = Stacker()
    stacker.register_operator("abs", lambda a: 42, 1, True, "replaced abs")
    # The bare `abs` runs (returning 42) as every bare name is a reference
    with pytest.raises(StackerSyntaxError, match="42"):
        stacker.eval("3 abs set", stack=stacker.stack)
    assert "abs" not in stacker.variables
    assert list(stacker.eval("3 :abs set abs", stack=stacker.stack)) == [3]


def test_a_plugin_registered_later_does_not_change_a_cached_function_body():
    # The body names `foo` through its symbol, so what `foo` means at run time
    # cannot turn the binding into a call
    stacker = Stacker()
    stacker.eval("{} {7 :foo set foo} :f defun", stack=stacker.stack)
    assert list(stacker.eval("f", stack=stacker.stack)) == [7]
    stacker.stack.clear()
    stacker.register_plugin("foo", lambda a: a * 2, True, False, "double")
    assert list(stacker.eval("f", stack=stacker.stack)) == [7]


class TestLiteralsAreNeverNames:
    """`5 3 set 3` used to bind a variable named `3`, and `3 {5} set` one
    keyed by the integer 5."""

    @pytest.mark.parametrize(
        "expression",
        ["5 3 set", "3 {5} set", "{a} {a} 7 defun", "5 True set", "5 None set"],
        ids=["number-set", "quoted-number", "number-defun", "True", "None"],
    )
    def test_a_literal_where_a_name_is_expected_is_a_syntax_error(self, expression):
        with pytest.raises(StackerSyntaxError):
            run(expression)

    @pytest.mark.parametrize(("name", "value"), [("{x}", 5), ("{:x}", 5)], ids=["bare", "symbol"])
    def test_one_token_blocks_holding_a_name_are_names(self, name, value):
        assert run(f"{value} {name} set x") == [value]

    def test_one_token_block_holding_a_string_is_not_a_name(self):
        # A string literal is data wherever it is written (1.16.0).
        with pytest.raises(StackerSyntaxError):
            run('5 {"x"} set')

    def test_multi_token_block_is_not_a_name(self):
        with pytest.raises(StackerSyntaxError):
            run("5 {x y} set")


class TestEveryNameTakingWordReadsSymbols:
    """`macroexpand` and the two names before the block of `reduce` / `fold`
    take their names the same way as `set`."""

    def test_a_bare_macro_name_before_macroexpand_is_expanded(self):
        (block,) = run("{} {{1}} :m defmacro", ":m macroexpand")
        assert list(block.tokens) == [1]
        # The bare `m` is the macro call itself: it expands to 1, which is
        # then handed to `macroexpand`
        with pytest.raises(StackerSyntaxError, match="`macroexpand` expects a name, got 1"):
            run("{} {{1}} :m defmacro", "m macroexpand")

    @pytest.mark.parametrize("word", ["reduce", "fold"])
    def test_both_names_before_the_block_are_symbols_even_when_variables_exist(self, word):
        assert run("9 :x set 9 :acc set", f"[1 2 3] 0 :acc :x {{acc x +}} {word}") == [6]

    @pytest.mark.parametrize("word", ["reduce", "fold"])
    def test_a_bare_name_before_the_block_is_its_value(self, word):
        # `acc` holds 9, so the word is handed a number where it expects a name
        with pytest.raises(StackerSyntaxError, match="got 9"):
            run("9 :acc set", f"[1 2 3] 0 acc :x {{acc x +}} {word}")
