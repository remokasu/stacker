from __future__ import annotations
import copy
from typing import TYPE_CHECKING, Any
import ast
from functools import lru_cache
from stacker.constant import constants
from stacker.error import (
    StackUnderflowError,
    StackerSyntaxError,
    UndefinedSymbolError,
    # UnexpectedTokenError,
)
from stacker.syntax.parser import (
    convert_custom_array_to_proper_list,
    is_block,
    is_code_block,
    # is_contains_transpose_command,
    # is_label_symbol,
    is_string,
    is_list,
    # is_transpose_command,
    # is_tuple,  # REMOVED: Tuples no longer supported, () now creates code blocks
    is_symbol,
    parse_expression,
)
from stacker.reserved import (
    __BREAK__,
    # __TRANSPOSE__
)
from stacker.engine.data_type import String, stack_data, VOID
from stacker.engine.slambda import StackerLambda
from stacker.engine.scope import ScopedVariables
from stacker.operators.manager import OperatorManager

if TYPE_CHECKING:
    # from stacker.engine.sfunction import StackerFunction
    from stacker.engine.smacro import StackerMacro


# Cache for literal_eval to avoid re-evaluating the same tokens
@lru_cache(maxsize=1024)
def _cached_literal_eval(token: str) -> Any:
    """Cached version of ast.literal_eval for performance."""
    try:
        return ast.literal_eval(token)
    except Exception:
        return token


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
        self.bracket_type = "{"  # Default bracket type for display ({} or ())

        # Source location tracking for error reporting
        self.current_file: str | None = None
        self.current_line: int | None = None
        self.source_lines: dict[int, str] = {}  # Map line number to source code

        if self.parent is not None:  # it is a substack of a parent stacker
            self.operator_manager = self.parent.operator_manager
            self.macros = self.parent.macros
            self.variables = self.parent.variables
            self.plugins = self.parent.plugins
            self.sfunctions = self.parent.sfunctions
            self.labels = self.parent.labels
            # Share source location tracking with parent
            self.current_file = self.parent.current_file
            self.current_line = self.parent.current_line
            self.source_lines = self.parent.source_lines
            if expression is not None:
                self.tokens = list(
                    map(self._block_token_format, parse_expression(expression))
                )
            return

        if expression is not None and self.parent is None:
            raise NotImplementedError

        self.operator_manager = OperatorManager()
        # Use ScopedVariables for efficient variable scoping
        self.variables = ScopedVariables(local_vars=dict(constants))
        self.sfunc_args = {}
        self.macros = {}
        self.plugins = {}
        self.sfunctions = {}
        self.labels = {}

    def _block_token_format(self, token: str) -> str:
        if token in self.operator_manager.operators["regular"]:
            return self._literal_eval2(f'"{token}"')
        return self._literal_eval2(token)

    def _substack(self, token: str, stack: stack_data) -> None:
        """Creates a substack from a code block.

        :param token: Code block with {...} or (...) delimiters.
        """
        # Strip delimiters and remember bracket type for display
        if token.startswith("{") and token.endswith("}"):
            expression = token[1:-1]
            bracket_type = "{"
        elif token.startswith("(") and token.endswith(")"):
            expression = token[1:-1]
            bracket_type = "("
        else:
            raise ValueError(f"Invalid code block: {token}")

        self.child = type(self)(expression=expression, parent=self)
        self.child.bracket_type = bracket_type
        stack.append(self.child)

    def _substack_with_expression(self, expression: str, stack: stack_data) -> None:
        self.child = type(self)(expression=expression, parent=self)
        stack.append(self.child)

    def _substack_with_tokens(self, tokens: list, stack: stack_data) -> None:
        self.child = type(self)(parent=self)
        self.child.tokens = tokens
        stack.append(self.child)

    def _safe_pop(self, stack: stack_data, operator: str = "unknown", num_args: int = 1) -> Any:
        """Safely pop from stack with informative error messages.

        Args:
            stack: The stack to pop from
            operator: Name of the operator requesting the pop (for error messages)
            num_args: Number of arguments the operator requires

        Returns:
            The popped value

        Raises:
            StackUnderflowError: If stack is empty
        """
        try:
            return stack.pop()
        except IndexError:
            raise StackUnderflowError(operator, num_args)

    def _pop_only(self, stack: stack_data) -> Any:
        top = stack.pop()
        self.trace.append(top)
        return

    def _pop_and_eval(self, stack: stack_data) -> Any:
        from stacker.engine.data_type import UndefinedSymbol
        from stacker.error import UndefinedSymbolError

        value = stack.pop()

        # Check if value is an UndefinedSymbol
        if isinstance(value, UndefinedSymbol):
            raise UndefinedSymbolError(value.name)

        if isinstance(value, StackerCore):
            value._evaluate(value.tokens, stack=value.stack)
            sub = value.stack
            if sub:
                stack.extend(sub)
                return stack.pop()
            else:
                # Return VOID if the code block produces no value
                # This allows void functions (functions with side effects only)
                # VOID will not be pushed to the stack, unlike None
                return VOID
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
        # Commands that expect a symbol name as the preceding argument
        symbol_consuming_commands = {"set", "=", "defun", "defmacro"}

        for i, token in enumerate(tokens):
            if not isinstance(token, str):
                stack.append(token)  # Literal value
            elif token in self.macros:
                self._expand_macro(token, stack)
            # Inline is_string check for performance
            elif (token.startswith("'") and token.endswith("'")) or (
                token.startswith('"') and token.endswith('"')
            ):
                stack.append(String(token[1:-1]))
            # REMOVED: Tuple handling - () now creates code blocks like {}
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
            elif is_symbol(token):
                token = token[1:]
                stack.append(token)
            # Check for code blocks (both {} and ())
            elif is_code_block(token):
                self._substack(token, stack)
            else:
                # For all other string tokens, perform lookahead to determine treatment
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                next_next_token = tokens[i + 2] if i + 2 < len(tokens) else None
                should_treat_as_symbol = next_token in symbol_consuming_commands or (
                    is_code_block(str(next_token))
                    and next_next_token in {"do", "dolist"}
                )

                if should_treat_as_symbol:
                    # Treat as symbol name regardless of whether it's a variable or operator
                    stack.append(token)
                elif token in self.variables:
                    # Variable reference - evaluate it
                    value = self.variables[token]
                    if isinstance(value, StackerLambda):
                        args = []
                        for _ in range(value.arg_count):
                            args.insert(0, self._pop_and_eval(stack))
                        stack.append(value(*args))
                    else:
                        stack.append(value)
                elif (
                    token in self.operator_manager.built_in_operators
                    or token in self.sfunctions
                    or token in self.plugins
                ):
                    self._execute(token, stack)
                else:
                    # Try to evaluate as literal
                    evaluated = self._literal_eval(token)
                    if isinstance(evaluated, String):
                        stack.append(evaluated)
                    elif isinstance(evaluated, str):
                        # Undefined identifiers are treated as UndefinedSymbol
                        from stacker.engine.data_type import UndefinedSymbol

                        stack.append(UndefinedSymbol(evaluated))
                    else:
                        stack.append(evaluated)
        return stack

    def _var_str_to_literal(self, value: Any) -> Any:
        from stacker.engine.data_type import UndefinedSymbol

        # Inline is_string check for performance
        if isinstance(value, str) and (
            (value.startswith("'") and value.endswith("'"))
            or (value.startswith('"') and value.endswith('"'))
        ):
            return String(value[1:-1])
        elif isinstance(value, str) and is_symbol(value):
            if value[1:] in self.variables:
                return self.variables[value[1:]]
            else:
                # Return UndefinedSymbol instead of raising error
                return UndefinedSymbol(value[1:])
        elif isinstance(value, str) and value in self.variables:
            return self.variables[value]
        elif isinstance(value, str):
            # Return UndefinedSymbol instead of raising error
            return UndefinedSymbol(value)
        return value

    # Cache for common literal values (optimization)
    _literal_cache = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "true": True,
        "false": False,
        "True": True,
        "False": False,
    }

    def _literal_eval(self, token: str) -> Any:
        # Handle non-string tokens (already evaluated)
        if not isinstance(token, str):
            return token
        # Check for code blocks (both {} and ())
        if is_code_block(token):
            return token
        elif token in self.variables:
            return self.variables[token]
        # Inline is_string check for performance
        elif (token.startswith("'") and token.endswith("'")) or (
            token.startswith('"') and token.endswith('"')
        ):
            return String(token[1:-1])
        else:
            # Check cache first for common literals
            if token in StackerCore._literal_cache:
                return StackerCore._literal_cache[token]
            try:
                return ast.literal_eval(token)
            except Exception:
                return token

    def _literal_eval2(self, token: str) -> Any:
        # Check for code blocks (both {} and ())
        # token is guaranteed to be str by type hint, so no isinstance check needed
        if is_code_block(token):
            return token
        # Inline is_string check for performance
        elif (token.startswith("'") and token.endswith("'")) or (
            token.startswith('"') and token.endswith('"')
        ):
            return String(token[1:-1])
        else:
            # Use cached literal_eval for performance
            return _cached_literal_eval(token)

    def _execute(self, token: str, stack: stack_data) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        try:
            self._execute_impl(token, stack)
        except IndexError as e:
            # Convert IndexError to StackUnderflowError with operator info
            # Get operator info if available
            arg_count = self._get_operator_arg_count(token)
            raise StackUnderflowError(token, arg_count) from e
        except TypeError as e:
            # Provide more helpful type error messages
            error_msg = str(e)
            if "unsupported operand type" in error_msg:
                raise TypeError(
                    f"Operator `{token}` received incompatible types. {error_msg}"
                ) from e
            raise

    def _get_operator_arg_count(self, token: str) -> int:
        """Get the argument count for an operator."""
        if token in self.sfunctions:
            return self.sfunctions[token]["arg_count"]
        elif token in self.plugins:
            return self.plugins[token]["arg_count"]
        elif token in self.operator_manager.operators["priority"]:
            return self.operator_manager.operators["priority"][token].get("arg_count", 0)
        elif token in self.operator_manager.operators["stack"]:
            return self.operator_manager.operators["stack"][token]["arg_count"]
        elif token in self.operator_manager.operators["system"]:
            return self.operator_manager.operators["system"][token]["arg_count"]
        elif token in self.operator_manager.operators["regular"]:
            return self.operator_manager.operators["regular"][token]["arg_count"]
        elif token in self.operator_manager.operators["hof"]:
            return self.operator_manager.operators["hof"][token]["arg_count"]
        elif token in self.operator_manager.operators["aggregate"]:
            return self.operator_manager.operators["aggregate"][token]["arg_count"]
        elif token in self.operator_manager.operators["file"]:
            return self.operator_manager.operators["file"][token]["arg_count"]
        elif token in self.operator_manager.operators["settings"]:
            return self.operator_manager.operators["settings"][token].get("arg_count", 0)
        return 1  # Default

    def _execute_impl(self, token: str, stack: stack_data) -> None:
        """
        Internal implementation of operator execution.
        IndexError and TypeError are caught by _execute and converted to better errors.
        """
        if token in self.sfunctions:  # sfunctions
            args = []
            sfunc = self.sfunctions[token]
            for _ in range(sfunc["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if sfunc["push_result_to_stack"]:
                result = sfunc["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                sfunc["func"](*args)
        elif token in self.plugins:
            args = []
            op = self.plugins[token]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                result = op["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)
        elif token in self.operator_manager.operators["priority"]:  # priority operators
            op = self.operator_manager.operators["priority"][token]
            if token == "do":
                body = stack.pop()
                symbol = stack.pop()
                end_value = self._pop_and_eval(stack)
                start_value = self._pop_and_eval(stack)
                name = self._dollar_to_var_name(symbol)
                op["func"](start_value, end_value, name, body, self)
            elif token == "dolist":
                body = stack.pop()
                symbol = stack.pop()
                lst = self._pop_and_eval(stack)
                name = self._dollar_to_var_name(symbol)
                op["func"](name, lst, body, self)
            elif token == "times":
                n_times = self._pop_and_eval(stack)
                body = stack.pop()
                op["func"](n_times, body, self)
            elif token == "break":
                stack.append(__BREAK__)
            elif token == "if":
                true_block = stack.pop()
                condition = stack.pop()
                op["func"](condition, true_block, self)
            elif token == "ifelse":
                false_block = stack.pop()
                true_block = stack.pop()
                condition = stack.pop()
                op["func"](condition, true_block, false_block, self)
            elif token == "iferror":
                catch_block = stack.pop()
                try_block = stack.pop()
                op["func"](try_block, catch_block, self)
            elif token == "set" or token == "=":
                symbol = stack.pop()
                name = self._dollar_to_var_name(symbol)
                value = self._pop_and_eval(stack)
                # Try to update existing variable in scope chain
                # If not found, create in local scope
                if not self.variables.update_existing(name, value):
                    self.variables[name] = value
            elif token == "global":
                # RPN: value varname global
                # Stack: [..., value, varname]
                symbol = stack.pop()  # Pop varname
                name = self._dollar_to_var_name(symbol)
                value = self._pop_and_eval(stack)  # Pop and eval value
                # Always set in global (root) scope
                self.variables.set_global(name, value)
            elif token == "defun":
                symbol = stack.pop()
                name = self._dollar_to_var_name(symbol)
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
                symbol = stack.pop()
                body = stack.pop()
                name = self._dollar_to_var_name(symbol)
                op["func"](self, name, body)
            elif token == "lambda":
                body = stack.pop()
                fargs = stack.pop()
                if op["push_result_to_stack"]:
                    result = op["func"](fargs, body)
                    if result is not VOID:
                        stack.append(result)
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
            elif token == "listn":
                n = stack.pop()
                elms = [stack.pop() for _ in range(n)]
                elms.reverse()
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
        elif token in self.operator_manager.operators["stack"]:  # stack operators
            op = self.operator_manager.operators["stack"][token]
            args = [stack]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                result = op["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)
        elif token in self.operator_manager.operators["system"]:  # system operators
            op = self.operator_manager.operators["system"][token]
            args = [stack, self]
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                result = op["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)
        elif token in self.operator_manager.operators["regular"]:  # Other operators
            op = self.operator_manager.operators["regular"][token]
            args = []
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                result = op["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)
        elif token in self.operator_manager.operators["hof"]:  # higher-order functions
            op = self.operator_manager.operators["hof"][token]
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
            elif token in ["reduce", "fold"]:
                body = stack.pop()
                symbol_x = stack.pop()  # Second variable name (element)
                symbol_acc = stack.pop()  # First variable name (accumulator)
                init = stack.pop()
                args = stack.pop()

                # Extract variable names (same as dolist pattern)
                name_acc = self._dollar_to_var_name(symbol_acc)
                name_x = self._dollar_to_var_name(symbol_x)

                # Create binary function with variable binding
                def reduce_func(acc, x):
                    # Create child scope for this reduction step
                    original_parent_vars = self.variables
                    original_parent_stack = self.stack
                    self.variables = self.variables.create_child_scope()
                    # Bind accumulator and element to their variable names
                    self.variables[name_acc] = acc
                    self.variables[name_x] = x
                    # Evaluate the body using a temporary stack
                    result_stack = []
                    self.stack = result_stack  # Temporarily replace stack
                    self._evaluate(body.tokens, stack=result_stack)
                    # Restore parent scope and stack
                    self.stack = original_parent_stack
                    self.variables = original_parent_vars
                    # Return the result
                    if len(result_stack) == 1:
                        return result_stack[0]
                    elif len(result_stack) == 0:
                        return None
                    return result_stack[0]

                args = args.tokens if isinstance(args, StackerCore) else args
                if op["push_result_to_stack"]:
                    result = op["func"](reduce_func, init, args)
                    stack.append(result)
                else:
                    op["func"](reduce_func, init, args)
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
            token in self.operator_manager.operators["transform"]
        ):  # transform operators
            op = self.operator_manager.operators["transform"][token]
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
            token in self.operator_manager.operators["aggregate"]
        ):  # aggregate operators
            op = self.operator_manager.operators["aggregate"][token]
            args = stack.pop()
            args_org = copy.deepcopy(args)
            args = (
                list(map(self._literal_eval, args.tokens))
                if isinstance(args, StackerCore)
                else self._var_str_to_literal(args)
            )
            if op["push_result_to_stack"]:
                result = op["func"](args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](args)
        elif token in self.operator_manager.operators["file"]:
            op = self.operator_manager.operators["file"][token]
            args = []
            for _ in range(op["arg_count"]):
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:
                result = op["func"](*args)
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)
        elif token in self.operator_manager.operators["settings"]:  # settings operators
            op = self.operator_manager.operators["settings"][token]
            if token == "disable_plugin":
                operator_name = stack.pop()
                op["func"](self, operator_name)
            else:
                op["func"](self)
        else:
            raise StackerSyntaxError(f"Unknown operator '{token}'")
        return

    def _dollar_to_var_name(self, symbol: str | StackerCore) -> str:
        """
        - $symbol -> symbol
        - {$symbol} -> symbol
        - symbol -> raise StackerSyntaxError
        - {symbol} -> raise StackerSyntaxError
        """
        if isinstance(symbol, str):
            if is_symbol(symbol):
                return symbol[1:]
            else:
                return symbol
        elif isinstance(symbol, StackerCore):
            if len(symbol.tokens) == 1:
                if is_symbol(symbol.tokens[0]):
                    return symbol.tokens[0][1:]
                else:
                    return symbol.tokens[0]
        raise StackerSyntaxError(f"Expected a symbol, got {symbol}")

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
            elif body in self.operator_manager.operators["regular"]:
                return self.operator_manager.operators["regular"][body]["func"]
            else:
                raise StackerSyntaxError(f"Unknown operator '{body}'")

    def _get_reduce_func(self, body: str | StackerCore | StackerLambda) -> callable:
        """Get a binary function for reduce/fold operations."""
        if isinstance(body, StackerCore):
            def binary_func(acc, x):
                stack = []
                body_copy = body.copy()
                # Push accumulator and current element to stack
                body_copy.tokens.insert(0, acc)
                body_copy.tokens.insert(1, x)
                body_copy._evaluate(body_copy.tokens, stack=stack)
                if len(stack) == 1:
                    return stack[0]
                elif len(stack) == 0:
                    return self._substack("{}")
                return stack[0]
            return binary_func
        elif isinstance(body, StackerLambda):
            return body
        else:
            if body in self.sfunctions:
                return self.sfunctions[body]["func"]
            elif body in self.plugins:
                return self.plugins[body]["func"]
            elif body in self.operator_manager.operators["regular"]:
                return self.operator_manager.operators["regular"][body]["func"]
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

    def __eq__(self, other: StackerCore) -> bool:
        if isinstance(other, StackerCore):
            return self.tokens == other.tokens
        else:
            if len(self.tokens) == 0:
                return other is None
            return self.tokens == other

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, index):
        return self.tokens[index]

    def __str__(self):
        def format_item(item):
            if isinstance(item, StackerCore):
                # return f"{str(item)}".replace(",", " ")
                raise NotImplementedError
            elif is_list(item):
                return item.replace(",", " ")
            # REMOVED: Tuple handling - () now creates code blocks
            elif isinstance(item, str):
                if item in self.operator_manager.built_in_operators:
                    return item
                elif is_code_block(item):
                    return item
                elif item in self.variables:
                    return item
                else:
                    return repr(item)
            return str(item)

        formatted_items = " ".join(map(format_item, self.tokens))
        # Use the bracket type that was used to create this code block
        if self.bracket_type == "(":
            return f"({formatted_items})"
        else:
            return f"{{{formatted_items}}}"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(str(self))  # TODO Check if this is correct
