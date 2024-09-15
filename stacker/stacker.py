from __future__ import annotations

import copy
from collections import deque
from typing import TYPE_CHECKING, Any, Callable

from stacker.error import StackerSyntaxError
from stacker.core import StackerCore
from stacker.syntax.parser import parse_expression

if TYPE_CHECKING:
    from stacker.sfunction import StackerFunction


class Stacker(StackerCore):
    def include(self, filename: str) -> None:
        return self.priority_operators["include"]["func"](self, filename)

    def push(self, value: Any) -> None:  # TODO: remove
        self.stack.append(value)

    def pop_and_eval(self, stack: deque) -> Any:
        return self._pop_and_eval(stack)

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=self.stack)

    def evaluate(self, tokens: list, stack: deque = deque()) -> deque:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        try:
            return self._evaluate(tokens, stack=stack)
        except Exception as e:
            if self.parent is not None:
                self.parent.trace = self.trace
            raise e

    def register_operator(
        self,
        operator_name: str,
        operator_func: Callable,
        arg_count: int,
        push_result_to_stack: bool,
        desc: str | None = None,
    ) -> None:
        if operator_name in self.priority_operators:
            del self.priority_operators[operator_name]
            self.priority_operators[operator_name] = {
                "func": operator_func,
                "arg_count": arg_count,
                "push_result_to_stack": push_result_to_stack,
                "desc": desc,
            }
        if operator_name in self.operators:
            del self.operators[operator_name]
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
        # self.register_operator(
        #     operator_name, operator_func, arg_count, push_result_to_stack, desc
        # )
        if operator_name in self.plugins:
            del self.plugins[operator_name]
        self.plugins[operator_name] = {
            "func": operator_func,
            "arg_count": arg_count,
            "push_result_to_stack": push_result_to_stack,
            "desc": desc,
        }
        self.plugin_descriptions[operator_name] = desc

    def register_label(self, label_name: str, index: int) -> None:
        self.labels[label_name] = index

    # ========================
    # Setting
    # ========================

    @property
    def disp_stack_mode(self) -> bool:
        return self._disp_stack_mode

    @property
    def disp_logo_mode(self) -> bool:
        return self._disp_logo

    @property
    def disp_ans_mode(self) -> bool:
        return self._disp_ans

    # ========================
    # Getter
    # ========================

    def get_any_operator_arg_count(self, operator_name: str) -> int:
        if operator_name in self.operators:
            return self.operators[operator_name]["arg_count"]
        elif operator_name in self.sfunctions:
            return self.sfunctions[operator_name]["arg_count"]
        elif operator_name in self.plugins:
            return self.plugins[operator_name]["arg_count"]
        else:
            raise StackerSyntaxError(f"Unknown operator '{operator_name}'")

    def get_stack_ref(self) -> deque:
        return self.stack

    def get_stack_copy(self) -> deque:
        return self.stack.copy()

    def get_stack_copy_as_list(self) -> deque:
        return list(self.stack.copy())

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

    def get_stack_operators_ref(self) -> dict:
        return self.stack_operators

    def get_stack_operators_copy(self) -> dict:
        return self.stack_operators.copy()

    def get_settings_operators_ref(self) -> dict:
        return self.settings_operators

    def get_settings_operators_copy(self) -> dict:
        return self.settings_operators.copy()

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

    def get_trace_ref(self) -> list[Any]:
        return self.trace

    def get_trace_copy(self) -> list[Any]:
        return self.trace.copy()

    def get_labels_ref(self) -> dict:
        return self.labels

    def get_labels_copy(self) -> dict:
        return self.labels.copy()

    def get_operator_descriptions(self) -> dict:
        operator_descriptions = {}
        for operator_name, operator_description in self.operators.items():
            operator_descriptions[operator_name] = operator_description["desc"]
        for operator_name, operator_description in self.priority_operators.items():
            operator_descriptions[operator_name] = operator_description["desc"]
        return operator_descriptions

    def get_plugin_descriptions(self) -> dict:
        return self.plugin_descriptions

    def get_stack_operator_descriptions(self) -> dict:
        return {k: v["desc"] for k, v in self.stack_operators.items()}

    def get_settings_operator_descriptions(self) -> dict:
        return {k: v["desc"] for k, v in self.settings_operators.items()}

    def get_expression(self) -> str:
        return self.expression

    # ========================
    # Clear
    # ========================

    def clear_trace(self) -> None:
        self.trace = []

    # def clear_ans(self) -> None:
    #     self._ans = None

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
        return list(copy.deepcopy(self.evaluate(tokens)))
