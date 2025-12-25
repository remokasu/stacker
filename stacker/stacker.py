from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from stacker.engine.core import StackerCore
from stacker.syntax.parser import parse_expression

if TYPE_CHECKING:
    from stacker.engine.sfunction import StackerFunction

from stacker.engine.data_type import stack_data


class Stacker(StackerCore):
    def __init__(
        self, expression: str | None = None, parent: StackerCore | None = None
    ):
        super().__init__(expression, parent)
        self.trace = []
        self.plugin_descriptions = {}

    def include(self, filename: str) -> None:
        return self.operator_manager.operators["priority"]["include"]["func"](
            self, filename
        )

    def push(self, value: Any) -> None:  # TODO: remove
        self.stack.append(value)

    def pop_and_eval(self, stack: stack_data) -> Any:
        return self._pop_and_eval(stack)

    def pop(self) -> Any:
        return self.stack.pop()

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=self.stack)

    # @staticmethod
    # def new(expression: str | None = None, parent: Stacker | None = None) -> Stacker:
    #     return Stacker(expression=expression, parent=parent)

    def evaluate(self, tokens: list, stack: stack_data = stack_data()) -> stack_data:
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
        self.operator_manager.register_operator(
            operator_name,
            operator_func,
            arg_count,
            push_result_to_stack,
            desc,
        )

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
    # Getter
    # ========================

    def get_stack_ref(self) -> stack_data:
        return self.stack

    def get_stack_copy(self) -> stack_data:
        return self.stack.copy()

    def get_stack_copy_as_list(self) -> list:
        return list(self.stack.copy())

    def get_macros_ref(self) -> dict:
        return self.macros

    def get_macros_copy(self) -> dict:
        return self.macros.copy()

    def get_variables_ref(self) -> dict:
        return self.variables

    def get_variables_copy(self) -> dict:
        return self.variables.copy()

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

    def get_all_keys_for_completer(self) -> list[str]:
        return list(
            set(
                self.operator_manager.get_all_keys_for_completer()
                + list(self.sfunctions.keys())
                + list(self.plugins.keys())
                + list(self.macros.keys())
                + list(self.variables.keys())
            )
        )

    def get_plugin_descriptions(self) -> dict:
        return self.plugin_descriptions

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

    def eval(self, expression: str, stack: stack_data = stack_data()) -> Any:
        """Evaluates a given RPN expression.
        Returns the result of the evaluation.

        Example:
        ``` python
        stacker = Stacker()
        and = stacker.eval("1 2 +")
        ```
        """
        tokens = parse_expression(expression)
        return self.evaluate(tokens, stack=stack)
