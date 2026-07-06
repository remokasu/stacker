import unittest

from stacker.stacker import Stacker


class TestListPrimitives(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    # car
    def test_car_basic(self):
        ans = self.stacker.eval("[1 2 3] car")
        self.assertEqual(ans[-1], 1)

    def test_car_single(self):
        ans = self.stacker.eval("[42] car")
        self.assertEqual(ans[-1], 42)

    def test_car_empty_raises(self):
        with self.assertRaises(Exception):
            self.stacker.eval("[] car")

    # cdr
    def test_cdr_basic(self):
        ans = self.stacker.eval("[1 2 3] cdr")
        self.assertEqual(ans[-1], [2, 3])

    def test_cdr_single(self):
        ans = self.stacker.eval("[1] cdr")
        self.assertEqual(ans[-1], [])

    def test_cdr_empty_raises(self):
        with self.assertRaises(Exception):
            self.stacker.eval("[] cdr")

    # cons
    def test_cons_basic(self):
        ans = self.stacker.eval("1 [2 3] cons")
        self.assertEqual(ans[-1], [1, 2, 3])

    def test_cons_empty_list(self):
        ans = self.stacker.eval("1 [] cons")
        self.assertEqual(ans[-1], [1])

    # null?
    def test_null_empty_list(self):
        ans = self.stacker.eval("[] null?")
        self.assertEqual(ans[-1], True)

    def test_null_nonempty_list(self):
        ans = self.stacker.eval("[1 2] null?")
        self.assertEqual(ans[-1], False)

    def test_null_empty_tuple(self):
        ans = self.stacker.eval("[] null?")
        self.assertEqual(ans[-1], True)

    # pair?
    def test_pair_nonempty(self):
        ans = self.stacker.eval("[1 2 3] pair?")
        self.assertEqual(ans[-1], True)

    def test_pair_empty(self):
        ans = self.stacker.eval("[] pair?")
        self.assertEqual(ans[-1], False)

    def test_pair_single(self):
        ans = self.stacker.eval("[1] pair?")
        self.assertEqual(ans[-1], True)

    # car/cdr の組み合わせ
    def test_car_cdr_chain(self):
        ans = self.stacker.eval("[1 2 3] cdr car")
        self.assertEqual(ans[-1], 2)

    # cons で再構築
    def test_cons_rebuild(self):
        self.stacker.eval("[1 2 3] $xs set")
        ans = self.stacker.eval("xs car xs cdr cons")
        self.assertEqual(ans[-1], [1, 2, 3])


class TestIdentifierNaming(unittest.TestCase):
    """Test Scheme-style identifier names with ?, !, -"""

    def setUp(self):
        self.stacker = Stacker()

    def test_question_mark_in_defun(self):
        self.stacker.eval("{x} {x 0 >} $positive? defun")
        ans = self.stacker.eval("5 positive?")
        self.assertEqual(ans[-1], True)

    def test_question_mark_false(self):
        self.stacker.eval("{x} {x 0 >} $positive? defun")
        ans = self.stacker.eval("-1 positive?")
        self.assertEqual(ans[-1], False)

    def test_hyphen_in_name(self):
        self.stacker.eval("{x} {x 1 +} $add-one defun")
        ans = self.stacker.eval("5 add-one")
        self.assertEqual(ans[-1], 6)

    def test_bang_in_name(self):
        self.stacker.eval("42 $my-val! set")
        ans = self.stacker.eval("my-val!")
        self.assertEqual(ans[-1], 42)
