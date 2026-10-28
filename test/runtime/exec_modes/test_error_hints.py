"""Pins the hint the error display adds for each kind of error.

The hint is chosen from the error's class name and message text, in a
fixed order of checks, so a change to any of these changes what the user
reads under ``hint:``. Every branch is listed here, including the ones no
word reaches from Stacker code, and a few cases that pin the order.
"""

from __future__ import annotations

import pytest

from stacker.error import (
    IncludeError,
    NoValueProducedError,
    ResultCountError,
    StackerIndexError,
    StackerRecursionError,
    StackerRuntimeError,
    StackerSyntaxError,
    StackerTypeError,
    StackUnderflowError,
    UndefinedSymbolError,
    UndefinedVariableError,
    UnterminatedTokenError,
    UserError,
)
from stacker.runtime.exec_modes.execution_mode import ExecutionMode
from stacker.stacker import Stacker


def _caused_by(error: BaseException, cause: BaseException) -> BaseException:
    """Returns ``error`` as if raised with ``from cause``."""
    error.__cause__ = cause
    return error


NAME_HINT = "To use the name itself, write `:{0}` or `{{{0}}}`"
BLOCK_HINT = "Make the block leave a value on the stack"
DOLIST_HINT = BLOCK_HINT + ", or use `dolist` for side-effect-only iteration"
RESULT_COUNT_HINT = "To keep several values for each element, collect them into one inside the function (e.g. 2 listn)"
UNDERFLOW_HINT = "Check that you have enough values on the stack before calling this operator"
EMPTY_DEQUE_HINT = "Stack underflow: Not enough elements on the stack for this operation"
ZERO_DIVISION_HINT = "Cannot divide by zero. Check your divisor value"
CONCAT_HINT = "Cannot mix string and number types. Use 'str' to convert numbers to strings"
PLUS_HINT = "The '+' operator requires compatible types (both numbers or both strings)"
MUL_HINT = "Multiplication requires numeric types or string * int"
ARITHMETIC_HINT = "Arithmetic operators require numeric types"
OPERAND_HINT = "Check that the operator receives compatible argument types"
SUBSCRIPT_HINT = "Cannot index into this type. Use `nth` to read an element of a list or a string"
CALLABLE_HINT = "This value cannot be called as a function"
KEY_HINT = "Variable '{0}' is not defined. Define it first: '0 {0} ='"
BRACKET_HINT = "Check for matching brackets: {} for code blocks, [] for lists"
QUOTE_HINT = "Check for matching quotes in strings"
FILE_HINT = "File not found. Check the file path is correct"
PERMISSION_HINT = "Permission denied. Check file permissions"
ATTRIBUTE_HINT = "This value does not have the requested attribute or method"

