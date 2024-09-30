import unittest
from stacker.syntax.lexer import lex_string


class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        self.assertEqual(lex_string("a b c"), ["a", "b", "c"])
        self.assertEqual(lex_string("a [b c]"), ["a", "[b c]"])
        self.assertEqual(lex_string("a (b c)"), ["a", "(b c)"])
        self.assertEqual(lex_string("a {b c}"), ["a", "{b c}"])
        self.assertEqual(lex_string("a 'b c'"), ["a", "'b c'"])
        self.assertEqual(lex_string('a "b c"'), ["a", '"b c"'])

    def test_mixed_tokens(self):
        self.assertEqual(lex_string("a 'b c' d"), ["a", "'b c'", "d"])
        self.assertEqual(lex_string('a "b c" d'), ["a", '"b c"', "d"])
        self.assertEqual(lex_string("a 'b c' d 'e f'"), ["a", "'b c'", "d", "'e f'"])
        self.assertEqual(lex_string("a {b c} {d e}"), ["a", "{b c}", "{d e}"])
        self.assertEqual(
            lex_string("a {b c {d e}} {f h}"), ["a", "{b c {d e}}", "{f h}"]
        )

    def test_single_brackets(self):
        self.assertEqual(lex_string("[1]"), ["[1]"])
        self.assertEqual(lex_string("(1)"), ["(1)"])

    def test_complex_expression(self):
        expr = "1 2 3 [4 5 6] 7 8 (9 10 11) a1 b1 c1 {1 2 +} '1+1' eval"
        exprs = [
            "1",
            "2",
            "3",
            "[4 5 6]",
            "7",
            "8",
            "(9 10 11)",
            "a1",
            "b1",
            "c1",
            "{1 2 +}",
            "'1+1'",
            "eval",
        ]
        self.assertEqual(lex_string(expr), exprs)


if __name__ == "__main__":
    unittest.main()
