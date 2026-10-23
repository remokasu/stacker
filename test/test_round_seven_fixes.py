"""Words own their errors; cbrt and lcm are right; counts are 0 or more; an argument is one value; files are UTF-8."""

import math

import pytest

from stacker import Stacker
from stacker.error import (
    ResultCountError,
    ScriptReadError,
    StackerIndexError,
    StackerRuntimeError,
    StackerTypeError,
    ValidationError,
)
from stacker.runtime.exec_modes.script_mode import ScriptMode


def run(program: str) -> list[object]:
    stacker = Stacker()
    stacker.process_expression(program)
    return list(stacker.stack)


class TestHostErrorsBecomeTheWords:
    @pytest.mark.parametrize(
        "program, error, text",
        [
            ('5 "a" <', StackerTypeError, "`<` cannot use 5 and 'a'"),
            ("5 asin", ValidationError, "`asin` cannot use 5"),
            ('"a" sin', StackerTypeError, "`sin` cannot use 'a'"),
            ("10 20 ^ exp", ValidationError, "`exp` cannot use"),
            ('"nan" float round', ValidationError, "`round` cannot use nan"),
            ("-3 !", ValidationError, "`!` cannot use -3"),
            ("5 -1 <<", ValidationError, "`<<` cannot use 5 and -1"),
            ("[1 2] 5 nth", StackerIndexError, "`nth` index 5 is out of range for a length of 2"),
            ('"a" 5 contains', StackerTypeError, "`contains` cannot use 'a' and 5"),
            ("[1 2] parse", StackerTypeError, "`parse` expects a string of code, got [1 2]"),
            ('"" car', ValidationError, "`car` cannot use ''"),
            ("{x} {x} lambda len", StackerTypeError, "`len` expects a list, an array, a string or a block"),
            ("{x} {x} lambda {true} filter", StackerTypeError, "`filter` expects a list"),
            ("[1 2] complex", StackerTypeError, "`complex` cannot use [1 2]"),
            ('5 "a" comb', StackerTypeError, "`comb` expects an integer, got 'a'"),
            ("-1 5 comb", ValidationError, "`comb` cannot use -1 and 5"),
            ("5 1.5 gcd", StackerTypeError, "`gcd` expects an integer, got 1.5"),
            (":s asin", StackerTypeError, "`asin` cannot use the symbol `s`"),
        ],
    )
    def test_the_word_names_itself_with_the_right_kind(self, program, error, text):
        with pytest.raises(error) as info:
            run(program)
        message = str(info.value)
        assert text in message and "object" not in message.split(":")[0]


class TestCbrtAndLcm:
    @pytest.mark.parametrize("program, expected", [("-8 cbrt", -2.0), ("-1 cbrt", -1.0), ("64 cbrt", 4.0), ("1000 cbrt", 10.0), ("0 cbrt", 0.0), ("27 cbrt", 3.0)])
    def test_cbrt_is_the_real_root_exact_for_perfect_cubes(self, program, expected):
        assert run(program) == [expected]

    def test_cbrt_of_an_infinity_or_nan_is_itself(self):
        values = run("inf cbrt -inf cbrt nan cbrt")
        assert values[0] == math.inf and values[1] == -math.inf and math.isnan(values[2])

    def test_cbrt_cubed_comes_back(self):
        assert run("-8 cbrt 3 ^") == [-8.0]

    @pytest.mark.parametrize("program, expected", [("0 0 lcm", 0), ("-4 6 lcm", 12), ("4 6 lcm", 12), ("0 5 lcm", 0)])
    def test_lcm_is_zero_or_more(self, program, expected):
        assert run(program) == [expected]

    def test_lcm_refuses_a_fraction(self):
        with pytest.raises(StackerTypeError, match="`lcm` expects an integer"):
            run("4 1.5 lcm")


