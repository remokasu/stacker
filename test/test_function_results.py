"""A function or a lambda pushes every value its body leaves; `map`, `filter`,
`reduce` and `fold` need exactly one value per element."""

import pytest

from stacker import Stacker
from stacker.error import NoValueProducedError, ResultCountError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


class TestFunctionResults:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{} {1 2 3} :f defun f", [1, 2, 3]),
            ("{} {} :f defun f", []),
            ("{a b} {b a} :swap2 defun 1 2 swap2", [2, 1]),
            ("{n} {n 0 > {n 1 - h n} if} :h defun 3 h", [1, 2, 3]),
            ("{} {1 2} :two defun {} {two two} :four defun four", [1, 2, 1, 2]),
            ("{} {1 2} :two defun two +", [3]),
            ("{} {[1 2]} :f defun f", [[1, 2]]),
            ("{n} {n 1 <= {1} {n n 1 - fact *} ifelse} :fact defun 5 fact", [120]),
            ("{} {1 2} :f defun :f eval", [1, 2]),
            ("{} {1 2} :f defun {f} eval", [1, 2]),
            ("{x} {x x} :twice defun [3] :twice apply", [3, 3]),
            ("{x y} {x y + 5} :g defun 3 4 5 g", [3, 9, 5]),
        ],
    )
    def test_a_function_pushes_every_value_its_body_leaves(self, program, expected):
        assert run(program) == expected

    def test_a_body_that_prints_and_leaves_nothing_pushes_nothing(self, capsys):
        assert run('{} {"x" echo} :f defun f') == []
        assert capsys.readouterr().out == "x\n"

    def test_a_body_left_by_break_pushes_nothing(self):
        assert run("{} {1 2 3 break} :f defun 1 3 :i {f} do") == []

    def test_a_body_left_by_an_error_pushes_nothing(self, capsys):
        assert run('{} {1 2 0 /} :f defun {f} {"e" echo} iferror') == []
        assert capsys.readouterr().out == "e\n"

    def test_the_values_are_pushed_in_order_onto_the_callers_stack(self):
        assert run("{} {1 2 3} :f defun 0 f 4") == [0, 1, 2, 3, 4]


class TestLambdaResults:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{} {1 2 3} lambda eval", [1, 2, 3]),
            ("5 {x} {x x} lambda eval", [5, 5]),
            ("[3] {x} {x x} lambda apply", [3, 3]),
            ("{} {} lambda eval", []),
            ("{n} {{x} {x n +} lambda} :adder defun 10 adder :add10 set 5 add10 eval", [15]),
        ],
    )
    def test_a_lambda_pushes_every_value_its_body_leaves(self, program, expected):
        assert run(program) == expected

    def test_results_do_not_accumulate_across_calls(self):
        assert run("{x} {x x} lambda :d set 5 d eval 3 d eval 9 d eval") == [5, 5, 3, 3, 9, 9]


class TestOneValueContexts:
    @pytest.mark.parametrize(
        "program",
        [
            "{x} {x x} :twice defun [1 2] :twice map",
            "{x} {x x} :twice defun [1 2] {twice} map",
            "[1 2] {x} {x x} lambda map",
            "[1 2] {dup} map",
            "[1 2 3 4] {x} {x 2 % 0 == x} lambda filter",
            "[1 2] {dup} filter",
            "{a b} {a b + 0} :plus0 defun [1 2 3] 0 :acc :x {acc x plus0} reduce",
            "[1 2 3] 0 :acc :x {acc x + dup} reduce",
            "[1 2 3] 0 :acc :x {acc x + dup} fold",
        ],
    )
    def test_more_than_one_value_per_element_is_an_error(self, program):
        with pytest.raises(ResultCountError) as info:
            run(program)
        assert "but it left 2" in str(info.value)

    def test_the_error_names_the_word_and_the_function(self):
        with pytest.raises(ResultCountError) as info:
            run("{x} {x x} :twice defun [1 2] :twice map")
        assert "`map` needs one value from `twice`" in str(info.value)

    @pytest.mark.parametrize(
        "program",
        [
            "{x} {x echo} :p defun [1 2] :p map",
            "[1 2] {x} {x echo} lambda map",
            "[1 2] {echo} map",
            "{x} {x echo} :p defun [1 2] :p filter",
            "[1 2] {drop} 0 :acc :x {} reduce",
        ],
    )
    def test_no_value_per_element_is_still_an_error(self, program, capsys):
        with pytest.raises(NoValueProducedError):
            run(program)

    @pytest.mark.parametrize(
        "program, expected",
        [
            ("{x} {x 1 +} :inc defun [1 2] :inc map", [[2, 3]]),
            ("{x} {x 1 +} :inc defun [1 2] {inc} map", [[2, 3]]),
            ("[1 2] {x} {x 1 +} lambda map", [[2, 3]]),
            ("{x} {x x} :twice defun [1 2] {twice 2 listn} map", [[[1, 1], [2, 2]]]),
            ("[1 2] {dup 2 listn} map", [[[1, 1], [2, 2]]]),
            ("[1 2 3] 0 :acc :x {acc x +} reduce", [6]),
        ],
    )
    def test_exactly_one_value_per_element_works(self, program, expected):
        assert run(program) == expected


class TestPythonApi:
    def test_a_function_called_from_python_returns_the_list_of_its_results(self):
        stacker = Stacker()
        stacker.process_expression("{a b} {b a} :swap2 defun {} {} :none defun")
        assert stacker.sfunctions["swap2"]["func"](1, 2) == [2, 1]
        assert stacker.sfunctions["none"]["func"]() == []

    def test_a_lambda_called_from_python_returns_the_list_of_its_results(self):
        stacker = Stacker()
        stacker.process_expression("{x} {x x} lambda :d set")
        assert stacker.variables["d"](7) == [7, 7]

    def test_a_python_function_registered_as_a_word_still_pushes_one_value(self):
        stacker = Stacker()
        stacker.register_sfunction("pair", lambda x: (x, x), 1)
        stacker.process_expression("3 pair")
        assert list(stacker.stack) == [(3, 3)]
