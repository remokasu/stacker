from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from stacker.version import __version__

if TYPE_CHECKING:
    from stacker.engine.core import StackerCore


def _args(core: StackerCore) -> list[str]:
    """``args``: the command-line arguments of the program, as a new list of strings."""
    root = core
    while root.parent is not None:
        root = root.parent
    return list(root.arguments)


def _script_path(core: StackerCore) -> str | None:
    """``script-path``: the absolute path of the file that is running, or null in the REPL and -e."""
    return core.current_file


def _main_script_path(core: StackerCore) -> str | None:
    """``main-script-path``: the absolute path of the script the command line ran, or null in the REPL and -e."""
    root = core
    while root.parent is not None:
        root = root.parent
    return root.main_script


def _is_main(core: StackerCore) -> bool:
    """``main?``: whether the running code is the script the command line ran (not an included file); true in the REPL and -e."""
    return core.current_file == _main_script_path(core)


def _script_dir(core: StackerCore) -> str | None:
    """``script-dir``: the directory of the file that is running, or null in the REPL and -e."""
    return None if core.current_file is None else str(Path(core.current_file).parent)


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
    "args": {
        "func": (lambda stack, core: _args(core)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "The command-line arguments after the script name, as a list of strings (`stacker s.stk 200 100` gives ['200' '100'])",
    },
    "script-path": {
        "func": (lambda stack, core: _script_path(core)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "The absolute path of the file that is running (inside an included file, that file); null in the REPL and with -e",
    },
    "main-script-path": {
        "func": (lambda stack, core: _main_script_path(core)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "The absolute path of the script the command line ran; null in the REPL and with -e",
    },
    "main?": {
        "func": (lambda stack, core: _is_main(core)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Whether the running code is the script the command line ran (false inside an included file; true in the REPL and with -e)",
    },
    "script-dir": {
        "func": (lambda stack, core: _script_dir(core)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "The directory of the file that is running; null in the REPL and with -e",
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
