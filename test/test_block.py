import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def test_enmpty_block(self):
        stacker = Stacker()
        expr = "{}"
        try:
            stacker.process_expression(expr)
            assert True
        except Exception as e:
            assert False, e

        assert stacker.stack[0].tokens == []

    def test_block(self):
        stacker = Stacker()
        expr = "{0}"
        ans = stacker.eval(expr)
        assert ans[-1].tokens == [0]

    def test_block2(self):
        stacker = Stacker()
        expr = "{0 1 +}"
        ans = stacker.eval(expr)
        assert ans[-1].tokens == [0, 1, "+"]
