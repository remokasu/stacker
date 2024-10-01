from __future__ import annotations
import copy
from typing import TYPE_CHECKING, Any
import ast
from stacker.constant import constants
from stacker.error import (
    # StackUnderflowError,
    StackerSyntaxError,
    UndefinedSymbolError,
    # UnexpectedTokenError,
)
from stacker.lib.function.algebra import alge_operators
from stacker.lib.function.arith import arith_operators
from stacker.lib.function.aggregate import aggregate_operators
from stacker.lib.function.transform import transform_operators
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
from stacker.lib.function.defmacro import macro_operators
from stacker.lib.function.hof import hof_operators
from stacker.syntax.parser import (
    convert_custom_array_to_proper_list,
    is_block,
    # is_contains_transpose_command,
    # is_label_symbol,
    is_reference_symbol,
    is_string,
    is_list,
    # is_transpose_command,
    is_tuple,
    is_undefined_symbol,
    parse_expression,
)
from stacker.reserved import (
    __BREAK__,
    # __TRANSPOSE__
)
from stacker.data_type import String, stack_data

if TYPE_CHECKING:
    # from stacker.sfunction import StackerFunction
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
    "sub": {
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Substack the top element",
    },
    "subn": {
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Cluster elements between the top and the nth (make substacks)",
    },
}


