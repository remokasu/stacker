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

from stacker.engine.core import TokenList


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


if __name__ == "__main__":
    unittest.main()
