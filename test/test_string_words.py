"""`split` gives a list; a string word given the wrong type names itself."""

import pytest

from stacker import Stacker
from stacker.error import StackerTypeError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestSplit:
    def test_split_pushes_one_list(self):
        assert run('"a,b,c" "," split') == [["a", "b", "c"]]

    def test_the_parts_are_strings(self, capsys):
        run('"a,b,c" "," split :x {x echo} dolist')
        assert capsys.readouterr().out == "a\nb\nc\n"

    def test_len_counts_the_parts(self):
        assert run('"a,bb,c" "," split len')[-1] == 3

    def test_expand_gives_the_parts_one_by_one(self):
        assert run('"a,b" "," split expand') == ["a", "b"]


class TestTypeErrors:
    @pytest.mark.parametrize(
        "program, word",
        [
            ("5 upper", "upper"),
            ("5 lower", "lower"),
            ("5 title", "title"),
            ("5 strip", "strip"),
            ("5 lstrip", "lstrip"),
            ("5 rstrip", "rstrip"),
            ("[1 2 3] 2 search", "search"),
            ('"abc" 1 search', "search"),
            ('[1 2] "a" "b" replace', "replace"),
            ('"ab" 1 "b" replace', "replace"),
            ("5 2 format", "format"),
            ('[1 2] "," join', "join"),
            ('5 "," join', "join"),
            ('["a"] 1 join', "join"),
            ("5 0 nth", "nth"),
            ('[1 2] "a" nth', "nth"),
            ("{x} {x 0 nth} :f defun 5 f", "nth"),
        ],
    )
    def test_the_error_names_the_word(self, program, word):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert f"`{word}`" in str(info.value)

    def test_the_value_is_shown_like_the_stack(self):
        with pytest.raises(StackerTypeError) as info:
            run("[1 2 3] 2 search")
        assert "[1 2 3]" in str(info.value)

    def test_join_on_numbers_says_to_make_them_strings_first(self):
        with pytest.raises(StackerTypeError) as info:
            run('[1 2] "," join')
        assert "str" in str(info.value)

    @pytest.mark.parametrize("program", [":x upper", '"a" :x split', ":x 1 nth", "[1 2] :x nth", '"," :x join'])
    def test_a_symbol_is_still_reported_as_a_symbol(self, program):
        with pytest.raises(StackerTypeError) as info:
            run(program)
        assert "cannot use the symbol `x`" in str(info.value)
