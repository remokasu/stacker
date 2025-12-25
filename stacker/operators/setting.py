from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stacker.stacker import Stacker


def _disable_plugin(stacker: Stacker, operator_name: str) -> None:
    if operator_name in stacker.plugins:
        del stacker.plugins[operator_name]
    else:
        print(f"Plugin '{operator_name}' is not registered.")


def _disable_all_plugins(stacker: Stacker) -> None:
    stacker.plugins = {}


settings_operators = {
    "disable_plugin": {
        "func": (
            lambda stacker, operator_name: _disable_plugin(stacker, operator_name)
        ),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Disables a plugin.",
    },
    "disable_all_plugins": {
        "func": (lambda stacker: _disable_all_plugins(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Disables all plugins.",
    },
}
