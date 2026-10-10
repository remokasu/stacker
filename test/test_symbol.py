"""Symbols are a type of their own: `$x` is always a symbol, never a value lookup.

Language-level tests for the symbol semantics (the edge-case table of the
1.16.0 specification). Unit tests for the ``Symbol`` class itself live in
``test/engine/test_data_type.py``.
"""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.engine.data_type import String, Symbol
from stacker.error import StackerSyntaxError, StackerTypeError, StackUnderflowError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestDollarIsAlwaysASymbol:
    def test_pushes_a_symbol(self):
        assert run("$x") == [Symbol("x")]

    def test_does_not_resolve_to_a_bound_value(self):
        assert run("5 x set $x") == [Symbol("x")]

    def test_bound_symbol_stays_a_symbol(self):
        assert run("5 x set $x y set y") == [Symbol("x")]

    def test_symbol_equality(self):
        assert run("$x $x ==") == [True]
        assert run("$x $y ==") == [False]

    def test_symbol_is_not_a_string(self):
        assert run('$x "x" ==') == [False]
        assert run('"x" $x ==') == [False]

    def test_symbol_is_not_a_quoted_name_block(self):
        assert run("$x {x} ==") == [False]
        assert run("{x} $x ==") == [False]

    def test_str_gives_the_name(self):
        assert run("5 x set $x str") == ["x"]

    def test_gensym_is_a_symbol(self):
        (sym,) = run("gensym")
        assert isinstance(sym, Symbol)
        assert sym.name.startswith("__g")

    def test_symbol_as_a_loop_variable_and_binding_name(self):
        assert run("0 1 3 $i {i +} do") == [6]
        assert run("[1 2 3] 0 $acc $x {acc x +} reduce") == [6]


class TestSymbolEval:
    def test_symbol_eval_runs_the_name(self):
        assert run("3 4 $+ eval") == [7]

    def test_symbol_eval_equals_quoted_name_eval(self):
        assert run("3 4 $+ eval") == run("3 4 {+} eval")

    def test_symbol_eval_of_a_variable_pushes_its_value(self):
        assert run("5 x set $x eval") == [5]

    def test_symbol_eval_of_a_block_variable_pushes_the_block(self):
        (block,) = run("{1 2 +} b set $b eval")
        assert isinstance(block, StackerCore)

    def test_bare_name_eval_of_a_block_variable_runs_it(self):
        assert run("{1 2 +} b set b eval") == [3]

    def test_string_eval_is_source(self):
        (block,) = run('{1 2 +} b set "b" eval')
        assert isinstance(block, StackerCore)

    def test_symbol_eval_of_a_macro_expands_it(self):
        assert run("{} {{2}} m defmacro $m eval") == [2]


class TestLambdaIsAValue:
    def test_bare_reference_pushes_the_lambda(self):
        result = run("{a} {a 2 *} lambda f set 5 f")
        assert result[0] == 5
        assert type(result[1]).__name__ == "StackerLambda"

    def test_eval_calls_it(self):
        assert run("{a} {a 2 *} lambda f set 5 f eval") == [10]

    def test_symbol_eval_pushes_it(self):
        result = run("{a} {a 2 *} lambda f set 5 $f eval")
        assert result[0] == 5
        assert type(result[1]).__name__ == "StackerLambda"
        assert run("{a} {a 2 *} lambda f set 5 $f eval eval") == [10]

    def test_void_result_is_not_pushed(self):
        assert run("{} {} lambda z set z eval") == []

    def test_missing_arguments_raise_stack_underflow(self):
        with pytest.raises(StackUnderflowError):
            run("{a} {a 2 *} lambda f set f eval")

    def test_block_argument_binds_raw(self):
        (block,) = run("{x} {x} lambda idf set {2 *} idf eval")
        assert isinstance(block, StackerCore)

    def test_lambda_passed_to_a_function_as_a_value(self):
        assert run(
            "{xs lf} {xs null? {[]} {xs car lf eval xs cdr lf my-map cons} ifelse} $my-map defun",
            "[1 2 3] {x} {x 2 *} lambda my-map",
        ) == [[2, 4, 6]]

    def test_defun_functions_are_still_called_by_name(self):
        assert run("{x y} {x y *} multiply defun 3 4 multiply") == [12]


class TestConditions:
    def test_symbol_is_true(self):
        assert run("0 x = $x {1} if") == [1]

    def test_bare_name_tests_the_value(self):
        assert run("0 x = x {1} if") == []

    def test_string_is_not_looked_up(self):
        assert run('0 flag = "flag" {1} if') == [1]
        assert run('"" {1} if') == []

    def test_cond_agrees_with_if(self):
        assert run("0 x = $x {1} 1 cond") == [1]


