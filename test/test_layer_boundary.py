"""Blocks read as data hand out symbols; values spliced into blocks become tokens.

One test per path of the token-layer / value-layer boundary: `nth`, `apply`,
`map` / `filter`, `reduce` / `fold`, `zip`, the transforms, the aggregates,
`sub` / `subn` and the blocks those words build.
"""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.engine.data_type import String, Symbol
from stacker.error import StackerTypeError, UndefinedSymbolError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


def tokens(block: object) -> list[object]:
    assert isinstance(block, StackerCore)
    return list(block.tokens)


class TestTokensBecomeValues:
    def test_nth_on_a_block_gives_a_symbol(self):
        # `nth` leaves the block on the stack and pushes the element.
        assert run("{x} 0 nth")[-1] == Symbol("x")
        assert run("5 :x set {x} 0 nth")[-1] == Symbol("x")
        assert run("{1 2 +} 2 nth")[-1] == Symbol("+")

    def test_nth_on_a_block_keeps_literals(self):
        value = run('{"x"} 0 nth')[-1]
        assert isinstance(value, String) and value == "x"
        assert run("{1 2 +} 0 nth")[-1] == 1

    def test_symbol_from_a_block_is_not_a_value(self):
        with pytest.raises(TypeError):
            run("5 :x set {x} 0 nth 1 +")

    def test_apply_pushes_block_arguments_as_values(self):
        assert run("{{x y}} {} apply") == [Symbol("x"), Symbol("y")]
        assert run("[3 4] {+} apply") == [7]

    def test_map_over_a_block_sees_symbols(self):
        (block,) = run("1 :x set 2 :y set {x y} {} map")
        assert tokens(block) == ["x", "y"]
        assert all(type(t) is str for t in tokens(block))

    def test_map_over_a_block_of_values(self):
        (block,) = run("{1 2 3} {2 *} map")
        assert tokens(block) == [2, 4, 6]

    def test_reduce_over_a_block_sees_symbols(self):
        with pytest.raises(TypeError):
            run("1 :a set 2 :b set {a b} 0 :acc :x {acc x +} reduce")
        assert run("{1 2 3} 0 :acc :x {acc x +} reduce") == [6]

    def test_zip_blocks(self):
        (block,) = run("{x y} {1 2} zip")
        assert tokens(block) == [[Symbol("x"), 1], [Symbol("y"), 2]]
        assert run("[1 2] [3 4] zip") == [[[1, 3], [2, 4]]]

    def test_list_of_a_block_gives_symbols(self):
        assert run("1 :x set 2 :y set {x y} list") == [[Symbol("x"), Symbol("y")]]

    def test_sorted_block_of_names(self):
        (block,) = run("{c a b} sorted")
        assert tokens(block) == ["a", "b", "c"]

    def test_string_elements_stay_strings_in_map(self):
        assert run('"ab" list {upper} map') == [["A", "B"]]
        assert run('5 :ab set "ab" list') == [["a", "b"]]


class TestAggregatesReferenceNames:
    def test_names_are_the_variables_values(self):
        assert run("1 :x set 2 :y set {x y} sum") == [3]

    def test_undefined_name_raises(self):
        with pytest.raises(UndefinedSymbolError):
            run("{x y} sum")

    def test_operator_name_is_not_a_value(self):
        with pytest.raises(UndefinedSymbolError):
            run("{1 2 +} sum")

    def test_len_counts_tokens_without_referencing(self):
        assert run("{alpha beta 1} len") == [3]
        assert run("{} len") == [0]

    def test_keyword_literals(self):
        assert run("{true false true} all") == [False]
        assert run("{true false true} any") == [True]

    def test_string_literal_is_a_value(self):
        assert run("5 :a set", '{"a"} max') == ["a"]


