from __future__ import annotations

"""
SyntaxError:
This error is thrown during syntax parsing when an unexpected token is found, or an expected token is not found.
Specifically, it occurs when the input expression does not follow the grammar of the language.

UnexpectedTokenError:
A subclass of SyntaxError, this error is thrown during syntax parsing when an unexpected token is encountered.
It is associated with a specific token.

SemanticError:
This error occurs during the evaluation of an expression.
It is thrown when an operation that is syntactically correct but semantically incorrect is performed,
such as referencing an undefined variable.

RuntimeError:
This error is thrown during the execution of the program when a problem occurs in the execution environment.
It includes situations such as memory shortage or failure to access external resources.

ResourceError:
This error is associated with the allocation and release of resources.
It is thrown when necessary resources are not adequately available.

ValidationError:
This error is thrown during the validation of input values when an invalid value is detected.
It applies when the input value is not of the expected type or is outside the allowable range.

LoadPluginError:
This error is thrown when an error occurs while loading a plugin.

UndefinedVariableError:
This error is thrown when an undefined variable is referenced.

------------------------------------------------------------------------------
"""


class StackerError(Exception):
    """Base class for every error Stacker raises on purpose."""


def attach_macro_context(error: StackerError, context: str) -> None:
    """Appends a macro context to ``error``'s message, once.

    Nested macros each try to attach their own context; only the innermost
    (first) one sticks, so a message never carries more than one.

    Args:
        error: Error raised while expanding a macro or running its expansion.
        context: Text such as ``"while expanding macro 'while'"``.
    """
    if getattr(error, "macro_context", None) is not None:
        return
    error.macro_context = context  # type: ignore[attr-defined]
    if error.args:
        error.args = (f"{error.args[0]} ({context})",) + tuple(error.args[1:])
    else:
        error.args = (f"({context})",)


class StackUnderflowError(StackerError):
    """Stack underflow error"""

    def __init__(self, operator: str, num_args: int, message: str | None = None) -> None:
        if message is None:
            message = f"Operator `{operator}` requires {num_args} arguments."
        super().__init__(message)


def symbol_as_value_message(word: str, name: str) -> str:
    """The message for a word that was handed a symbol where a value is needed.

    Args:
        word: The word that received the symbol.
        name: The symbol's name.

    Returns:
        A message that shows how to write the value and how to write the text.
    """
    return (
        f"`{word}` cannot use the symbol `{name}` as a value. "
        f"Write `{name}` for the variable's value, or `:{name} str` for its name as text."
    )


class StackerSyntaxError(StackerError):
    """Syntax error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while parsing the expression."
        super().__init__(message)


class UnterminatedTokenError(StackerSyntaxError):
    """Raised when input ends inside an unterminated construct.

    Covers strings (single or triple quoted), arrays, code blocks, and
    block comments. Raised by the lexer scan core once the input is
    final (script / ``-e`` / confirmed REPL input); interactive modes
    use ``analyze_terminals`` first to offer continuation input instead.
    """

    def __init__(self, what: str, start_line: int | None = None) -> None:
        message = f"Unterminated {what}"
        if start_line is not None:
            message += f" starting at line {start_line}"
        super().__init__(message)
        self.what = what
        self.start_line = start_line


class UnexpectedTokenError(StackerError):
    """Unexpected token error"""

    def __init__(self, token: str, message: str | None = None) -> None:
        if message is None:
            message = f"`{token}`. If `{token}` is intended as a variable or symbol, ensure it is defined or prepend it with ':'."
        super().__init__(message)


class UndefinedVariableError(StackerError):
    """Undefined variable error"""

    def __init__(self, token: str, message: str | None = None) -> None:
        if message is None:
            message = f"`{token}` is not defined."
        super().__init__(message)


class UndefinedSymbolError(StackerError):
    """Undefined symbol error"""

    def __init__(self, token: str, message: str | None = None) -> None:
        if message is None:
            message = f"`{token}` is not defined."
        super().__init__(message)


class StackerTypeError(StackerError, TypeError):
    """Raised when a value of the wrong type reaches a word.

    Also a ``TypeError`` so that callers catching Python's type errors keep
    working.
    """


class StackerRecursionError(StackerError):
    """Raised when Stacker-level function recursion exceeds the limit.

    Raised by the process-wide recursion guard (engine/recursion.py) at
    the entry of StackerFunction/StackerLambda calls, before the Python
    C stack is at risk. The limit counts Stacker recursion levels and
    can be changed with the --recursion-limit CLI flag.
    """

    def __init__(self, name: str, limit: int, kind: str = "function") -> None:
        message = f"Maximum recursion depth ({limit}) exceeded in {kind} `{name}`"
        super().__init__(message)
        self.name = name
        self.limit = limit
        self.kind = kind


class MacroExpansionError(StackerError):
    """Raised when a macro body leaves more than one value as its expansion."""

    def __init__(self, name: str, count: int) -> None:
        message = (
            f"Macro `{name}` must leave exactly one value as its expansion, "
            f"but left {count}."
        )
        super().__init__(message)
        self.name = name
        self.count = count


class PreludeLoadError(StackerError):
    """Raised when a prelude (slib) file fails to load."""

    def __init__(self, filename: str, cause: BaseException) -> None:
        super().__init__(f"Failed to load prelude file `{filename}`: {cause}")
        self.filename = filename


class NoValueProducedError(StackerError):
    """Raised when a block that must produce a value leaves the stack empty."""

    def __init__(self, operator: str, message: str | None = None) -> None:
        if message is None:
            message = (
                f"The block passed to `{operator}` must leave a value on the stack. "
                f"Use `dolist` for side-effect-only iteration."
            )
        super().__init__(message)


class SemanticError(StackerError):
    """Semantic error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while evaluating the expression."
        super().__init__(message)


class StackerRuntimeError(StackerError):
    """Runtime error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred during execution."
        super().__init__(message)


class ResourceError(StackerError):
    """Resource error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while allocating resources."
        super().__init__(message)


class ValidationError(StackerError):
    """Validation error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while validating the input."
        super().__init__(message)


class LoadPluginError(StackerError):
    """Load plugin error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while loading the plugin."
        super().__init__(message)


class IncludeError(StackerError):
    """Include error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while including the file."
        super().__init__(message)


class ScriptReadError(StackerError):
    """Script read error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while reading the script."
        super().__init__(message)


class BreakException(BaseException):
    """Raised by break to immediately exit a loop."""
    pass


class DropError(StackerError):
    pass


class DupError(StackerError):
    pass


class OverError(StackerError):
    pass


class SwapError(StackerError):
    pass


class RollError(StackerError):
    pass


class RotError(StackerError):
    pass


class PickError(StackerError):
    pass


class NipError(StackerError):
    pass


class InsertError(StackerError):
    pass
