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


def _enable_disp_stack(stacker: Stacker) -> None:
    stacker._disp_stack_mode = True


def _disable_disp_stack(stacker: Stacker) -> None:
    stacker._disp_stack_mode = False


def _enable_disp_logo(stacker: Stacker) -> None:
    stacker._disp_logo = True


def _disable_disp_logo(stacker: Stacker) -> None:
    stacker._disp_logo = False


def _enable_disp_ans(stacker: Stacker) -> None:
    stacker._disp_ans = True


def _disable_disp_ans(stacker: Stacker) -> None:
    stacker._disp_ans = False


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
    "enable_disp_stack": {
        "func": (lambda stacker: _enable_disp_stack(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Enables showing stack.",
    },
    "disable_disp_stack": {
        "func": (lambda stacker: _disable_disp_stack(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Disables showing stack.",
    },
    "disable_disp_logo": {
        "func": (lambda stacker: _disable_disp_logo(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Disables showing logo.",
    },
    "enable_disp_logo": {
        "func": (lambda stacker: _enable_disp_logo(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Enables showing logo.",
    },
    "enable_disp_ans": {
        "func": (lambda stacker: _enable_disp_ans(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Enables showing ans.",
    },
    "disable_disp_ans": {
        "func": (lambda stacker: _disable_disp_ans(stacker)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Disables showing ans.",
    },
}
