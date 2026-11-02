import logging
import unittest

import pytest

from stacker.error import StackerSyntaxError
from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_function_definition_and_call_1(self):
        self.stacker.stack.clear()
        self.stacker.eval("{x} {x 2 + x 3 * +} :f defun")
        ans = self.stacker.eval("4 f")
        self.assertEqual(ans[-1], 18)

    def test_function_definition_and_call_2(self):
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} :test_sum defun")
        ans = self.stacker.eval("[1 2 3] test_sum")
        self.assertEqual(ans[-1], 6)

    def test_function_definition_and_call_3(self):
        # 1.13.0: arguments bind blocks raw, so pass the
        # list itself; previously `{[4 5 6]}` worked only because the
        # block was force-evaluated at call time
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} :test_sum defun")
        ans = self.stacker.eval("[4 5 6] test_sum")
        self.assertEqual(ans[-1], 15)

    def test_function_definition_and_call_4(self):
        # 1.13.0: a numeric block passed raw reaches the
        # body, where `sum` consumes its tokens natively
        self.stacker.stack.clear()
        self.stacker.eval("{xs} {xs sum} :test_sum defun")
        ans = self.stacker.eval("(7 8 9) test_sum")
        self.assertEqual(ans[-1], 24)


@pytest.mark.parametrize("body", ["5", '"abc"', "[1 2]", ":sym", "{x} {x} lambda"])
def test_defun_refuses_a_body_that_is_not_a_code_block(body):
    stacker = Stacker()
    with pytest.raises(StackerSyntaxError, match="`defun` expects a code block as the function body, got "):
        stacker.eval(f"{{x}} {body} :f defun")
    assert "f" not in stacker.sfunctions


@pytest.mark.parametrize("program", ["{x} 5 :dup defun", "5 {x} :dup defun"])
def test_a_definition_with_a_bad_part_is_refused_before_the_redefinition_warning(program, caplog):
    stacker = Stacker()
    with caplog.at_level(logging.WARNING, logger="stacker"), pytest.raises(StackerSyntaxError):
        stacker.eval(program)
    assert caplog.records == []


def test_try_sees_the_refused_body_as_a_syntax_error():
    stacker = Stacker()
    assert list(stacker.eval('{{x} 5 :f defun} {"kind" get} try')) == ["StackerSyntaxError"]
