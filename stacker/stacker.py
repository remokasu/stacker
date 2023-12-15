from __future__ import annotations

import ast
import copy

from collections import deque
from typing import Any, Callable

from stacker.constant import constants
from stacker.error import (  # SemanticError,; StackerRuntimeError,; ResourceError,; ValidationError,; LoadPluginError,
    StackerSyntaxError,
    UnexpectedTokenError,
)
from stacker.include import include_stacker_script
from stacker.lib.function.algebra import alge_operators
from stacker.lib.function.arith import arith_operators
from stacker.lib.function.base import base_operators
from stacker.lib.function.bitwise import bitwise_operators
from stacker.lib.function.comparison import compare_operators
from stacker.lib.function.eval import eval_operators
from stacker.lib.function.io import io_operators
from stacker.lib.function.list import list_operators
from stacker.lib.function.logic import logic_operators
from stacker.lib.function.math import math_operators
from stacker.lib.function.random import random_operators
from stacker.lib.function.stack import stack_operators
from stacker.lib.function.types import type_operators
from stacker.lib.function.string import string_operators
from stacker.lib.function.time import time_operators
from stacker.syntax.parser import (
    convert_custom_string_tuple_to_proper_tuple,
    is_block,
    is_string,
    is_tuple,
    is_array,
    is_undefined_symbol,
    parse_expression,
)