class TestFunctionSpecifiers:
    def test_symbol_names_an_operator(self):
        assert run("[1 4 9] :sqrt map") == [[1.0, 2.0, 3.0]]
        assert run("[3 4] :+ apply") == [7]

    def test_symbol_names_a_stack_operator(self):
        # `:dup` is not a one-argument host word, so it runs like `{dup}`.
        assert run("[1 2] :dup map") == [[[1, 1], [2, 2]]]

    def test_symbol_names_a_function_or_macro(self):
        assert run("{x} {x 1 +} :f defun [1 2] :f map") == [[2, 3]]
        assert run("{} {{2 *}} :m defmacro [1 2] :m map") == [[2, 4]]

    def test_symbol_shadowed_by_a_variable_is_not_shortcut(self):
        # `sqrt` is a variable here, so `:sqrt` means `{sqrt}`: push its value.
        assert run("7 :sqrt set [1 2] :sqrt map") == [[[1, 7], [2, 7]]]

    def test_lambda_value_as_function(self):
        assert run("{a} {a 2 *} lambda :f set [1 2] f map") == [[2, 4]]

    def test_quoted_lambda_variable_pushes_the_lambda(self):
        (result,) = run("{a} {a 2 *} lambda :f set [1 2] {f} map")
        assert [len(pair) for pair in result] == [2, 2]
        assert result[0][0] == 1 and type(result[0][1]).__name__ == "StackerLambda"

    @pytest.mark.parametrize("program", ['[1 4] "sqrt" map', '[3 4] "+" apply', "[3 4] 5 apply", "[1 2] 3 filter"])
    def test_other_values_are_rejected(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_reduce_symbol_function_means_the_quoted_name(self):
        assert run("{x} {x 1 +} :f defun {1 2} 0 :acc :x {acc x + f} reduce") == [5]

    def test_block_element_is_evaluated_before_a_host_word(self):
        # The shortcut prepares the element exactly as `_execute` would.
        assert run("{1 2 +} 1 listn :sqrt map") == [[3 ** 0.5]]


class TestValuesBecomeTokens:
    def test_subn_of_symbols(self):
        (block,) = run(":a :b 2 subn")
        assert tokens(block) == ["a", "b"]

    def test_map_result_block_quotes_computed_strings(self):
        (block,) = run('{"a" "b"} {"!" +} map')
        assert all(isinstance(t, String) for t in tokens(block))
        assert tokens(block) == ["a!", "b!"]

    def test_sorted_result_block_keeps_string_literals(self):
        (block,) = run('{"b" "a"} sorted')
        assert all(isinstance(t, String) for t in tokens(block))

    def test_literal_block_forced_by_an_operator_is_unchanged(self):
        assert run("{1 2 +} dup +") == [6]


class TestElementsHandedToABlockBody:
    """`map` / `filter` give each element to the body as a value, never as a name."""

    def test_symbols_in_a_list_stay_symbols(self):
        assert run("[:a :b] {symbol?} map") == [[True, True]]

    def test_symbols_in_a_block_stay_symbols(self):
        (block,) = run("{x y} {symbol?} map")
        assert tokens(block) == [True, True]

    def test_strings_in_a_list_are_not_symbols(self):
        assert run('["a"] {symbol?} map') == [[False]]

    def test_str_of_a_block_element_makes_string_literals(self):
        (block,) = run("{x y} {str} map")
        assert all(isinstance(t, String) for t in tokens(block))
        assert tokens(block) == ["x", "y"]

    def test_symbol_word_turns_strings_into_symbols(self):
        assert run('["a" "b"] {symbol} map') == [[Symbol("a"), Symbol("b")]]

    def test_filter_over_a_block_keeps_the_tokens(self):
        (block,) = run('{x "a" 1} {symbol?} filter')
        assert tokens(block) == ["x"]

    def test_filter_over_a_list_of_mixed_values(self):
        assert run("[:a 1] {symbol?} filter") == [[Symbol("a")]]

    def test_identity_map_over_a_block_keeps_names_as_names(self):
        (block,) = run('{"b" a} {} map')
        assert tokens(block) == [String("b"), "a"]
        assert type(tokens(block)[1]) is str

    def test_a_bound_name_in_the_block_is_not_looked_up(self):
        (block,) = run("5 :a set {a b} {} map")
        assert tokens(block) == ["a", "b"]


class TestBlocksReadAsDataKeepTokenKinds:
    def test_nth_of_a_negative_index(self):
        assert run("{x y} -1 nth")[-1] == Symbol("y")

    def test_nth_of_a_nested_block_gives_the_block(self):
        value = run("{{x}} 0 nth")[-1]
        assert isinstance(value, StackerCore) and str(value) == "{x}"

    def test_nth_of_a_list_token_is_text_not_a_symbol(self):
        value = run("{[1 2]} 0 nth")[-1]
        assert type(value) is str and not isinstance(value, Symbol)

    def test_nth_of_a_dollar_token_is_the_symbol(self):
        assert run("{:x} 0 nth")[-1] == Symbol("x")

    def test_apply_of_a_nested_block_keeps_its_name_tokens(self):
        first, second = run("{{x y} 1} {} apply")
        assert tokens(first) == ["x", "y"] and second == 1

    def test_apply_with_a_lambda_value_calls_it_with_the_list(self):
        assert run("[3] {a} {a 2 *} lambda apply") == [6]

    def test_reversed_block_reads_as_symbols(self):
        assert run("{x y} reversed 0 nth")[-1] == Symbol("y")

    def test_sorted_block_reads_as_symbols(self):
        assert run("{y x} sorted 0 nth")[-1] == Symbol("x")


class TestZipEnumerateReversed:
    def test_zip_two_blocks_of_names_and_values(self):
        (block,) = run('{x y} {"a" 1} zip')
        assert tokens(block) == [[Symbol("x"), "a"], [Symbol("y"), 1]]

    def test_zip_block_with_a_list(self):
        (block,) = run("{x y} [1 2] zip")
        assert tokens(block) == [[Symbol("x"), 1], [Symbol("y"), 2]]

    def test_zip_list_of_symbols(self):
        assert run("[:a :b] [1 2] zip") == [[[Symbol("a"), 1], [Symbol("b"), 2]]]

    def test_zip_with_a_string_splits_it_into_characters(self):
        assert run('"ab" [1 2] zip') == [[["a", 1], ["b", 2]]]

    def test_zip_with_a_string_holding_a_dollar_name_does_not_make_a_symbol(self):
        assert run('"$x" [1 2] zip') == [[["$", 1], ["x", 2]]]

    def test_zip_with_a_bound_string_does_not_look_the_name_up(self):
        assert run('5 :ab set "ab" [1 2] zip') == [[["a", 1], ["b", 2]]]

    @pytest.mark.parametrize("program", [":x [1 2] zip", "[1 2] :x zip"])
    def test_zip_with_a_symbol_argument_is_a_type_error(self, program):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert "`zip` cannot use the symbol `x`" in str(info.value)

    def test_zip_does_not_look_up_bare_names_in_a_block(self):
        (block,) = run("1 :x set {x} [9] zip")
        assert tokens(block) == [[Symbol("x"), 9]]

    def test_zip_with_a_list_literal_resolves_bare_names(self):
        assert run("1 :x set [x] [9] zip") == [[[1, 9]]]

    def test_enumerate_a_block_pairs_indices_with_symbols(self):
        (block,) = run("{x y} enumerate")
        assert tokens(block) == [[0, Symbol("x")], [1, Symbol("y")]]

    def test_enumerate_a_block_keeps_string_literals_and_numbers(self):
        (block,) = run('{x "a" 1} enumerate')
        assert tokens(block) == [[0, Symbol("x")], [1, "a"], [2, 1]]

    def test_enumerate_a_list_of_symbols(self):
        assert run("[:a :b] enumerate") == [[[0, Symbol("a")], [1, Symbol("b")]]]

    def test_enumerate_a_list_of_numbers(self):
        assert run("[5 6] enumerate") == [[[0, 5], [1, 6]]]

    def test_enumerate_a_string(self):
        assert run('"ab" enumerate') == [[[0, "a"], [1, "b"]]]

    def test_enumerate_a_list_literal_with_an_undefined_name_raises(self):
        with pytest.raises(UndefinedSymbolError):
            run("[a] enumerate")

    def test_enumerate_a_symbol_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run(":x enumerate")

    def test_reversed_block_keeps_each_token_kind(self):
        (block,) = run('{x "a" 1} reversed')
        reversed_tokens = tokens(block)
        assert reversed_tokens == [1, "a", "x"]
        assert isinstance(reversed_tokens[1], String)
        assert type(reversed_tokens[2]) is str

    def test_reversed_block_does_not_look_up_names(self):
        (block,) = run("5 :x set {x y} reversed")
        assert tokens(block) == ["y", "x"]

    def test_reversed_list_of_symbols(self):
        assert run("[:a :b] reversed") == [[Symbol("b"), Symbol("a")]]

    def test_reversed_string_gives_characters(self):
        assert run('"abc" reversed') == [["c", "b", "a"]]

    def test_reversed_numbers(self):
        assert run("[1 2 3] reversed") == [[3, 2, 1]]

    def test_list_of_a_string_is_not_resolved(self):
        assert run('"$x" :y set y list') == [["$", "x"]]

    def test_sorted_block_with_a_number_and_a_name_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run("{b 1} sorted")

    def test_sorted_list_of_symbols(self):
        assert run("[:b :a] sorted") == [[Symbol("a"), Symbol("b")]]


class TestFilterFunctionSpecifiers:
    def test_symbol_of_a_user_function(self):
        assert run("{x} {x 2 % 0 ==} :even2? defun [1 2 3 4] :even2? filter") == [[2, 4]]

    def test_quoted_name_of_a_user_function_is_the_same(self):
        assert run("{x} {x 2 % 0 ==} :even2? defun [1 2 3 4] {even2?} filter") == [[2, 4]]

    def test_symbol_of_a_macro(self):
        assert run("{} {{2 >}} :gt2 defmacro [1 2 3 4] :gt2 filter") == [[3, 4]]

    def test_symbol_of_an_operator_that_pushes_one_value(self):
        assert run("[0 1 0] :bool filter") == [[1]]
        assert run("[0 1 0] :not filter") == [[0, 0]]

    def test_symbol_of_a_stack_word_runs_like_the_quoted_name(self):
        assert run("[1 2] :dup filter") == run("[1 2] {dup} filter")
        assert run("[0 0] :dup filter") == run("[0 0] {dup} filter")

    def test_lambda_value(self):
        assert run("[1 2 3 4] {a} {a 2 >} lambda filter") == [[3, 4]]

    def test_lambda_in_a_variable_by_bare_name(self):
        assert run("{a} {a 2 >} lambda :big set [1 2 3 4] big filter") == [[3, 4]]

    def test_symbol_that_is_a_variable_pushes_its_value(self):
        # `:flag` means `{flag}`: the variable's value is pushed and the stack decides.
        assert run("1 :flag set [7 8] :flag filter") == [[7, 8]]

    @pytest.mark.parametrize("specifier", ['"bool"', "5", "[1]", "1.5", "true"])
    def test_other_values_are_type_errors(self, specifier):
        with pytest.raises(StackerTypeError):
            run(f"[1 2] {specifier} filter")

    @pytest.mark.parametrize("word", ["map", "filter", "apply"])
    def test_symbol_of_an_undefined_name_is_an_undefined_reference(self, word):
        with pytest.raises(UndefinedSymbolError):
            run(f"[1 2] :nope {word}")

    def test_map_symbol_of_a_macro(self):
        assert run("{} {{2 *}} :twice defmacro [1 2] :twice map") == [[2, 4]]

    def test_symbol_made_from_a_string_works_as_a_specifier(self):
        assert run('[1 4] "sqrt" symbol filter') == [[1, 4]]


class TestReduceFoldFunctionPosition:
    def test_fold_with_a_user_function_symbol_in_the_body(self):
        assert run("{x} {x 1 +} :f defun {1 2} 0 :acc :x {acc x + f} fold") == [5]

    def test_reduce_over_a_list_of_symbols_adding_is_a_type_error(self):
        with pytest.raises(StackerTypeError):
            run("[:a :b] 0 :acc :x {acc x +} reduce")

    def test_reduce_collecting_symbols_into_a_list(self):
        assert run("{a b} [] :acc :x {acc x 1 listn +} reduce") == [[Symbol("a"), Symbol("b")]]

    def test_reduce_over_a_block_binds_symbols_not_values(self):
        assert run("1 :a set 2 :b set {a b} 0 :acc :x {x} reduce") == [Symbol("b")]

    def test_reduce_over_a_list_of_strings(self):
        assert run('["a" "b"] "" :acc :x {acc x +} reduce') == ["ab"]

    def test_reduce_init_symbol_is_kept(self):
        assert run("[1 2] :z :acc :x {acc} reduce") == [Symbol("z")]


class TestInterpolatedValues:
    @pytest.mark.parametrize(
        "argument, check",
        [
            ("[1 2]", lambda v: v == [1, 2]),
            ("3", lambda v: v == 3),
            ('"s"', lambda v: v == "s" and not isinstance(v, Symbol)),
            ("[:a]", lambda v: v == [Symbol("a")]),
            ("{1}", lambda v: isinstance(v, StackerCore) and str(v) == "{1}"),
        ],
    )
    def test_value_spliced_into_a_template_comes_out_as_the_same_kind(self, argument, check):
        (value,) = run("{v} {{v}} :m defmacro", f"{argument} m")
        assert check(value)

    def test_symbol_is_spliced_as_a_bare_name_that_is_then_a_reference(self):
        assert run("1 :z set", "{v} {{v}} :m defmacro", ":z m") == [1]
        assert run("1 :z set", "{v} {v} :m defmacro", ":z m") == [Symbol("z")]

    def test_lambda_value_is_spliced_as_a_value_token(self):
        (value,) = run("{v} {{v}} :m defmacro", "{a} {a} lambda m")
        assert type(value).__name__ == "StackerLambda"
