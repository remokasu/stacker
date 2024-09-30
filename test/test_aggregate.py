import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    ############################
    # any
    ############################
    def test_any_block_true_1(self):
        stacker = Stacker()
        ans = stacker.eval("{true true true} any")
        self.assertEqual(ans[-1], True)

    def test_any_block_true_2(self):
        stacker = Stacker()
        ans = stacker.eval("{true false true} any")
        self.assertEqual(ans[-1], True)

    def test_any_list_true_1(self):
        stacker = Stacker()
        ans = stacker.eval("[true true true] any")
        self.assertEqual(ans[-1], True)

    def test_any_list_true_2(self):
        stacker = Stacker()
        ans = stacker.eval("[true false true] any")
        self.assertEqual(ans[-1], True)

    def test_any_list_false(self):
        stacker = Stacker()
        ans = stacker.eval("[false false false] any")
        self.assertEqual(ans[-1], False)

    def test_any_tuple_true_1(self):
        stacker = Stacker()
        ans = stacker.eval("(true true true) any")
        self.assertEqual(ans[-1], True)

    def test_any_tuple_true_2(self):
        stacker = Stacker()
        ans = stacker.eval("(true false true) any")
        self.assertEqual(ans[-1], True)

    def test_any_tuple_false(self):
        stacker = Stacker()
        ans = stacker.eval("(false false false) any")
        self.assertEqual(ans[-1], False)

    ############################
    # all
    ############################
    def test_all_block_true(self):
        stacker = Stacker()
        ans = stacker.eval("{true true true} all")
        self.assertEqual(ans[-1], True)

    def test_all_block_false(self):
        stacker = Stacker()
        ans = stacker.eval("{true false true} all")
        self.assertEqual(ans[-1], False)

    def test_all_list_true(self):
        stacker = Stacker()
        ans = stacker.eval("[true true true] all")
        self.assertEqual(ans[-1], True)

    def test_all_list_false(self):
        stacker = Stacker()
        ans = stacker.eval("[true false true] all")
        self.assertEqual(ans[-1], False)

    def test_all_tuple_true(self):
        stacker = Stacker()
        ans = stacker.eval("(true true true) all")
        self.assertEqual(ans[-1], True)

    def test_all_tuple_false(self):
        stacker = Stacker()
        ans = stacker.eval("(true false true) all")
        self.assertEqual(ans[-1], False)

    ############################
    # sum
    ############################
    def test_sum_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} sum")
        self.assertEqual(ans[-1], 6)

    def test_sum_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] sum")
        self.assertEqual(ans[-1], 6)

    def test_sum_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) sum")
        self.assertEqual(ans[-1], 6)

    ############################
    # max
    ############################
    def test_max_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} max")
        self.assertEqual(ans[-1], 3)

    def test_max_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] max")
        self.assertEqual(ans[-1], 3)

    def test_max_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) max")
        self.assertEqual(ans[-1], 3)

    ############################
    # min
    ############################
    def test_min_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} min")
        self.assertEqual(ans[-1], 1)

    def test_min_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] min")
        self.assertEqual(ans[-1], 1)

    def test_min_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) min")
        self.assertEqual(ans[-1], 1)

    ############################
    # len
    ############################
    def test_len_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} len")
        self.assertEqual(ans[-1], 3)

    def test_len_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] len")
        self.assertEqual(ans[-1], 3)

    def test_len_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) len")
        self.assertEqual(ans[-1], 3)
