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

    # Tests for () code blocks (Lisp-style syntax)
    def test_paren_empty_block(self):
        stacker = Stacker()
        expr = "()"
        try:
            stacker.process_expression(expr)
            assert True
        except Exception as e:
            assert False, e
        assert stacker.stack[0].tokens == []

    def test_paren_code_block(self):
        stacker = Stacker()
        expr = "(1 2 +)"
        ans = stacker.eval(expr)
        # Should create code block, not execute
        # Check that the last element is a code block with the right tokens
        assert hasattr(ans[-1], "tokens")
        assert ans[-1].tokens == [1, 2, "+"]

    def test_paren_block_execution(self):
        stacker = Stacker()
        ans = stacker.eval("(1 2 +) eval")
        # Should execute and return 3
        self.assertEqual(ans[-1], 3)

    def test_paren_with_if_statement(self):
        stacker = Stacker()
        stacker.process_expression("true (10 20 +) if")
        # Should execute block when condition is true
        self.assertEqual(list(stacker.stack), [30])

    def test_paren_lisp_style_function(self):
        stacker = Stacker()
        stacker.eval("(x y) (x y *) $mul defun")
        ans = stacker.eval("3 4 mul")
        self.assertEqual(ans[-1], 12)

    def test_paren_brace_interchangeable(self):
        stacker = Stacker()
        ans1 = stacker.eval("(1 2 +) eval")
        stacker2 = Stacker()
        ans2 = stacker2.eval("{1 2 +} eval")
        # () and {} should behave identically
        self.assertEqual(ans1[-1], ans2[-1])

    def test_bracket_type_display_paren(self):
        """Test that () code blocks display with () not {}"""
        stacker = Stacker()
        ans = stacker.eval("(1 2 +)")
        # Should display as () not {}
        self.assertEqual(str(ans[-1]), "(1 2 +)")

    def test_bracket_type_display_brace(self):
        """Test that {} code blocks display with {} not ()"""
        stacker = Stacker()
        ans = stacker.eval("{3 4 *}")
        # Should display as {} not ()
        self.assertEqual(str(ans[-1]), "{3 4 *}")

    def test_nested_bracket_type_preservation(self):
        """Test that nested blocks preserve their bracket types"""
        stacker = Stacker()

        # Test ({...})
        ans = stacker.eval("({1 2 +})")
        self.assertEqual(str(ans[-1]), "({1 2 +})")

        # Test {(...)}
        stacker.stack.clear()
        ans = stacker.eval("{(5 6 -)}")
        self.assertEqual(str(ans[-1]), "{(5 6 -)}")
