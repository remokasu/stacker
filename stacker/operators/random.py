from __future__ import annotations

import random

from stacker.operators.arguments import integer_argument


def _rand() -> float:
    return random.random()


def _randint(x1: object, x2: object) -> int:
    return random.randint(integer_argument("randint", x1), integer_argument("randint", x2))


def _uniform(x1: float, x2: float) -> float:
    return random.uniform(float(x1), float(x2))


def _dice(num_dice: object, num_faces: object) -> int:
    # Roll dice (e.g., 3d6)
    count = integer_argument("dice", num_dice)
    faces = integer_argument("dice", num_faces)
    return sum(random.randint(1, faces) for _ in range(count))


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
