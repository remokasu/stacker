import unittest
from io import StringIO
from unittest.mock import patch
from stacker.runtime.exec_modes.repl_mode import ReplMode
from stacker.stacker import Stacker


class TestReplMode(unittest.TestCase):
    def setUp(self):
        self.rpn_calculator = Stacker()
        self.repl_mode = ReplMode(self.rpn_calculator)

    @patch("stacker.runtime.exec_modes.repl_mode.version")
    def test_get_version(self, mock_version):
        mock_version.return_value = "1.0.0"
        rpn_calculator = Stacker()
        repl_mode = ReplMode(rpn_calculator)
        result = repl_mode.get_version()
        self.assertEqual(result, "1.0.0")
        mock_version.assert_called_once_with("pystacker")

    def test_repl_mode_initialization(self):
        """Test that ReplMode initializes with correct default settings."""
        self.assertTrue(self.repl_mode.disp_stack_mode)
        self.assertTrue(self.repl_mode.disp_logo_mode)
        self.assertFalse(self.repl_mode.disp_ans_mode)

    def test_repl_commands_list(self):
        """Test that REPL commands list is properly initialized."""
        self.assertIn("help", self.repl_mode.repl_commands)
        self.assertIn("about", self.repl_mode.repl_commands)
        self.assertIn("delete_history", self.repl_mode.repl_commands)

    def test_get_completer(self):
        """Test that get_completer returns expected words."""
        completer_words = self.repl_mode.get_completer()

        # Should include REPL commands
        self.assertIn("help", completer_words)
        self.assertIn("about", completer_words)

        # Should include operators
        self.assertIn("+", completer_words)
        self.assertIn("dup", completer_words)

        # Should include system operators
        self.assertIn("vars", completer_words)
        self.assertIn("funcs", completer_words)

    def test_handle_repl_command_help(self):
        """Test that help command is handled correctly."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = self.repl_mode._handle_repl_command("help")
            self.assertTrue(result)
            output = fake_out.getvalue()
            self.assertIn("operators", output.lower())

    def test_handle_repl_command_about(self):
        """Test that about command is handled correctly."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = self.repl_mode._handle_repl_command("about")
            self.assertTrue(result)
            output = fake_out.getvalue()
            self.assertIn("Stacker", output)

    def test_handle_repl_command_enable_disp_stack(self):
        """Test enable_disp_stack command."""
        self.repl_mode.disp_stack_mode = False
        result = self.repl_mode._handle_repl_command("enable_disp_stack")
        self.assertTrue(result)
        self.assertTrue(self.repl_mode.disp_stack_mode)

    def test_handle_repl_command_disable_disp_stack(self):
        """Test disable_disp_stack command."""
        self.repl_mode.disp_stack_mode = True
        result = self.repl_mode._handle_repl_command("disable_disp_stack")
        self.assertTrue(result)
        self.assertFalse(self.repl_mode.disp_stack_mode)

    def test_handle_repl_command_enable_disp_logo(self):
        """Test enable_disp_logo command."""
        self.repl_mode.disp_logo_mode = False
        result = self.repl_mode._handle_repl_command("enable_disp_logo")
        self.assertTrue(result)
        self.assertTrue(self.repl_mode.disp_logo_mode)

    def test_handle_repl_command_disable_disp_logo(self):
        """Test disable_disp_logo command."""
        self.repl_mode.disp_logo_mode = True
        result = self.repl_mode._handle_repl_command("disable_disp_logo")
        self.assertTrue(result)
        self.assertFalse(self.repl_mode.disp_logo_mode)

    def test_handle_repl_command_enable_disp_ans(self):
        """Test enable_disp_ans command."""
        self.repl_mode.disp_ans_mode = False
        result = self.repl_mode._handle_repl_command("enable_disp_ans")
        self.assertTrue(result)
        self.assertTrue(self.repl_mode.disp_ans_mode)

    def test_handle_repl_command_disable_disp_ans(self):
        """Test disable_disp_ans command."""
        self.repl_mode.disp_ans_mode = True
        result = self.repl_mode._handle_repl_command("disable_disp_ans")
        self.assertTrue(result)
        self.assertFalse(self.repl_mode.disp_ans_mode)

    def test_handle_repl_command_case_insensitive(self):
        """Test that REPL commands are case-insensitive."""
        with patch("sys.stdout", new=StringIO()):
            # Test uppercase
            result1 = self.repl_mode._handle_repl_command("HELP")
            self.assertTrue(result1)

            # Test mixed case
            result2 = self.repl_mode._handle_repl_command("HeLp")
            self.assertTrue(result2)

    def test_handle_repl_command_not_a_command(self):
        """Test that non-commands return False."""
        result = self.repl_mode._handle_repl_command("1 2 +")
        self.assertFalse(result)

        result = self.repl_mode._handle_repl_command("not_a_command")
        self.assertFalse(result)

    def test_handle_repl_command_delete_history(self):
        """Test delete_history command."""
        with patch(
            "stacker.runtime.exec_modes.repl_mode.delete_history"
        ) as mock_delete:
            result = self.repl_mode._handle_repl_command("delete_history")
            self.assertTrue(result)
            mock_delete.assert_called_once()

    def test_cmd_help_includes_system_operators(self):
        """Test that help command includes system operators."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.repl_mode._cmd_help()
            output = fake_out.getvalue()

            # Should include system operators section
            self.assertIn("System operators:", output)
            self.assertIn("vars", output)
            self.assertIn("funcs", output)
            self.assertIn("macros", output)
            self.assertIn("operators", output)


if __name__ == "__main__":
    unittest.main()
