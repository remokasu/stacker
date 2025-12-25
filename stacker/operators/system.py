from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore


def _vars(core: StackerCore) -> None:
    """
    Display all defined variables.
    Example:
        stacker> 5 $x set
        stacker> 10 $y set
        stacker> vars
        x = 5
        y = 10
    """
    variables = core.variables
    if len(variables) == 0:
        print("No variables defined.")
        return
    for key, value in variables.items():
        print(f"{key} = {value}")


def _funcs(core: StackerCore) -> None:
    """
    Display all defined functions.
    Example:
        stacker> {x} {x x *} $square defun
        stacker> funcs
        square: {x} {x x *}
    """
    functions = core.sfunctions
    if len(functions) == 0:
        print("No functions defined.")
        return
    for name, func_dict in functions.items():
        func = func_dict["func"]
        print(f"{name}: args={func.args}, body={func.blockstack}")


def _macros(core: StackerCore) -> None:
    """
    Display all defined macros.
    Example:
        stacker> {x} {x x *} $square defmacro
        stacker> macros
        square: {x} {x x *}
    """
    macros = core.macros
    if len(macros) == 0:
        print("No macros defined.")
        return
    for name, macro in macros.items():
        print(f"{name}: {macro.blockstack}")


def _operators(core: StackerCore) -> None:
    """
    Display all available operators grouped by category.
    Example:
        stacker> operators
        Regular operators:
          +: Addition
          -: Subtraction
          ...
        Stack operators:
          dup: Duplicate top of stack
          ...
    """
    print("Regular operators:")
    regular_ops = {}
    regular_ops.update(core.operator_manager.get_regular_descriptions())
    regular_ops.update(core.operator_manager.get_priority_descriptions())
    for name, desc in regular_ops.items():
        print(f"  {name}: {desc}")

    print("\nStack operators:")
    for name, desc in core.operator_manager.get_stack_descriptions().items():
        print(f"  {name}: {desc}")

    print("\nSettings operators:")
    for name, desc in core.operator_manager.get_settings_descriptions().items():
        print(f"  {name}: {desc}")

    print("\nSystem operators:")
    for name, desc in core.operator_manager.get_system_descriptions().items():
        print(f"  {name}: {desc}")


# Export operators
system_operators = {
    "vars": {
        "func": (lambda stack, core: _vars(core)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Display all defined variables.",
    },
    "funcs": {
        "func": (lambda stack, core: _funcs(core)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Display all defined functions.",
    },
    "macros": {
        "func": (lambda stack, core: _macros(core)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Display all defined macros.",
    },
    "operators": {
        "func": (lambda stack, core: _operators(core)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Display all available operators.",
    },
}
