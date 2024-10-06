import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_times(self):
        stacker = Stacker()
        stacker.push(1)
        self.assertEqual(list(stacker.stack), [1])
        expr = "{dup ++} 3 times"
        stacker.process_expression(expr)
        self.assertEqual(list(stacker.stack), [1, 2, 3, 4])

    def test_do(self):
        stacker = Stacker()
        expr = "0 $s set 1 100 $i {s i 2 ^ + $s set} do s"
        ans = stacker.eval(expr)
        self.assertEqual(ans[-1], 338350)
