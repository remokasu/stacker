from __future__ import annotations

from stacker.error import StackerSyntaxError

# def _stacker_eval(expr: str, stacker: "Stacker"):
#     """Evaluates a given RPN expression.
#     Returns the result of the evaluation.
#     """
#     if not isinstance(expr, str):
#         raise StackerSyntaxError("Invalid expression")
#     if (expr.startswith("'") and expr.endswith("'")) or (
#         expr.startswith('"') and expr.endswith('"')
#     ):
#         return eval(expr[1:-1])
#     else:
#         raise StackerSyntaxError("Invalid expression. Only string is allowed.")


eval_operators = {
    # "eval": {
    # },
}
