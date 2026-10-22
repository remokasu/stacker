"""An array or a dictionary is one thing wherever it goes; reading words take it as a list."""

import pytest

from stacker import Stacker
from stacker.error import StackerRuntimeError, StackerTypeError
from stacker.util.disp import plain_text


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestSharing:
    def test_dup_set_arguments_closures_and_list_elements_share_one_array(self):
        assert run("[1 2] array :a set [a 1] :p set 9 a 0 at! p 0 at 0 at") == [9]
        assert run("[1 2] array :a set {x} {9 x 0 at!} :f defun a f a 0 at") == [9]
        assert run("[1 2] array :a set {} {7 a 1 at!} lambda eval a") == [[1, 7]]

    def test_a_block_holds_the_same_array(self):
        assert run("[1 2] array :a set a sub :b set 9 a 0 at! b eval") == [[9, 2]]

    def test_an_included_file_changes_the_includers_array(self, tmp_path):
        lib = tmp_path / "lib.stk"
        lib.write_text("{} {9 shared 0 at!} :poke defun\n", encoding="utf-8")
        assert run("[1 2] array :shared set", f'"{lib}" include', "poke shared") == [[9, 2]]

    def test_a_list_stays_a_value_a_second_array_is_separate(self):
        assert run("[1 2] :l set l array :a set 9 a 0 at! l") == [[1, 2]]


class TestReadingWords:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("[1 2 3] array len", 3),
            ("[3 1 2] array sorted", [1, 2, 3]),
            ("[1 2 3] array reversed", [3, 2, 1]),
            ("[1 2 3] array {2 *} map", [2, 4, 6]),
            ("[1 2 3] array {1 >} filter", [2, 3]),
            ("[1 2 3] array 0 :acc :x {acc x +} reduce", 6),
            ("[1 2 3] array sum", 6),
            ("[1 2 3] array cdr", [2, 3]),
            ("0 [1 2] array cons", [0, 1, 2]),
            ("[1 2] array [3] +", [1, 2, 3]),
            ("[1 2] array list", [1, 2]),
            ("[1 2] array 1 nth nip", 2),
            ("[1 2] array 2 contains", True),
            ("[1 2] array enumerate", [[0, 1], [1, 2]]),
            ("[1 2] array [3 4] zip", [[1, 3], [2, 4]]),
            ('dict :d set 1 d "a" put! d len', 1),
        ],
    )
    def test_reading_words_take_an_array(self, program, expected):
        result = run(program)[-1]
        assert result == expected
        if isinstance(expected, list):
            assert type(result) is list, "a word that makes a new sequence makes a list"

    def test_dolist_and_expand_go_through_an_array(self):
        assert run("[1 2 3] array :x {x} dolist") == [1, 2, 3]
        assert run("[1 2] array expand") == [1, 2]

    @pytest.mark.parametrize("program", ["dict :x {x} dolist", "dict sorted", "dict list", "dict sum", "dict {1} map", "dict car", "dict expand", 'dict "a" contains'])
    def test_a_dictionary_is_not_a_sequence(self, program):
        with pytest.raises(StackerTypeError, match="keys"):
            run(program)

    def test_iteration_goes_through_the_elements_the_array_had_at_the_start(self):
        assert run("[1 2] array :a set a :x {x a append!} dolist a") == [[1, 2, 1, 2]]
        assert run("[1 2 3] array :a set a {drop a pop!} map a") == [[3, 2, 1], []]

    def test_truth(self):
        assert run("[] array {1} {0} ifelse [1] array {1} {0} ifelse dict {1} {0} ifelse") == [0, 1, 0]


class TestEquality:
    def test_a_cyclic_array_equals_itself_but_two_cyclic_ones_are_an_error(self):
        assert run("[1 2] array :a set a a 0 at! a a ==") == [True]
        with pytest.raises(StackerRuntimeError, match="same\\?"):
            run("[1] array :a set a a 0 at! [1] array :b set b b 0 at! a b ==")


class TestDisplay:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("[1 2 3] array", "[1 2 3]"),
            ("[] array", "[]"),
            ('[1 "a" :b null] array', "[1 'a' b null]"),
            ("dict", "{:}"),
            ('dict :d set 1 d "a" put! 2 d :b put! d', "{'a' 1 b 2}"),
            ("[1 2] array dict 2 listn", "[[1 2] {:}]"),
            ("[1 2] array :a set a a 0 at! a", "[[...] 2]"),
            ("dict :d set d d :self put! d", "{self {...}}"),
        ],
    )
    def test_arrays_are_shown_like_lists_and_dicts_in_braces(self, program, expected):
        assert plain_text(run(program)[-1]) == expected

    def test_the_colored_display_tells_an_array_from_a_list(self):
        from stacker.util.disp import disp_colored

        assert disp_colored([[1, 2]]) != disp_colored(run("[1 2] array"))
        assert disp_colored(run("dict")) != disp_colored(run("{}"))

    def test_str_echo_and_format_use_the_same_text(self, capsys):
        assert run("[1 2] array str") == ["[1 2]"]
        assert run('"v={}" [1 2] array format') == ["v=[1 2]"]
        run("[1 2] array echo")
        assert capsys.readouterr().out == "[1 2]\n"

    def test_deep_nesting_is_cut_instead_of_overflowing(self):
        stacker = Stacker()
        stacker.process_expression("dict :head set head :node set 1 10000 :i {dict :n set node n :next put! n node :prev put! n :node set} do")
        text = plain_text(stacker.variables["head"])
        assert "{...}" in text and len(text) < 2000

    def test_the_display_read_back_is_a_list_not_the_array(self):
        assert run('[1 2] array str parse eval array?') == [False]

    def test_python_repr(self):
        from stacker import Array

        a, = run("[1 2] array")
        assert repr(a) == "Array([1, 2])" and isinstance(a, Array) and isinstance(a, list)


class TestReviewFindings:
    def test_an_order_comparison_of_cyclic_arrays_is_a_stacker_error(self):
        with pytest.raises(StackerRuntimeError, match="`<`"):
            run("[] array :a set a a append! [] array :b set b b append! a b <")

    def test_array_of_a_count_that_cannot_be_made(self):
        from stacker.error import ValidationError

        with pytest.raises(ValidationError, match="array-of"):
            run("1000000000000000000000 0 array-of")

    def test_the_display_state_is_restored_after_an_error_inside(self):
        from stacker.util import disp

        class Bad:
            def __str__(self):
                raise RuntimeError("boom")

        from stacker import Array

        with pytest.raises(RuntimeError):
            plain_text(Array([Bad()]))
        assert disp._showing() == []


def test_an_empty_dictionary_is_shown_apart_from_an_empty_block():
    from stacker.util.disp import plain_text

    assert plain_text({}) == "{:}"
    assert plain_text({"k": 1}) == "{'k' 1}"
    stacker = Stacker()
    stacker.process_expression("dict")
    assert plain_text(stacker.stack[0]) == "{:}"
