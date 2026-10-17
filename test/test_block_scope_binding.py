"""A block is bound to the scope it is pushed from, and keeps it.

A lambda made inside a function call remembers that call's variables, not
the latest call's. A `map` / `filter` block runs in the caller's scope, so
what it assigns stays assigned. A variable first set in a loop body
outlives the loop, as it does in `while`, `times` and `loop`.
"""

import pytest

from stacker import Stacker
from stacker.engine.core import StackerCore
from stacker.error import UndefinedSymbolError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


def printed(program: str, capsys) -> list[str]:
    Stacker().process_expression(program)
    return capsys.readouterr().out.splitlines()


class TestClosures:
    def test_two_closures_from_one_function_keep_their_own_scope(self):
        assert run(
            "{n} {{x} {x n +} lambda} :adder defun",
            "10 adder :add10 set 20 adder :add20 set",
            "5 add10 eval 5 add20 eval",
        ) == [15, 25]

    def test_a_lambda_made_in_a_recursive_call_sees_its_own_argument(self, capsys):
        program = """
{n} {
  n 0 > {n 1 - fd drop} if
  1 {x} {x n +} lambda eval echo
  0
} :fd defun
1 fd drop
"""
        assert printed(program, capsys) == ["1", "2"]

    def test_a_lambda_made_in_a_recursive_call_sees_its_own_local(self, capsys):
        program = """
{n} {
  n 100 * :loc set
  n 0 > {n 1 - fc drop} if
  1 {x} {x loc +} lambda eval echo
  0
} :fc defun
1 fc drop
"""
        assert printed(program, capsys) == ["1", "101"]

    def test_a_lambda_evaluated_in_a_loop_body_sees_that_iteration(self, capsys):
        program = """
{n} {
  [10 20] :e {
    n 0 > {n 1 - fb drop} if
    1 {x} {x e +} lambda eval echo
  } dolist
  0
} :fb defun
1 fb drop
"""
        assert printed(program, capsys) == ["11", "21", "11", "11", "21", "21"]

    def test_a_map_block_in_a_recursive_call_sees_its_own_argument(self, capsys):
        program = "{n} {n 0 > {n 1 - fm drop} if [1] {n +} map echo 0} :fm defun 1 fm drop"
        assert printed(program, capsys) == ["[1]", "[2]"]

    def test_a_lambda_in_a_lambda_keeps_its_scope(self):
        assert run(
            "{n} {{x} {x n +} lambda} lambda :adder set",
            "10 adder eval :add10 set 20 adder eval :add20 set",
            "5 add10 eval 5 add20 eval",
        ) == [15, 25]


class TestMapAndFilterBlocks:
    def test_a_map_block_runs_in_the_callers_scope(self):
        assert run("0 :c set [1 2 3] {c 1 + :c set 0} map drop c") == [3]

    def test_a_filter_block_runs_in_the_callers_scope(self):
        assert run("0 :c set [1 2 3] {c 1 + :c set true} filter drop c") == [3]

    def test_a_map_block_is_not_deep_copied(self, monkeypatch):
        def fail(self):
            pytest.fail("map deep-copied the block")

        monkeypatch.setattr(StackerCore, "copy", fail)
        assert run("[1 2 3] {1 +} map") == [[2, 3, 4]]
        assert run("[1 2 3] {2 >} filter") == [[3]]
        assert run("[1 2 3] :neg map") == [[-1, -2, -3]]

    def test_a_map_block_reads_the_callers_variables(self):
        assert run("10 :k set [1 2] {k +} map") == [[11, 12]]


class TestLoopBodyVariables:
    @pytest.mark.parametrize(
        "program, expected",
        [
            ("1 3 :i {i :last set} do last", [3]),
            ("[1 2] :x {x :lastx set} dolist lastx", [2]),
            ("{} {1 3 :i {i :last set} do last} :f defun f", [3]),
            ("1 2 :i {1 2 :j {i j * :p set} do} do p", [4]),
            ("[1 2 3] 0 :acc :x {acc x + :seen set acc x +} reduce drop seen", [6]),
        ],
    )
    def test_a_variable_first_set_in_a_loop_body_outlives_the_loop(self, program, expected):
        assert run(program) == expected

    @pytest.mark.parametrize("program", ["1 3 :i {} do i", "[1 2] :x {} dolist x"])
    def test_the_loop_variable_does_not_outlive_the_loop(self, program):
        with pytest.raises(UndefinedSymbolError):
            run(program)

    def test_a_variable_set_in_a_loop_inside_a_function_stays_local_to_the_function(self):
        with pytest.raises(UndefinedSymbolError):
            run("{} {1 3 :i {i :tmp set} do} :f defun f tmp")

    def test_an_existing_variable_is_updated_in_place(self):
        assert run("0 :s set 1 3 :i {s i + :s set} do s") == [6]
