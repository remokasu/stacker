"""`loop` is the single looping primitive: repeat a block until `break`."""

import pytest

from stacker.error import StackerSyntaxError
from stacker.stacker import Stacker


def run(expression: str) -> list[object]:
    return list(Stacker().eval(expression))


def test_loop_runs_until_break():
    assert run("0 {1 + dup 10 > {break} if} loop") == [11]


def test_loop_body_sees_values_pushed_before_loop():
    assert run("5 {dup 10 >= {break} if 1 +} loop") == [10]


def test_loop_does_not_consume_recursion_depth():
    # 100,000 iterations would exceed any recursion limit if iterations recursed.
    assert run("0 i = {i 100000 >= {break} if i 1 + i =} loop i") == [100000]


def test_nested_loop_break_exits_innermost_only():
    expression = (
        "0 outer = "
        "{ outer 3 >= {break} if "
        "  0 inner = { inner 2 >= {break} if inner 1 + inner = } loop "
        "  outer 1 + outer = } loop "
        "outer inner"
    )
    assert run(expression) == [3, 2]


def test_break_inside_iferror_try_block_exits_loop():
    # BreakException derives from BaseException, so iferror does not catch it
    # and the catch block must not run.
    assert run('0 { {break} {"caught"} iferror 1 + } loop') == [0]


def test_loop_with_non_block_body_is_a_syntax_error():
    with pytest.raises(StackerSyntaxError):
        run("5 loop")


def test_loop_appears_in_operator_listing():
    stacker = Stacker()
    assert "loop" in stacker.operator_manager.built_in_operators


def test_break_inside_times_inside_loop_exits_only_the_times():
    expression = (
        "0 n = 0 k = "
        "{ k 2 >= {break} if  { n 1 + n = break } 3 times  k 1 + k = } loop "
        "n k"
    )
    # `times` is left on its first pass each round (n += 1), `loop` runs twice.
    assert run(expression) == [2, 2]


def test_loop_accepts_a_round_bracket_body():
    assert run("0 ( 1 + dup 3 > {break} if ) loop") == [4]
