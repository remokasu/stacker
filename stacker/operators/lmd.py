from __future__ import annotations

from stacker.engine.slambda import StackerLambda


lambda_operators = {
    "lambda": {
        "func": lambda fargs, body: StackerLambda(fargs, body),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Defines a function.",
    },
}
