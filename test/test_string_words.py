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


class TestSliceAndSubseq:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('"hello" 1 3 slice', "el"),
            ('"hello" -3 -1 slice', "ll"),
            ('"hello" 3 1 slice', ""),
            ('"hello" 0 99 slice', "hello"),
            ("[1 2 3 4] 1 3 slice", [2, 3]),
            ("[1 2 3] array 0 5 slice", [1, 2, 3]),
            ('"hello" 1 3 subseq', "el"),
        ],
    )
    def test_slice_cuts_a_sequence(self, program, expected):
        assert run(program) == [expected]

    def test_slice_of_an_array_is_a_new_array(self):
        assert run("[1 2 3] array :a set a 0 2 slice :b set 9 b append! a b array? b") == [[1, 2, 3], True, [1, 2, 9]]

    @pytest.mark.parametrize(
        "program, text",
        [
            ('"hello" 1.0 3 slice', "`slice` expects an integer, got 1.0"),
            ("dict 0 1 slice", "`slice` expects a list, an array or a string"),
            ("[1 2] 0 1 subseq", "`subseq` expects a string"),
        ],
    )
    def test_slice_names_itself(self, program, text):
        with pytest.raises(StackerTypeError, match=text.replace("`", "`").replace("(", "\\(")):
            run(program)


class TestWordsAndAffixes:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ('"  a\\tb\\n c " words', ["a", "b", "c"]),
            ('"" words', []),
            ('"one" words', ["one"]),
            ('"hello" "he" starts-with?', True),
            ('"hello" "lo" starts-with?', False),
            ('"hello" "lo" ends-with?', True),
            ('"hello" "" starts-with?', True),
            ('"hello" "" ends-with?', True),
        ],
    )
    def test_words_and_affixes(self, program, expected):
        assert run(program) == [expected]

    @pytest.mark.parametrize("program, word", [("1 words", "words"), ('"a" 1 starts-with?', "starts-with?"), ("1 \"a\" ends-with?", "ends-with?")])
    def test_a_non_string_is_refused_by_name(self, program, word):
        with pytest.raises(StackerTypeError, match=f"`{word}` expects a string".replace("?", "\\?")):
            run(program)

    def test_an_empty_separator_is_refused_with_the_alternatives(self):
        with pytest.raises(StackerTypeError, match="empty separator"):
            run('"abc" "" split')
