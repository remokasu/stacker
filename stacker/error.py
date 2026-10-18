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


def attach_include_location(
    error: BaseException,
    file: str,
    line: int | None,
    source_line: str | None,
    frames: list[tuple[str, int | None]],
) -> None:
    """Records where inside an included file ``error`` was raised, once.

    Nested includes each try to attach their own position; only the
    innermost (first) one sticks. The message is left alone: the position
    travels as attributes for the error display to use.

    Args:
        error: The exception raised while an included file was running.
        file: Absolute path of the file that was running.
        line: First line of the expression that was running, if known.
        source_line: Text of that line, if known.
        frames: The files that included it, innermost first, each with the
            line of the expression that did the including (``None`` when
            the includer has no line, as the REPL and ``-e`` have none).
    """
    if include_location_of(error) is not None:
        return
    error.include_location = (file, line, source_line)  # type: ignore[attr-defined]
    error.include_frames = frames  # type: ignore[attr-defined]


def include_location_of(
    error: BaseException,
) -> tuple[tuple[str, int | None, str | None], list[tuple[str, int | None]]] | None:
    """The include position ``error`` carries, looking through the exceptions it was raised from.

    A word that re-raises an error ``from`` the original (a type error
    attributed to the word, an index error turned into a stack underflow)
    keeps the position on the original; only the ``__cause__`` chain is
    followed, never ``__context__``, so an error raised while handling
    another (a `iferror` catch block) is not placed in the file the first
    one came from.

    Args:
        error: The exception being reported.

    Returns:
        ``((file, line, source_line), frames)`` or None.
    """
    current: BaseException | None = error
    while current is not None:
        location = getattr(current, "include_location", None)
        if location is not None:
            return location, getattr(current, "include_frames", [])
        current = current.__cause__
    return None


def copy_include_location(source: BaseException, target: BaseException) -> None:
    """Moves the include position of ``source`` onto ``target``, if it has one.

    Args:
        source: The exception that was raised inside an included file.
        target: The exception that replaces it.
    """
    found = include_location_of(source)
    if found is not None:
        target.include_location, target.include_frames = found  # type: ignore[attr-defined]


class StackUnderflowError(StackerError):
    """Stack underflow error"""

    def __init__(self, operator: str, num_args: int, message: str | None = None) -> None:
        if message is None:
            message = f"Operator `{operator}` requires {num_args} arguments."
        super().__init__(message)


def word_in_list_literal_message(name: str) -> str:
    """The message for a word written inside a list literal, which holds values only.

    Args:
        name: The word as written (`dup`, `+`, ...).

    Returns:
        A message that says how to build the list on the stack instead.
    """
    return (
        f"`{name}` is a word, and a list literal holds values only. "
        f"Build the list on the stack and collect it with `listn`: ... {name} ... n listn, "
        f"or run the words in a block and collect what they leave: {{... {name} ...}} collect"
    )


def not_a_sequence_message(word: str) -> str:
    """The message for a dictionary handed to ``word``, which goes through a sequence.

    Args:
        word: The word that received the dictionary.

    Returns:
        A message that says to go through the keys instead.
    """
    return f"`{word}` cannot go through a dictionary; go through its keys: d keys :k {{...}} dolist"


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


class UserError(StackerError):
    """An error the program raised itself with `throw`.

    ``kind`` is shown where a built-in error shows its class name, so a
    program can name its errors as it likes (``IllegalArgumentException``,
    ``empty queue``); ``message`` is the text.
    """

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message

    def __reduce__(self) -> tuple[type[UserError], tuple[str, str]]:
        return (UserError, (self.kind, self.message))


def error_kind(error: BaseException) -> str:
    """The kind of ``error`` as the display and `try` show it: the `throw` kind or the class name."""
    if isinstance(error, UserError):
        return error.kind
    return type(error).__name__


class StackerSyntaxError(StackerError):
    """Syntax error"""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "An error occurred while parsing the expression."
        super().__init__(message)


class UnterminatedTokenError(StackerSyntaxError):
    """Raised when input ends inside an unterminated construct.

    Covers strings (single or triple quoted), lists, code blocks, and
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


class StackerIndexError(StackerError, IndexError):
    """Raised when an index points outside an array or a list, or an empty array is popped.

    Also an ``IndexError`` so that callers catching Python's index errors
    keep working; the stack-underflow conversion in the executor goes by
    the message, so it is not mistaken for a missing argument.
    """


class KeyNotFoundError(StackerError):
    """Raised when a key is removed from a dictionary that does not have it.

    Not a ``KeyError``: the error display reads a ``KeyError`` as an
    undefined variable, which this is not.
    """


class ResultCountError(StackerError):
    """Raised when a function, lambda or block leaves more values than its context takes.

    `map` / `filter` read one value per element and `reduce` / `fold` one
    value per step; a body that leaves several is this error (leaving none
    is ``NoValueProducedError``).
    """


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
