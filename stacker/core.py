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
from stacker.slambda import StackerLambda
from stacker.manager.operator_manager import OperatorManager

if TYPE_CHECKING:
    # from stacker.sfunction import StackerFunction
    from stacker.smacro import StackerMacro


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
            self.operator_manager = self.parent.operator_manager
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

        self.operator_manager = OperatorManager()
        self.variables = {}
        self.variables.update(constants)
        self.macros = {}
        self.plugins = {}
        self.sfunctions = {}
        self.labels = {}

    def _block_token_format(self, token: str) -> str:
        if token in self.operator_manager.oprerators["regular"]:
            return self._literal_eval2(f'"{token}"')
        return self._literal_eval2(token)

    def _substack(self, token: str, stack: stack_data) -> None:
        """Creates a substack.
        :param token: {...}.
        """
        expression = token[1:-1]
        self.child = type(self)(expression=expression, parent=self)
        stack.append(self.child)

    def _substack_with_expression(self, expression: str, stack: stack_data) -> None:
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
        self.trace = tokens
        for token in tokens:
            # if token == "#":  # Comment
            #     break
            if not isinstance(token, str):
                stack.append(token)  # Literal value
            elif (
                token in self.operator_manager.oprerators["priority"]
                or token in self.operator_manager.oprerators["regular"]
                or token in self.operator_manager.oprerators["stack"]
                or token in self.operator_manager.oprerators["hof"]
                or token in self.operator_manager.oprerators["transform"]
                or token in self.operator_manager.oprerators["aggregate"]
                or token in self.operator_manager.oprerators["settings"]
                or token in self.sfunctions
                or token in self.plugins
            ):
                self._execute(token, stack)
            elif token in self.macros:
                self._expand_macro(token, stack)
            elif token in self.variables:
                # stack.append(token)
                stack.append(self.variables[token])
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
        elif (
            token in self.operator_manager.oprerators["priority"]
        ):  # priority operators
            op = self.operator_manager.oprerators["priority"][token]
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
                if not isinstance(name, str):
                    raise StackerSyntaxError(f"Expected a string, got {name}")
                value = self._pop_and_eval(stack)
                self.variables[name] = value
            elif token == "defun":
                name = stack.pop()
                if not isinstance(name, str):
                    raise StackerSyntaxError(f"Expected a string, got {name}")
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
                if not isinstance(name, str):
                    raise StackerSyntaxError(f"Expected a string, got {name}")
                op["func"](self, name, body)
            elif token == "lambda":
                body = stack.pop()
                fargs = stack.pop()
                if op["push_result_to_stack"]:
                    stack.append(op["func"](fargs, body))
                else:
                    op["func"](fargs, body)
            elif token == "eval":
                expression = stack.pop()
                if expression in self.variables:
                    expression = self.variables[expression]
                if isinstance(expression, String):
                    self._eval(expression.value, stack=stack)
                elif isinstance(expression, StackerCore):
                    self._eval_block(expression, stack=stack)
                elif isinstance(expression, StackerLambda):
                    args = []
                    for _ in range(expression.arg_count):
                        args.insert(0, self._pop_and_eval(stack))
                    stack.append(expression(*args))
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
            elif token == "listn" or token == "tuplen":
                n = stack.pop()
                elms = [stack.pop() for _ in range(n)]
                elms.reverse()
                if token == "listn":
                    stack.append(elms)
                else:
                    stack.append(tuple(elms))
                stack.append(elms)
            elif token == "read-from-string":
                self._substack_with_expression(stack.pop(), stack)
            elif token == "read":
                self._substack_with_expression(input(), stack)
            elif token == "split":
                sep = stack.pop()
                word = stack.pop()
                for string in word.split(sep):
                    stack.append(string)
            elif token == "nth":
                n = stack.pop()
                lst = stack[-1]
                if isinstance(lst, String):
                    stack.append(String(lst[n]))
                else:
                    stack.append(lst[n])
            elif token == "expand":
                iterable = stack.pop()
                if isinstance(iterable, list or tuple):
                    stack.extend(iterable)
                elif isinstance(iterable, StackerCore):
                    stack.extend(iterable.tokens)
                else:
                    raise StackerSyntaxError(f"Cannot expand {iterable}")
            elif token == "include":
                filename = stack.pop()
                op["func"](self, filename)
            elif token == "exit":
                op["func"]()
        elif token in self.operator_manager.oprerators["stack"]:  # stack operators
            op = self.operator_manager.oprerators["stack"][token]
            args = [stack]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.operator_manager.oprerators["regular"]:  # Other operators
            op = self.operator_manager.oprerators["regular"][token]
            args = []
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                stack.append(op["func"](*args))
            else:
                op["func"](*args)
        elif token in self.operator_manager.oprerators["hof"]:  # higher-order functions
            op = self.operator_manager.oprerators["hof"][token]
            if token in ["map", "filter"]:
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
        elif (
            token in self.operator_manager.oprerators["transform"]
        ):  # transform operators
            op = self.operator_manager.oprerators["transform"][token]
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
        elif (
            token in self.operator_manager.oprerators["aggregate"]
        ):  # aggregate operators
            op = self.operator_manager.oprerators["aggregate"][token]
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
        elif isinstance(token, StackerLambda):
            args = []
            for _ in range(token.arg_count):
                args.insert(0, self._pop_and_eval(stack))
            stack.append(token(*args))
        elif (
            token in self.operator_manager.oprerators["settings"]
        ):  # settings operators
            op = self.operator_manager.oprerators["settings"][token]
            if token == "disable_plugin":
                operator_name = stack.pop()
                op["func"](self, operator_name)
            else:
                op["func"](self)
        else:
            raise StackerSyntaxError(f"Unknown operator '{token}'")
        return

    def _get_hof_func(self, body: str | StackerCore | StackerLambda) -> callable:
        if isinstance(body, StackerCore):
            return lambda args: self._stacker_lambda(args, body.copy())
        elif isinstance(body, StackerLambda):
            return body
        else:
            if body in self.sfunctions:
                return self.sfunctions[body]["func"]
            elif body in self.plugins:
                return self.plugins[body]["func"]
            elif body in self.operator_manager.oprerators["regular"]:
                return self.operator_manager.oprerators["regular"][body]["func"]
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
                if item in self.operator_manager.get_all_keys() or (
                    item.startswith("{") and item.endswith("}")
                ):
                    return item
                elif item in self.variables:
                    return item
                else:
                    return repr(item)
            return str(item)

        formatted_items = " ".join(map(format_item, self.tokens))
        return f"{{{formatted_items}}}"

    def __repr__(self):
        return self.__str__()
