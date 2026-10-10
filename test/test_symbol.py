"""Symbols are a type of their own: `$x` is always a symbol, never a value lookup.

Language-level tests for the symbol semantics (the edge-case table of the
1.16.0 specification). Unit tests for the ``Symbol`` class itself live in
``test/engine/test_data_type.py``.
"""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.engine.data_type import String, Symbol
from stacker.error import (
    StackerSyntaxError,
    StackerTypeError,
    StackUnderflowError,
    UndefinedSymbolError,
)


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
        # `==` evaluates a block argument, so `x` must be bound for the comparison to happen.
        assert run("5 x set $x {x} ==") == [False]
        (block,) = run("{x}")
        assert (Symbol("x") == block) is False
        assert (block == Symbol("x")) is False

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
            "[1 2] {a b +} f defun",
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


class TestDollarSyntax:
    @pytest.mark.parametrize("token", ["$1", "${x}", '$"x"', "$[1 2]", "$", "$$x", "$x$", "$true"])
    def test_dollar_must_be_followed_by_a_name(self, token):
        with pytest.raises(StackerSyntaxError) as info:
            run(token)
        assert "is not a symbol" in str(info.value)

    def test_operator_and_dotted_names_are_symbols(self):
        assert run("$+ $x.y") == [Symbol("+"), Symbol("x.y")]

    def test_error_is_raised_at_the_execution_position(self, capsys):
        with pytest.raises(StackerSyntaxError):
            run("1 echo $1")
        assert capsys.readouterr().out.strip() == "1"

    def test_inside_a_block_the_error_waits_for_evaluation(self):
        (block,) = run("{$1}")
        assert isinstance(block, StackerCore)
        with pytest.raises(StackerSyntaxError):
            run("{$1} eval")


