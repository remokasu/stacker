"""A word given a value it cannot use names itself and shows the value, never the host's message."""

import pytest

from stacker import Stacker
from stacker.error import StackerSyntaxError, StackerTypeError, ValidationError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestConversionsAndMath:
    @pytest.mark.parametrize(
        "program, word, shown",
        [
            ('"abc" asc', "asc", "'abc'"),
            ("5 asc", "asc", "5"),
            ('"a" chr', "chr", "'a'"),
            ('"x" int', "int", "'x'"),
            ('"3.5x" float', "float", "'3.5x'"),
            ("1+0j int", "int", "(1+0j)"),
            ("[1] int", "int", "[1]"),
            ('[3 "a"] sorted', "sorted", "'a'"),
            ('[3 "a"] min', "min", "'a'"),
            ('[3 "a"] max', "max", "'a'"),
        ],
    )
    def test_a_type_error_names_the_word_and_shows_the_value(self, program, word, shown):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert f"`{word}`" in str(info.value)
        assert shown in str(info.value)

    @pytest.mark.parametrize(
        "program, word, shown",
        [
            ("-1 chr", "chr", "-1"),
            ("1114112 chr", "chr", "1114112"),
            ("-1 sqrt", "sqrt", "-1"),
            ("0 log", "log", "0"),
            ("-2 log2", "log2", "-2"),
            ("0 log10", "log10", "0"),
        ],
    )
    def test_a_value_outside_the_domain_names_the_word_and_shows_the_value(self, program, word, shown):
        with pytest.raises(ValidationError) as info:
            run(program)
        assert f"`{word}`" in str(info.value)
        assert shown in str(info.value)

    def test_the_host_names_never_show(self):
        for program in ['"abc" asc', '"x" int', "-1 sqrt", '[3 "a"] sorted']:
            with pytest.raises(Exception) as info:
                run(program)
            text = str(info.value)
            assert "ord()" not in text and "int()" not in text and "math domain" not in text and "String" not in text

    def test_a_complex_square_root_still_works(self):
        assert run("-1+0j sqrt") == [1j]

    def test_fractions_and_bools_are_numbers_as_before(self):
        assert run("1 4 frac sqrt true sqrt true log true chr 1 3 frac float") == [0.5, 1.0, 0.0, "\x01", 1 / 3]

    @pytest.mark.parametrize("program, word, shown", [('"a" ++', "++", "'a'"), ('"a" --', "--", "'a'")])
    def test_the_one_argument_arithmetic_words_name_themselves(self, program, word, shown):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert f"`{word}`" in str(info.value) and shown in str(info.value)

    def test_min_of_an_empty_list_and_of_a_number(self):
        with pytest.raises(ValidationError, match="`min` expects at least one value"):
            run("[] min")
        with pytest.raises(StackerTypeError, match="`max` expects a list"):
            run("1 max")

    def test_sorted_finds_the_pair_that_cannot_be_compared(self):
        with pytest.raises(StackerTypeError) as info:
            run('[1 2 "a" 3] sorted')
        assert "'a'" in str(info.value) and "1" in str(info.value)


class TestArithmetic:
    @pytest.mark.parametrize(
        "program, shown",
        [
            ('"a" 1 +', "'a'"),
            ("[1] \"a\" +", "[1]"),
            ('1 "a" +', "'a'"),
            ('"a" 2 -', "'a'"),
            ('"a" "b" *', "'a'"),
            ("[1] 2 /", "[1]"),
            ('"a" 2 ^', "'a'"),
            ("null 1 +", "null"),
        ],
    )
    def test_an_arithmetic_type_error_names_the_word_and_both_values(self, program, shown):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        text = str(info.value)
        assert text.startswith("`") and shown in text
        assert "unsupported operand" not in text and "concatenate" not in text

    def test_adding_text_and_a_number_says_how_to_join_them(self):
        with pytest.raises(StackerTypeError) as info:
            run('"a" 1 +')
        assert "str" in str(info.value)

    def test_a_symbol_operand_is_still_reported_as_a_symbol(self):
        with pytest.raises(StackerTypeError) as info:
            run(":x 1 +")
        assert "cannot use the symbol `x`" in str(info.value)

    def test_division_by_zero_is_unchanged(self):
        with pytest.raises(ZeroDivisionError):
            run("1 0 /")

    def test_arithmetic_that_works_is_unchanged(self):
        assert run('1 2 + "a" "b" + [1] [2] + 2 3 ^ "ab" 2 * 7 2 // 7 2 %') == [3, "ab", [1, 2], 8, "abab", 3, 1]


class TestFormat:
    def test_a_template_asking_for_more_values_than_given_names_format(self):
        from stacker.error import StackerIndexError

        with pytest.raises(StackerIndexError) as info:
            run('"x={} y={}" [1 2] format')
        assert "`format`" in str(info.value) and "one value" in str(info.value)
        assert "positional" not in str(info.value)

    def test_a_template_with_a_name_names_format(self):
        from stacker.error import StackerIndexError

        with pytest.raises(StackerIndexError) as info:
            run('"x={a}" 1 format')
        assert "`format`" in str(info.value)


class TestWordsInsideAListLiteral:
    @pytest.mark.parametrize("program, word", [("[1 2 +]", "+"), ("[1 2 ^]", "^"), ("[1 2 ==]", "=="), ("[1 2 -]", "-"), ("[1 dup]", "dup")])
    def test_a_symbolic_operator_gets_the_same_explanation_as_a_named_word(self, program, word):
        with pytest.raises(StackerSyntaxError) as info:
            run(program)
        assert f"`{word}` is a word" in str(info.value)
        assert "listn" in str(info.value)
