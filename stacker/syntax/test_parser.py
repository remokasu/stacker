import unittest

from stacker.syntax.parser import (
    evaluate_token_or_return_str,
    starts_with_char,
    remove_start_end_quotes,
    is_balanced,
    is_single,
    is_array,
    is_tuple,
    is_brace,
    is_array_balanced,
    is_tuple_balanced,
    is_brace_balanced,
    is_single_array,
    is_single_tuple,
    is_single_brace,
    is_block,
    is_string,
    is_list,
    is_symbol,
    is_label_symbol,
    is_transpose_command,
    is_contains_transpose_command,
    convert_custom_array_to_proper_list,
    parse_expression,
    lex_string,
)


class TestParser(unittest.TestCase):
    def test_evaluate_token_or_return_str(self):
        self.assertEqual(evaluate_token_or_return_str("123"), 123)
        self.assertEqual(evaluate_token_or_return_str("123.45"), 123.45)
        self.assertEqual(evaluate_token_or_return_str("'string'"), "string")
        self.assertEqual(evaluate_token_or_return_str("{block}"), "{block}")
        self.assertEqual(evaluate_token_or_return_str("invalid"), "invalid")

    def test_starts_with_char(self):
        self.assertTrue(starts_with_char("[1, 2, 3]", "["))
        self.assertFalse(starts_with_char("(1, 2, 3)", "["))

    def test_remove_start_end_quotes(self):
        self.assertEqual(remove_start_end_quotes("'string'"), "string")
        self.assertEqual(remove_start_end_quotes('"string"'), "string")
        self.assertEqual(remove_start_end_quotes("no_quotes"), "no_quotes")

    def test_is_balanced(self):
        self.assertTrue(is_balanced("[1, 2, 3]", "[", "]"))
        self.assertFalse(is_balanced("[1, 2, 3", "[", "]"))

    def test_is_single(self):
        self.assertTrue(is_single("[1, 2, 3]", "[", "]"))
        self.assertFalse(is_single("[1, 2, 3][4, 5, 6]", "[", "]"))

    def test_is_array(self):
        self.assertTrue(is_array("[1, 2, 3]"))
        self.assertFalse(is_array("(1, 2, 3)"))

    def test_is_tuple(self):
        # DEPRECATED: is_tuple() now checks for parenthesized code blocks, not tuples
        # Tuples were removed in v1.9.0
        self.assertTrue(is_tuple("(1, 2, 3)"))
        self.assertFalse(is_tuple("[1, 2, 3]"))

    def test_is_brace(self):
        self.assertTrue(is_brace("{1, 2, 3}"))
        self.assertFalse(is_brace("[1, 2, 3]"))

    def test_is_array_balanced(self):
        self.assertTrue(is_array_balanced("[1, 2, 3]"))
        self.assertFalse(is_array_balanced("[1, 2, 3"))

    def test_is_tuple_balanced(self):
        # DEPRECATED: is_tuple_balanced() now checks parentheses balance for code blocks
        # Tuples were removed in v1.9.0
        self.assertTrue(is_tuple_balanced("(1, 2, 3)"))
        self.assertFalse(is_tuple_balanced("(1, 2, 3"))

    def test_is_brace_balanced(self):
        self.assertTrue(is_brace_balanced("{1, 2, 3}"))
        self.assertFalse(is_brace_balanced("{1, 2, 3"))

    def test_is_single_array(self):
        self.assertTrue(is_single_array("[1, 2, 3]"))
        self.assertFalse(is_single_array("[1, 2, 3][4, 5, 6]"))

    def test_is_single_tuple(self):
        self.assertTrue(is_single_tuple("(1, 2, 3)"))
        self.assertFalse(is_single_tuple("(1, 2, 3)(4, 5, 6)"))

    def test_is_single_brace(self):
        self.assertTrue(is_single_brace("{1, 2, 3}"))
        self.assertFalse(is_single_brace("{1, 2, 3}{4, 5, 6}"))

    def test_is_block(self):
        self.assertTrue(is_block("{block}"))
        self.assertFalse(is_block("not_a_block"))

    def test_is_string(self):
        self.assertTrue(is_string("'string'"))
        self.assertTrue(is_string('"string"'))
        self.assertFalse(is_string("not_a_string"))

    def test_is_list(self):
        self.assertTrue(is_list("[1, 2, 3]"))
        self.assertFalse(is_list("(1, 2, 3)"))

    def test_is_symbol(self):
        self.assertTrue(is_symbol("$symbol"))
        self.assertFalse(is_symbol("symbol$"))

    def test_is_label_symbol(self):
        self.assertTrue(is_label_symbol("label:"))
        self.assertFalse(is_label_symbol(":label"))

    def test_is_transpose_command(self):
        self.assertTrue(is_transpose_command("^T"))
        self.assertFalse(is_transpose_command("not_transpose"))

    def test_is_contains_transpose_command(self):
        self.assertTrue(is_contains_transpose_command("matrix^T"))
        self.assertFalse(is_contains_transpose_command("matrix"))

    # ------------------------------------ #
    # convert_custom_array_to_proper_list  #
    # ------------------------------------ #
    def test_convert_custom_array_to_proper_list(self):
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 2 3; 4 5 6]"), "[[1,2,3],[4,5,6]]"
        )
        self.assertEqual(convert_custom_array_to_proper_list("[1 2 3]"), "[1,2,3]")
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 2 3; 4 5 6]"), "[[1,2,3],[4,5,6]]"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("['a' 'b' 'c']"),
            """['"a"','"b"','"c"']""",
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[a b c]"), "['a','b','c']"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 'b' 3; 'd' 5 'f']"),
            "[[1,'\"b\"',3],['\"d\"',5,'\"f\"']]",
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[a 'b' c]"), "['a','\"b\"','c']"
        )
        self.assertEqual(convert_custom_array_to_proper_list("(1 2 3)"), "(1,2,3)")
        self.assertEqual(
            convert_custom_array_to_proper_list("(1 2 3; 4 5 6)"), "((1,2,3),(4,5,6))"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("((1 2; 3 4); (5 6; 7 8))"),
            "(((1,2),(3,4)),((5,6),(7,8)))",
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 2 3; (4 5 6; 7 8 9)]"),
            "[[1,2,3],((4,5,6),(7,8,9))]",
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 2.5 3.5]"), "[1,2.5,3.5]"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[-1 -2 -3]"), "[-1,-2,-3]"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("[1 2+3j 4+5j]"), "[1,(2+3j),(4+5j)]"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("(1 2.5 3.5)"), "(1,2.5,3.5)"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("(-1 -2 -3)"), "(-1,-2,-3)"
        )
        self.assertEqual(
            convert_custom_array_to_proper_list("(1 2+3j 4+5j)"), "(1,(2+3j),(4+5j))"
        )

    def test_convert_custom_array_to_proper_list_3d_array(self):
        self.assertEqual(
            convert_custom_array_to_proper_list(
                "[[[1 2 3; 4 5 6]; [7 8 9; 10 11 12]]; [[13 14 15; 16 17 18]; [19 20 21; 22 23 24]]]"
            ),
            "[[[[1,2,3],[4,5,6]],[[7,8,9],[10,11,12]]],[[[13,14,15],[16,17,18]],[[19,20,21],[22,23,24]]]]",
        )

    def test_parse_expression(self):
        self.assertEqual(parse_expression("[1 2 3] 4 5 a"), ["[1 2 3]", "4", "5", "a"])
        self.assertEqual(parse_expression("(1)"), ["(1)"])

    def test_block_1(self):
        self.assertEqual(
            parse_expression("{x}{x 1 +}lambda"), ["{x}", "{x 1 +}", "lambda"]
        )

    def test_block_2(self):
        self.assertEqual(parse_expression("3{1 +}"), ["3", "{1 +}"])


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
