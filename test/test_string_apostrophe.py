"""Test for string literals containing apostrophes.

This tests the fix for the bug where apostrophes inside string literals
would break tokenization.
"""

import pytest
from stacker.stacker import Stacker


def test_apostrophe_in_string():
    """Test that apostrophes in double-quoted strings work correctly."""
    stacker = Stacker()
    # Just verify it doesn't cause a syntax error
    stacker.eval('"won\'t" drop')
    assert len(stacker.stack) == 0  # drop removed it from stack


def test_apostrophe_in_code_block_with_if():
    """Test apostrophe in string inside code block with if statement."""
    stacker = Stacker()
    stacker.eval('true {"This won\'t fail" echo} if')
    # echo doesn't push to stack, but we can verify no error occurred
    assert True  # If we got here, it worked


def test_apostrophe_with_false_condition():
    """Test apostrophe in string with false condition (shouldn't execute)."""
    stacker = Stacker()
    stacker.eval('false {"This won\'t print" echo} if')
    # Stack should be empty since the block didn't execute
    assert len(stacker.stack) == 0


def test_multiple_apostrophes():
    """Test multiple apostrophes in a string."""
    stacker = Stacker()
    stacker.eval('"It\'s working! Don\'t worry." drop')
    assert len(stacker.stack) == 0  # drop removed it from stack


def test_apostrophe_in_nested_blocks():
    """Test apostrophe in nested code blocks."""
    stacker = Stacker()
    stacker.eval('true {true {"won\'t"} if} if')
    result = stacker.stack.pop()
    assert result == "won't"


def test_apostrophe_with_ifelse():
    """Test apostrophe in ifelse blocks."""
    stacker = Stacker()
    stacker.eval('true {"it\'s true"} {"it\'s false"} ifelse')
    assert stacker.stack.pop() == "it's true"

    stacker = Stacker()
    stacker.eval('false {"it\'s true"} {"it\'s false"} ifelse')
    assert stacker.stack.pop() == "it's false"


def test_escaped_quotes():
    """Test escaped quotes in strings."""
    stacker = Stacker()
    stacker.eval('"Testing \\"quotes\\" inside" drop')
    assert len(stacker.stack) == 0  # Verifies no syntax error


def test_escaped_quotes_with_apostrophe():
    """Test both escaped quotes and apostrophes together."""
    stacker = Stacker()
    stacker.eval('"It\\"s a \\"test\\" that won\'t fail" drop')
    assert len(stacker.stack) == 0  # Verifies no syntax error
