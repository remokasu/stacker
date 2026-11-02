"""Tests for settings operators (disable_plugin, disable_all_plugins)."""

import unittest
from io import StringIO
from unittest.mock import patch

import pytest

from stacker.error import UndefinedSymbolError
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


@pytest.fixture
def with_plugin() -> Stacker:
    """An interpreter with one plugin word, `twice`."""
    stacker = Stacker()
    stacker.register_plugin("twice", lambda x: x * 2)
    return stacker


@pytest.mark.parametrize(
    "code",
    [
        "disable_all_plugins",
        "{disable_all_plugins} eval",
        "{} {disable_all_plugins} :plugins-off defun plugins-off",
        "true {disable_all_plugins} {} ifelse",
    ],
    ids=["top level", "block", "function body", "if branch"],
)
def test_disable_all_plugins_takes_effect_wherever_it_is_written(with_plugin, code):
    with_plugin.eval(code)
    with pytest.raises(UndefinedSymbolError):
        with_plugin.eval("3 twice")


def test_disable_all_plugins_takes_effect_from_an_included_file(with_plugin, tmp_path):
    script = tmp_path / "plugins_off.stk"
    script.write_text("disable_all_plugins\n")
    with_plugin.eval(f'"{script}" include')
    with pytest.raises(UndefinedSymbolError):
        with_plugin.eval("3 twice")


@pytest.mark.parametrize(
    "definition, call",
    [("{} {3 twice} :f defun", "f"), ("{3 twice} :blk set", "blk eval")],
    ids=["function", "stored block"],
)
def test_disable_all_plugins_reaches_code_defined_before_it(
    with_plugin, definition, call
):
    with_plugin.eval(definition)
    with_plugin.eval("disable_all_plugins")
    with pytest.raises(UndefinedSymbolError):
        with_plugin.eval(call)


def test_disable_all_plugins_leaves_another_interpreter_alone(with_plugin):
    other = Stacker()
    other.register_plugin("twice", lambda x: x * 2)
    with_plugin.eval("disable_all_plugins")
    assert list(other.eval("3 twice")) == [6]


def test_disable_all_plugins_leaves_a_copy_alone(with_plugin):
    twin = with_plugin.copy()
    with_plugin.eval("disable_all_plugins")
    assert list(twin.eval("3 twice")) == [6]


@pytest.mark.parametrize(
    "code",
    ['"twice" disable_plugin', '{"twice" disable_plugin} eval', "disable_all_plugins", "{disable_all_plugins} eval"],
    ids=["disable_plugin", "disable_plugin in a block", "disable_all_plugins", "disable_all_plugins in a block"],
)
def test_a_disabled_plugin_is_no_longer_described(code):
    stacker = Stacker()
    stacker.register_plugin("twice", lambda x: x * 2, desc="Doubles a number")
    stacker.eval(code)
    assert "twice" not in stacker.get_plugin_descriptions()


def test_disabling_one_plugin_keeps_the_others_described():
    stacker = Stacker()
    stacker.register_plugin("twice", lambda x: x * 2, desc="Doubles a number")
    stacker.register_plugin("thrice", lambda x: x * 3, desc="Triples a number")
    stacker.eval('"twice" disable_plugin')
    assert stacker.get_plugin_descriptions() == {"thrice": "Triples a number"}


@pytest.mark.parametrize(
    "code",
    [
        '{ { "twice" disable_plugin } eval } eval',
        '{ { { "twice" disable_plugin } eval } eval } eval',
        "{ { disable_all_plugins } eval } eval",
        '{} { { "twice" disable_plugin } eval } :off defun off',
    ],
    ids=["two blocks deep", "three blocks deep", "all plugins, two deep", "a block inside a function body"],
)
def test_a_plugin_disabled_from_a_nested_block_is_no_longer_described(code):
    stacker = Stacker()
    stacker.register_plugin("twice", lambda x: x * 2, desc="Doubles a number")
    stacker.eval(code)
    assert "twice" not in stacker.plugins
    assert "twice" not in stacker.get_plugin_descriptions()


if __name__ == "__main__":
    unittest.main()
