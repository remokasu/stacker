from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.version import __version__

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore


def _vars(core: StackerCore) -> None:
    """
    Display all defined variables.
    Example:
        stacker> 5 :x set
        stacker> 10 :y set
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
        stacker> {x} {x x *} :square defun
        stacker> funcs
        square: {x} {x x *}
    """
    functions = core.sfunctions
    if len(functions) == 0:
        print("No functions defined.")
        return
    prelude_names = core._prelude["names"]
    for name, func_dict in functions.items():
        func = func_dict["func"]
        suffix = " (prelude)" if name in prelude_names else ""
        print(f"{name}: args={func.args}, body={func.blockstack}{suffix}")


def _macros(core: StackerCore) -> None:
    """
    Display all defined macros.
    Example:
        stacker> {x} {{x x *}} :square defmacro
        stacker> macros
        square: {x} {{x x *}}
    """
    macros = core.macros
    if len(macros) == 0:
        print("No macros defined.")
        return
    for name, macro in macros.items():
        suffix = " (prelude)" if getattr(macro, "is_prelude", False) else ""
        print(f"{name}: {macro!r}{suffix}")


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

    for title, descriptions in (
        ("Higher-order operators:", core.operator_manager.get_hof_descriptions()),
        ("Aggregate operators:", core.operator_manager.get_aggregate_descriptions()),
        ("Transform operators:", core.operator_manager.get_transform_descriptions()),
        ("Array and dictionary operators:", core.operator_manager.get_collection_descriptions()),
    ):
        print(f"\n{title}")
        for name, desc in descriptions.items():
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
    "version": {
        "func": (lambda stack, core: __version__),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": f"Pushes the version of this Stacker as a string: version -> '{__version__}'",
    },
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
