"""Semantics-freeze tests for the interpreter core.

These tests pin the *observed* behavior of the current interpreter
(dynamic name resolution, list-literal freshness, error ordering, ...)
so that performance work on the evaluation loop cannot silently change
the language. Expected values were captured by running each program
against the unmodified interpreter; they are frozen observations, not
derived from first principles. If one of these tests fails after an
optimization, the optimization changed the language.
"""

import contextlib
import io
import unittest

from stacker import Stacker
from stacker.engine.data_type import String, UndefinedSymbol
from stacker.error import UndefinedSymbolError


class TestDynamicNameResolution(unittest.TestCase):
    """The meaning of a token may change between loop iterations."""

    def setUp(self):
        self.stacker = Stacker()

    def test_defun_redefined_mid_loop(self):
        # f is redefined on iteration 2; iterations 2..4 must use the new body:
        # r = 0 + f(1)=2, then +20, +30, +40 = 92
        self.stacker.process_expression(
            "{x} {x 1 +} $f defun "
            "0 r set "
            "1 4 $i { i 2 == { {x} {x 10 *} $f defun } if r i f + r set } do "
            "r"
        )
        self.assertEqual(list(self.stacker.stack), [92])

    def test_set_shadows_symbolic_operator(self):
        # Variables are looked up before operators, even for symbolic names.
        self.stacker.process_expression("99 $+ set +")
        self.assertEqual(list(self.stacker.stack), [99])

    def test_set_shadows_symbolic_operator_mid_loop(self):
        # From iteration 2 on, `+` resolves to the variable (99) instead of
        # the addition operator, so `s i +` pushes s, i and 99 and `s set`
        # consumes only the 99 — leaving s, i behind on the stack.
        self.stacker.process_expression(
            "0 s set 1 3 $i { i 2 == { 99 $+ set } if s i + s set } do s"
        )
        self.assertEqual(list(self.stacker.stack), [1, 2, 99, 3, 99])

    def test_macro_redefined_mid_loop(self):
        # m is redefined on iteration 2; r = 0 + 1*2 + 2*3 + 3*3 + 4*3 = 29
        self.stacker.process_expression(
            "{2 *} $m defmacro "
            "0 r set "
            "1 4 $i { i 2 == { {3 *} $m defmacro } if r i m + r set } do "
            "r"
        )
        self.assertEqual(list(self.stacker.stack), [29])

    def test_operator_override_visible_in_defun_body(self):
        # A function body built *before* register_operator must see the
        # override when called *after* it: x 2 + -> 3 * 2 = 6.
        self.stacker.process_expression("{x} {x 2 +} $f defun")
        self.stacker.register_operator("+", lambda a, b: a * b, 2, True, "override")
        self.stacker.process_expression("3 f")
        self.assertEqual(list(self.stacker.stack), [6])

    def test_set_eagerly_evaluates_block_value(self):
        # `set` evaluates a code-block value at assignment time; the variable
        # holds the block's result, not the block itself.
        self.stacker.process_expression("{1 2 +} b set b")
        self.assertEqual(list(self.stacker.stack), [3])


class TestListLiteralFreshness(unittest.TestCase):
    """List literals are re-materialized on every evaluation."""

    def setUp(self):
        self.stacker = Stacker()

    def test_multi_var_list_literal_in_loop(self):
        # [i i] must re-resolve i on each iteration.
        self.stacker.process_expression(
            "[] lst set 1 3 $i { lst [i i] + lst set } do lst"
        )
        self.assertEqual(list(self.stacker.stack), [[1, 1, 2, 2, 3, 3]])

    def test_nested_list_literal_freshness(self):
        # Evaluating the same block twice must produce two independent lists,
        # including nested containers (no aliasing between evaluations).
        self.stacker.process_expression("{[[1 2] 3]} 2 times")
        first, second = self.stacker.stack[-2], self.stacker.stack[-1]
        self.assertEqual(first, [[1, 2], 3])
        self.assertEqual(second, [[1, 2], 3])
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0].append(99)
        self.assertEqual(second, [[1, 2], 3])


class TestStringTokenQuirks(unittest.TestCase):
    """String is a str subclass; the classification chain must keep treating
    it exactly as today, including the block-built String quirk."""

    def setUp(self):
        self.stacker = Stacker()

    def test_string_token_toplevel_with_same_named_variable(self):
        # At top level, "foo" stays a String literal even if a variable
        # named foo exists (quote check precedes variable lookup).
        self.stacker.process_expression('5 foo set "foo"')
        top = self.stacker.stack[-1]
        self.assertIsInstance(top, String)
        self.assertEqual(top, "foo")

    def test_string_token_in_block_with_same_named_variable(self):
        # Inside a block, "foo" is pre-converted to String("foo") at block
        # build time; on evaluation its overridden startswith sees no quotes,
        # so it falls through to variable lookup and resolves to 5.
        self.stacker.process_expression('5 foo set {"foo"} 1 times')
        self.assertEqual(list(self.stacker.stack), [5])


class TestUndefinedSymbolBehavior(unittest.TestCase):
    """Lookahead classification and the UndefinedSymbol fallback."""

    def setUp(self):
        self.stacker = Stacker()

    def test_undefined_symbol_lookahead_set(self):
        # An undefined name directly before `set` is treated as a symbol.
        self.stacker.process_expression("42 undefined_name set undefined_name")
        self.assertEqual(list(self.stacker.stack), [42])
        self.assertIsInstance(self.stacker.stack[-1], int)

    def test_undefined_symbol_in_arithmetic_raises(self):
        with self.assertRaises(UndefinedSymbolError):
            self.stacker.process_expression("3 no_such_name +")

    def test_bare_undefined_pushes_undefined_symbol(self):
        self.stacker.process_expression("bare_undefined")
        top = self.stacker.stack[-1]
        self.assertIsInstance(top, UndefinedSymbol)
        self.assertEqual(top, "bare_undefined")


class TestErrorOrdering(unittest.TestCase):
    """Errors must be raised at the failing token's execution position,
    after earlier tokens' side effects have happened."""

    def setUp(self):
        self.stacker = Stacker()

    def test_side_effect_before_malformed_list_error(self):
        # `print` runs first; the malformed list token then raises a
        # syntax error when *it* is executed — never earlier (e.g. during
        # an eager classification pass).
        # 1.12.1: the exception type changed from a bare SyntaxError to
        # StackerSyntaxError (audit #16, project rule "no bare
        # exceptions"); the ORDERING contract frozen here is unchanged.
        from stacker.error import StackerSyntaxError

        buf = io.StringIO()
        with self.assertRaises(StackerSyntaxError):
            with contextlib.redirect_stdout(buf):
                self.stacker.process_expression('"hello" print [1 2 }]')
        self.assertEqual(buf.getvalue(), "hello\n")


if __name__ == "__main__":
    unittest.main()
