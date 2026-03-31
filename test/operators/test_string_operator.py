import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_asc(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'A' asc")
        self.assertEqual(ans[-1], 65)

        self.stacker.stack.clear()
        ans = self.stacker.eval("'a' asc")
        self.assertEqual(ans[-1], 97)

        self.stacker.stack.clear()
        ans = self.stacker.eval("'0' asc")
        self.assertEqual(ans[-1], 48)

    def test_chr(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("65 chr")
        self.assertEqual(ans[-1], "A")

        self.stacker.stack.clear()
        ans = self.stacker.eval("97 chr")
        self.assertEqual(ans[-1], "a")

        self.stacker.stack.clear()
        ans = self.stacker.eval("48 chr")
        self.assertEqual(ans[-1], "0")

    def test_asc_chr_roundtrip(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'Z' asc chr")
        self.assertEqual(ans[-1], "Z")

    def test_concat(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' ' world' concat")
        self.assertEqual(ans[-1], "hello world")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'foo' 'bar' concat")
        self.assertEqual(ans[-1], "foobar")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'' 'abc' concat")
        self.assertEqual(ans[-1], "abc")

    def test_search(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello world' 'world' search")
        self.assertEqual(ans[-1], 6)

        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' 'xyz' search")
        self.assertEqual(ans[-1], -1)

        self.stacker.stack.clear()
        ans = self.stacker.eval("'abcabc' 'b' search")
        self.assertEqual(ans[-1], 1)

    def test_replace(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello world' 'world' 'python' replace")
        self.assertEqual(ans[-1], "hello python")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'aabbcc' 'b' 'X' replace")
        self.assertEqual(ans[-1], "aaXXcc")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'abc' 'xyz' 'Z' replace")
        self.assertEqual(ans[-1], "abc")

    def test_lower(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'HELLO' lower")
        self.assertEqual(ans[-1], "hello")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'Hello World' lower")
        self.assertEqual(ans[-1], "hello world")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'already lower' lower")
        self.assertEqual(ans[-1], "already lower")

    def test_upper(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' upper")
        self.assertEqual(ans[-1], "HELLO")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'Hello World' upper")
        self.assertEqual(ans[-1], "HELLO WORLD")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'ALREADY UPPER' upper")
        self.assertEqual(ans[-1], "ALREADY UPPER")

    def test_title(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello world' title")
        self.assertEqual(ans[-1], "Hello World")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'foo bar baz' title")
        self.assertEqual(ans[-1], "Foo Bar Baz")

    def test_strip(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'  hello  ' strip")
        self.assertEqual(ans[-1], "hello")

        self.stacker.stack.clear()
        ans = self.stacker.eval("'no spaces' strip")
        self.assertEqual(ans[-1], "no spaces")

    def test_lstrip(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'  hello  ' lstrip")
        self.assertEqual(ans[-1], "hello  ")

    def test_rstrip(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'  hello  ' rstrip")
        self.assertEqual(ans[-1], "  hello")

    def test_join(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("['a' 'b' 'c'] '-' join")
        self.assertEqual(ans[-1], "a-b-c")

        self.stacker.stack.clear()
        ans = self.stacker.eval("['hello' 'world'] ' ' join")
        self.assertEqual(ans[-1], "hello world")

        self.stacker.stack.clear()
        ans = self.stacker.eval("['x' 'y'] '' join")
        self.assertEqual(ans[-1], "xy")

    def test_contains(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello world' 'world' contains")
        self.assertTrue(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello world' 'xyz' contains")
        self.assertFalse(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("'abc' '' contains")
        self.assertTrue(ans[-1])

    def test_format(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'Hello, {}!' 'World' format")
        self.assertEqual(ans[-1], "Hello, World!")
