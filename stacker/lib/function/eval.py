from __future__ import annotations

from stacker.compiler import py_eval
from stacker.error import StackerSyntaxError


def stacker_eval(expr: str):
    """Evaluates a given RPN expression.
    Returns the result of the evaluation.
    """
    if not isinstance(expr, str):
        raise StackerSyntaxError("Invalid expression")
    if (expr.startswith("'") and expr.endswith("'")) or (
        expr.startswith('"') and expr.endswith('"')
    ):
        return eval(expr[1:-1])
    else:
        return eval(expr)


eval_operators = {
    "eval": {
        "func": (lambda pyexpr: stacker_eval(pyexpr)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Evaluates a Python expression. ex) 1+2 eval",
    },
    # "ipy": {
    #     "func": (lambda code: py_eval(code, globals=globals())),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "Import Python module."
    # },
    # "py": {
    #     "func": (lambda code: py_eval(code)),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "excute Python module."
    # },
}
