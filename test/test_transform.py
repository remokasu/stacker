import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    ############################
    # enumerate
    ############################
    def test_enumerate_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} enumerate list")
        self.assertEqual(ans[-1], [(0, 1), (1, 2), (2, 3)])

    def test_enumerate_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] enumerate")
        self.assertEqual(ans[-1], [(0, 1), (1, 2), (2, 3)])

    def test_enumerate_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) enumerate")
        self.assertEqual(ans[-1], ((0, 1), (1, 2), (2, 3)))

    ############################
    # sorted
    ############################
    def test_sorted_block(self):
        stacker = Stacker()
        ans = stacker.eval("{3 1 2} sorted list")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_sorted_list(self):
        stacker = Stacker()
        ans = stacker.eval("[3 1 2] sorted")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_sorted_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(3 1 2) sorted")
        self.assertEqual(ans[-1], (1, 2, 3))

    ############################
    # reversed
    ############################
    def test_reversed_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} reversed list")
        self.assertEqual(ans[-1], [3, 2, 1])

    def test_reversed_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] reversed")
        self.assertEqual(ans[-1], [3, 2, 1])

    def test_reversed_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) reversed")
        self.assertEqual(ans[-1], (3, 2, 1))

    ############################
    # list
    ############################
    def test_list_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} list")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_list_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] list")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_list_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) list")
        self.assertEqual(ans[-1], [1, 2, 3])

    ############################
    # tuple
    ############################
    def test_tuple_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} tuple")
        self.assertEqual(ans[-1], (1, 2, 3))

    def test_tuple_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] tuple")
        self.assertEqual(ans[-1], (1, 2, 3))

    def test_tuple_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) tuple")
        self.assertEqual(ans[-1], (1, 2, 3))
