"""Regression tests pinning the TokenList classification-cache contract.

TokenList.classification() (stacker/engine/core.py) only recomputes its
cached entries when the list LENGTH changes. This length guard relies on
a codebase-wide invariant: every in-place mutation of a block's .tokens
goes through insert() (lambda/reduce argument binding), which always
changes the length; wholesale replacements create a fresh TokenList.

If a same-length in-place mutation (e.g. ``tokens[i] = x``) is ever
introduced, the cache MUST be invalidated explicitly — the stale-cache
test below documents what silently goes wrong otherwise.
"""

import copy
import unittest

from stacker import Stacker
from stacker.engine.core import (
    K_DYNAMIC,
    K_INVALID,
    K_LIST,
    K_LOOKAHEAD_SYMBOL,
    K_LOOP_VAR,
    K_STRING,
    K_SYMBOL,
    TokenList,
)
from stacker.engine.data_type import String, Symbol
from stacker.error import StackerSyntaxError, UndefinedSymbolError


class TestTokenListClassificationCache(unittest.TestCase):
    def test_length_changing_insert_invalidates_cache(self):
        tokens = TokenList(["1", "2", "+"])
        before = tokens.classification()
        self.assertEqual(len(before), 3)
        tokens.insert(0, "5")
        after = tokens.classification()
        self.assertEqual(len(after), 4)
        self.assertEqual([entry[1] for entry in after][0], "5")

    def test_same_length_mutation_returns_stale_classification(self):
        # KNOWN LIMITATION of the length guard, pinned as a contract:
        # a same-length in-place rewrite is NOT detected, so the stale
        # classification (still referencing the old token) is returned.
        # Anyone adding such a mutation must invalidate the cache
        # explicitly (or make this test obsolete by improving the guard).
        tokens = TokenList(["1", "2", "+"])
        stale = tokens.classification()
        tokens[0] = "9"  # Same length: invisible to the length guard
        self.assertIs(tokens.classification(), stale)
        self.assertEqual(tokens.classification()[0][1], "1")

    def test_deepcopy_drops_cache(self):
        tokens = TokenList(["1", "2", "+"])
        original_entries = tokens.classification()
        clone = copy.deepcopy(tokens)
        self.assertIsNone(getattr(clone, "_cls_entries", None))
        clone_entries = clone.classification()
        self.assertIsNot(clone_entries, original_entries)
        self.assertEqual(
            [entry[1] for entry in clone_entries],
            [entry[1] for entry in original_entries],
        )


def _kinds(tokens):
    return [entry[0] for entry in TokenList(tokens).classification()]


class TestSymbolClassification(unittest.TestCase):
    """Symbols and `$` errors are decided once per token list, then reused."""

    def test_dollar_name_is_classified_with_its_symbol(self):
        entries = TokenList([":x", ":+"]).classification()
        self.assertEqual([e[0] for e in entries], [K_SYMBOL, K_SYMBOL])
        self.assertEqual([e[2] for e in entries], [Symbol("x"), Symbol("+")])

    def test_invalid_dollar_token_is_classified_with_its_message(self):
        entries = TokenList([":1", ":", "::x", ":true", "$x"]).classification()
        self.assertEqual({e[0] for e in entries}, {K_INVALID})
        self.assertIn("`:1` is not a symbol", entries[0][2])
        self.assertIn("written `:x`", entries[4][2])

    def test_a_string_literal_that_looks_like_a_symbol_is_a_string(self):
        entries = TokenList([String(":x"), '"$x"']).classification()
        self.assertEqual([e[0] for e in entries], [K_STRING, K_STRING])
        self.assertEqual([e[2] for e in entries], [":x", "$x"])

    def test_names_before_binding_words_are_lookahead_symbols(self):
        entries = TokenList(["x", "set"]).classification()
        self.assertEqual(entries[0][0], K_LOOKAHEAD_SYMBOL)
        self.assertEqual(entries[0][2], Symbol("x"))

    def test_loop_variable_is_classified_with_its_symbol(self):
        entries = TokenList(["1", "3", "i", "{i}", "do"]).classification()
        self.assertEqual(entries[2][0], K_LOOP_VAR)
        self.assertEqual(entries[2][2], Symbol("i"))

    def test_bound_or_not_a_bare_name_stays_dynamic(self):
        self.assertEqual(_kinds(["foo", "+"])[0], K_DYNAMIC)

    def test_repeated_classification_returns_the_same_entries(self):
        tokens = TokenList([":x", "$1", "foo"])
        self.assertIs(tokens.classification(), tokens.classification())

    def test_insert_reclassifies_a_new_dollar_token(self):
        tokens = TokenList([":x"])
        tokens.classification()
        tokens.insert(0, "$1")
        self.assertEqual([e[0] for e in tokens.classification()], [K_INVALID, K_SYMBOL])

    def test_classification_does_not_depend_on_interpreter_state(self):
        stacker = Stacker()
        before = _kinds(["foo", ":foo"])
        stacker.process_expression("5 :foo set")
        self.assertEqual(_kinds(["foo", ":foo"]), before)

    def test_list_literal_token_keeps_one_template(self):
        tokens = TokenList(["[:a 1]"])
        entries = tokens.classification()
        self.assertEqual(entries[0][0], K_LIST)
        self.assertIs(tokens.classification()[0][2], entries[0][2])


