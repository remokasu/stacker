"""Control-flow words must evaluate their blocks on the stack they were invoked on.

``Stacker.eval()`` creates a fresh stack when none is given (the CLI ``-e``
mode relies on this). The control-flow words used to evaluate their blocks on
the interpreter's own ``self.stack`` instead, so values pushed before the word
were invisible to the block and results leaked into ``self.stack``.
"""

import pytest

from stacker.stacker import Stacker


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("3 true {1 -} if", [2]),
        ("3 false {1 -} if", [3]),
        ("3 true {1 -} {1 +} ifelse", [2]),
        ("3 false {1 -} {1 +} ifelse", [4]),
        ("3 {1 -} {99} iferror", [2]),
        ("{1 0 /} {99} iferror", [99]),
        ("5 {dup ++} 3 times", [5, 6, 7, 8]),
        ("3 {dup 0 >} {1 -} while", [0]),
        ("0 1 3 :i {i +} do", [6]),
        ("0 [1 2 3] :x {x +} dolist", [6]),
        ("3 {dup 0 >} {1 -} 1 cond", [2]),
    ],
)
def test_control_flow_uses_evaluation_stack(expression, expected):
    stacker = Stacker()
    result = stacker.eval(expression)
    assert list(result) == expected
    # Nothing may leak into the interpreter's own stack.
    assert list(stacker.stack) == []


def test_times_accepts_a_non_integer_count():
    # 2.5 means "while count < 2.5", i.e. three iterations, as before 1.15.0.
    assert list(Stacker().eval("0 {1 +} 2.5 times")) == [3]


def test_times_with_non_block_pushes_value_each_iteration():
    stacker = Stacker()
    assert list(stacker.eval("7 3 times")) == [7, 7, 7]


def test_do_restores_scope_when_body_raises():
    stacker = Stacker()
    with pytest.raises(ZeroDivisionError):
        stacker.eval("1 3 :i {i 0 /} do")
    # The loop's child scope must not remain installed after the error.
    assert "i" not in stacker.variables
