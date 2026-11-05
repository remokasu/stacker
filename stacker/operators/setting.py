from __future__ import annotations

from typing import TYPE_CHECKING

from stacker.lang import console

if TYPE_CHECKING:
    from stacker.lang.protocols import CoreView


def _disable_plugin(stacker: CoreView, operator_name: str) -> None:
    if operator_name in stacker.plugins:
        del stacker.plugins[operator_name]
        stacker.operator_manager.words_changed()
        # A bare StackerCore keeps no descriptions; a CoreView shares them with its cores
        getattr(stacker, "plugin_descriptions", {}).pop(operator_name, None)
    else:
        print(f"Plugin '{operator_name}' is not registered.", file=console.stdout())


def _disable_all_plugins(stacker: CoreView) -> None:
    # Emptied in place: every child core (a block, a function body, an
    # included file) shares these tables with the root
    if stacker.plugins:
        stacker.plugins.clear()
        stacker.operator_manager.words_changed()
    getattr(stacker, "plugin_descriptions", {}).clear()


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