# (name, a factory making the error, the hint); the factory keeps the
# instances out of module import, so a constructor change fails one case
CASES = [
    ("user_error", lambda: UserError("MyError", "boom"), None),
    ("undefined_symbol", lambda: UndefinedSymbolError("foo"), NAME_HINT.format("foo")),
    ("undefined_symbol_no_backticks", lambda: UndefinedSymbolError("foo", "foo is missing"), None),
    ("undefined_variable", lambda: UndefinedVariableError("bar", "`bar` is not defined."), NAME_HINT.format("bar")),
    ("undefined_variable_no_backticks", lambda: UndefinedVariableError("bar", "bar is missing"), None),
    ("no_value_left_nothing", lambda: NoValueProducedError("map", "The block passed to `map` left nothing on the stack."), BLOCK_HINT),
    ("no_value_other", lambda: NoValueProducedError("map", "no value"), DOLIST_HINT),
    ("result_count", lambda: ResultCountError("two values"), RESULT_COUNT_HINT),
    ("stack_underflow", lambda: StackUnderflowError("+", 2), UNDERFLOW_HINT),
    ("empty_deque", lambda: IndexError("pop from an empty deque"), EMPTY_DEQUE_HINT),
    ("empty_list", lambda: IndexError("pop from empty list"), None),
    ("stacker_index", lambda: StackerIndexError("`nth` index 3 is out of range for a length of 2"), None),
    ("zero_division", lambda: ZeroDivisionError("division by zero"), ZERO_DIVISION_HINT),
    ("type_concat", lambda: TypeError('can only concatenate str (not "int") to str'), CONCAT_HINT),
    ("type_concat_short", lambda: TypeError("concatenate str"), CONCAT_HINT),
    ("type_plus", lambda: TypeError("unsupported operand type(s) for +: 'int' and 'str'"), PLUS_HINT),
    ("type_plus_before_mul", lambda: TypeError("unsupported operand type(s) for *: 'int' and '+'"), PLUS_HINT),
    ("type_mul", lambda: TypeError("unsupported operand type(s) for *: 'list' and 'float'"), MUL_HINT),
    ("type_minus", lambda: TypeError("unsupported operand type(s) for -: 'str' and 'int'"), ARITHMETIC_HINT),
    ("type_div", lambda: TypeError("unsupported operand type(s) for /: 'str' and 'int'"), ARITHMETIC_HINT),
    ("type_other_operand", lambda: TypeError("unsupported operand type(s) for @: 'int' and 'int'"), OPERAND_HINT),
    ("type_subscript", lambda: TypeError("'int' object is not subscriptable"), SUBSCRIPT_HINT),
    ("type_callable", lambda: TypeError("'int' object is not callable"), CALLABLE_HINT),
    ("type_unknown", lambda: TypeError("bad type"), None),
    ("type_wins_over_file_cause", lambda: _caused_by(TypeError("bad type"), FileNotFoundError("x")), None),
    ("stacker_type", lambda: StackerTypeError("`-` cannot use 1 and [1 2] together"), None),
    ("key_error", lambda: KeyError("name"), KEY_HINT.format("name")),
    ("key_error_quoted", lambda: KeyError("'quoted'"), KEY_HINT.format("quoted")),
    ("syntax_bracket", lambda: SyntaxError("Unmatched bracket"), BRACKET_HINT),
    ("syntax_bracket_any_case", lambda: SyntaxError("UNMATCHED BRACKET"), BRACKET_HINT),
    ("syntax_paren", lambda: SyntaxError("Missing paren"), BRACKET_HINT),
    ("syntax_quote", lambda: SyntaxError("Unterminated quote"), QUOTE_HINT),
    ("stacker_syntax_bracket", lambda: StackerSyntaxError("Unmatched bracket"), BRACKET_HINT),
    ("stacker_syntax_quote", lambda: StackerSyntaxError("Unterminated quote"), QUOTE_HINT),
    ("stacker_syntax_other", lambda: StackerSyntaxError("`break` outside a loop"), None),
    ("unterminated_block", lambda: UnterminatedTokenError("block", 1), None),
    ("file_not_found_cause", lambda: _caused_by(StackerRuntimeError("`read-file` cannot open x"), FileNotFoundError("x")), FILE_HINT),
    ("file_not_found_raw", lambda: FileNotFoundError("x"), FILE_HINT),
    ("permission_cause", lambda: _caused_by(StackerRuntimeError("`write-file` cannot open x"), PermissionError("x")), PERMISSION_HINT),
    ("permission_raw", lambda: PermissionError("x"), PERMISSION_HINT),
    ("attribute", lambda: AttributeError("'int' object has no attribute 'upper'"), ATTRIBUTE_HINT),
    ("include", lambda: IncludeError("Circular include detected: a.stk"), None),
    ("recursion", lambda: StackerRecursionError("f", 10), None),
    ("runtime", lambda: StackerRuntimeError("x"), None),
    ("host_runtime", lambda: RuntimeError("x"), None),
    ("eof", lambda: EOFError("EOF when reading a line"), None),
]


@pytest.fixture(scope="module")
def hint_of():
    """The hint function under test: the one place to change if it moves."""
    return ExecutionMode(Stacker())._get_error_hint


@pytest.mark.parametrize("make_error, expected", [(make, expected) for _, make, expected in CASES], ids=[name for name, _, _ in CASES])
def test_hint(hint_of, make_error, expected):
    assert hint_of(make_error()) == expected
