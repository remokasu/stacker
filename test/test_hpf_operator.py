import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    ############################
    # map
    ############################
    def test_map_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} {2 *} map list")
        self.assertEqual(ans[-1], [2, 4, 6])

    def test_map_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] {2 *} map")
        self.assertEqual(ans[-1], [2, 4, 6])

    def test_map_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) {2 *} map")
        self.assertEqual(ans[-1], (2, 4, 6))

    ############################
    # filter
    ############################
    def test_filter_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} {2 >} filter list")
        self.assertEqual(ans[-1], [3])

    def test_filter_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] {2 >} filter")
        self.assertEqual(ans[-1], [3])

    def test_filter_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) {2 >} filter")
        self.assertEqual(ans[-1], (3,))

    ############################
    # zip
    ############################
    def test_zip_block(self):
        stacker = Stacker()
        ans = stacker.eval("{1 2 3} {4 5 6} zip list")
        self.assertEqual(ans[-1], [(1, 4), (2, 5), (3, 6)])

    def test_zip_list(self):
        stacker = Stacker()
        ans = stacker.eval("[1 2 3] [4 5 6] zip")
        self.assertEqual(ans[-1], [(1, 4), (2, 5), (3, 6)])

    def test_zip_tuple(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 3) (4 5 6) zip")
        self.assertEqual(ans[-1], ((1, 4), (2, 5), (3, 6)))
