import unittest

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_int_from_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3.7 int")
        self.assertEqual(ans[-1], 3)
        self.assertIsInstance(ans[-1], int)

    def test_int_from_string(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'42' int")
        self.assertEqual(ans[-1], 42)
        self.assertIsInstance(ans[-1], int)

    def test_int_from_bool(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("true int")
        self.assertEqual(ans[-1], 1)

        self.stacker.stack.clear()
        ans = self.stacker.eval("false int")
        self.assertEqual(ans[-1], 0)

    def test_float_from_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3 float")
        self.assertEqual(ans[-1], 3.0)
        self.assertIsInstance(ans[-1], float)

    def test_float_from_string(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'3.14' float")
        self.assertAlmostEqual(ans[-1], 3.14)
        self.assertIsInstance(ans[-1], float)

    def test_str_from_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 str")
        self.assertEqual(ans[-1], "42")
        self.assertIsInstance(ans[-1], str)

    def test_str_from_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3.14 str")
        self.assertEqual(ans[-1], "3.14")
        self.assertIsInstance(ans[-1], str)

    def test_str_from_bool(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("true str")
        self.assertEqual(ans[-1], "True")

    def test_bool_from_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("1 bool")
        self.assertTrue(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("0 bool")
        self.assertFalse(ans[-1])

    def test_bool_from_string(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' bool")
        self.assertTrue(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("'' bool")
        self.assertFalse(ans[-1])

    def test_bool_from_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] bool")
        self.assertTrue(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("[] bool")
        self.assertFalse(ans[-1])

    def test_complex_from_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3 complex")
        self.assertEqual(ans[-1], complex(3))
        self.assertIsInstance(ans[-1], complex)

    def test_complex_from_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("1.5 complex")
        self.assertEqual(ans[-1], complex(1.5))

    def test_type_of_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 type")
        self.assertEqual(ans[-1], int)

    def test_type_of_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3.14 type")
        self.assertEqual(ans[-1], float)

    def test_type_of_string(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' type")
        self.assertEqual(ans[-1], str)

    def test_type_of_bool(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("true type")
        self.assertEqual(ans[-1], bool)

    def test_type_of_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] type")
        self.assertEqual(ans[-1], list)

    def test_int_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 int?")
        self.assertTrue(ans[-1])

    def test_int_check_false_for_float(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3.14 int?")
        self.assertFalse(ans[-1])

    def test_int_check_false_for_bool(self):
        # bool は int のサブクラスだが int? は False を返す
        self.stacker.stack.clear()
        ans = self.stacker.eval("true int?")
        self.assertFalse(ans[-1])

    def test_float_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("3.14 float?")
        self.assertTrue(ans[-1])

    def test_float_check_false_for_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 float?")
        self.assertFalse(ans[-1])

    def test_str_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' str?")
        self.assertTrue(ans[-1])

    def test_str_check_false_for_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 str?")
        self.assertFalse(ans[-1])

    def test_bool_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("true bool?")
        self.assertTrue(ans[-1])

        self.stacker.stack.clear()
        ans = self.stacker.eval("false bool?")
        self.assertTrue(ans[-1])

    def test_bool_check_false_for_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("1 bool?")
        self.assertFalse(ans[-1])

    def test_complex_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("1+2j complex?")
        self.assertTrue(ans[-1])

    def test_complex_check_false_for_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("42 complex?")
        self.assertFalse(ans[-1])

    def test_list_check_true(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[1 2 3] list?")
        self.assertTrue(ans[-1])

    def test_list_check_false_for_string(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("'hello' list?")
        self.assertFalse(ans[-1])

    def test_null_check_true_for_null(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("null null?")
        self.assertTrue(ans[-1])

    def test_null_check_true_for_empty_list(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("[] null?")
        self.assertTrue(ans[-1])

    def test_null_check_false_for_int(self):
        self.stacker.stack.clear()
        ans = self.stacker.eval("0 null?")
        self.assertFalse(ans[-1])