class TestCountsAreZeroOrMore:
    @pytest.mark.parametrize("program, word", [("1 2 3 -1 dupn", "dupn"), ("1 2 3 -1 dropn", "dropn"), ("1 2 3 -2 listn", "listn"), ("1 2 3 -1 subn", "subn")])
    def test_a_negative_count_is_refused(self, program, word):
        with pytest.raises(ValidationError, match=f"`{word}` expects a count of 0 or more, got -"):
            run(program)

    @pytest.mark.parametrize("program, word", [("5 2.9 comb", "comb"), ("5.9 2 comb", "comb"), ("5 2.9 perm", "perm"), ("5 2.9 ncr", "ncr"), ("5 2.9 npr", "npr"), ("1.5 5 randint", "randint"), ("2 6.5 dice", "dice")])
    def test_a_fraction_is_not_truncated(self, program, word):
        with pytest.raises(StackerTypeError, match=f"`{word}` expects an integer"):
            run(program)

    def test_roundn_digits_are_limited(self):
        with pytest.raises(ValidationError, match="`roundn` expects a digit count between -1000 and 1000"):
            run("1 2 frac 100000000 roundn")
        assert run("3.14159 2 roundn 1234 -2 roundn") == [3.14, 1200]


class TestAnArgumentIsOneValue:
    @pytest.mark.parametrize("program, shown", [("10 {1 2} -", "1 2"), ("{1 2} 10 -", "1 2"), ("{1 2} {3 4} -", "3 4"), ("{1 2} echo", "1 2"), ("{1 2} sqrt", "1 2")])
    def test_a_block_leaving_two_values_is_an_error_that_shows_them(self, program, shown):
        with pytest.raises(ResultCountError, match=f"left 2 values on the stack \\({shown}\\); an argument must be one value"):
            run(program)

    def test_one_value_still_works_and_a_string_is_unwrapped(self):
        assert run('{1 2 +} 3 * {"ab"} upper') == [9, "AB"]


class TestFilesAreUtf8:
    def test_a_byte_order_mark_is_skipped(self, tmp_path):
        path = tmp_path / "bom.stk"
        path.write_bytes("﻿1 2 + :x set\n".encode())
        stacker = Stacker()
        ScriptMode(stacker).run(str(path))
        stacker.process_expression("x")
        assert list(stacker.stack) == [3]

    def test_a_script_that_is_not_utf8_names_the_line(self, tmp_path):
        path = tmp_path / "bad.stk"
        path.write_bytes(b'"ok"\n1 2 +\n# \xff\n')
        with pytest.raises(ScriptReadError, match="is not UTF-8 text at line 3"):
            from stacker.include.stk_file_read import readtxt

            readtxt(path)

    def test_file_words_write_and_read_utf8(self, tmp_path):
        path = tmp_path / "w.txt"
        run(f'"\\u00e9\\u3042" "{path}" write-to-file')
        assert path.read_bytes() == "éあ".encode()
        assert run(f'"{path}" read-from-file') == ["éあ"]


class TestTooDeepToShow:
    def test_a_deep_linked_list_is_reported_by_name(self):
        with pytest.raises(StackerRuntimeError, match="cannot show a value nested this deep"):
            run("[] :xs set 1 3000 :i {i xs 2 listn :xs set} do xs str")

    def test_the_value_itself_is_still_usable(self):
        assert run("[] :xs set 1 3000 :i {i xs 2 listn :xs set} do xs 0 at") == [3000]


class TestSignedSpecialFloats:
    def test_minus_inf_is_a_number_everywhere(self):
        values = run("-inf +inf {-inf} eval [inf -inf]")
        assert values[0] == -math.inf and values[1] == math.inf and values[2] == -math.inf
        assert values[3] == [math.inf, -math.inf]

    def test_minus_nan_is_nan(self):
        assert math.isnan(run("-nan")[0])

    def test_a_name_starting_like_one_is_still_a_name(self):
        assert run("5 :infx set infx") == [5]
