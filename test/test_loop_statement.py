import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_times(self):
        stacker = Stacker()
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1])
        expr = "{dup ++} 3 times"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])

    def test_do(self):
        stacker = Stacker()
        expr = "0 :s set 1 100 :i {s i 2 ^ + :s set} do s"
        ans = stacker.eval(expr)
        self.assertEqual(ans[-1], 338350)


import pytest

from stacker.error import StackerSyntaxError


@pytest.mark.parametrize("expression", ['0 {"x" echo} times', '{1} "3" times', "{1} [3] times"])
def test_times_reports_a_count_that_is_not_a_number(expression):
    # The block and the count written the wrong way round used to leak a
    # Python TypeError. (A block on top is still evaluated once as the
    # "count", as every block consumed by a word is; a symbol on top is a
    # type error, as everywhere a value is needed.)
    with pytest.raises(StackerSyntaxError, match="`times` expects a number of repetitions"):
        Stacker().eval(expression)


@pytest.mark.parametrize(("expression", "expected"), [("{1} 2.5 times", [1, 1, 1]), ("{1} {3} times", [1, 1, 1]), ("{1} 0 times", [])])
def test_times_still_takes_any_number_as_the_count(expression, expected):
    assert list(Stacker().eval(expression)) == expected
