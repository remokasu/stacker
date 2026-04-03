import unittest

from stacker.stacker import Stacker


class TestCond(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_cond_first_match(self):
        self.stacker.eval("5 $x set")
        ans = self.stacker.eval("{x 0 >} {\"positive\"} {x 0 <} {\"negative\"} {true} {\"zero\"} 3 cond")
        self.assertEqual(ans[-1], "positive")

    def test_cond_second_match(self):
        self.stacker.eval("-3 $x set")
        ans = self.stacker.eval("{x 0 >} {\"positive\"} {x 0 <} {\"negative\"} {true} {\"zero\"} 3 cond")
        self.assertEqual(ans[-1], "negative")

    def test_cond_last_match(self):
        self.stacker.eval("0 $x set")
        ans = self.stacker.eval("{x 0 >} {\"positive\"} {x 0 <} {\"negative\"} {true} {\"zero\"} 3 cond")
        self.assertEqual(ans[-1], "zero")

    def test_cond_stops_at_first_match(self):
        ans = self.stacker.eval("{true} {1} {true} {2} {true} {3} 3 cond")
        self.assertEqual(ans[-1], 1)

    def test_cond_no_match(self):
        ans = self.stacker.eval("{false} {1} {false} {2} 2 cond")
        self.assertEqual(len(ans), 0)

    def test_cond_single_pair(self):
        ans = self.stacker.eval("{true} {42} 1 cond")
        self.assertEqual(ans[-1], 42)

    def test_cond_with_computation(self):
        self.stacker.eval("7 $n set")
        ans = self.stacker.eval("{n 2 % 0 ==} {\"even\"} {true} {\"odd\"} 2 cond")
        self.assertEqual(ans[-1], "odd")

    def test_cond_result_is_expression(self):
        self.stacker.eval("3 $n set")
        ans = self.stacker.eval("{n 0 >} {n 2 *} {true} {0} 2 cond")
        self.assertEqual(ans[-1], 6)
