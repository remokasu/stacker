from __future__ import annotations

import ast
from collections import deque
from typing import TYPE_CHECKING, Any

from stacker.constant import constants
from stacker.error import (
    StackUnderflowError,
    StackerSyntaxError,
    UndefinedSymbolError,
    UnexpectedTokenError,
)
from stacker.lib.function.algebra import alge_operators
from stacker.lib.function.arith import arith_operators
from stacker.lib.function.base import base_operators
from stacker.lib.function.bitwise import bitwise_operators
from stacker.lib.function.comparison import compare_operators
from stacker.lib.function.eval import eval_operators
from stacker.lib.function.file import file_operators
from stacker.lib.function.io import io_operators
from stacker.lib.function.list import list_operators
from stacker.lib.function.logic import logic_operators
from stacker.lib.function.math import math_operators
from stacker.lib.function.random import random_operators
from stacker.lib.function.stack import stack_operators
from stacker.lib.function.string import string_operators
from stacker.lib.function.time import time_operators
from stacker.lib.function.types import type_operators
from stacker.lib.function.loop import loop_operators
from stacker.lib.function.if_else import condition_operators
from stacker.lib.function.include import include_operators
from stacker.lib.function.setting import settings_operators
from stacker.lib.function.exit import exit_operators
from stacker.lib.function.defun import defun_operators
from stacker.lib.function.alias import macro_operators
from stacker.syntax.parser import (
    convert_custom_string_tuple_to_proper_tuple,
    is_array,
    is_block,
    # is_contains_transpose_command,
    # is_label_symbol,
    is_reference_symbol,
    is_string,
    # is_transpose_command,
    is_tuple,
    is_undefined_symbol,
    parse_expression,
)
from stacker.reserved import __BREAK__, __TRANSPOSE__

if TYPE_CHECKING:
    from stacker.sfunction import StackerFunction
    from stacker.smacro import StackerMacro


special_operators = {
    "ans": {
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Returns the last result.",
    },
    "set": {
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Sets a variable.",
    },
    "eval": {
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Evaluates a given RPN expression.",
    },
    "break": {
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Breaks a loop.",
    },
}


