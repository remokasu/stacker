import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_map_with_lambda(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3 4 5] {x} {x x *} lambda map list")
        self.assertEqual(ans[-1], [1, 4, 9, 16, 25])

    def test_filter_with_lambda(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3 4 5 6] {x} {x 2 % 0 ==} lambda filter list")
        self.assertEqual(ans[-1], [2, 4, 6])

    def test_map_then_filter(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            "[1 2 3 4 5] {x} {x 2 *} lambda map list {x} {x 5 >} lambda filter list"
        )
        self.assertEqual(ans[-1], [6, 8, 10])

    def test_filter_then_map(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            "[1 2 3 4 5] {x} {x 2 % 0 ==} lambda filter list {x} {x x *} lambda map list"
        )
        self.assertEqual(ans[-1], [4, 16])

    def test_reduce_sum(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3 4 5] 0 acc x {acc x +} reduce")
        self.assertEqual(ans[-1], 15)

    def test_reduce_product(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3 4 5] 1 acc x {acc x *} reduce")
        self.assertEqual(ans[-1], 120)

    def test_map_empty_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[] {x} {x 2 *} lambda map list")
        self.assertEqual(ans[-1], [])

    def test_filter_empty_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[] {x} {x 0 >} lambda filter list")
        self.assertEqual(ans[-1], [])

    def test_filter_all_excluded(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] {x} {x 10 >} lambda filter list")
        self.assertEqual(ans[-1], [])

    def test_zip_basic(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] ['a' 'b' 'c'] zip list")
        self.assertEqual(ans[-1], [(1, "a"), (2, "b"), (3, "c")])

    def test_fold_alias(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3 4 5] 0 acc x {acc x +} fold")
        self.assertEqual(ans[-1], 15)
