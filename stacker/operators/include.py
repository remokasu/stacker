from __future__ import annotations

from stacker.include.include import include_file


include_operators = {
    "include": {
        "func": (lambda stacker, filename: include_file(stacker, filename)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": 'Runs another script here, in the current scope, every time it is included: "lib.stk" include',
    },
    "require": {
        "func": (lambda stacker, filename: include_file(stacker, filename, once=True)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": 'Runs another script once per interpreter; requiring it again does nothing: "lib.stk" require',
    },
}
