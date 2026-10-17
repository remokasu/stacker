"""A list literal keeps the nesting it is written with, and holds values only."""

import pytest

from stacker import Stacker
from stacker.error import StackerSyntaxError, UndefinedSymbolError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestNesting:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("[[1 2]]", [[1, 2]]),
            ("[[[1 2]]]", [[[1, 2]]]),
            ("[[]]", [[]]),
            ('[["a" "b"]]', [["a", "b"]]),
            ("[[[1 2]] 5]", [[[1, 2]], 5]),
            ("[1 2 3]", [1, 2, 3]),
            ("[1 2; 3 4]", [[1, 2], [3, 4]]),
            # `;` wraps every row, whatever it holds: `[a; b]` is `[[a] [b]]`
            ("[[1 2] [3 4]; [5 6]]", [[[1, 2], [3, 4]], [[5, 6]]]),
            ("[[1 2]; [3 4]]", [[[1, 2]], [[3, 4]]]),
            ("[[1 2; 3 4]; [5 6; 7 8]]", [[[[1, 2], [3, 4]]], [[[5, 6], [7, 8]]]]),
            ("[[1 2; 3 4] [5 6; 7 8]]", [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]),
            # A trailing `;` ends the last row; an empty row is nothing
            ("[1 2 3;]", [[1, 2, 3]]),
            ("[1 2 3; 4 5 6;]", [[1, 2, 3], [4, 5, 6]]),
        ],
    )
    def test_a_literal_keeps_its_depth(self, program, expected):
        assert run(program) == [expected]

    def test_len_counts_the_outer_list(self):
        assert run("[[1 2]] len")[-1] == 1

    def test_inside_a_block(self):
        assert run("{[[1 2]]} eval") == [[[1, 2]]]

    def test_a_trailing_row_separator_means_the_same_in_a_script(self, tmp_path):
        from stacker.runtime.exec_modes import ScriptMode

        script = tmp_path / "m.stk"
        script.write_text("[1 2 3;]\n:m set\n[1 2;\n 3 4;]\n:n set\n", encoding="utf-8")
        stacker = Stacker()
        ScriptMode(stacker).run(str(script))
        assert stacker.variables["m"] == [[1, 2, 3]]
        assert stacker.variables["n"] == [[1, 2], [3, 4]]

    def test_with_a_name(self):
        assert run("[1 2] :v set [[v]]") == [[[[1, 2]]]]


class TestWordsInsideALiteral:
    @pytest.mark.parametrize(
        "program, word",
        [("[1 dup]", "dup"), ("{x} {x} :f defun [1 f]", "f"), ("[len]", "len")],
    )
    def test_a_word_is_a_syntax_error_that_names_the_word(self, program, word):
        with pytest.raises(StackerSyntaxError) as info:
            run(program)
        assert f"`{word}`" in str(info.value)
        assert "listn" in str(info.value)

    def test_an_unknown_name_is_still_undefined(self):
        with pytest.raises(UndefinedSymbolError):
            run("[1 zzz]")

    def test_a_variable_named_like_a_word_is_its_value(self):
        assert run("5 :dup set [dup]") == [[5]]
