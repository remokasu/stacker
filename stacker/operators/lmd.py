from __future__ import annotations

from stacker.engine.slambda import StackerLambda


lambda_operators = {
    "lambda": {
        "func": lambda fargs, body: StackerLambda(fargs, body),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Makes an anonymous function value (call it with eval); a call pushes every value its body leaves: {args} {body} lambda",
    },
}