class TestRepeatedEvaluation(unittest.TestCase):
    """Evaluating a block twice gives the same answer and the same errors."""

    def _stacker(self, *lines):
        stacker = Stacker()
        for line in lines:
            stacker.process_expression(line)
        return stacker

    def test_symbols_are_equal_across_evaluations(self):
        stacker = self._stacker("{:x :y} :b set", "b eval", "b eval")
        self.assertEqual(list(stacker.stack), [Symbol("x"), Symbol("y"), Symbol("x"), Symbol("y")])

    def test_symbol_stays_a_symbol_when_a_variable_of_that_name_appears_later(self):
        stacker = self._stacker("{:x} :b set", "b eval")
        stacker.process_expression("5 :x set")
        stacker.process_expression("b eval")
        self.assertEqual(list(stacker.stack), [Symbol("x"), Symbol("x")])

    def test_symbol_made_by_a_block_is_equal_but_may_be_shared(self):
        stacker = self._stacker("{:x} :b set", "b eval b eval")
        first, second = stacker.stack
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_block_with_a_reference_follows_the_current_binding(self):
        stacker = self._stacker("{foo} :b set")
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("b eval")
        stacker.process_expression("5 :foo set")
        stacker.process_expression("b eval")
        self.assertEqual(list(stacker.stack), [5])

    def test_block_with_a_reference_raises_again_after_the_binding_is_gone(self):
        stacker = self._stacker("5 :foo set {foo} :b set", "b eval")
        stacker.variables.pop("foo")
        with self.assertRaises(UndefinedSymbolError):
            stacker.process_expression("b eval")

    def test_invalid_dollar_raises_a_fresh_error_each_time_with_the_same_text(self):
        stacker = self._stacker("{:1} :b set")
        errors = []
        for _ in range(3):
            with self.assertRaises(StackerSyntaxError) as context:
                stacker.process_expression("b eval")
            errors.append(context.exception)
        self.assertEqual(len({id(e) for e in errors}), 3)
        self.assertEqual({str(e) for e in errors}, {"`:1` is not a symbol: `:` must be followed by a name"})
        self.assertTrue(all(len(e.args) == 1 for e in errors))
        self.assertTrue(all(not getattr(e, "__notes__", None) for e in errors))

    def test_invalid_dollar_error_traceback_does_not_grow(self):
        stacker = self._stacker("{:1} :b set")
        depths = []
        for _ in range(3):
            with self.assertRaises(StackerSyntaxError) as context:
                stacker.process_expression("b eval")
            depth, frame = 0, context.exception.__traceback__
            while frame is not None:
                depth, frame = depth + 1, frame.tb_next
            depths.append(depth)
        self.assertEqual(len(set(depths)), 1)

    def test_malformed_list_literal_raises_each_time_with_the_same_text(self):
        stacker = self._stacker("{[{x}]} :b set")
        messages = []
        for _ in range(3):
            with self.assertRaises(StackerSyntaxError) as context:
                stacker.process_expression("b eval")
            messages.append(str(context.exception))
        self.assertEqual(len(set(messages)), 1)
        self.assertIn("cannot be written inside a list literal", messages[0])

    def test_error_inside_a_macro_expansion_does_not_accumulate_its_suffix(self):
        stacker = self._stacker("{} {{foo}} :m defmacro")
        messages = []
        for _ in range(3):
            with self.assertRaises(UndefinedSymbolError) as context:
                stacker.process_expression("m")
            messages.append(str(context.exception))
        self.assertEqual(len(set(messages)), 1)
        self.assertEqual(messages[0].count("in code generated by macro"), 1)

    def test_invalid_dollar_in_the_same_block_before_and_after_a_valid_one(self):
        stacker = self._stacker("{:x $1 :y} :b set")
        for _ in range(2):
            stacker.stack.clear()
            with self.assertRaises(StackerSyntaxError):
                stacker.process_expression("b eval")
            self.assertEqual(list(stacker.stack), [Symbol("x")])

    def test_list_literal_is_fresh_on_every_evaluation(self):
        stacker = self._stacker("{[:a 1]} :b set", "b eval b eval")
        first, second = stacker.stack
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first.append(2)
        self.assertEqual(list(second), [Symbol("a"), 1])

    def test_string_literal_in_a_block_is_the_same_string_each_time(self):
        stacker = self._stacker('{"$x"} :b set', "b eval b eval")
        self.assertEqual(list(stacker.stack), ["$x", "$x"])
        self.assertTrue(all(not isinstance(v, Symbol) for v in stacker.stack))


if __name__ == "__main__":
    unittest.main()
