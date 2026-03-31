import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_dolist_basic(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("0 $s set [1 2 3 4 5] $i {s i + $s set} dolist s")
        self.assertEqual(ans[-1], 15)

    def test_dolist_with_string_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[] $result set ['a' 'b' 'c'] $item {result [item] + $result set} dolist result")
        self.assertEqual(ans[-1], ["a", "b", "c"])

    def test_dolist_empty_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("0 $s set [] $i {s i + $s set} dolist s")
        self.assertEqual(ans[-1], 0)

    def test_do_break(self):
        # i==5 の時 break → s = 1+2+3+4 = 10
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            "0 $s set 1 10 $i {i 5 == {break} if s i + $s set} do s"
        )
        self.assertEqual(ans[-1], 10)

    def test_dolist_break(self):
        # i==3 の時 break → s = 1+2 = 3
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            "0 $s set [1 2 3 4 5] $i {i 3 == {break} if s i + $s set} dolist s"
        )
        self.assertEqual(ans[-1], 3)

    def test_times_break(self):
        # s が 3 になったら break → s = 3
        self.stacker.stack.clear()
        ans = self.stacker.eval(
            "0 $s set {s ++ $s set s 3 == {break} if} 10 times s"
        )
        self.assertEqual(ans[-1], 3)

    def test_times_nested(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("0 $s set {0 $t set {t ++ $t set} 3 times s t + $s set} 2 times s")
        self.assertEqual(ans[-1], 6)

    def test_do_accumulate(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("1 $p set 1 5 $i {p i * $p set} do p")
        self.assertEqual(ans[-1], 120)

    def test_do_with_list_build(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[] $result set 1 5 $i {result [i] + $result set} do result")
        self.assertEqual(ans[-1], [1, 2, 3, 4, 5])

    def test_times_counter(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("0 $n set {n ++ $n set} 10 times n")
        self.assertEqual(ans[-1], 10)
