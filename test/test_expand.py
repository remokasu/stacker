import unittest

from stacker.stacker import Stacker


class TestExpand(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_expand_list(self):
        ans = self.stacker.eval("[1 2 3] expand")
        self.assertEqual(list(ans), [1, 2, 3])

    def test_expand_works_on_tuples(self):
        # Tuples cannot be created from stacker syntax anymore, but
        # plugins and the Python API can still push them onto the stack.
        # Regression: `isinstance(x, list or tuple)` only matched lists,
        # so expanding a tuple raised "Cannot expand" (core.py)
        self.stacker.stack.append((1, 2, 3))
        self.stacker.process_expression("expand")
        self.assertEqual(list(self.stacker.stack), [1, 2, 3])

    def test_expand_code_block(self):
        ans = self.stacker.eval("{1 2 3} expand")
        self.assertEqual(list(ans), [1, 2, 3])
