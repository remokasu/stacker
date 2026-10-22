from __future__ import annotations

from fractions import Fraction

from stacker.engine.data_type import Array, Symbol
from stacker.engine.slambda import StackerLambda
from stacker.error import StackerTypeError, symbol_as_value_message
from stacker.util.disp import display_text, plain_text

#: The name `type` gives each kind of value, in the order the kinds are told apart
#: (a bool before an int, an array before a list, a string literal with any string).
_TYPE_NAMES: tuple[tuple[type, str], ...] = (
    (bool, "bool"),
    (int, "int"),
    (float, "float"),
    (complex, "complex"),
    (Fraction, "fraction"),
    (str, "str"),
    (Array, "array"),
    (list, "list"),
    (dict, "dict"),
    (Symbol, "symbol"),
    (StackerLambda, "lambda"),
)


def _type_name(x: object) -> Symbol:
    """``x type``: the kind of ``x`` as a symbol (`:int`, `:str`, `:array`, `:null`, ...). A block is evaluated as an argument first."""
    if x is None:
        return Symbol("null")
    for kind, name in _TYPE_NAMES:
        if isinstance(x, kind):
            return Symbol(name)
    return Symbol(type(x).__name__)  # a value a plugin pushed: its host class name


def _convert(word: str, convert: type, kind: str):  # type: ignore[no-untyped-def]
    """Wraps ``int`` / ``float`` so a value that cannot be read names the word."""

    def apply(x: object) -> object:
        if isinstance(x, Symbol):
            raise StackerTypeError(symbol_as_value_message(word, x.name))
        try:
            return convert(x)
        except ValueError as error:
            raise StackerTypeError(f"`{word}` cannot read {plain_text(x)} as {kind}") from error
        except TypeError as error:
            raise StackerTypeError(f"`{word}` expects a number or a string, got {plain_text(x)}") from error

    return apply


type_operators = {
    "int": {
        "func": _convert("int", int, "an integer"),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to int",
    },
    "float": {
        "func": _convert("float", float, "a number"),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to float",
    },
    "str": {
        "func": (lambda x: display_text(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to str",
    },
    "bool": {
        "func": (lambda x: bool(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to bool",
    },
    "complex": {
        "func": (lambda x: complex(x)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Convert to complex",
    },
    "type": {
        "func": _type_name,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "The kind of a value as a symbol: :int :float :complex :fraction :bool :str :list :array :dict :symbol :lambda :null (a plugin's value: its class name)",
    },
    "int?": {
        "func": (lambda x: isinstance(x, int) and not isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is an int",
    },
    "float?": {
        "func": (lambda x: isinstance(x, float)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a float",
    },
    "str?": {
        "func": (lambda x: isinstance(x, str)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a string",
    },
    "bool?": {
        "func": (lambda x: isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a bool",
    },
    "complex?": {
        "func": (lambda x: isinstance(x, complex)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a complex number",
    },
    "list?": {
        "func": (lambda x: isinstance(x, list) and not isinstance(x, Array)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a list (an array is not a list)",
    },
    "array?": {
        "func": (lambda x: isinstance(x, Array)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is an array",
    },
    "dict?": {
        "func": (lambda x: isinstance(x, dict)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a dictionary",
    },
    "number?": {
        "func": (lambda x: isinstance(x, (int, float, complex)) and not isinstance(x, bool)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a number (int, float, or complex)",
    },
    "symbol?": {
        "func": (lambda x: isinstance(x, Symbol)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Returns true if the value is a symbol (:name)",
    },
}
