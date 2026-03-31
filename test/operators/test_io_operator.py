import unittest
from io import StringIO
from unittest.mock import patch

from stacker.stacker import Stacker


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()

    def test_echo_int(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("42 echo")
            self.assertEqual(mock_out.getvalue(), "42\n")

    def test_echo_string(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("'hello' echo")
            self.assertEqual(mock_out.getvalue(), "hello\n")

    def test_echo_float(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("3.14 echo")
            self.assertEqual(mock_out.getvalue(), "3.14\n")

    def test_print_int(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("99 print")
            self.assertEqual(mock_out.getvalue(), "99\n")

    def test_print_string(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("'world' print")
            self.assertEqual(mock_out.getvalue(), "world\n")

    def test_printc_no_newline(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("'hi' printc")
            self.assertEqual(mock_out.getvalue(), "hi")

    def test_printc_multiple(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("'foo' printc 'bar' printc")
            self.assertEqual(mock_out.getvalue(), "foobar")

    def test_newline(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()) as mock_out:
            self.stacker.eval("newline")
            self.assertEqual(mock_out.getvalue(), "\n")

    def test_echo_does_not_push_to_stack(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()):
            self.stacker.eval("42 echo")
            self.assertEqual(len(self.stacker.stack), 0)

    def test_print_does_not_push_to_stack(self):
        self.stacker.stack.clear()
        with patch("sys.stdout", new=StringIO()):
            self.stacker.eval("42 print")
            self.assertEqual(len(self.stacker.stack), 0)
