"""Tests for SPEC-0004: assignment binds code blocks without evaluating.

`=` / `set` / `global` are binding forms (like defun/lambda/if bodies),
so a code-block value is stored raw and executed only explicitly via
`eval` (or forced by a computing operator). This restores the README's
"code is data" contract, broken since 1.9.0.
"""

import unittest

from stacker.engine.core import StackerCore
from stacker.error import StackUnderflowError
from stacker.stacker import Stacker


class TestLazyBlockBinding(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_open_block_assignment_does_not_crash(self):
        # `{2 *}` needs an outside operand; storing it must not run it
        self.stacker.process_expression("{2 *} double_op =")
        self.assertIsInstance(self.stacker.variables["double_op"], StackerCore)

    def test_stored_block_applies_via_eval(self):
        self.stacker.process_expression("{2 *} double_op =")
        self.stacker.process_expression("5 double_op eval")
        self.assertEqual(self.stacker.stack[-1], 10)

    def test_self_contained_block_stays_a_block(self):
        # Used to store the evaluated result (8) instead of the block
        self.stacker.process_expression("{5 3 +} x =")
        self.assertIsInstance(self.stacker.variables["x"], StackerCore)
        self.stacker.process_expression("x eval")
        self.assertEqual(self.stacker.stack[-1], 8)

    def test_global_binds_blocks_raw_too(self):
        self.stacker.process_expression("{2 *} g global")
        self.assertIsInstance(self.stacker.variables["g"], StackerCore)
        self.stacker.process_expression("7 g eval")
        self.assertEqual(self.stacker.stack[-1], 14)

    def test_variable_to_variable_copy_keeps_block_raw(self):
        self.stacker.process_expression("{2 *} g =")
        self.stacker.process_expression("g f =")
        self.assertIsInstance(self.stacker.variables["f"], StackerCore)
        self.stacker.process_expression("3 f eval")
        self.assertEqual(self.stacker.stack[-1], 6)

    def test_non_block_assignment_unchanged(self):
        self.stacker.process_expression("5 x =")
        self.assertEqual(self.stacker.variables["x"], 5)
        self.stacker.process_expression('"hello" s =')
        self.assertEqual(self.stacker.variables["s"], "hello")
        # Assigning a variable's value resolves the name as before
        self.stacker.process_expression("x y =")
        self.assertEqual(self.stacker.variables["y"], 5)

    def test_computing_operators_still_force_blocks(self):
        # Consistency: `f 3 +` behaves exactly like `{2 *} 3 +` —
        # the computing operator forces the block, which underflows
        self.stacker.process_expression("{2 *} f =")
        with self.assertRaises(StackUnderflowError):
            self.stacker.process_expression("f 3 +")



class TestFunctionArgumentBinding(unittest.TestCase):
    """SPEC-0004 amendment: function/lambda parameters are binding forms
    too — a block argument binds raw, which is what makes user-defined
    higher-order functions possible (the `apply` pattern in
    examples/advanced/eval_examples.stk)."""

    def setUp(self):
        self.stacker = Stacker()

    def test_user_defined_higher_order_function(self):
        self.stacker.process_expression("{op a b} {a b op eval} myapply defun")
        self.stacker.process_expression("{+} 5 3 myapply")
        self.assertEqual(self.stacker.stack[-1], 8)
        self.stacker.process_expression("{*} 5 3 myapply")
        self.assertEqual(self.stacker.stack[-1], 15)

    def test_function_receives_block_raw(self):
        self.stacker.process_expression("{x} {x} identity defun")
        self.stacker.process_expression("{2 *} identity")
        self.assertIsInstance(self.stacker.stack[-1], StackerCore)

    def test_lambda_receives_block_raw(self):
        self.stacker.process_expression("{x} {x} lambda idf set")
        self.stacker.process_expression("{2 *} idf")
        self.assertIsInstance(self.stacker.stack[-1], StackerCore)

    def test_numeric_arguments_unchanged(self):
        self.stacker.process_expression("{x y} {x y +} add2 defun")
        self.stacker.process_expression("3 4 add2")
        self.assertEqual(self.stacker.stack[-1], 7)

if __name__ == "__main__":
    unittest.main()