class Stacker:
    """A class for evaluating RPN expressions."""

    depth_counter = 0

    def __init__(self, expression: str | None = None, parent: "Stacker" | None = None):
        self.parent = parent
        self.depth = Stacker.depth_counter
        Stacker.depth_counter += 1
        self.expression = expression
        if self.expression is not None:
            self.tokens = parse_expression(self.expression)
        self.child = None
        # self.stack: list[Any] = []
        self.stack: deque[Any] = deque()
        if self.parent is not None:  # it is a substack of a parent stacker
            self.operators = self.parent.get_operators_ref()
            self.priority_operators = self.parent.get_priority_operators_ref()
            self.macros = self.parent.get_macros_ref()
            self.variables = self.parent.get_variables_ref()
            self.sfunctions = self.parent.get_sfuntions_ref()
            return
        self.loop_operators = {
            "times": {
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Executes a block of code a specified number of times.",
            },
            "do": {
                "arg_count": 4,
                "push_result_to_stack": False,
                "desc": "Executes a block of code a specified number of times.",
            },
        }
        self.condition_operators = {
            "if": {
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Executes a block of code if a condition is true.",
            },
            "ifelse": {
                "arg_count": 3,
                "push_result_to_stack": False,
                "desc": (
                    "Executes a block of code if a condition is true, "
                    "otherwise executes another block of code."
                ),
            },
        }
        self.special_operators = {
            "set": {
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Sets a variable.",
            },
            "defun": {
                "arg_count": 3,
                "push_result_to_stack": False,
                "desc": "Defines a function.",
            },
            "alias": {
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Defines a macro.",
            },
            "include": {
                "arg_count": 1,
                "push_result_to_stack": False,
                "desc": "Includes another stacker script.",
            },
        }
        self.operators = {}
        self.operators.update(alge_operators)
        self.operators.update(arith_operators)
        self.operators.update(base_operators)
        self.operators.update(bitwise_operators)
        self.operators.update(compare_operators)
        self.operators.update(io_operators)
        self.operators.update(logic_operators)
        self.operators.update(math_operators)
        self.operators.update(random_operators)
        self.operators.update(type_operators)
        self.operators.update(list_operators)
        self.operators.update(stack_operators)
        self.operators.update(eval_operators)
        self.operators.update(string_operators)
        self.operators.update(time_operators)
        self.operators.update(self.condition_operators)
        self.operators.update(self.loop_operators)
        self.operators.update(self.special_operators)
        self.priority_operators = {}
        self.priority_operators.update(stack_operators)
        self.priority_operators.update(self.loop_operators)
        self.priority_operators.update(self.condition_operators)
        self.priority_operators.update(self.special_operators)
        self.variables = {}
        self.variables.update(constants)
        self.macros = {}
        self.plugins = {}
        self.sfunctions = {}
        self.operator_descriptions = {}
        for operator_name, operator_descriptions in self.operators.items():
            self.operator_descriptions[operator_name] = operator_descriptions["desc"]
        self.plugin_descriptions = {}

    # ========================
    # Include
    # ========================

    def include(self, filename: str) -> None:
        """Includes another stacker script."""
        _stacker = include_stacker_script(filename)
        _operator = _stacker.get_operators_ref()
        _macros = _stacker.get_macros_ref()
        _variables = _stacker.get_variables_copy()
        _sfunctions = _stacker.get_sfuntions_ref()
        self.operators.update(_operator)
        self.macros.update(_macros)
        self.variables.update(_variables)
        self.sfunctions.update(_sfunctions)

    # ========================
    # Substack
    # ========================

    def substack(self, token: str, stack: deque) -> None:
        """Creates a substack.
        :param token: {...}.
        """
        expression = token[1:-1]
        self.child = Stacker(expression=expression, parent=self)
        stack.append(self.child)

    # ========================
    # Stack
    # ========================

    def push(self, value: Any) -> None:  # TODO: remove
        self.stack.append(value)

    def pop_and_eval(self, stack: deque) -> Any:
        value = stack.pop()
        if isinstance(value, Stacker):
            value.evaluate(value.tokens, stack=value.stack)
            sub = value.get_stack_ref()
            if sub:
                stack.extend(sub)
            return stack.pop()
        else:
            if isinstance(value, (list, tuple)):
                return value
            return self.variables.get(value, value)

    # ========================
    # Loop (do, times)
    # ========================

    def execute_do(
        self,
        start_value: int,
        end_value: int,
        symbol: str,
        block: Stacker,
        stack: deque,
    ) -> None:
        result = []
        for i in range(start_value, end_value + 1):
            block.variables[symbol] = i
            result += block.evaluate(block.tokens, stack=block.stack)
        stack.extend(result)

    def execute_times(
        self, n_times: int, block: Stacker | Any, stack: deque = None
    ) -> None:
        """Executes a block of code a specified number of times."""
        if isinstance(block, Stacker):
            i_count = 0
            stack.append(i_count)
            while stack[-1] < n_times:
                stack.pop()
                block.evaluate(block.tokens, stack=block.stack)
                sub_stack = block.get_stack_ref()
                if len(sub_stack) > 0:
                    stack += sub_stack
                block.stack.clear()
                i_count = i_count + 1
                stack.append(i_count)
            stack.pop()
        else:  # e.g. a numeric object
            i_count = 0
            stack.append(i_count)
            while stack[-1] < n_times:
                stack.pop()
                stack.append(block)
                i_count = i_count + 1
                stack.append(i_count)
            stack.pop()

    # ========================
    # Condition (if, ifelse)
    # ========================

    def execute_if(
        self, condition: Stacker | bool, blockstack: Stacker | Any, stack: deque
    ) -> None:
        """Executes a block of code if a condition is true."""
        if isinstance(condition, Stacker):
            condition.evaluate(condition.tokens, stack=condition.stack)
            sub_stack = condition.get_stack_ref()
            if sub_stack:
                stack.extend(sub_stack)
            condition.stack.clear()
            condition = stack.pop()

        if condition:
            if isinstance(blockstack, Stacker):
                blockstack.evaluate(blockstack.tokens, stack=blockstack.stack)
                sub_stack = blockstack.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                    blockstack.stack.clear()
            else:  # e.g. a numeric object
                stack.append(blockstack)

    def execute_if_else(
        self,
        condition: Stacker | bool,
        true_block: Stacker | Any,
        false_block: Stacker | Any,
        stack: deque,
    ) -> None:
        """Executes a block of code if a condition is true, otherwise executes another block of code."""
        if isinstance(condition, Stacker):
            condition.evaluate(condition.tokens, stack=condition.stack)
            sub_stack = condition.get_stack_ref()
            if sub_stack:
                stack.extend(sub_stack)
            condition.stack.clear()
            condition = stack.pop()

        if condition:
            if isinstance(true_block, Stacker):
                true_block.evaluate(true_block.tokens, stack=true_block.stack)
                sub_stack = true_block.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                true_block.stack.clear()
            else:  # e.g. a numeric object
                stack.append(true_block)
        else:
            if isinstance(false_block, Stacker):
                false_block.evaluate(false_block.tokens, stack=false_block.stack)
                sub_stack = false_block.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                false_block.stack.clear()
            else:
                stack.append(false_block)

    # ========================
    # Evaluation
    # ========================

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=self.stack)

    def evaluate(self, tokens: list, stack: deque = deque()) -> deque:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        # Iterate over each token in the token list
        enum_tokens = enumerate(tokens)
        for index, token in enum_tokens:
            if not isinstance(token, str):
                stack.append(token)  # Literal value
            elif token in self.operators or token in self.sfunctions:
                # execute operator
                self._execute(token, stack)
            elif token in self.macros:
                # expand macro
                self.expand_macro(token, stack)
            elif token in self.variables or is_tuple(token) or is_array(token):
                stack.append(token)
            elif is_undefined_symbol(token):
                token = token[1:]
                stack.append(token)
            elif is_string(token):
                stack.append(token[1:-1])
            elif is_block(token):
                self.substack(token, stack)
            else:
                raise UnexpectedTokenError(token)
        return stack

    def _execute(self, token: str, stack: deque) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        if token in self.priority_operators:
            if token == "do":
                body = stack.pop()  # not evaluate
                symbol = stack.pop()
                end_value = self.pop_and_eval(stack)
                start_value = self.pop_and_eval(stack)
                self.execute_do(start_value, end_value, symbol, body, stack)
            elif token == "times":
                n_times = self.pop_and_eval(stack)
                body = stack.pop()
                self.execute_times(n_times, body, stack)
            elif token == "if":
                condition = stack.pop()
                true_block = stack.pop()
                self.execute_if(condition, true_block, stack)
            elif token == "ifelse":
                condition = stack.pop()
                false_block = stack.pop()
                true_block = stack.pop()
                self.execute_if_else(condition, true_block, false_block, stack)
            elif token == "set":
                name = stack.pop()
                value = self.pop_and_eval(stack)
                self.variables[name] = value
            elif token == "defun":
                name = stack.pop()
                body = stack.pop()
                fargs = self.pop_and_eval(stack)
                fargs = convert_custom_string_tuple_to_proper_tuple(fargs)
                fargs = ast.literal_eval(fargs)
                self.defun_sfunction(name, fargs, body)
            elif token == "alias":
                name = stack.pop()
                body = stack.pop()
                self.define_macro(name, body)
            elif token == "include":
                filename = stack.pop()
                self.include(filename)
            elif token in stack_operators:  # stack operators
                args = [stack]
                for _ in range(stack_operators[token]["arg_count"]):
                    args.insert(0, self.pop_and_eval(stack))
                op = stack_operators[token]
                if op["push_result_to_stack"]:
                    stack.append(op["func"](*args))
                else:
                    op["func"](*args)
        elif token in self.operators:  # Other operators
            args = []
            for _ in range(self.operators[token]["arg_count"]):
                args.insert(0, self.pop_and_eval(stack))
            op = self.operators[token]
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.sfunctions:  # sfunctions
            args = []
            for _ in range(self.sfunctions[token]["arg_count"]):
                args.insert(0, self.pop_and_eval(stack))
            sfunc = self.sfunctions[token]
            if sfunc["push_result_to_stack"]:
                stack.append(sfunc["func"](*args))
            else:
                sfunc["func"](*args)
        else:
            raise StackerSyntaxError(f"Unknown operator '{token}'")

    def expand_macro(self, name: str, stack: deque) -> None:
        """Executes a macro."""
        macro = self.macros[name]
        expression = macro.blockstack.expression
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=stack)

    # ========================
    # Definition
    # ========================

    def defun_sfunction(self, func_name: str, fargs, body: Stacker) -> None:
        function = StackerFunction(fargs, body)
        args_count = len(fargs)
        self.register_sfunction(
            func_name, function, args_count, push_result_to_stack=True
        )

    def define_macro(self, name: str, body: Stacker) -> None:
        """Defines a macro."""
        macro = StackerMacro(name, body)
        self.register_macro(name, macro)

    # ========================
    # Registration
    # ========================

    def register_operator(
        self,
        operator_name: str,
        operator_func: Callable,
        arg_count: int,
        push_result_to_stack: bool,
        desc: str | None = None,
    ) -> None:
        self.operators[operator_name] = {
            "func": operator_func,
            "arg_count": arg_count,
            "push_result_to_stack": push_result_to_stack,
            "desc": desc,
        }

    def register_sfunction(
        self,
        sfunction_name: str,
        sfunction_func: StackerFunction,
        arg_count: int,
        push_result_to_stack: bool = True,
        desc: str | None = None,
    ) -> None:
        self.sfunctions[sfunction_name] = {
            "func": sfunction_func,
            "arg_count": arg_count,
            "push_result_to_stack": push_result_to_stack,
            "desc": desc,
        }

    def register_macro(self, macro_name: str, macro_body: Callable) -> None:
        self.macros[macro_name] = macro_body

    def register_parameter(self, parameter_name: str, parameter_value: Any) -> None:
        self.variables[parameter_name] = parameter_value

    def register_plugin(
        self,
        operator_name: str,
        operator_func: Any,
        push_result_to_stack: bool = True,
        pass_core: bool = False,
        desc: str | None = None,
    ) -> None:
        if pass_core:
            original_operator_func = operator_func

            def wrapped_operator_func(*args, **kwargs):
                wraped = original_operator_func(self, *args, **kwargs)
                return wraped

            wrapped_operator_func.arg_count = (
                original_operator_func.__code__.co_argcount - 1
            )
            operator_func = wrapped_operator_func
            arg_count = wrapped_operator_func.arg_count
        else:
            arg_count = operator_func.__code__.co_argcount
        self.register_operator(
            operator_name, operator_func, arg_count, push_result_to_stack, desc
        )
        self.plugin_descriptions[operator_name] = desc

    # ========================
    # Getter
    # ========================

    def get_stack_ref(self) -> deque:
        return self.stack

    def get_stack_copy(self) -> deque:
        return self.stack.copy()

    def get_macros_ref(self) -> dict:
        return self.macros

    def get_macros_copy(self) -> dict:
        return self.macros.copy()

    def get_variables_ref(self) -> dict:
        return self.variables

    def get_variables_copy(self) -> dict:
        return self.variables.copy()

    def get_operators_ref(self) -> dict:
        return self.operators

    def get_operators_copy(self) -> dict:
        return self.operators.copy()

    def get_priority_operators_ref(self) -> dict:
        return self.priority_operators

    def get_priority_operators_copy(self) -> dict:
        return self.priority_operators.copy()

    def get_sfuntions_ref(self) -> dict:
        return self.sfunctions

    def get_sfuntions_copy(self) -> dict:
        return self.sfunctions.copy()

    def get_plugins_ref(self) -> dict:
        return self.plugins

    def get_plugins_copy(self) -> dict:
        return self.plugins.copy()

    def get_stack_length(self) -> int:
        return len(self.stack)

    # ========================
    # Debug
    # ========================

    def eval(self, expression: str) -> Any:
        """Evaluates a given RPN expression.
        Returns the result of the evaluation.

        Example:
        ``` python
        stacker = Stacker()
        and = stacker.eval("1 2 +")
        ```
        """
        tokens = parse_expression(expression)
        return copy.deepcopy(self.evaluate(tokens))


class StackerFunction:
    """A callable object that represents a function defined in Stacker."""

    def __init__(self, args: list[str], blockstack: Stacker) -> None:
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)

    def __call__(self, *values) -> Any:
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        # Create a new stack for the function call
        # Bind the arguments to the values
        for arg, value in zip(self.args, values):
            # stacker.variables[arg] = value
            self.blockstack.variables[arg] = value
            self.blockstack.stack.append(arg)
        self.blockstack.stack.append(self.blockstack)
        result = self.blockstack.pop_and_eval(self.blockstack.stack)
        return result


class StackerMacro:
    """A callable object that represents a macro defined in Stacker."""

    def __init__(self, name: str, blockstack: Stacker) -> None:
        self.name = name
        self.blockstack = blockstack
        self.arg_count = 0

    def __call__(self) -> Stacker:
        return self.blockstack