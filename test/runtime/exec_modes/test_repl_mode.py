import unittest
from io import StringIO
from unittest.mock import patch

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from stacker.lib import disp_help
from stacker.runtime.exec_modes.repl_mode import ReplMode
from stacker.stacker import Stacker


class TestReplMode(unittest.TestCase):
    def setUp(self):
        self.rpn_calculator = Stacker()
        self.repl_mode = ReplMode(self.rpn_calculator)

    def test_get_version(self):
        from stacker import __version__

        self.assertEqual(self.repl_mode.get_version(), __version__)

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
            for word in ("map", "sum", "sorted"):
                self.assertIn(f"  {word}:", output)
            self.assertIn(":name", output)
            self.assertNotIn("Tuple", output)

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


def _with_listed_words(stacker: Stacker) -> Stacker:
    """Adds a plugin with a description, one without, and a replaced built-in word."""
    stacker.register_plugin("hyp", lambda a, b: (a * a + b * b) ** 0.5, desc="Length of the hypotenuse")
    stacker.register_plugin("shout", lambda s: s.upper())
    stacker.register_operator("dup", lambda x: x, 1, True, "replaced dup")
    return stacker


def _section(title: str, items: dict, separator: str) -> str:
    return title + "\n" + "".join(f"  {name}{separator}{desc}\n" for name, desc in items.items())


def test_help_lists_every_group_and_the_plugins_word_for_word(capsys):
    stacker = _with_listed_words(Stacker())
    manager = stacker.operator_manager
    assert list(manager.get_stack_descriptions())[-1] == "dup"  # a replaced word moves to the end
    disp_help()
    help_text = capsys.readouterr().out
    expected = help_text + "\n"
    regular = {**manager.get_regular_descriptions(), **manager.get_priority_descriptions()}
    expected += _section("Supported operators and functions:", regular, ":\t") + "\n"
    for title, items in (
        ("Higher-order operators:", manager.get_hof_descriptions()),
        ("Aggregate operators:", manager.get_aggregate_descriptions()),
        ("Transform operators:", manager.get_transform_descriptions()),
        ("Array and dictionary operators:", manager.get_collection_descriptions()),
        ("Stack operators:", manager.get_stack_descriptions()),
        ("Settings operators:", manager.get_settings_descriptions()),
        ("System operators:", manager.get_system_descriptions()),
    ):
        expected += _section(title, items, ":\t") + "\n"
    expected += _section("Plugin commands:", stacker.get_plugin_descriptions(), ": ")

    ReplMode(stacker)._cmd_help()

    out = capsys.readouterr().out
    assert out == expected
    assert "  hyp: Length of the hypotenuse\n" in out
    assert "  shout: None\n" in out
    assert "  dup:\treplaced dup\n" in out
    lists = out[len(help_text) :]
    assert [line for line in lists.splitlines() if not line.startswith("  ")] == [
        "",
        "Supported operators and functions:",
        "",
        "Higher-order operators:",
        "",
        "Aggregate operators:",
        "",
        "Transform operators:",
        "",
        "Array and dictionary operators:",
        "",
        "Stack operators:",
        "",
        "Settings operators:",
        "",
        "System operators:",
        "",
        "Plugin commands:",
    ]


def test_help_ends_with_the_plugin_heading_when_there_is_no_plugin(capsys):
    ReplMode(Stacker())._cmd_help()
    assert capsys.readouterr().out.endswith("\n\nPlugin commands:\n")


def test_help_lists_a_plugin_registered_after_the_repl_started(capsys):
    stacker = Stacker()
    repl = ReplMode(stacker)
    stacker.register_plugin("later", lambda: 1, desc="Registered later")
    repl._cmd_help()
    assert capsys.readouterr().out.endswith("Plugin commands:\n  later: Registered later\n")


def test_the_completer_offers_every_name_the_interpreter_knows():
    stacker = _with_listed_words(Stacker())
    stacker.eval("{x} {x} :early defun 5 :early-value set {n} {{n}} :early-macro defmacro")
    repl = ReplMode(stacker)
    words = _offered(repl, "")

    assert words == set(repl.repl_commands) | set(stacker.get_all_keys_for_completer())
    assert {
        "help", "about", "delete_history", "+", "dup", "if", "defun", "times", "mean", "pi",
        "hyp", "shout", "early", "early-value", "early-macro",
    } <= words
    # The settings words and the REPL's display settings are not offered
    assert "disable_plugin" not in words
    assert "enable_disp_stack" not in words


def _offered(repl: ReplMode, text: str) -> set[str]:
    """The words the REPL's prompt offers to complete ``text``."""
    return {completion.text for completion in repl.completer.get_completions(Document(text), CompleteEvent())}


def test_the_completer_offers_a_name_defined_after_the_repl_started():
    stacker = Stacker()
    repl = ReplMode(stacker)
    stacker.eval("{x} {x} :defined_after_start defun 1 :set_after_start set")
    assert _offered(repl, "defined_after") == {"defined_after_start"}
    assert _offered(repl, "set_after") == {"set_after_start"}


if __name__ == "__main__":
    unittest.main()
