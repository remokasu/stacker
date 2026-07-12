import unittest

from stacker.error import NoValueProducedError
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

    def test_map_block_with_no_result_raises_clear_error(self):
        # Regression: a block producing no stack value crashed with an
        # internal TypeError. HOF blocks must leave a value;
        # the error should name the operator and point to dolist.
        self.stacker.stack.clear()
        with self.assertRaises(NoValueProducedError) as ctx:
            self.stacker.eval("[1 2] {drop} map")
        self.assertIn("map", str(ctx.exception))
        self.assertIn("dolist", str(ctx.exception))

    def test_filter_block_with_no_result_raises_clear_error(self):
        self.stacker.stack.clear()
        with self.assertRaises(NoValueProducedError) as ctx:
            self.stacker.eval("[1 2 3] {drop} filter")
        self.assertIn("filter", str(ctx.exception))

    def test_reduce_block_with_no_result_raises_clear_error(self):
        # Regression: reduce_func returned None, causing an unrelated
        # TypeError (`None 2 +`) on the next fold step
        self.stacker.stack.clear()
        with self.assertRaises(NoValueProducedError) as ctx:
            self.stacker.eval("[1 2 3] 0 acc x {acc x + drop} reduce")
        self.assertIn("reduce", str(ctx.exception))

    def test_fold_block_with_no_result_raises_clear_error(self):
        self.stacker.stack.clear()
        with self.assertRaises(NoValueProducedError) as ctx:
            self.stacker.eval("[1 2 3] 0 acc x {acc x + drop} fold")
        self.assertIn("fold", str(ctx.exception))

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
