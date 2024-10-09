import unittest

from stacker.stacker import Stacker


class TestStacker(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_macro_definition_and_call_1(self):
        self.stacker.stack.clear()
        self.stacker.eval("{4 +} $add defmacro")
        ans = self.stacker.eval("3 add")
        self.assertEqual(ans[-1], 7)
