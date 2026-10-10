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

    # REMOVED: test_any_tuple_* - () now creates code blocks, not tuples

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

    # REMOVED: test_all_tuple_* - () now creates code blocks, not tuples

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

    # REMOVED: test_sum_tuple - () now creates code blocks, not tuples

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

    # REMOVED: test_max_tuple - () now creates code blocks, not tuples

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

    # REMOVED: test_min_tuple - () now creates code blocks, not tuples

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

    # REMOVED: test_len_tuple - () now creates code blocks, not tuples


class TestUndefinedNameArgument(unittest.TestCase):
    """An undefined name used to be treated as a one-character string
    (`q len` answered 1); it is an error, as for every other operator."""

    def test_undefined_name_raises(self):
        from stacker.error import UndefinedSymbolError

        for operator in ("len", "sum", "max", "min", "any", "all"):
            with self.subTest(operator=operator):
                with self.assertRaises(UndefinedSymbolError):
                    Stacker().eval(f"q {operator}")

    def test_defined_name_still_works(self):
        stacker = Stacker()
        self.assertEqual(stacker.eval("[1 2 3] q set q len").pop(), 3)