class TestKeywordLiterals:
    def test_true_false_null_are_values(self):
        assert run("true false null") == [True, False, None]
        assert run("[true None null]") == [[True, None, None]]
        assert run("{true false} all") == [False]

    @pytest.mark.parametrize("program", ["5 true set", "5 false set", "5 null set", "5 True set", "5 $true set"])
    def test_cannot_be_bound(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_other_constants_are_still_variables(self):
        assert run("5 pi set pi") == [5]
        assert run("1 3 e {e} do") == [1, 2, 3]

    def test_not_listed_by_vars(self, capsys):
        run("vars")
        out = capsys.readouterr().out
        assert "true =" not in out and "pi =" in out


class TestListLiterals:
    def test_symbols(self):
        assert run("[$a $b]") == [[Symbol("a"), Symbol("b")]]
        assert run("[$+]") == [[Symbol("+")]]

    @pytest.mark.parametrize("program", ["[$]", "[$1]"])
    def test_invalid_symbols(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_bare_names_are_references(self):
        assert run("5 x set [x]") == [[5]]
        with pytest.raises(UndefinedSymbolError):
            run("[x]")

    def test_nested_names_are_references_too(self):
        assert run("5 x set [[x 1] [2 3]]") == [[[5, 1], [2, 3]]]
        with pytest.raises(UndefinedSymbolError):
            run("[[x]]")

    def test_block_inside_a_list_literal_is_rejected(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("[{x}]")
        assert "cannot be written inside a list literal" in str(info.value)

    def test_error_is_raised_at_the_execution_position(self, capsys):
        with pytest.raises(StackerSyntaxError):
            run("1 echo [{x}]")
        assert capsys.readouterr().out.strip() == "1"

    def test_lists_are_fresh_on_every_evaluation(self):
        assert run("[] lst set 1 3 $i {lst [i i] + lst set} do lst") == [[1, 1, 2, 2, 3, 3]]


class TestStringsAreNotNames:
    @pytest.mark.parametrize(
        "program",
        ['5 "x" set', '5 {"x"} set', '"m" macroexpand', '[1 2] 0 "acc" "x" {acc x +} reduce', '{a} {a} "f" defun'],
    )
    def test_rejected_at_name_positions(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_message_shows_the_three_ways_to_write_a_name(self):
        with pytest.raises(StackerSyntaxError) as info:
            run('5 "x" set')
        assert "`set` expects a name, got the string 'x'" in str(info.value)
        assert "$x or {x}" in str(info.value) and "`symbol`" in str(info.value)

    def test_a_string_holding_a_dollar_name_is_still_a_string(self):
        with pytest.raises(StackerSyntaxError):
            run('5 "$x" set')

    def test_non_names_are_rejected_with_the_word(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("5 {x y} set")
        assert "`set` expects a name" in str(info.value)


class TestSymbolWord:
    @pytest.mark.parametrize("program", ['"x" symbol', "{x} symbol", "{$x} symbol", "$x symbol"])
    def test_makes_the_same_symbol(self, program):
        assert run(program) == [Symbol("x")]

    @pytest.mark.parametrize(
        "program",
        ['"1" symbol', '"a b" symbol', '"" symbol', '"$x" symbol', '"{x}" symbol', '"true" symbol',
         '{"x"} symbol', "{x y} symbol", "5 symbol", "[1] symbol"],
    )
    def test_rejects_what_cannot_be_a_name(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    def test_makes_a_name_usable_at_name_positions(self):
        assert run('5 "x" symbol set x') == [5]
        assert run('[1 4 9] "sqrt" symbol map') == [[1.0, 2.0, 3.0]]

    def test_round_trip_with_str(self):
        assert run('"x" symbol str') == ["x"]


class TestSymbolPredicateAndType:
    def test_symbol_predicate(self):
        assert run("$x symbol?") == [True]
        assert run("gensym symbol?") == [True]
        assert run('"x" symbol?') == [False]
        assert run("5 symbol?") == [False]
        assert run("[$x] symbol?") == [False]

    def test_str_predicate_is_false_for_symbols(self):
        assert run("$x str?") == [False]
        assert run('"x" str?') == [True]

    def test_type_of_a_symbol(self):
        assert run("$x type") == [Symbol]


class TestStringArguments:
    def test_disable_plugin_takes_a_string(self, capsys):
        run('"nonexistent" disable_plugin')
        assert "not registered" in capsys.readouterr().out
        with pytest.raises(StackerTypeError):
            run("$nonexistent disable_plugin")

    def test_include_takes_a_string(self):
        with pytest.raises(StackerTypeError):
            run("$lib include")



def run_without_prelude(*lines: str) -> list[object]:
    stacker = Stacker(prelude=False)
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestEdgeCasesNotCoveredElsewhere:
    def test_name_position_reference_to_an_undefined_name(self):
        # `x` is a reference here (the value position of `swap`'s operand), not a name.
        with pytest.raises(UndefinedSymbolError):
            run("x 5 swap set")

    def test_block_name_is_evaluated_back_into_a_symbol_then_run(self):
        assert run("3 4 {+} 0 nth swap drop eval") == [7]

    def test_sub_of_a_string_evaluates_to_the_string_not_the_operator(self):
        assert run('3 4 "+" sub eval') == [3, 4, "+"]

    def test_string_eval_runs_the_source(self):
        assert run('3 4 "+" eval') == [7]

    def test_symbol_equality_with_a_bound_variable_of_the_same_name(self):
        assert run("5 x set $x $x ==") == [True]

    def test_quoted_name_passes_through_a_macro_unchanged(self):
        (block,) = run("{v} {{v}} m defmacro", "{foo} m")
        assert str(block) == "{foo}"

    def test_macro_given_an_unbound_symbol_fails_where_the_expansion_references_it(self):
        with pytest.raises(UndefinedSymbolError):
            run("{v} {{v}} m defmacro", "$foo m")

    def test_macro_given_a_bound_symbol_does_not_turn_it_into_the_value_early(self):
        assert run("3 foo =", "{v} {v} m defmacro", "$foo m") == [Symbol("foo")]

    def test_literals_in_a_list_literal(self):
        assert run("[true None]") == [[True, None]]

    @pytest.mark.parametrize("token", ["$null", "$false", "$None", "$True"])
    def test_keyword_literals_cannot_follow_a_dollar(self, token):
        with pytest.raises(StackerSyntaxError):
            run(token)

    def test_keyword_literal_is_not_an_argument_name(self):
        with pytest.raises(StackerSyntaxError):
            run("{true} {1} lambda")

    def test_sorting_symbols_is_by_name(self):
        assert run("[$b $a] sorted") == [[Symbol("a"), Symbol("b")]]

    def test_symbols_in_a_list_compare_by_name(self):
        assert run("[$a] [$a] ==") == [True]

    def test_dollar_name_with_punctuation(self):
        assert run("$a-b $a? $1a $>=") == [Symbol("a-b"), Symbol("a?"), Symbol("1a"), Symbol(">=")]

    def test_string_holding_a_dollar_name_listed_char_by_char(self):
        assert run('"$x" y set y list') == [["$", "x"]]

    def test_symbol_bound_through_a_name_keeps_its_type(self):
        assert run("$x y set y type") == [Symbol]

    def test_listn_of_symbols(self):
        assert run("$x 1 listn") == [[Symbol("x")]]
        assert run("$a $b 2 listn") == [[Symbol("a"), Symbol("b")]]

    def test_nth_symbol_is_not_a_value_in_arithmetic(self):
        with pytest.raises(StackerTypeError):
            run("5 x set {x} 0 nth 1 +")

    def test_symbols_survive_stack_words(self):
        assert run("$x $y swap") == [Symbol("y"), Symbol("x")]
        assert run("$x 1 over") == [Symbol("x"), 1, Symbol("x")]

    def test_symbol_is_truthy_for_logic_words(self):
        assert run("$x not") == [False]
        assert run("$x bool") == [True]

    def test_symbol_is_not_a_list_for_len(self):
        with pytest.raises(StackerTypeError):
            run("$x len")

    def test_len_of_the_name_as_text(self):
        assert run("$x str len") == [1]


class TestSymbolRoundTripsThroughBlocks:
    def test_read_from_string_of_a_symbol_is_a_quoted_name(self):
        (block,) = run("$x read-from-string")
        assert isinstance(block, StackerCore)
        assert str(block) == "{x}"

    def test_read_from_string_then_nth_gives_the_symbol_back(self):
        assert run("$x read-from-string 0 nth")[-1] == Symbol("x")

    def test_read_from_string_of_text_with_a_dollar_gives_a_symbol_token(self):
        assert run('"$x" read-from-string 0 nth')[-1] == Symbol("x")

    def test_read_from_string_does_not_look_up_the_name(self):
        (block,) = run("5 x set $x read-from-string")
        assert str(block) == "{x}"

    def test_read_from_string_then_eval_references_the_name(self):
        assert run("5 x set $x read-from-string eval") == [5]
        with pytest.raises(UndefinedSymbolError):
            run("$x read-from-string eval")

    def test_expand_keeps_a_quoted_name_a_quoted_name(self):
        (block,) = run("{x} expand")
        assert str(block) == "{x}"

    def test_expand_splits_a_block_into_one_token_blocks(self):
        blocks = run("{x y} expand")
        assert [str(b) for b in blocks] == ["{x}", "{y}"]

    def test_expand_of_a_sub_is_the_sub(self):
        (block,) = run("$x sub expand")
        assert str(block) == "{x}"

    def test_expand_of_a_list_gives_the_elements(self):
        assert run("[1 $a] expand") == [1, Symbol("a")]

    def test_expand_keeps_string_literals_as_string_tokens(self):
        first, second = run('{"a" b} expand')
        assert str(first) == '{"a"}'
        assert str(second) == "{b}"

    def test_expand_then_nth_gives_a_symbol(self):
        assert run("{x y} expand drop 0 nth")[-1] == Symbol("x")

    def test_subn_of_mixed_values_types_each_token(self):
        (block,) = run('$a "b" 5 3 subn')
        assert type(block.tokens[0]) is str and block.tokens[0] == "a"
        assert isinstance(block.tokens[1], String)
        assert block.tokens[2] == 5

    def test_subn_evaluates_back_to_the_values(self):
        assert run("5 a set", '$a "b" 2 subn eval') == [5, "b"]

    def test_sub_of_other_values_is_a_value_token(self):
        assert str(run("5 sub")[0]) == "{5}"
        assert run("5 sub eval") == [5]

    def test_concat_block_joins_names_and_literals(self):
        (block,) = run('{x} {"y" 1} concat-block')
        assert str(block) == '{x "y" 1}'

    def test_concat_block_of_subs(self):
        (block,) = run("$x sub $y sub concat-block")
        assert str(block) == "{x y}"

    def test_concat_block_of_sub_string_and_sub_symbol_keeps_types(self):
        (block,) = run('"a" sub $b sub concat-block')
        assert isinstance(block.tokens[0], String)
        assert type(block.tokens[1]) is str

    @pytest.mark.parametrize("program", ["{x} $y concat-block", "{x} 5 concat-block"])
    def test_concat_block_needs_two_blocks(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)


class TestSymbolsInControlFlow:
    def test_cond_with_a_symbol_condition_is_true(self):
        assert run("$x {1} 1 cond") == [1]

    @pytest.mark.parametrize("condition, expected", [('"s"', [1]), ('""', []), ("0", []), ("1", [1])])
    def test_cond_with_a_non_block_condition_uses_python_truth(self, condition, expected):
        assert run(f"{condition} {{1}} 1 cond") == expected

    def test_cond_with_a_string_is_not_looked_up(self):
        assert run('0 flag = "flag" {1} 1 cond') == [1]

    def test_second_clause_of_cond_sees_a_symbol_as_true(self):
        assert run("0 {1} $x {2} 2 cond") == [2]

    def test_ifelse_with_a_symbol_takes_the_true_branch(self):
        assert run("0 x = $x {1} {2} ifelse") == [1]

    def test_ifelse_with_an_empty_string_takes_the_false_branch(self):
        assert run('"" {1} {2} ifelse') == [2]

    def test_times_with_a_symbol_count_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run("{1} $n times")

    def test_times_with_a_bound_name_uses_the_value(self):
        assert run("3 n set {1} n times") == [1, 1, 1]

    def test_dolist_with_a_symbol_list_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run("$xs x {x} dolist")

    def test_dolist_with_a_symbol_variable_and_symbol_elements(self):
        assert run("[$a $b] $x {x} dolist") == [Symbol("a"), Symbol("b")]

    def test_dolist_with_a_quoted_variable(self):
        assert run("[1 2] {x} {x 10 *} dolist") == [10, 20]

    def test_dolist_over_a_string_yields_characters(self):
        assert run('"ab" x {x} dolist') == ["a", "b"]

    @pytest.mark.parametrize(
        "program",
        ['1 3 "i" {i} do', '1 3 {i j} {i} do', '[1] "x" {x} dolist', '[1 2] 0 "acc" x {acc} reduce'],
    )
    def test_loop_variable_must_be_a_name(self, program):
        with pytest.raises(StackerSyntaxError):
            run(program)

    @pytest.mark.parametrize("variable", ["i", "$i", "{i}"])
    def test_do_loop_variable_spellings_are_equivalent(self, variable):
        assert run(f"1 3 {variable} {{i 2 *}} do") == [2, 4, 6]

    def test_do_loop_variable_does_not_leak(self):
        with pytest.raises(UndefinedSymbolError):
            run("1 3 $i {i} do i")

    def test_do_loop_variable_shadows_an_outer_binding_only_inside(self):
        assert run("5 i set 1 2 $i {i} do i") == [1, 2, 5]

    def test_loop_variable_symbol_value_is_the_number_not_the_name(self):
        assert run("1 3 $i {i} do") == [1, 2, 3]

    def test_do_with_a_symbol_bound_to_a_number_is_still_a_symbol(self):
        with pytest.raises(StackerTypeError):
            run("2 n set 1 $n i {i} do")

    def test_reduce_with_all_name_spellings(self):
        for names in ("acc x", "$acc $x", "{acc} {x}"):
            assert run(f"[1 2 3] 0 {names} {{acc x +}} reduce") == [6]

    def test_fold_with_symbol_names(self):
        assert run("[1 2 3] 0 $acc $x {acc x +} fold") == [6]

    def test_fold_with_a_function_defined_by_defun(self):
        assert run("{x} {x 1 +} f defun {1 2} 0 acc x {acc x + f} fold") == [5]

    def test_fold_over_a_list_of_symbols_yields_the_last_symbol(self):
        assert run("[$a $b] 0 acc x {x} fold") == [Symbol("b")]

    def test_reduce_adding_symbols_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run("[$a $b] 0 acc x {acc x +} reduce")

    def test_reduce_over_a_block_binds_symbols(self):
        assert run("{a b} 0 acc x {x} reduce") == [Symbol("b")]

    def test_reduce_over_a_block_of_strings_concatenates(self):
        assert run('{"a" "b"} "" acc x {acc x +} reduce') == ["ab"]

    def test_macroexpand_accepts_the_three_spellings(self):
        for spelling in ("$dbl", "{dbl}", "dbl"):
            (block,) = run("{a} {{a a +}} dbl defmacro", f"{{3}} {spelling} macroexpand")
            assert str(block) == "{{3} {3} +}"

    def test_macroexpand_of_an_unknown_name(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("$nope macroexpand")
        assert "not a macro" in str(info.value)

    def test_macroexpand_of_a_non_name(self):
        with pytest.raises(StackerSyntaxError):
            run("5 macroexpand")

    def test_alias_with_a_symbol_name(self):
        assert run("{2 *} $double alias", "4 double") == [8]

    def test_alias_with_a_string_name_is_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run('{2 *} "double" alias')

    def test_alias_with_a_number_is_rejected(self):
        with pytest.raises(StackerSyntaxError):
            run("{2 *} 5 alias")

    def test_alias_is_a_word_so_its_symbol_names_it(self):
        assert run("{2 *} $double alias", "{double} 0 nth")[-1] == Symbol("double")
        assert run("{2 *} $double alias", "4 $double eval") == [8]


class TestGensymHygiene:
    def test_consecutive_gensyms_are_distinct_symbols(self):
        first, second = run("gensym gensym")
        assert isinstance(first, Symbol) and isinstance(second, Symbol)
        assert first != second

    def test_gensym_never_equals_the_text_of_its_name(self):
        (sym,) = run("gensym")
        assert sym != sym.name

    def test_a_variable_with_the_next_generated_name_is_not_clobbered_or_read(self):
        # Another variable already holds the name the next gensym will produce.
        # The symbol must reach `set` as a name, not as that variable's value.
        (probe,) = run("gensym")
        clash = f"__g{int(probe.name[3:]) + 1}"
        stacker = Stacker()
        stacker.process_expression(f"99 {clash} set")
        stacker.process_expression("{x} { gensym t = { x eval t set t t + } } {double!} defmacro")
        stacker.process_expression("{3 4 +} double!")
        assert list(stacker.stack) == [14]

    def test_symbol_made_by_gensym_is_a_symbol_after_binding(self):
        assert run("gensym t = t symbol?") == [True]

    def test_gensym_symbol_works_as_a_variable_name(self):
        assert run("gensym n = 7 n set 3") == [3]


class TestPythonApi:
    def test_eval_returns_a_symbol_for_dollar_names(self):
        (value,) = Stacker().eval("$x")
        assert isinstance(value, Symbol)
        assert not isinstance(value, str)
        assert value.name == "x"

    def test_eval_does_not_resolve_a_bound_name(self):
        stacker = Stacker()
        stacker.eval("5 x set")
        assert list(stacker.eval("$x")) == [Symbol("x")]

    def test_eval_returns_strings_as_str(self):
        (value,) = Stacker().eval('"a" "b" +')
        assert isinstance(value, str) and not isinstance(value, Symbol)
        assert value == "ab"

    def test_eval_distinguishes_a_symbol_from_a_string_of_the_same_text(self):
        symbol, text = Stacker().eval('$x "x"')
        assert symbol != text
        assert isinstance(symbol, Symbol) and not isinstance(text, Symbol)

    def test_eval_of_an_undefined_name_raises_the_documented_error(self):
        with pytest.raises(UndefinedSymbolError) as info:
            Stacker().eval("foo")
        assert "`foo` is not defined" in str(info.value)

    def test_pop_and_eval_does_not_turn_a_symbol_into_a_value(self):
        stacker = Stacker()
        stacker.eval("5 x set")
        stacker.stack.append(Symbol("x"))
        assert stacker.pop_and_eval(stacker.stack) == Symbol("x")

    def test_pop_and_eval_of_a_string(self):
        stacker = Stacker()
        stacker.stack.append(String("a"))
        value = stacker.pop_and_eval(stacker.stack)
        assert value == "a" and not isinstance(value, Symbol)

    def test_variables_are_keyed_by_plain_str(self):
        stacker = Stacker()
        stacker.eval("5 x set 6 $y set 7 {z} set")
        keys = [k for k, _ in stacker.variables.items() if k in {"x", "y", "z"}]
        assert sorted(keys) == ["x", "y", "z"]
        assert all(type(k) is str for k in keys)

    def test_symbol_is_hashable_and_distinct_from_a_str_key(self):
        table = {Symbol("x"): 1, "x": 2}
        assert table[Symbol("x")] == 1 and table["x"] == 2


class TestPluginArguments:
    @staticmethod
    def plugin_stacker() -> tuple[Stacker, list[object]]:
        stacker = Stacker()
        received: list[object] = []
        stacker.register_plugin("grab", lambda v: received.append(v) or 1)
        return stacker, received

    def test_a_symbol_reaches_the_plugin_as_a_symbol(self):
        stacker, received = self.plugin_stacker()
        stacker.process_expression("5 x set $x grab")
        assert received == [Symbol("x")]

    def test_a_string_reaches_the_plugin_as_a_string(self):
        stacker, received = self.plugin_stacker()
        stacker.process_expression('"x" grab')
        assert received == ["x"] and not isinstance(received[0], Symbol)

    def test_a_bare_name_reaches_the_plugin_as_its_value(self):
        stacker, received = self.plugin_stacker()
        stacker.process_expression("5 x set x grab")
        assert received == [5]

    def test_a_type_error_caused_by_a_symbol_becomes_a_stacker_type_error(self):
        stacker = Stacker()
        stacker.register_plugin("inc", lambda v: v + 1)
        with pytest.raises(StackerTypeError) as info:
            stacker.process_expression("$x inc")
        assert "`inc` cannot use the symbol `x`" in str(info.value)

    def test_a_type_error_without_a_symbol_is_unchanged(self):
        stacker = Stacker()
        stacker.register_plugin("inc", lambda v: v + 1)
        with pytest.raises(TypeError) as info:
            stacker.process_expression('"a" inc')
        assert not isinstance(info.value, StackerTypeError)

    def test_a_type_error_from_a_symbol_inside_a_list_argument(self):
        stacker = Stacker()
        stacker.register_plugin("total", lambda v: sum(v))
        with pytest.raises(StackerTypeError):
            stacker.process_expression("[$a $b] total")


class TestWithoutPrelude:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("$x", [Symbol("x")]),
            ("5 x set $x", [Symbol("x")]),
            ('$x "x" ==', [False]),
            ("3 4 $+ eval", [7]),
            ("[1 4 9] $sqrt map", [[1.0, 2.0, 3.0]]),
            ("[1 2] $dup map", [[[1, 1], [2, 2]]]),
            ('"x" symbol', [Symbol("x")]),
            ("$x symbol?", [True]),
            ("0 x = $x {1} if", [1]),
            ("true false null", [True, False, None]),
            ("0 1 3 $i {i +} do", [6]),
            ("{x} {x 2 *} f defun [1 2] $f map", [[2, 4]]),
        ],
    )
    def test_same_result_as_with_the_prelude(self, program, expected):
        assert run_without_prelude(program) == expected
        assert run(program) == expected

    @pytest.mark.parametrize("program", ["$x 1 +", '5 "x" set', "foo", "$1", '[1 4] "sqrt" map', "5 {x y} set"])
    def test_same_errors_as_with_the_prelude(self, program):
        with pytest.raises(Exception) as without:
            run_without_prelude(program)
        with pytest.raises(Exception) as with_prelude:
            run(program)
        assert type(without.value) is type(with_prelude.value)
        assert str(without.value) == str(with_prelude.value)


class TestErrorMessages:
    def test_type_error_names_the_word_the_symbol_and_both_ways_out(self):
        with pytest.raises(StackerTypeError) as info:
            run("$total 1 *")
        message = str(info.value)
        assert message.startswith("`*` cannot use the symbol `total` as a value.")
        assert "Write `total` for the variable's value" in message
        assert "`$total str` for its name as text" in message

    def test_type_error_keeps_the_original_exception_as_its_cause(self):
        with pytest.raises(StackerTypeError) as info:
            run("$x 1 +")
        assert isinstance(info.value.__cause__, TypeError)

    def test_type_error_is_a_stacker_error(self):
        from stacker.error import StackerError

        assert issubclass(StackerTypeError, StackerError)

    def test_type_error_names_the_symbol_found_in_a_list_argument(self):
        with pytest.raises(StackerTypeError) as info:
            run("[$a $b] sum")
        assert "symbol `a`" in str(info.value)

    def test_type_error_in_an_aggregate_over_a_block_of_values(self):
        with pytest.raises(StackerTypeError):
            run("1 2 $z 3 listn sum")

    def test_string_at_a_name_position_quotes_the_string_and_suggests_three_fixes(self):
        with pytest.raises(StackerSyntaxError) as info:
            run('5 "total" set')
        assert str(info.value) == (
            "`set` expects a name, got the string 'total'. "
            "Write $total or {total}, or convert a string with `symbol`."
        )

    @pytest.mark.parametrize(
        "program, word",
        [
            ('5 "x" global', "global"),
            ('{} {1} "m" defmacro', "defmacro"),
            ('"m" macroexpand', "macroexpand"),
            ('1 3 "i" {i} do', "do"),
            ('[1] "x" {x} dolist', "dolist"),
            ('[1] 0 "a" x {a} reduce', "reduce"),
        ],
    )
    def test_every_name_position_names_itself_in_the_message(self, program, word):
        with pytest.raises(StackerSyntaxError) as info:
            run(program)
        assert f"`{word}` expects a name, got the string" in str(info.value)

    @pytest.mark.parametrize("program", ["5 5 set", "5 {5} set", "5 {{x}} set", "5 {} set", "5 {x y} set", "5 {$1} set"])
    def test_non_names_say_what_they_got(self, program):
        with pytest.raises(StackerSyntaxError) as info:
            run(program)
        assert "`set` expects a name, got " in str(info.value)

    def test_dollar_error_quotes_the_offending_token(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("$1")
        assert str(info.value) == "`$1` is not a symbol: `$` must be followed by a name"

    @pytest.mark.parametrize("token", ["$a$b", "$'a'"])
    def test_dollar_error_quotes_the_whole_token(self, token):
        with pytest.raises(StackerSyntaxError) as info:
            run(token)
        assert f"`{token}` is not a symbol" in str(info.value)

    def test_bare_dollar_message(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("$ x")
        assert "`$` is not a symbol" in str(info.value)

    def test_list_literal_block_message_shows_both_alternatives(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("[{x}]")
        assert str(info.value) == (
            "a code block cannot be written inside a list literal; use {x} 1 listn, or [$x] for a symbol"
        )

    def test_nested_list_literal_block_message(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("[[{x}]]")
        assert "cannot be written inside a list literal" in str(info.value)

    @pytest.mark.parametrize(
        "program, got",
        [("{a a} {a} f defun", "unique"), ("{$a} {a} lambda", "bare names"), ("{1} {a} f defun", "bare names"),
         ("{[b]} {a} f defun", "bare names"), ("{true} {1} lambda", "bare names")],
    )
    def test_argument_list_messages(self, program, got):
        with pytest.raises(StackerSyntaxError) as info:
            run(program)
        assert got in str(info.value)

    def test_argument_list_message_shows_the_offending_argument(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("{$a} {a 2 *} f defun")
        assert str(info.value) == "`defun` argument names must be bare names, got $a"

    def test_lambda_argument_list_must_be_a_block(self):
        with pytest.raises(StackerSyntaxError) as info:
            run('"ab" {a} lambda')
        assert "`lambda` expects a code block of argument names" in str(info.value)

    def test_symbol_word_messages(self):
        with pytest.raises(StackerSyntaxError) as info:
            run("5 symbol")
        assert "`symbol` expects a string or a quoted name, got 5" in str(info.value)
        with pytest.raises(StackerSyntaxError) as info:
            run('"a b" symbol')
        assert "`symbol` expects a string that reads as a name, got 'a b'" in str(info.value)

    @pytest.mark.parametrize("word", ["map", "filter", "apply"])
    @pytest.mark.parametrize("specifier, shown", [("5", "5"), ('"sqrt"', "'sqrt'")])
    def test_function_specifier_message(self, word, specifier, shown):
        with pytest.raises(StackerTypeError) as info:
            run(f"[1 4] {specifier} {word}")
        assert (
            f"`{word}` expects a code block, a lambda or a symbol as the function, got {shown}"
            in str(info.value)
        )

    @pytest.mark.parametrize(
        "program, word",
        [("$foo disable_plugin", "disable_plugin"), ("{foo} disable_plugin", "disable_plugin"),
         ("5 disable_plugin", "disable_plugin"), ("$lib include", "include"), ("{lib} include", "include"),
         ("5 include", "include")],
    )
    def test_string_only_words_reject_non_strings(self, program, word):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert f"`{word}` expects" in str(info.value) and "as a string" in str(info.value)

    def test_undefined_name_message_is_unchanged_for_python_callers(self):
        with pytest.raises(UndefinedSymbolError) as info:
            Stacker().eval("3 foo +")
        assert str(info.value) == "`foo` is not defined."


class TestIncludedWordsAndSymbols:
    @pytest.fixture
    def library(self, tmp_path):
        path = tmp_path / "lib.stk"
        path.write_text("{x} {x 2 *} dbl defun\n{} {{3}} three defmacro\n10 base set\n")
        return path

    def test_symbol_of_an_included_function_maps(self, library):
        assert run(f'"{library}" include', "[1 2] $dbl map") == [[2, 4]]

    def test_symbol_of_an_included_function_evals(self, library):
        assert run(f'"{library}" include', "4 $dbl eval") == [8]

    def test_symbol_of_an_included_macro_evals(self, library):
        assert run(f'"{library}" include', "$three eval") == [3]

    def test_symbol_of_an_included_variable_is_not_its_value(self, library):
        assert run(f'"{library}" include', "$base") == [Symbol("base")]
        assert run(f'"{library}" include', "base") == [10]

    def test_symbol_of_an_included_variable_pushes_the_value_on_eval(self, library):
        assert run(f'"{library}" include', "$base eval") == [10]

    def test_symbol_made_from_a_string_finds_an_included_word(self, library):
        assert run(f'"{library}" include', '[1 2] "dbl" symbol map') == [[2, 4]]

    def test_string_of_an_included_word_is_not_a_function(self, library):
        with pytest.raises(StackerTypeError):
            run(f'"{library}" include', '[1 2] "dbl" map')

    def test_included_name_as_a_quoted_name_round_trips_through_nth(self, library):
        assert run(f'"{library}" include', "{dbl} 0 nth")[-1] == Symbol("dbl")

    def test_symbol_of_a_name_the_include_did_not_define(self, library):
        with pytest.raises(UndefinedSymbolError):
            run(f'"{library}" include', "[1] $nothing map")


class TestSymbolsGivenToWordsThatDoNotAcceptThem:
    @pytest.mark.parametrize("program", ["$x upper", "$x lower", "$x strip", '"," $x join'])
    def test_string_method_on_a_symbol_is_a_stacker_type_error(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    @pytest.mark.parametrize("program", ["$x 1 nth", '"a" $x split'])
    def test_priority_word_on_a_symbol_is_a_stacker_type_error(self, program):
        with pytest.raises(StackerTypeError):
            run(program)