class TestArgumentLists:
    @pytest.mark.parametrize(
        "program",
        [
            "{$a} {a} lambda",
            '{"a"} {a} f defun',
            "$a {a 2 *} f defun",
            "[a b] {a b +} f defun",
            "{a a} {a} f defun",
            "{5} {5} f defun",
            "{{a}} {a} f defun",
        ],
    )
    def test_non_bare_names_are_rejected(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_empty_argument_list(self):
        assert run("{} {42} f defun f") == [42]


class TestValuesSplicedIntoBlocks:
    def test_sub_of_a_symbol_is_a_quoted_name(self):
        (block,) = run("$x sub")
        assert type(block.tokens[0]) is str and block.tokens[0] == "x"
        assert run("5 x set $x sub eval") == [5]

    def test_sub_of_a_string_is_a_string_literal(self):
        (block,) = run('"x" sub')
        assert isinstance(block.tokens[0], String)
        assert run('5 x set "x" sub eval') == ["x"]

    def test_sub_of_a_computed_string_is_a_string_literal(self):
        assert run('"a" "b" + sub eval') == ["ab"]

    def test_bound_string_keeps_its_type(self):
        (value,) = run('"x" y set y')
        assert isinstance(value, String)


class TestMacroArguments:
    def test_symbol_argument_is_spliced_as_a_bare_name(self):
        assert run("3 foo =", "{v} {{v}} m defmacro", "$foo m") == [3]

    def test_symbol_argument_used_directly_is_a_symbol(self):
        assert run("{v} {v} m defmacro", "$foo m") == [Symbol("foo")]

    def test_string_bound_in_the_body_is_spliced_as_a_literal(self):
        (block,) = run('{} { "s" t = {t} } m defmacro', "$m macroexpand")
        assert isinstance(block.tokens[0], String)

    def test_gensym_name_is_spliced_as_a_bare_name(self):
        assert run(
            "{x} { gensym t = { x eval t set t t + } } {double!} defmacro",
            "{3 4 +} double!",
        ) == [14]


class TestSymbolInComputation:
    def test_arithmetic_on_a_symbol_is_a_stacker_type_error(self):
        with pytest.raises(StackerTypeError) as info:
            run("$x 1 +")
        assert "`+` cannot use the symbol `x` as a value" in str(info.value)
        assert "Write `x`" in str(info.value)

    def test_binding_does_not_help(self):
        with pytest.raises(StackerTypeError):
            run("5 x set $x 1 +")

    def test_inside_a_block(self):
        with pytest.raises(StackerTypeError):
            run("{$x 1 +} eval")

    @pytest.mark.parametrize(
        "program",
        ["2 n set 0 $n i {i} do", "{1} $n times", "$x {} map", "$xs x {x} dolist", "$n cond"],
    )
    def test_symbol_where_a_value_is_needed(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_plugin_argument(self):
        stacker = Stacker()
        stacker.register_plugin("twice", lambda x: x * 2)
        with pytest.raises(StackerTypeError):
            stacker.process_expression("$x twice")

    def test_other_type_errors_are_unchanged(self):
        with pytest.raises(TypeError) as info:
            run('"a" 1 +')
        assert not isinstance(info.value, StackerTypeError)

    def test_stack_words_accept_symbols(self):
        assert run("$x dup") == [Symbol("x"), Symbol("x")]

    def test_iferror_catches_it(self):
        assert run("{$q 1 +} {2} iferror") == [2]


class TestDisplay:
    def test_symbols_are_bare_and_strings_quoted(self):
        from stacker.util.disp import disp_default

        assert disp_default([Symbol("x"), "ab", String("ab")]) == "[x 'ab' 'ab']"

    def test_computed_strings_are_quoted(self):
        from stacker.util.disp import disp_default

        assert disp_default(run('"a" "b" +')) == "['ab']"
        assert disp_default(run('"hello" s = s')) == "['hello']"

    def test_block_tokens_are_shown_as_written(self):
        (block,) = run("{foo}")
        assert str(block) == "{foo}"
        (block,) = run("5 foo set {foo}")
        assert str(block) == "{foo}"
        (block,) = run("{$x}")
        assert str(block) == "{$x}"
        (block,) = run('{"a b" echo}')
        assert str(block) == '{"a b" echo}'

    def test_lambda_display(self):
        (fn,) = run("{x y} {x y *} lambda")
        assert str(fn) == "λxλy.{x y *}"

