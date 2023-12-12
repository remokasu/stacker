import unittest

from stacker.stacker import Stacker


class TestImportStacker(unittest.TestCase):
    def test_include(self):
        filename = "test/src_test/test.stk"
        stacker = Stacker()
        stacker.stack.clear()
        stacker.process_expression(f"'{filename}' include")
        stacker.process_expression(f"5 increment")
        self.assertEqual(stacker.stack[-1], 6)
