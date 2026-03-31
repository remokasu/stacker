import unittest

from stacker.stacker import Stacker


class TestWhileLoop(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_basic_while(self):
        ans = self.stacker.eval("0 $i set 0 $s set {i 5 <} {s i + $s set i ++ $i set} while s")
        self.assertEqual(ans[-1], 10)

    def test_while_not_executed(self):
        # 条件が最初から false → 一度も実行されない
        ans = self.stacker.eval("0 $s set {false} {s ++ $s set} while s")
        self.assertEqual(ans[-1], 0)

    def test_while_once(self):
        ans = self.stacker.eval("0 $i set {i 1 <} {i ++ $i set} while i")
        self.assertEqual(ans[-1], 1)

    def test_while_with_break(self):
        ans = self.stacker.eval(
            "0 $i set 0 $s set {i 10 <} {i 5 == {break} if s i + $s set i ++ $i set} while s"
        )
        self.assertEqual(ans[-1], 10)

    def test_while_countdown(self):
        ans = self.stacker.eval("10 $n set {n 0 >} {n -- $n set} while n")
        self.assertEqual(ans[-1], 0)

    def test_while_accumulate(self):
        ans = self.stacker.eval("1 $p set 1 $i set {i 6 <=} {p i * $p set i ++ $i set} while p")
        self.assertEqual(ans[-1], 720)

    def test_while_newton_sqrt(self):
        # ニュートン法で sqrt(2) を求める
        ans = self.stacker.eval(
            "1.0 $x set {x x * 2 - abs 0.000001 >} {x 2 x / + 2 / $x set} while x"
        )
        self.assertAlmostEqual(ans[-1], 1.4142135623730951, places=6)

    def test_while_clears_stack(self):
        self.stacker.eval("1 2 3 4 5")
        ans = self.stacker.eval("{depth 0 >} {drop} while depth")
        self.assertEqual(ans[-1], 0)
