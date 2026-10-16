import unittest

import pytest

from stacker.error import DropError, NoValueProducedError, StackerSyntaxError
from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_if_1(self):
        # True
        stacker = Stacker()
        expr = "true 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

    def test_if_2(self):
        stacker = Stacker()
        expr = "True 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [123])

    def test_if_3(self):
        stacker = Stacker()
        expr = "-1 :x set {0 x >} {3 5 +} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [8])

        # False

    def test_if_4(self):
        stacker = Stacker()
        expr = "false 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_5(self):
        stacker = Stacker()
        expr = "False 123 if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_6(self):
        stacker = Stacker()
        expr = "-1 :x set {0 x <} {3 5 +} if"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [])

    def test_if_else(self):
        # True
        stacker = Stacker()
        expr = "true 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "True 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [114])

        stacker = Stacker()
        expr = "True {114 514 +} {810 1008 +} ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        stacker = Stacker()
        expr = "-1 :x set 0 x > {114 514 +} {810 1008 +}  ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [628])

        # False
        stacker.stack.clear()
        expr = "false 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker.stack.clear()
        expr = "False 114 514 ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [514])

        stacker = Stacker()
        expr = "False {114 514 +} {810 1008 +} ifelse"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1818])

    def test_if_error(self):
        # error
        stacker = Stacker()
        expr = "{1 +} {99} iferror"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [99])

        # no error
        stacker = Stacker()
        expr = "{1 1 +} {99} iferror"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [2])

    def test_iferror_does_not_catch_break(self):
        # break inside the try block must exit the enclosing loop instead of
        # triggering the catch block. BreakException derives from BaseException
        # precisely so that iferror's except Exception lets it through; if it
        # were ever changed to derive from Exception, the catch block (999)
        # would run and this test would fail.
        stacker = Stacker()
        expr = (
            "0 :s set [1 2 3 4 5] :i"
            " { {i 3 == {break} if s i + :s set} {999 :s set} iferror } dolist s"
        )
        stacker.process_expression(expr)
        self.assertEqual(stacker.stack[-1], 3)



@pytest.mark.parametrize(
    "expression",
    ["{} {1} if", "{} {1} {2} ifelse", "{} {1} 1 cond", "{} {1} while"],
    ids=["if", "ifelse", "cond", "while"],
)
def test_a_condition_block_that_leaves_no_value_is_reported_as_such(expression):
    # It used to be reported as the word itself lacking arguments
    with pytest.raises(NoValueProducedError, match="condition block"):
        Stacker().eval(expression)


def test_an_error_inside_a_condition_block_is_reported_as_it_is():
    with pytest.raises(DropError):
        Stacker().eval("{drop} {1} if")


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("7 {} {1} if", [1]), ("0 {} {1} if", []), ("7 {0 >} {1} if", [1])],
    ids=["empty-block-truthy-below", "empty-block-falsy-below", "block-consumes-below"],
)
def test_a_condition_block_runs_on_the_current_stack(expression, expected):
    # The block is a function from the stack to the stack, and `{}` is the
    # identity: what is on top after it has run is the condition
    assert list(Stacker().eval(expression)) == expected


def test_while_takes_a_condition_block_only():
    # A plain value would test the same every time
    with pytest.raises(StackerSyntaxError, match="`while` expects a condition block"):
        Stacker().eval("3 {1} while")


def test_cond_skips_false_pairs_and_runs_the_first_true_one():
    assert list(Stacker().eval("0 {} {5} {1} {9} 2 cond")) == [9]


def test_while_runs_its_body_until_the_condition_block_is_false():
    assert list(Stacker().eval("3 {dup 0 >} {1 -} while")) == [0]
