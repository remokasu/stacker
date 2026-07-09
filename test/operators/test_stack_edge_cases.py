"""Regression tests for stack-operator edge cases (audit #8, #9, #13, nip).

All four operators used to mishandle boundaries or duplicate values:
value-based removal picked the wrong element, out-of-range indices
wrapped around silently, the bottom element was unreachable, and raw
IndexError leaked as a misleading stack-underflow message.
"""

import unittest
from collections import deque

from stacker.error import InsertError, PickError, RollError
from stacker.operators.stack import _insert, _nip, _pick, _roll
from stacker.stacker import Stacker


class TestNip(unittest.TestCase):
    def test_nip_removes_positional_element_not_first_duplicate(self):
        # stack[-2] is the second "A" (index 2); value-based removal
        # used to delete the first "A" (index 0) instead
        stack = deque(["A", "B", "A", "X"])
        _nip(stack)
        self.assertEqual(list(stack), ["A", "B", "X"])

    def test_nip_without_duplicates(self):
        stack = deque([1, 2, 3])
        _nip(stack)
        self.assertEqual(list(stack), [1, 3])


class TestInsertBounds(unittest.TestCase):
    def test_insert_within_range(self):
        stack = deque([1, 2, 3, 4])
        _insert(2, 999, stack)
        self.assertEqual(list(stack), [1, 2, 999, 3, 4])

    def test_insert_at_bottom(self):
        stack = deque([1, 2, 3, 4])
        _insert(4, 999, stack)
        self.assertEqual(list(stack), [999, 1, 2, 3, 4])

    def test_insert_beyond_depth_raises(self):
        # Used to wrap around and insert at a bogus position silently
        for index in (5, 6, 8):
            with self.subTest(index=index):
                stack = deque([1, 2, 3, 4])
                with self.assertRaises(InsertError):
                    _insert(index, 999, stack)

    def test_insert_negative_raises(self):
        stack = deque([1, 2, 3, 4])
        with self.assertRaises(InsertError):
            _insert(-1, 999, stack)


class TestPickBounds(unittest.TestCase):
    def test_pick_bottom_element(self):
        # Off-by-one: the bottom element (num == len) was rejected
        stack = deque(["a", "b", "c", "d"])
        _pick(4, stack)
        self.assertEqual(stack[-1], "a")

    def test_pick_top_and_middle(self):
        stack = deque(["a", "b", "c", "d"])
        _pick(1, stack)
        self.assertEqual(stack[-1], "d")

    def test_pick_beyond_depth_raises_pick_error(self):
        stack = deque(["a", "b", "c"])
        with self.assertRaises(PickError):
            _pick(4, stack)

    def test_pick_large_negative_raises_pick_error_not_index_error(self):
        # Used to leak a raw IndexError, which the engine translated
        # into a misleading StackUnderflowError
        stack = deque([1, 2, 3])
        with self.assertRaises(PickError):
            _pick(-99, stack)

    def test_pick_negative_from_bottom(self):
        stack = deque(["a", "b", "c", "d"])
        _pick(-1, stack)  # -1 counts from the bottom
        self.assertEqual(stack[-1], "a")


class TestRollBounds(unittest.TestCase):
    def test_zero_roll_is_a_no_op(self):
        # Forth ROLL semantics; used to rotate the bottom element
        # because stack[-0] aliases stack[0]
        stack = deque([1, 2, 3, 4])
        _roll(0, stack)
        self.assertEqual(list(stack), [1, 2, 3, 4])

    def test_negative_roll_raises(self):
        stack = deque([1, 2, 3, 4])
        with self.assertRaises(RollError):
            _roll(-1, stack)

    def test_roll_regression(self):
        stack = deque([1, 2, 3, 4])
        _roll(3, stack)
        self.assertEqual(list(stack), [1, 3, 4, 2])


class TestOperatorLevelIntegration(unittest.TestCase):
    def test_pick_bottom_via_expression(self):
        stacker = Stacker()
        for v in ["a", "b", "c", "d"]:
            stacker.push(v)
        stacker.process_expression("4 pick")
        self.assertEqual(stacker.stack[-1], "a")


if __name__ == "__main__":
    unittest.main()
