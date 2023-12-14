from __future__ import annotations

from time import time


def _time() -> float:
    """Returns the current time in seconds since the Epoch."""
    return time()


time_operators = {
    "time": {
        "func": (lambda: _time()),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Returns the current time in seconds since the Epoch.",
    },
}
