import unittest

from stacker.stacker import Stacker
from stacker.sfunction import StackerFunction
from stacker.syntax.parser import parse_expression

class TestUnit(unittest.TestCase):
    def test_enmpty_block(self):
        stacker = Stacker()
        expr = "{}"
        try:
            stacker.process_expression(expr)
            assert True
        except Exception as e:
            assert False, e
    
        assert stacker.stack[0].get_expression() == ""

    def test_block(self):
        stacker = Stacker()
        expr = "{0}"
        stacker.process_expression(expr)
        assert stacker.stack[0].get_expression() == '0'

    def test_block2(self):
        stacker = Stacker()
        expr = "{0 1 +}"
        stacker.process_expression(expr)
        assert stacker.stack[0].get_expression() == '0 1 +'