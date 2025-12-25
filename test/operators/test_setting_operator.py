"""Tests for settings operators (disable_plugin, disable_all_plugins)."""

import unittest
from io import StringIO
from unittest.mock import patch
from stacker.stacker import Stacker


class TestSettingsOperators(unittest.TestCase):
    def setUp(self):
        self.stacker = Stacker()
        self.stacker.stack.clear()

    def test_disable_plugin_existing(self):
        """Test disabling an existing plugin."""
        # Check if there are any plugins loaded
        initial_plugins = dict(self.stacker.plugins)

        if len(initial_plugins) > 0:
            # Get first plugin name
            plugin_name = list(initial_plugins.keys())[0]

            # Disable it
            self.stacker.process_expression(f"'{plugin_name}' disable_plugin")

            # Verify it's removed
            self.assertNotIn(plugin_name, self.stacker.plugins)

    def test_disable_plugin_nonexistent(self):
        """Test disabling a non-existent plugin."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.stacker.process_expression("'nonexistent_plugin' disable_plugin")
            output = fake_out.getvalue()
            self.assertIn("not registered", output)

    def test_disable_all_plugins(self):
        """Test disabling all plugins."""
        # Store initial plugin count
        initial_count = len(self.stacker.plugins)

        # Disable all plugins
        self.stacker.process_expression("disable_all_plugins")

        # Verify all plugins are removed
        self.assertEqual(len(self.stacker.plugins), 0)
        self.assertEqual(self.stacker.plugins, {})

    def test_disable_all_plugins_when_empty(self):
        """Test disabling all plugins when none are loaded."""
        # First disable all
        self.stacker.process_expression("disable_all_plugins")
        self.assertEqual(len(self.stacker.plugins), 0)

        # Disable again (should not error)
        self.stacker.process_expression("disable_all_plugins")
        self.assertEqual(len(self.stacker.plugins), 0)

    def test_disable_plugin_does_not_affect_stack(self):
        """Test that disable_plugin doesn't modify the stack."""
        self.stacker.process_expression("1 2 3")
        initial_stack = list(self.stacker.stack)

        self.stacker.process_expression("'nonexistent' disable_plugin")

        # Stack should be unchanged
        self.assertEqual(list(self.stacker.stack), initial_stack)

    def test_disable_all_plugins_does_not_affect_stack(self):
        """Test that disable_all_plugins doesn't modify the stack."""
        self.stacker.process_expression("1 2 3")
        initial_stack = list(self.stacker.stack)

        self.stacker.process_expression("disable_all_plugins")

        # Stack should be unchanged
        self.assertEqual(list(self.stacker.stack), initial_stack)


if __name__ == "__main__":
    unittest.main()
