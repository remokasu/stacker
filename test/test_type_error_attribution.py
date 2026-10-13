"""A type error is blamed on a symbol only when the symbol caused it.

Host functions raise Python's TypeError / AttributeError; the executors turn
one into a StackerTypeError with a hint when a symbol was among the
arguments *and* the message names the Symbol type. Anything else passes
through unchanged, so an unrelated error inside a map body is not blamed on
a symbol that happened to be an element.
"""

import pytest

from stacker import Stacker
from stacker.error import StackerSyntaxError, StackerTypeError
from stacker.syntax.token_rules import is_symbol_name


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestAttribution:
    @pytest.mark.parametrize(
        "program",
        ['[:x] {drop "a" 1 +} map', '[:x :y] {drop 1 "a" +} map', '[:x] {drop "a" 1 +} filter'],
    )
    def test_unrelated_error_in_a_body_is_not_blamed_on_the_element(self, program):
        with pytest.raises(TypeError) as info:
            run(program)
        assert not isinstance(info.value, StackerTypeError)

    def test_symbol_element_that_is_dropped_causes_no_error(self):
        assert run("5 x set [:x] {drop x 1 +} map") == [[6]]

    @pytest.mark.parametrize(
        "program",
        [":x 1 nth", "[1 2] :x nth", '"a" :x split', ':x "a" split', ":n listn", ":n subn"],
    )
    def test_priority_words_report_a_symbol(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    @pytest.mark.parametrize("program", [":x upper", ":x lower", '"," :x join'])
    def test_string_method_on_a_symbol_is_a_stacker_type_error(self, program):
        with pytest.raises(StackerTypeError):
            run(program)

    def test_shortcut_names_the_word_the_symbol_names(self):
        with pytest.raises(StackerTypeError) as info:
            run("[1 :x] :neg map")
        assert "`neg` cannot use the symbol `x`" in str(info.value)

    def test_list_literal_inside_an_aggregated_block_is_a_value(self):
        assert run("{[1 2] [3]} max") == [[3]]


class TestSymbolNames:
    @pytest.mark.parametrize("text", ["a$b", "a(b", "a)b", "a[b", "a{b", "a;b", "a#b", "a'b", 'a"b', "a b", ""])
    def test_text_the_lexer_would_split_is_rejected(self, text):
        assert not is_symbol_name(text)
        with pytest.raises(StackerSyntaxError):
            run(f'"{text}" symbol' if '"' not in text else f"'{text}' symbol")

    @pytest.mark.parametrize("text", ["x", "x.y", "x-y?", "+", "<=", "1st"])
    def test_names_the_lexer_keeps_whole_are_accepted(self, text):
        assert is_symbol_name(text)
        assert run(f'"{text}" symbol str') == [text]