class StackerCore:
    """A class for evaluating RPN expressions."""

    def __init__(
        self, expression: str | None = None, parent: StackerCore | None = None
    ):
        self.parent = parent
        self.child = None
        self.trace: list[Any] = []  # for error trace
        self.stack: stack_data[Any] = stack_data()
        self.tokens = []
        if self.parent is not None:  # it is a substack of a parent stacker
            self.regular_operators = self.parent.regular_operators
            self.hof_operators = self.parent.hof_operators
            self.aggregate_operators = self.parent.aggregate_operators
            self.transform_operators = self.parent.transform_operators
            self.priority_operators = self.parent.priority_operators
            self.stack_operators = self.parent.stack_operators
            self.settings_operators = self.parent.settings_operators
            self.macros = self.parent.macros
            self.variables = self.parent.variables
            self.plugins = self.parent.plugins
            self.sfunctions = self.parent.sfunctions
            self.labels = self.parent.labels
            if expression is not None:
                self.tokens = list(
                    map(self._block_token_format, parse_expression(expression))
                )
            return

        if expression is not None and self.parent is None:
            raise NotImplementedError

        # it is a root stacker
        self.regular_operators = {}
        self.regular_operators.update(alge_operators)
        self.regular_operators.update(arith_operators)
        self.regular_operators.update(base_operators)
        self.regular_operators.update(bitwise_operators)
        self.regular_operators.update(compare_operators)
        self.regular_operators.update(file_operators)
        self.regular_operators.update(io_operators)
        self.regular_operators.update(logic_operators)
        self.regular_operators.update(math_operators)
        self.regular_operators.update(random_operators)
        self.regular_operators.update(type_operators)
        self.regular_operators.update(list_operators)
        self.regular_operators.update(eval_operators)
        self.regular_operators.update(string_operators)
        self.regular_operators.update(time_operators)

        self.priority_operators = {}
        self.priority_operators.update(loop_operators)
        self.priority_operators.update(condition_operators)
        self.priority_operators.update(special_operators)
        self.priority_operators.update(include_operators)
        self.priority_operators.update(defun_operators)
        self.priority_operators.update(macro_operators)
        self.priority_operators.update(exit_operators)

        self.hof_operators = hof_operators
        self.aggregate_operators = aggregate_operators
        self.transform_operators = transform_operators
        self.stack_operators = stack_operators
        self.settings_operators = settings_operators

        self.variables = {}
        self.variables.update(constants)

        self.macros = {}
        self.plugins = {}
        self.sfunctions = {}
        self.labels = {}

    def _block_token_format(self, token: str) -> str:
        if token in self.regular_operators:
            return self._literal_eval2(f'"{token}"')
        return self._literal_eval2(token)

    def _get_all_operators_keys(self) -> list[str]:
        return (
            list(self.regular_operators.keys())
            + list(self.priority_operators.keys())
            + list(self.hof_operators.keys())
            + list(self.aggregate_operators.keys())
            + list(self.transform_operators.keys())
            + list(self.stack_operators.keys())
            + list(self.settings_operators.keys())
            + list(self.sfunctions.keys())
            + list(self.plugins.keys())
        )

    def _substack(self, token: str, stack: stack_data) -> None:
        """Creates a substack.
        :param token: {...}.
        """
        expression = token[1:-1]
        self.child = type(self)(expression=expression, parent=self)
        stack.append(self.child)

    def _substack_with_tokens(self, tokens: list, stack: stack_data) -> None:
        self.child = type(self)(parent=self)
        self.child.tokens = tokens
        stack.append(self.child)

    def _pop_and_eval(self, stack: stack_data) -> Any:
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
            elif isinstance(value, String):
                return value.value
            elif value in self.variables:
                return self.variables[value]
            return self.variables.get(value, value)

    def _eval(self, expr: str, stack: stack_data = stack_data()) -> stack_data:
        tokens = list(map(self._literal_eval, parse_expression(expr)))
        self._evaluate(tokens, stack=stack)
        return stack

    def _eval_block(self, block: StackerCore, stack: stack_data) -> None:
        self._evaluate(block.tokens, stack=stack)

    def _evaluate(self, tokens: list, stack: stack_data = stack_data()) -> stack_data:
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
                token in self.regular_operators
                or token in self.priority_operators
                or token in self.hof_operators
                or token in self.aggregate_operators
                or token in self.transform_operators
                or token in self.stack_operators
                or token in self.settings_operators
                or token in self.sfunctions
                or token in self.plugins
            ):
                self._execute(token, stack)
                self._clear_trace()
            elif token in self.macros:
                self._expand_macro(token, stack)
            elif token in self.variables:
                stack.append(token)
            elif is_string(token):
                stack.append(String(token[1:-1]))
            elif is_tuple(token):
                evaled_token = ast.literal_eval(
                    convert_custom_array_to_proper_list(token)
                )
                if isinstance(evaled_token, tuple):
                    stack.append(tuple(map(self._var_str_to_literal, evaled_token)))
                else:
                    stack.append(self._var_str_to_literal(evaled_token))
            elif is_list(token):
                stack.append(
                    list(
                        map(
                            self._var_str_to_literal,
                            ast.literal_eval(
                                convert_custom_array_to_proper_list(token)
                            ),
                        )
                    )
                )
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
                token = self._literal_eval(token)
                if isinstance(token, String):
                    stack.append(token)
                elif isinstance(token, str):
                    if is_undefined_symbol(token):
                        stack.append(token)
                    else:
                        raise UndefinedSymbolError(token)
                else:
                    stack.append(token)
        return stack

    def _var_str_to_literal(self, value: Any) -> Any:
        if is_string(value):
            return String(value[1:-1])
        elif isinstance(value, str) and is_undefined_symbol(value):
            if value[1:] in self.variables:
                return self.variables[value[1:]]
            else:
                raise UndefinedSymbolError(value[1:])
        elif isinstance(value, str) and value in self.variables:
            return self.variables[value]
        elif isinstance(value, str):
            raise UndefinedSymbolError(value)
        return value

    def _literal_eval(self, token: str) -> Any:
        if is_block(token):
            return token
        elif token in self.variables:
            return self.variables[token]
        elif is_string(token):
            return String(token[1:-1])
        else:
            try:
                return ast.literal_eval(token)
            except Exception:
                return token

    def _literal_eval2(self, token: str) -> Any:
        if is_block(token):
            return token
        elif is_string(token):
            return String(token[1:-1])
        else:
            try:
                return ast.literal_eval(token)
            except Exception:
                return token

    def _execute(self, token: str, stack: stack_data) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        if token in self.sfunctions:  # sfunctions
            args = []
            sfunc = self.sfunctions[token]
            for _ in range(sfunc["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if sfunc["push_result_to_stack"]:
                stack.append(sfunc["func"](*args))
            else:
                sfunc["func"](*args)
        elif token in self.plugins:
            args = []
            op = self.plugins[token]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.priority_operators:
            op = self.priority_operators[token]
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
                fargs = stack.pop()  # str
                if isinstance(fargs, tuple):
                    fargs = list(fargs)
                elif isinstance(fargs, list):
                    fargs = fargs
                elif isinstance(fargs, StackerCore):
                    fargs = fargs.tokens
                else:
                    fargs = [fargs]
                op["func"](self, name, fargs, body)
            elif token == "defmacro":
                name = stack.pop()
                body = stack.pop()
                op["func"](self, name, body)
            elif token == "eval":
                expression = stack.pop()
                if isinstance(expression, String):
                    self._eval(expression.value, stack=stack)
                elif isinstance(expression, StackerCore):
                    self._eval_block(expression, stack=stack)
                else:
                    stack.append(expression)
            elif token == "sub":
                token = stack.pop()
                self._substack_with_tokens([token], stack)
            elif token == "subn":
                n = stack.pop()
                elms = [stack.pop() for _ in range(n)]
                elms.reverse()
                self._substack_with_tokens(elms, stack)
            elif token == "include":
                filename = stack.pop()
                op["func"](self, filename)
            elif token == "exit":
                op["func"]()
        elif token in self.stack_operators:  # stack operators
            args = [stack]
            op = self.stack_operators[token]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.regular_operators:  # Other operators
            args = []
            op = self.regular_operators[token]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.hof_operators:  # higher-order functions
            if token in ["map", "filter"]:
                op = self.hof_operators[token]
                body = stack.pop()
                args = stack.pop()
                args_org = copy.deepcopy(args)
                func = self._get_hof_func(body)
                args = args.tokens if isinstance(args, StackerCore) else args
                if op["push_result_to_stack"]:
                    lst = op["func"](func, args)
                    if isinstance(args_org, list):
                        stack.append(list(lst))
                    elif isinstance(args_org, tuple):
                        stack.append(tuple(lst))
                    else:
                        self._substack_with_tokens(list(lst), stack)
                else:
                    op["func"](func, args)
            elif token in ["zip"]:
                op = self.hof_operators[token]
                xs2 = stack.pop()
                xs1 = stack.pop()
                xs_org = copy.deepcopy(xs1)
                # ys_org = copy.deepcopy(ys)
                xs2 = (
                    xs2.tokens
                    if isinstance(xs2, StackerCore)
                    else self._var_str_to_literal(xs2)
                )
                xs1 = (
                    xs1.tokens
                    if isinstance(xs1, StackerCore)
                    else self._var_str_to_literal(xs1)
                )
                if op["push_result_to_stack"]:
                    lst = op["func"](xs1, xs2)
                    if isinstance(xs_org, list):
                        stack.append(list(lst))
                    elif isinstance(xs_org, tuple):
                        stack.append(tuple(lst))
                    else:
                        self._substack_with_tokens(list(lst), stack)
                else:
                    op["func"](xs1, xs2)
            else:
                ...
        elif token in self.transform_operators:  # transform operators
            op = self.transform_operators[token]
            args = stack.pop()
            args_org = copy.deepcopy(args)
            args = (
                args.tokens
                if isinstance(args, StackerCore)
                else self._var_str_to_literal(args)
            )
            if op["push_result_to_stack"]:
                lst = op["func"](args)
                if token == "list":
                    stack.append(list(lst))
                elif token == "tuple":
                    stack.append(tuple(lst))
                else:
                    if isinstance(args_org, list):
                        stack.append(list(lst))
                    elif isinstance(args_org, tuple):
                        stack.append(tuple(lst))
                    else:
                        self._substack_with_tokens(list(lst), stack)
            else:
                op["func"](args)
        elif token in self.aggregate_operators:  # aggregate operators
            op = self.aggregate_operators[token]
            args = stack.pop()
            args_org = copy.deepcopy(args)
            args = (
                list(map(self._literal_eval, args.tokens))
                if isinstance(args, StackerCore)
                else self._var_str_to_literal(args)
            )
            if op["push_result_to_stack"]:
                stack.append(op["func"](args))
            else:
                op["func"](args)
        elif token in self.settings_operators:  # settings operators
            op = self.settings_operators[token]
            if token == "disable_plugin":
                operator_name = stack.pop()
                op["func"](self, operator_name)
            else:
                op["func"](self)
        else:
            raise StackerSyntaxError(f"Unknown operator '{token}'")
        return

    def _get_hof_func(self, body: str | StackerCore) -> callable:
        if isinstance(body, StackerCore):
            return lambda args: self._stacker_lambda(args, body.copy())
        else:
            if body in self.sfunctions:
                return self.sfunctions[body]["func"]
            elif body in self.plugins:
                return self.plugins[body]["func"]
            elif body in self.regular_operators:
                return self.regular_operators[body]["func"]
            else:
                raise StackerSyntaxError(f"Unknown operator '{body}'")

    # def _execute_settings(self, token: str, stack: stack_data) -> None:
    #     op = self.settings_operators[token]
    #     if token == "disable_plugin":
    #         operator_name = stack.pop()
    #         op["func"](self, operator_name)
    #     else:
    #         op["func"](self)

    def _expand_macro(self, name: str, stack: stack_data) -> None:
        """Executes a macro."""
        macro: StackerMacro = self.macros[name]
        self._evaluate(macro.blockstack.tokens, stack=stack)

    def _clear_trace(self) -> None:
        self.trace = []

    def _stacker_lambda(self, arg, body: StackerCore) -> StackerCore:
        stack = []
        body.tokens.insert(0, arg)
        body._evaluate(body.tokens, stack=stack)
        if len(stack) == 1:
            return stack[0]
        elif len(stack) == 0:
            return self._substack("{}")
        return stack

    def copy(self) -> StackerCore:
        return copy.deepcopy(self)

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, key):
        return self.tokens[key]

    def __str__(self):
        def format_item(item):
            if isinstance(item, StackerCore):
                # return f"{str(item)}".replace(",", " ")
                raise NotImplementedError
            elif is_list(item):
                return item.replace(",", " ")
            elif is_tuple(item):
                return item.replace(",", " ")
            elif isinstance(item, str):
                if item in self._get_all_operators_keys() or (
                    item.startswith("{") and item.endswith("}")
                ):
                    return item
                elif item in self.variables:
                    return item
                return repr(item)
            return str(item)

        formatted_items = " ".join(map(format_item, self.tokens))
        return f"{{{formatted_items}}}"

    def __repr__(self):
        return self.__str__()