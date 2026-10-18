"""`collect` runs a block on an empty stack and pushes what it left as one list."""

import pytest

from stacker import Stacker
from stacker.error import StackerTypeError


def run(*lines: str) -> list[object]:
    stacker = Stacker()
    for line in lines:
        stacker.process_expression(line)
    return list(stacker.stack)


@pytest.mark.parametrize(
    "program, expected",
    [
        ("{1 2 3} collect", [[1, 2, 3]]),
        ("{} collect", [[]]),
        ("{8 5 frac 0} collect", [[run("8 5 frac")[0], 0]]),
        ("{0 3 :i {i i *} do} collect", [[0, 1, 4, 9]]),
        ('{"a" :b 1} collect', [["a", run(":b")[0], 1]]),
        ("{{1 2}} collect", [[run("{1 2}")[0]]]),
    ],
)
def test_collect_makes_a_list_of_everything_the_block_leaves(program, expected):
    assert run(program) == expected


def test_the_block_runs_in_the_callers_scope():
    assert run("5 :n set {n n 1 +} collect") == [[5, 6]]
    assert run("{7 :made set 1} collect made") == [[1], 7]


def test_the_block_does_not_see_the_callers_stack():
    with pytest.raises(Exception, match="requires"):
        run("1 2 {+} collect")


def test_values_below_stay_where_they_are():
    assert run("9 {1 2} collect") == [9, [1, 2]]


def test_collect_then_array():
    a, = run("{1 2} collect array")
    from stacker import Array

    assert isinstance(a, Array) and a == [1, 2]


def test_a_lambda_or_a_symbol_is_run_too():
    assert run("{} {1 2} lambda collect") == [[1, 2]]
    assert run("{} {3 4} :f defun :f collect") == [[3, 4]]


@pytest.mark.parametrize("program", ["5 collect", '"1 2" collect', "[1 2] collect"])
def test_anything_else_is_a_type_error(program):
    with pytest.raises(StackerTypeError, match="`collect`"):
        run(program)