class StackerCore:
    """A class for evaluating RPN expressions."""

    depth_counter = 0

    def __init__(
        self, expression: str | None = None, parent: StackerCore | None = None
    ):
        self.parent = parent
        self.depth = StackerCore.depth_counter
        StackerCore.depth_counter += 1
        self.expression = expression
        if self.expression is not None:
            self.tokens = parse_expression(self.expression)
        self.child = None
        self.trace: list[Any] = []  # for error trace
        self.stack: deque[Any] = deque()
        if self.parent is not None:  # it is a substack of a parent stacker
            self.operators = self.parent.operators
            self.priority_operators = self.parent.priority_operators
            self.stack_operators = self.parent.stack_operators
            self.settings_operators = self.parent.settings_operators
            self.macros = self.parent.macros
            self.variables = self.parent.variables
            self.plugins = self.parent.plugins
            self.sfunctions = self.parent.sfunctions
            self.labels = self.parent.labels
            return

        # it is a root stacker
        self.operators = {}
        self.operators.update(alge_operators)
        self.operators.update(arith_operators)
        self.operators.update(base_operators)
        self.operators.update(bitwise_operators)
        self.operators.update(compare_operators)
        self.operators.update(file_operators)
        self.operators.update(io_operators)
        self.operators.update(logic_operators)
        self.operators.update(math_operators)
        self.operators.update(random_operators)
        self.operators.update(type_operators)
        self.operators.update(list_operators)
        self.operators.update(eval_operators)
        self.operators.update(string_operators)
        self.operators.update(time_operators)

        self.priority_operators = {}
        self.priority_operators.update(loop_operators)
        self.priority_operators.update(condition_operators)
        self.priority_operators.update(special_operators)
        self.priority_operators.update(include_operators)
        self.priority_operators.update(defun_operators)
        self.priority_operators.update(macro_operators)
        self.priority_operators.update(exit_operators)

        self.stack_operators = stack_operators

        self.settings_operators = settings_operators

        self.variables = {}
        self.variables.update(constants)

        self.macros = {}

        self.plugins = {}

        self.sfunctions = {}

        self.labels = {}

        self.plugin_descriptions = {}

        self._disp_stack_mode = True
        self._disp_logo = True
        self._disp_ans = False

        self._ans = None

    def _substack(self, token: str, stack: deque) -> None:
        """Creates a substack.
        :param token: {...}.
        """
        expression = token[1:-1]
        self.child = type(self)(expression=expression, parent=self)
        stack.append(self.child)

    def _pop_and_eval(self, stack: deque) -> Any:
        value = stack.pop()
        if isinstance(value, StackerCore):
            value._evaluate(value.tokens, stack=value.stack)
            sub = value.stack
            if sub:
                stack.extend(sub)
            return stack.pop()
        else:
            if isinstance(value, (list, tuple)):
                return value
            elif is_string(value):
                return value[1:-1]  # 'hoge' -> hoge
            return self.variables.get(value, value)

    # ========================
    # Evaluation
    # ========================

    def _evaluate(self, tokens: list, stack: deque = deque()) -> deque:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        # enum_tokens = enumerate(tokens)
        # for index, token in enum_tokens:
        for token in tokens:
            self.trace.append(token)
            if not isinstance(token, str):
                stack.append(token)  # Literal value
            elif (
                token in self.operators
                or token in self.priority_operators
                or token in self.stack_operators
                or token in self.settings_operators
                or token in self.sfunctions
                or token in self.plugins
            ):
                self._execute(token, stack)
                self._clear_trace()
            elif token in self.macros:
                self._expand_macro(token, stack)
            elif (
                token in self.variables
                or is_tuple(token)
                or is_array(token)
                or is_string(token)
            ):
                stack.append(token)
            # elif is_transpose_command(token):
            #     # Example: [1 2; 3 4]^T
            #     self._execute(__TRANSPOSE__, stack)
            # elif is_contains_transpose_command(token):
            #     # Example: A^T
            #     token = token[:-2]
            #     if token in self.variables:
            #         stack.append(self.variables[token])
            #         self._execute(__TRANSPOSE__, stack)
            elif is_undefined_symbol(token):
                token = token[1:]
                stack.append(token)
            elif is_reference_symbol(token):
                token = token[1:]
                if token in self.variables:
                    stack.append(self.variables[token])
                else:
                    raise UndefinedSymbolError(token)
            elif is_block(token):
                self._substack(token, stack)
            else:
                raise UnexpectedTokenError(token)
        return stack

    def _execute(self, token: str, stack: deque) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        if token in self.sfunctions:  # sfunctions
            args = []
            sfunc = self.sfunctions[token]
            if sfunc["arg_count"] > len(stack):
                raise StackUnderflowError(token, sfunc["arg_count"])
            for _ in range(sfunc["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if sfunc["push_result_to_stack"]:
                stack.append(sfunc["func"](*args))
            else:
                sfunc["func"](*args)
        elif token in self.plugins:
            args = []
            op = self.plugins[token]
            if op["arg_count"] > len(stack):
                raise StackUnderflowError(token, op["arg_count"])
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.priority_operators:
            op = self.priority_operators[token]
            if op["arg_count"] > len(stack):
                raise StackUnderflowError(token, op["arg_count"])
            if token == "do":
                body = stack.pop()
                symbol = stack.pop()
                end_value = self._pop_and_eval(stack)
                start_value = self._pop_and_eval(stack)
                op["func"](start_value, end_value, symbol, body, self)
            elif token == "times":
                n_times = self._pop_and_eval(stack)
                body = stack.pop()
                op["func"](n_times, body, self)
            elif token == "break":
                stack.append(__BREAK__)
            elif token == "if":
                condition = stack.pop()
                true_block = stack.pop()
                op["func"](condition, true_block, self)
            elif token == "ifelse":
                condition = stack.pop()
                false_block = stack.pop()
                true_block = stack.pop()
                op["func"](condition, true_block, false_block, self)
            elif token == "iferror":
                catch_block = stack.pop()
                try_block = stack.pop()
                op["func"](try_block, catch_block, self)
            elif token == "set":
                name = stack.pop()
                value = self._pop_and_eval(stack)
                self.variables[name] = value
            elif token == "defun":
                name = stack.pop()
                body = stack.pop()
                fargs = self._pop_and_eval(stack)
                fargs = convert_custom_string_tuple_to_proper_tuple(fargs)
                fargs = ast.literal_eval(fargs)
                op["func"](self, name, fargs, body)
            elif token == "alias":
                name = stack.pop()
                body = stack.pop()
                op["func"](self, name, body)
            elif token == "eval":
                expression = stack.pop()
                if is_string(expression):
                    # 'hoge' -> hoge
                    self._eval(expression[1:-1], stack=stack)
                else:
                    raise StackerSyntaxError("Invalid expression.")
            elif token == "include":
                filename = stack.pop()
                op["func"](self, filename)
            elif token == "exit":
                op["func"]()
        elif token in self.stack_operators:  # stack operators
            args = [stack]
            op = self.stack_operators[token]
            if op["arg_count"] > len(stack):
                raise StackUnderflowError(token, op["arg_count"])
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.settings_operators:  # settings operators
            op = self.settings_operators[token]
            if op["arg_count"] > len(stack):
                raise StackUnderflowError(token, op["arg_count"])
            if token == "disable_plugin":
                operator_name = stack.pop()
                op["func"](self, operator_name)
            else:
                op["func"](self)
        elif token in self.operators:  # Other operators
            args = []
            op = self.operators[token]
            if op["arg_count"] > len(stack):
                raise StackUnderflowError(token, op["arg_count"])
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        else:
            raise StackerSyntaxError(f"Unknown operator '{token}'")
        return

    def _expand_macro(self, name: str, stack: deque) -> None:
        """Executes a macro."""
        macro: StackerMacro = self.macros[name]
        expression = macro.blockstack.expression
        tokens = parse_expression(expression)
        self._evaluate(tokens, stack=stack)

    def _eval(self, expr: str, stack: deque = deque()) -> deque:
        tokens = parse_expression(expr)
        self._evaluate(tokens, stack=stack)
        return stack

    def _clear_trace(self) -> None:
        self.trace = []
