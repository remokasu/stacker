from __future__ import annotations

import random


def _rand() -> float:
    try:
        return random.random()
    except ValueError:
        raise ValueError("Cannot generate random float")


def _randint(x1: int, x2: int) -> int:
    try:
        return random.randint(int(x1), int(x2))
    except ValueError:
        raise ValueError(f"Cannot generate random int between {x1} and {x2}")


def _uniform(x1: float, x2: float) -> float:
    try:
        return random.uniform(float(x1), float(x2))
    except ValueError:
        raise ValueError(f"Cannot generate random float between {x1} and {x2}")


def _dice(num_dice: int, num_faces: int) -> int:
    # Roll dice (e.g., 3d6)
    try:
        return sum(random.randint(1, int(num_faces)) for _ in range(int(num_dice)))
    except ValueError:
        raise ValueError(f"Cannot roll {num_dice}d{num_faces}")


random_operators = {
    "rand": {
        "func": (lambda: _rand()),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Generate random float between 0 and 1",
    },
    "randint": {
        "func": (lambda x1, x2: _randint(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate random int between x1 and x2",
    },
    "uniform": {
        "func": (lambda x1, x2: _uniform(x1, x2)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate random float between x1 and x2",
    },
    "dice": {
        "func": (lambda num_dice, num_faces: _dice(num_dice, num_faces)),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Roll D&D-style dice (e.g., 3d6 = 3 6 dice)",
    },
}
