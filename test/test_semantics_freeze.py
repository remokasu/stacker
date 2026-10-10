"""Semantics-freeze tests for the interpreter core.

These tests pin the *observed* behavior of the current interpreter
(dynamic name resolution, list-literal freshness, error ordering, ...)
so that performance work on the evaluation loop cannot silently change
the language. Expected values were captured by running each program
against the unmodified interpreter; they are frozen observations, not
derived from first principles. If one of these tests fails after an
optimization, the optimization changed the language.

A frozen observation is not a specification: when one turns out to be a
defect it is corrected on purpose, the test is rewritten to pin the fixed
behavior, and the change is recorded in the CHANGELOG (see the String
literal cases below and the lazy block binding case above).
"""

import contextlib
import io
import unittest

from stacker.engine.core import StackerCore

from stacker import Stacker
from stacker.engine.data_type import String, UndefinedSymbol
from stacker.error import StackerSyntaxError, UndefinedSymbolError


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

    def test_bare_kernel_word_before_set_executes_as_operator(self):
        # Shadowing rule (1.15.0): only kernel words are protected. A bare
        # `dup` right before `set` is not a name but the `dup` operator, so
        # `set` then fails to find a name. `$dup` / `{dup}` shadow explicitly.
        with self.assertRaises(StackerSyntaxError):
            self.stacker.process_expression("3 dup set")
        self.stacker.stack.clear()
        self.stacker.process_expression("3 $dup set dup")
        self.assertEqual(list(self.stacker.stack), [3])

    def test_literal_block_forced_by_operator_with_prelude_loaded(self):
        # `{1 2 +} dup +` = 6 must not change now that `Stacker()` loads the
        # prelude by default.
        self.stacker.process_expression("{1 2 +} dup +")
        self.assertEqual(list(self.stacker.stack), [6])

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
            "{} {{2 *}} $m defmacro "
            "0 r set "
            "1 4 $i { i 2 == { {} {{3 *}} $m defmacro } if r i m + r set } do "
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

    def test_set_binds_block_value_lazily(self):
        # 1.13.0: `set` is a binding form — a code-block value
        # is stored raw (code is data), and a bare reference pushes the
        # block unevaluated; `eval` executes it. This test previously froze
        # the opposite (eager) behavior, which contradicted the README and
        # was reclassified as a bug.
        self.stacker.process_expression("{1 2 +} b set b")
        self.assertIsInstance(self.stacker.stack[-1], StackerCore)
        self.stacker.process_expression("eval")
        self.assertEqual(list(self.stacker.stack), [3])


class TestSymbolValues(unittest.TestCase):
    """1.16.0: a symbol is a value of its own and is never looked up as text."""

    def setUp(self):
        self.stacker = Stacker()

    def test_symbol_does_not_resolve_to_a_bound_value(self):
        from stacker.engine.data_type import Symbol

        self.stacker.process_expression("5 x set $x")
        self.assertEqual(list(self.stacker.stack), [Symbol("x")])

    def test_symbol_eval_equals_quoted_name_eval(self):
        self.stacker.process_expression("3 4 $+ eval")
        self.assertEqual(list(self.stacker.stack), [7])
        self.stacker.stack.clear()
        self.stacker.process_expression("3 4 {+} eval")
        self.assertEqual(list(self.stacker.stack), [7])

    def test_lambda_in_a_variable_is_pushed_by_its_bare_name(self):
        from stacker.engine.slambda import StackerLambda

        self.stacker.process_expression("{a} {a 2 *} lambda f set 5 f")
        self.assertIsInstance(self.stacker.stack[-1], StackerLambda)
        self.stacker.process_expression("eval")
        self.assertEqual(list(self.stacker.stack), [10])


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
    """A string literal is a string literal wherever it is written.

    Before 1.15.0 a literal inside a block lost its quotes when the block was
    built, so `{"foo"}` was looked up as the name `foo` on evaluation (the
    "block-built String quirk", frozen here as a known defect). The quirk is
    fixed: the classifier treats every String object as a literal, so a
    variable, operator or macro named `foo` cannot capture `"foo"`.
    """

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
        # Inside a block, "foo" stays a String literal even if a variable
        # named foo exists, exactly as at top level.
        self.stacker.process_expression('5 foo set {"foo"} 1 times')
        top = self.stacker.stack[-1]
        self.assertIsInstance(top, String)
        self.assertEqual(list(self.stacker.stack), ["foo"])


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
        # StackerSyntaxError (project rule "no bare
        # exceptions"); the ORDERING contract frozen here is unchanged.
        from stacker.error import StackerSyntaxError

        buf = io.StringIO()
        with self.assertRaises(StackerSyntaxError):
            with contextlib.redirect_stdout(buf):
                self.stacker.process_expression('"hello" print [1 2 }]')
        self.assertEqual(buf.getvalue(), "hello\n")

    def test_side_effect_before_fatal_literal_error(self):
        # A pathological literal (1.14.0) raises MemoryError or RecursionError
        # from ast.literal_eval. Like any other error it must be raised when
        # the token executes, after `print` has run, never during the
        # classification pass that looks ahead for names.
        pathological = "-" * 100_000 + "1"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises((RecursionError, MemoryError)):
                self.stacker.process_expression(f'"hello" print {pathological}')
        self.assertIn("hello", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
