from __future__ import annotations

import ast
import copy
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


def is_int_or_float_or_complex(value_str: str) -> bool:
    try:
        int(value_str)
        float(value_str)
        complex(value_str)
        return True
    except Exception:
        return False


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
        self.stack: list[Any] = []
        self.loop_operators = {
            "times": {
                "func": (
                    lambda n_times, block, stack: self.execute_times(
                        block, n_times, stack
                    )
                ),
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Executes a block of code a specified number of times.",
            },
            "do": {
                "func": (
                    lambda start_value, end_value, symbol, block, stack: self.execute_do(
                        start_value, end_value, symbol, block, stack
                    )
                ),
                "arg_count": 4,
                "push_result_to_stack": False,
                "desc": "Executes a block of code a specified number of times.",
            },
        }
        self.condition_operators = {
            "if": {
                "func": (
                    lambda condition, block, stack: self.execute_if(
                        condition, block, stack
                    )
                ),
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Executes a block of code if a condition is true.",
            },
            "ifelse": {
                "func": (
                    lambda condition, true_block, false_block, stack: self.execute_if_else(
                        condition, true_block, false_block, stack
                    )
                ),
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
                "func": (lambda name, value: self.set_variable(name, value)),
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Sets a variable.",
            },
            "defun": {
                "func": (
                    lambda func_name, fargs, body: self.defun_sfunction(
                        func_name, fargs, body
                    )
                ),
                "arg_count": 3,
                "push_result_to_stack": False,
                "desc": "Defines a function.",
            },
            "alias": {
                "func": (lambda name, body: self.define_macro(name, body)),
                "arg_count": 2,
                "push_result_to_stack": False,
                "desc": "Defines a macro.",
            },
            "include": {
                "func": (lambda filename: self.include(filename)),
                "arg_count": 1,
                "push_result_to_stack": False,
                "desc": "Includes another stacker script.",
            },
            # "sfunc": {
            #     "func": (lambda func, n_args: self.sfunc(func, n_args)),
            #     "arg_count": 2,
            #     "push_result_to_stack": True,
            #     "desc": "Generate a sfunction."
            # },
            # "rf": {
            #     "func": (lambda func_name, func_body: self.register_function(func_name, func_body)),
            #     "arg_count": 2,
            #     "push_result_to_stack": False,
            #     "desc": "Register a function."
            # },
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

    def substack(self, token: str, stack: list) -> None:
        """Creates a substack.
        :param token: {...}.
        """
        expression = token[1:-1]
        self.child = Stacker(expression=expression, parent=self)
        self.child.variables = self.get_variables_ref()
        self.child.macros = self.get_macros_ref()
        self.child.operators = self.get_operators_ref()
        self.child.sfunctions = self.get_sfuntions_ref()
        if self.child.expression != {}:
            stack.append(self.child)

    # ========================
    # Stack
    # ========================

    def _clear_stack(self):
        self.stack = []

    def push(self, value: Any) -> None:
        self.stack.append(value)

    def pop_and_eval(self, stack) -> Any:
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
        blockstack: Stacker,
        stack: list,
    ) -> None:
        result = []
        for i in range(start_value, end_value + 1):
            blockstack.set_variable(symbol, i)
            result += blockstack.evaluate(blockstack.tokens, stack=blockstack.stack)
        stack.extend(result)

    def execute_times(
        self, n_times: int, blockstack: Stacker | Any, stack: list = None
    ) -> None:
        """Executes a block of code a specified number of times."""
        if isinstance(blockstack, Stacker):
            i_count = 0
            stack.append(i_count)
            while stack[-1] < n_times:
                stack.pop()
                blockstack.evaluate(blockstack.tokens, stack=blockstack.stack)
                sub_stack = blockstack.get_stack_ref()
                if len(sub_stack) > 0:
                    stack += sub_stack
                blockstack._clear_stack()
                i_count = i_count + 1
                stack.append(i_count)
            stack.pop()
        else:  # e.g. a numeric object
            i_count = 0
            stack.append(i_count)
            while stack[-1] < n_times:
                stack.pop()
                stack.append(blockstack)
                i_count = i_count + 1
                stack.append(i_count)
            stack.pop()

    # ========================
    # Condition (if, ifelse)
    # ========================

    def execute_if(
        self, condition: Stacker | bool, blockstack: Stacker | Any, stack: list
    ) -> None:
        """Executes a block of code if a condition is true."""
        if isinstance(condition, Stacker):
            condition.evaluate(condition.tokens, stack=condition.stack)
            sub_stack = condition.get_stack_ref()
            if sub_stack:
                stack.extend(sub_stack)
            condition._clear_stack()
            condition = stack.pop()

        if condition:
            if isinstance(blockstack, Stacker):
                blockstack.evaluate(blockstack.tokens, stack=blockstack.stack)
                sub_stack = blockstack.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                blockstack._clear_stack()
            else:  # e.g. a numeric object
                stack.append(blockstack)

    def execute_if_else(
        self,
        condition: Stacker | bool,
        true_block: Stacker | Any,
        false_block: Stacker | Any,
        stack: list,
    ) -> None:
        """Executes a block of code if a condition is true, otherwise executes another block of code."""
        if isinstance(condition, Stacker):
            condition.evaluate(condition.tokens, stack=condition.stack)
            sub_stack = condition.get_stack_ref()
            if sub_stack:
                stack.extend(sub_stack)
            condition._clear_stack()
            condition = stack.pop()

        if condition:
            if isinstance(true_block, Stacker):
                true_block.evaluate(true_block.tokens, stack=true_block.stack)
                sub_stack = true_block.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                true_block._clear_stack()
            else:  # e.g. a numeric object
                stack.append(true_block)
        else:
            if isinstance(false_block, Stacker):
                false_block.evaluate(false_block.tokens, stack=false_block.stack)
                sub_stack = false_block.get_stack_ref()
                if sub_stack:
                    stack.extend(sub_stack)
                false_block._clear_stack()
            else:
                stack.append(false_block)

    # ========================
    # Evaluation
    # ========================

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=self.stack)

    def evaluate(self, tokens: list, stack=[]) -> list:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        # Iterate over each token in the token list
        enum_tokens = enumerate(tokens)
        for index, token in enum_tokens:
            if not isinstance(token, str):
                stack.append(token)  # Literal value
            elif (
                token in self.operators or
                token in self.sfunctions or
                token in {"defun", "alias"}
            ):
                # execute operator
                self.apply_operator(token, stack)
            elif token in self.macros:
                # expand macro
                self.expand_macro(token, stack)
            elif (
                token in self.variables or
                is_tuple(token) or
                is_array(token)
            ):
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

    def _get_n_args_for_operator(self, token: str) -> int:
        """Returns the number of arguments required for a given operator."""
        if token in self.operators:
            op = self.operators[token]["func"]
            return self.operators[token].get(
                "arg_count", op.arg_count if hasattr(op, "arg_count") else op.__code__.co_argcount
            )
        elif token in self.sfunctions:
            return self.sfunctions[token]["arg_count"]
        else:
            raise UnexpectedTokenError(token)

    def _create_args(self, token: str, stack: list) -> list:
        """Creates a list of arguments for a given operator."""
        n_args = self._get_n_args_for_operator(token)
        if len(stack) < n_args:
            raise StackerSyntaxError(
                f"Operator '{token}' expects {n_args} arguments, but only {len(stack)} were provided."
            )
        if token == "do":
            body = stack.pop()  # not evaluate
            symbol = stack.pop()
            end_value = self.pop_and_eval(stack)
            start_value = self.pop_and_eval(stack)
            args = [start_value, end_value, symbol, body, stack]
        elif token == "times":
            n_times = self.pop_and_eval(stack)
            body = stack.pop()
            args = [body, n_times, stack]
        elif token == "if":
            condition = stack.pop()
            true_block = stack.pop()
            args = [condition, true_block, stack]
        elif token == "ifelse":
            condition = stack.pop()
            false_block = stack.pop()
            true_block = stack.pop()
            args = [condition, true_block, false_block, stack]
        elif token == "set":
            name = stack.pop()
            value = self.pop_and_eval(stack)
            args = [name, value]
        elif token == "defun":
            name = stack.pop()
            body = stack.pop()
            fargs = self.pop_and_eval(stack)
            fargs = convert_custom_string_tuple_to_proper_tuple(fargs)
            fargs = ast.literal_eval(fargs)
            args = [name, fargs, body]
        elif token == "alias":
            name = stack.pop()
            body = stack.pop()
            args = [name, body]
        else:
            args = [self.pop_and_eval(stack) for _ in range(n_args)]
            args.reverse()  # ! important
            if token in stack_operators:
                args.append(stack)
        return args

    def apply_operator(self, token: str, stack: list) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        args = self._create_args(token, stack)

        if token == "set":
            self.set_variable(*args)
        elif token == "defun":
            self.defun_sfunction(*args)
        elif token == "alias":
            self.define_macro(*args)
        elif token == "include":
            self.include(*args)
        else:
            if token in self.operators:
                op = self.operators[token]
                if op["push_result_to_stack"]:
                    stack.append(op["func"](*args))
                else:
                    op["func"](*args)
            elif token in self.sfunctions:
                sfunc = self.sfunctions[token]
                if sfunc["push_result_to_stack"]:
                    stack.append(sfunc["func"](*args))
                else:
                    sfunc["func"](*args)
            else:
                raise StackerSyntaxError(f"Unknown operator '{token}'")

    def expand_macro(self, name: str, stack: list) -> None:
        """Executes a macro."""
        macro = self.macros[name]
        expression = macro.blockstack.expression
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=stack)

    # ========================
    # Definition
    # ========================

    def defun_sfunction(self, func_name: str, fargs, blockstack: Stacker) -> None:
        # self.operators[func_name] = (lambda *args: self._debug(*args))
        function = StackerFunction(fargs, blockstack)
        args_count = len(fargs)
        self.register_sfunction(
            func_name, function, args_count, push_result_to_stack=True
        )

    def define_macro(self, name: str, body: Stacker) -> None:
        """Defines a macro."""
        macro = StackerMacro(name, body)
        self.register_macro(name, macro)

    # def sfunc(self, func: Callable, n_args: int):
    #     def wrapped_operator_func(*args, **kwargs):
    #         wraped = func(self, *args, **kwargs)
    #         return wraped
    #     wrapped_operator_func.arg_count = n_args
    #     return wrapped_operator_func

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
        operator_func: Callable,
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
    # Setter
    # ========================

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value

    # ========================
    # Getter
    # ========================

    def get_stack_ref(self) -> list:
        return self.stack

    def get_stack_copy(self) -> list:
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

    def eval(self, expression: str):
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

    def __init__(self, args: list[str], blockstack: Stacker):
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)

    def __call__(self, *values):
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        # Create a new stack for the function call
        # Bind the arguments to the values
        for arg, value in zip(self.args, values):
            # stacker.variables[arg] = value
            self.blockstack.set_variable(arg, value)
            self.blockstack.stack.append(arg)
        self.blockstack.stack.append(self.blockstack)
        result = self.blockstack.pop_and_eval(self.blockstack.stack)
        return result


class StackerMacro:
    """A callable object that represents a macro defined in Stacker."""

    def __init__(self, name: str, blockstack: Stacker):
        self.name = name
        self.blockstack = blockstack
        self.arg_count = 0

    def __call__(self):
        return self.blockstack
