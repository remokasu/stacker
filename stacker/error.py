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
    pass


class StackUnderflowError(StackerError):
    """Stack underflow error"""

    def __init__(self, operator: str, num_args: int):
        message = f"Operator `{operator}` requires {num_args} arguments."
        super().__init__(message)


class StackerSyntaxError(StackerError):
    """Syntax error"""

    def __init__(self, message):
        if message is None:
            message = "An error occurred while parsing the expression."
        super().__init__(message)


class UnexpectedTokenError(StackerError):
    """Unexpected token error"""

    def __init__(self, token, message=None):
        if message is None:
            message = f"`{token}`. If `{token}` is intended as a variable or symbol, ensure it is defined or prepend it with '$'."
        super().__init__(message)


class UndefinedVariableError(StackerError):
    """Undefined variable error"""

    def __init__(self, token, message=None):
        if message is None:
            message = f"`{token}` is not defined."
        super().__init__(message)


class UndefinedSymbolError(StackerError):
    """Undefined symbol error"""

    def __init__(self, token, message=None):
        if message is None:
            message = f"`{token}` is not defined."
        super().__init__(message)


class SemanticError(StackerError):
    """Semantic error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while evaluating the expression."
        super().__init__(message)


class StackerRuntimeError(StackerError):
    """Runtime error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred during execution."
        super().__init__(message)


class ResourceError(StackerError):
    """Resource error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while allocating resources."
        super().__init__(message)


class ValidationError(StackerError):
    """Validation error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while validating the input."
        super().__init__(message)


class LoadPluginError(StackerError):
    """Load plugin error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while loading the plugin."
        super().__init__(message)


class IncludeError(StackerError):
    """Include error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while including the file."
        super().__init__(message)


class ScriptReadError(StackerError):
    """Script read error"""

    def __init__(self, message=None):
        if message is None:
            message = "An error occurred while reading the script."
        super().__init__(message)


class DropError(Exception):
    pass


class DupError(Exception):
    pass


class OverError(Exception):
    pass


class SwapError(Exception):
    pass


class RollError(Exception):
    pass


class RotError(Exception):
    pass


class PickError(Exception):
    pass


class NipError(Exception):
    pass


class InsertError(Exception):
    pass
