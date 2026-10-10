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
        assert run("5 x set {x} 0 nth")[-1] == Symbol("x")
        assert run("{1 2 +} 2 nth")[-1] == Symbol("+")

    def test_nth_on_a_block_keeps_literals(self):
        value = run('{"x"} 0 nth')[-1]
        assert isinstance(value, String) and value == "x"
        assert run("{1 2 +} 0 nth")[-1] == 1

    def test_symbol_from_a_block_is_not_a_value(self):
        with pytest.raises(TypeError):
            run("5 x set {x} 0 nth 1 +")

    def test_apply_pushes_block_arguments_as_values(self):
        assert run("{{x y}} {} apply") == [Symbol("x"), Symbol("y")]
        assert run("[3 4] {+} apply") == [7]

    def test_map_over_a_block_sees_symbols(self):
        (block,) = run("1 x set 2 y set {x y} {} map")
        assert tokens(block) == ["x", "y"]
        assert all(type(t) is str for t in tokens(block))

    def test_map_over_a_block_of_values(self):
        (block,) = run("{1 2 3} {2 *} map")
        assert tokens(block) == [2, 4, 6]

    def test_reduce_over_a_block_sees_symbols(self):
        with pytest.raises(TypeError):
            run("1 a set 2 b set {a b} 0 acc x {acc x +} reduce")
        assert run("{1 2 3} 0 acc x {acc x +} reduce") == [6]

    def test_zip_blocks(self):
        (block,) = run("{x y} {1 2} zip")
        assert tokens(block) == [(Symbol("x"), 1), (Symbol("y"), 2)]
        assert run("[1 2] [3 4] zip") == [[(1, 3), (2, 4)]]

    def test_list_of_a_block_gives_symbols(self):
        assert run("1 x set 2 y set {x y} list") == [[Symbol("x"), Symbol("y")]]

    def test_sorted_block_of_names(self):
        (block,) = run("{c a b} sorted")
        assert tokens(block) == ["a", "b", "c"]

    def test_string_elements_stay_strings_in_map(self):
        assert run('"ab" list {upper} map') == [["A", "B"]]
        assert run('5 ab set "ab" list') == [["a", "b"]]


class TestAggregatesReferenceNames:
    def test_names_are_the_variables_values(self):
        assert run("1 x set 2 y set {x y} sum") == [3]

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
        assert run("5 a set", '{"a"} max') == ["a"]


class TestFunctionSpecifiers:
    def test_symbol_names_an_operator(self):
        assert run("[1 4 9] $sqrt map") == [[1.0, 2.0, 3.0]]
        assert run("[3 4] $+ apply") == [7]

    def test_symbol_names_a_stack_operator(self):
        # `$dup` is not a one-argument host word, so it runs like `{dup}`.
        assert run("[1 2] $dup map") == [[[1, 1], [2, 2]]]

    def test_symbol_names_a_function_or_macro(self):
        assert run("{x} {x 1 +} f defun [1 2] $f map") == [[2, 3]]
        assert run("{} {{2 *}} m defmacro [1 2] $m map") == [[2, 4]]

    def test_symbol_shadowed_by_a_variable_is_not_shortcut(self):
        # `sqrt` is a variable here, so `$sqrt` means `{sqrt}`: push its value.
        assert run("7 $sqrt set [1 2] $sqrt map") == [[[1, 7], [2, 7]]]

    def test_lambda_value_as_function(self):
        assert run("{a} {a 2 *} lambda f set [1 2] f map") == [[2, 4]]

    def test_quoted_lambda_variable_pushes_the_lambda(self):
        (result,) = run("{a} {a 2 *} lambda f set [1 2] {f} map")
        assert [len(pair) for pair in result] == [2, 2]
        assert result[0][0] == 1 and type(result[0][1]).__name__ == "StackerLambda"

    @pytest.mark.parametrize("program", ['[1 4] "sqrt" map', '[3 4] "+" apply', "[3 4] 5 apply", "[1 2] 3 filter"])
    def test_other_values_are_rejected(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_reduce_symbol_function_means_the_quoted_name(self):
        assert run("{x} {x 1 +} f defun {1 2} 0 acc x {acc x + f} reduce") == [5]

    def test_block_element_is_evaluated_before_a_host_word(self):
        # The shortcut prepares the element exactly as `_execute` would.
        assert run("{1 2 +} 1 listn $sqrt map") == [[3 ** 0.5]]


class TestValuesBecomeTokens:
    def test_subn_of_symbols(self):
        (block,) = run("$a $b 2 subn")
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
