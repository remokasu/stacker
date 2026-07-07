from __future__ import annotations
import copy
from typing import TYPE_CHECKING, Callable, Iterator
import ast
from functools import lru_cache
from stacker.constant import constants
from stacker.error import (
    NoValueProducedError,
    StackUnderflowError,
    StackerSyntaxError,
    UndefinedSymbolError,
    # UnexpectedTokenError,
)
from stacker.syntax.parser import (
    convert_custom_array_to_proper_list,
    is_code_block,
    # is_contains_transpose_command,
    # is_label_symbol,
    is_list,
    # is_transpose_command,
    # is_tuple,  # REMOVED: Tuples no longer supported, () now creates code blocks
    is_symbol,
    parse_expression,
)
from stacker.error import BreakException
from stacker.engine.data_type import String, UndefinedSymbol, stack_data, VOID
from stacker.engine.slambda import StackerLambda
from stacker.engine.scope import ScopedVariables
from stacker.operators.manager import OperatorManager

if TYPE_CHECKING:
    # from stacker.engine.sfunction import StackerFunction
    from stacker.engine.smacro import StackerMacro


# Commands that expect a symbol name as the preceding argument
_SYMBOL_CONSUMING_COMMANDS = frozenset({"set", "=", "defun", "defmacro"})
# Loop commands whose preceding block is itself preceded by a symbol name
_DO_DOLIST = frozenset({"do", "dolist"})
# Sentinel for single-lookup scope reads (None is a valid variable value)
_MISSING = object()


# Cache for literal_eval to avoid re-evaluating the same tokens
@lru_cache(maxsize=1024)
def _cached_literal_eval(token: str) -> object:
    """Cached version of ast.literal_eval for performance."""
    try:
        return ast.literal_eval(token)
    except Exception:
        return token


class StackerCore:
    """A class for evaluating RPN expressions."""

    _literal_cache: dict[str, int | bool] = {
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

    def __init__(
        self, expression: str | None = None, parent: StackerCore | None = None
    ) -> None:
        self.parent = parent
        self.child: StackerCore | None = None
        self.trace: list[object] = []  # for error trace
        self.stack: stack_data[object] = stack_data()
        self.tokens: list[object] = []
        self.bracket_type: str = "{"  # Default bracket type for display ({} or ())

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

        self.operator_manager: OperatorManager = OperatorManager()
        # Use ScopedVariables for efficient variable scoping
        self.variables: ScopedVariables = ScopedVariables(local_vars=dict(constants))
        self.sfunc_args: dict[str, list[str]] = {}
        self.macros: dict[str, object] = {}
        self.plugins: dict[str, object] = {}
        self.sfunctions: dict[str, object] = {}
        self.labels: dict[str, int] = {}

    def _block_token_format(self, token: str) -> object:
        # Check if token is a nested code block
        if is_code_block(token):
            # Convert to StackerCore instance
            temp_stack: stack_data[object] = stack_data()
            self._substack(token, temp_stack)
            return temp_stack.pop()
        # For non-code-block tokens, evaluate to preserve proper types
        # but don't resolve variables (keep them as strings for lazy evaluation)
        if token in self.operator_manager.operators["regular"]:
            return self._literal_eval2(f'"{token}"')
        # Try to evaluate as literal (numbers, strings, etc.)
        # but fallback to string if it's an identifier
        try:
            if (token.startswith("'") and token.endswith("'")) or (
                token.startswith('"') and token.endswith('"')
            ):
                return String(token[1:-1])
            else:
                return _cached_literal_eval(token)
        except Exception:
            # Keep as string for lazy evaluation (variables, operators, etc.)
            return token

    def _substack(self, token: str, stack: stack_data[object]) -> None:
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

    def _substack_with_expression(self, expression: str, stack: stack_data[object]) -> None:
        self.child = type(self)(expression=expression, parent=self)
        stack.append(self.child)

    def _substack_with_tokens(self, tokens: list[object], stack: stack_data[object]) -> None:
        self.child = type(self)(parent=self)
        self.child.tokens = tokens
        stack.append(self.child)

    def _safe_pop(self, stack: stack_data[object], operator: str = "unknown", num_args: int = 1) -> object:
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

    def _pop_only(self, stack: stack_data[object]) -> None:
        top = stack.pop()
        self.trace.append(top)
        return

    def _pop_and_eval(self, stack: stack_data[object]) -> object:
        value = stack.pop()

        # Check if value is an UndefinedSymbol
        if isinstance(value, UndefinedSymbol):
            raise UndefinedSymbolError(value.name)

        if isinstance(value, StackerCore):
            # Note: operators such as ifelse evaluate onto parent.stack, so
            # the evaluation stack must be the block's own stack attribute
            value._evaluate(value.tokens, stack=value.stack)
            sub = value.stack
            if sub:
                stack.extend(sub)
                # Clear leftovers so re-evaluating the same block object
                # (e.g. after dup) does not accumulate stale results
                sub.clear()
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
            return self.variables.get(value, value)

    def _eval(self, expr: str, stack: stack_data[object] | None = None) -> stack_data[object]:
        if stack is None:
            stack = stack_data()
        tokens = list(map(self._literal_eval, parse_expression(expr)))
        self._evaluate(tokens, stack=stack)
        return stack

    def _eval_block(self, block: StackerCore, stack: stack_data[object]) -> None:
        self._evaluate(block.tokens, stack=stack)

    def _evaluate(self, tokens: list[object], stack: stack_data[object] | None = None) -> stack_data[object]:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        if stack is None:
            stack = stack_data()
        self.trace = tokens

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
                should_treat_as_symbol = next_token in _SYMBOL_CONSUMING_COMMANDS or (
                    is_code_block(str(next_token))
                    and next_next_token in _DO_DOLIST
                )

                if should_treat_as_symbol:
                    # Treat as symbol name regardless of whether it's a variable or operator
                    stack.append(token)
                elif (value := self.variables.get(token, _MISSING)) is not _MISSING:
                    # Variable reference - evaluate it
                    if isinstance(value, StackerLambda):
                        args: list[object] = []
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
                        stack.append(UndefinedSymbol(evaluated))
                    else:
                        stack.append(evaluated)
        return stack

    def _var_str_to_literal(self, value: object) -> object:
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

    def _literal_eval(self, token: object) -> object:
        # Handle non-string tokens (already evaluated)
        if not isinstance(token, str):
            return token
        # Check for code blocks (both {} and ())
        if is_code_block(token):
            # Convert code block to StackerCore instance
            temp_stack: stack_data[object] = stack_data()
            self._substack(token, temp_stack)
            return temp_stack.pop()
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

    def _literal_eval2(self, token: str) -> object:
        # Check for code blocks (both {} and ())
        # token is guaranteed to be str by type hint, so no isinstance check needed
        if is_code_block(token):
            # Convert code block to StackerCore instance
            temp_stack: stack_data[object] = stack_data()
            self._substack(token, temp_stack)
            return temp_stack.pop()
        # Inline is_string check for performance
        elif (token.startswith("'") and token.endswith("'")) or (
            token.startswith('"') and token.endswith('"')
        ):
            return String(token[1:-1])
        else:
            # Use cached literal_eval for performance
            return _cached_literal_eval(token)

    def _execute(self, token: str, stack: stack_data[object]) -> None:
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
            return self.sfunctions[token]["arg_count"]  # type: ignore[index]
        elif token in self.plugins:
            return self.plugins[token]["arg_count"]  # type: ignore[index]
        entry = self.operator_manager.dispatch_table.get(token)
        if entry is not None:
            category, op = entry
            if category in ("priority", "settings"):
                # These categories may omit arg_count (matches the former
                # per-category walk's .get default)
                return op.get("arg_count", 0)  # type: ignore[return-value]
            return op["arg_count"]  # type: ignore[return-value]
        return 1  # Default

    def _execute_impl(self, token: str, stack: stack_data[object]) -> None:
        """
        Internal implementation of operator execution.
        IndexError and TypeError are caught by _execute and converted to better errors.
        """
        if token in self.sfunctions:  # sfunctions
            args: list[object] = []
            sfunc = self.sfunctions[token]
            for _ in range(sfunc["arg_count"]):  # type: ignore[index]
                args.insert(0, self._pop_and_eval(stack))
            if sfunc["push_result_to_stack"]:  # type: ignore[index]
                result = sfunc["func"](*args)  # type: ignore[index]
                if result is not VOID:
                    stack.append(result)
            else:
                sfunc["func"](*args)  # type: ignore[index]
        elif token in self.plugins:
            args = []
            op = self.plugins[token]
            for _ in range(op["arg_count"]):  # type: ignore[index]
                args.insert(0, self._pop_and_eval(stack))
            if op["push_result_to_stack"]:  # type: ignore[index]
                result = op["func"](*args)  # type: ignore[index]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*args)  # type: ignore[index]
        else:
            entry = self.operator_manager.dispatch_table.get(token)
            if entry is None:
                raise StackerSyntaxError(f"Unknown operator '{token}'")
            category, op = entry
            self._CATEGORY_EXECUTORS[category](self, token, op, stack)
        return

    # ------------------------------------------------------------------
    # Category executors. Bodies are moved verbatim from the former
    # _execute_impl elif chain; the unified dispatch table replaced the
    # per-category membership checks.
    # ------------------------------------------------------------------

    def _exec_priority(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        handler = self._PRIORITY_HANDLERS.get(token)
        # Some priority operators (e.g. `ans`) have no handler; falling
        # through silently preserves the former elif chain's behavior.
        if handler is not None:
            handler(self, op, stack)

    def _prio_do(self, op, stack) -> None:
        body = stack.pop()
        symbol = stack.pop()
        end_value = self._pop_and_eval(stack)
        start_value = self._pop_and_eval(stack)
        name = self._dollar_to_var_name(symbol)
        op["func"](start_value, end_value, name, body, self)

    def _prio_dolist(self, op, stack) -> None:
        body = stack.pop()
        symbol = stack.pop()
        lst = self._pop_and_eval(stack)
        name = self._dollar_to_var_name(symbol)
        op["func"](name, lst, body, self)

    def _prio_times(self, op, stack) -> None:
        n_times = self._pop_and_eval(stack)
        body = stack.pop()
        op["func"](n_times, body, self)

    def _prio_while(self, op, stack) -> None:
        body = stack.pop()
        condition = stack.pop()
        op["func"](condition, body, self)

    def _prio_break(self, op, stack) -> None:
        raise BreakException()
    def _prio_cond(self, op, stack) -> None:
        n = self._pop_and_eval(stack)
        pairs = []
        for _ in range(n):  # type: ignore[arg-type]
            result = stack.pop()
            condition = stack.pop()
            pairs.insert(0, (condition, result))
        op["func"](pairs, self, stack)

    def _prio_if(self, op, stack) -> None:
        true_block = stack.pop()
        condition = stack.pop()
        op["func"](condition, true_block, self)

    def _prio_ifelse(self, op, stack) -> None:
        false_block = stack.pop()
        true_block = stack.pop()
        condition = stack.pop()
        op["func"](condition, true_block, false_block, self)

    def _prio_iferror(self, op, stack) -> None:
        catch_block = stack.pop()
        try_block = stack.pop()
        op["func"](try_block, catch_block, self)

    def _prio_set(self, op, stack) -> None:
        symbol = stack.pop()
        name = self._dollar_to_var_name(symbol)
        value = self._pop_and_eval(stack)
        # Try to update existing variable in scope chain
        # If not found, create in local scope
        if not self.variables.update_existing(name, value):
            self.variables[name] = value

    def _prio_global(self, op, stack) -> None:
        # RPN: value varname global
        # Stack: [..., value, varname]
        symbol = stack.pop()  # Pop varname
        name = self._dollar_to_var_name(symbol)
        value = self._pop_and_eval(stack)  # Pop and eval value
        # Always set in global (root) scope
        self.variables.set_global(name, value)
    def _prio_defun(self, op, stack) -> None:
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

    def _prio_defmacro(self, op, stack) -> None:
        symbol = stack.pop()
        body = stack.pop()
        name = self._dollar_to_var_name(symbol)
        op["func"](self, name, body)

    def _prio_lambda(self, op, stack) -> None:
        body = stack.pop()
        fargs = stack.pop()
        if op["push_result_to_stack"]:
            result = op["func"](fargs, body)
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](fargs, body)

    def _prio_eval(self, op, stack) -> None:
        expression = stack.pop()
        if expression in self.variables:
            expression = self.variables[expression]
        if isinstance(expression, String):
            self._eval(expression.value, stack=stack)
        elif isinstance(expression, StackerCore):
            self._eval_block(expression, stack=stack)
        elif isinstance(expression, StackerLambda):
            largs: list[object] = []
            for _ in range(expression.arg_count):
                largs.insert(0, self._pop_and_eval(stack))
            stack.append(expression(*largs))
        else:
            stack.append(expression)

    def _prio_sub(self, op, stack) -> None:
        token = stack.pop()
        self._substack_with_tokens([token], stack)

    def _prio_subn(self, op, stack) -> None:
        n = stack.pop()
        elms = [stack.pop() for _ in range(n)]  # type: ignore[arg-type]
        elms.reverse()
        self._substack_with_tokens(elms, stack)

    def _prio_listn(self, op, stack) -> None:
        n = stack.pop()
        elms = [stack.pop() for _ in range(n)]  # type: ignore[arg-type]
        elms.reverse()
        stack.append(elms)

    def _prio_read_from_string(self, op, stack) -> None:
        self._substack_with_expression(stack.pop(), stack)  # type: ignore[arg-type]

    def _prio_read(self, op, stack) -> None:
        self._substack_with_expression(input(), stack)

    def _prio_split(self, op, stack) -> None:
        sep = stack.pop()
        word = stack.pop()
        for string in word.split(sep):  # type: ignore[union-attr]
            stack.append(string)

    def _prio_nth(self, op, stack) -> None:
        n = stack.pop()
        lst = stack[-1]
        if isinstance(lst, String):
            stack.append(String(lst[n]))  # type: ignore[index]
        else:
            stack.append(lst[n])  # type: ignore[index]

    def _prio_expand(self, op, stack) -> None:
        iterable = stack.pop()
        if isinstance(iterable, (list, tuple)):
            stack.extend(iterable)  # type: ignore[arg-type]
        elif isinstance(iterable, StackerCore):
            stack.extend(iterable.tokens)
        else:
            raise StackerSyntaxError(f"Cannot expand {iterable}")

    def _prio_apply(self, op, stack) -> None:
        func = stack.pop()
        args_list = self._pop_and_eval(stack)
        if isinstance(args_list, (list, tuple)):
            for arg in args_list:
                stack.append(arg)
        elif isinstance(args_list, StackerCore):
            for tok in args_list.tokens:
                stack.append(tok)
        else:
            stack.append(args_list)
        if isinstance(func, StackerCore):
            self._eval_block(func, stack=stack)
        elif isinstance(func, StackerLambda):
            largs: list[object] = []
            for _ in range(func.arg_count):
                largs.insert(0, self._pop_and_eval(stack))
            stack.append(func(*largs))
        elif isinstance(func, str):
            self._execute(func, stack)

    def _prio_include(self, op, stack) -> None:
        filename = stack.pop()
        op["func"](self, filename)

    def _prio_exit(self, op, stack) -> None:
        op["func"]()

    # Dispatch table for priority operators. Names absent here (e.g. `ans`)
    # are silent no-ops, matching the former elif chain's fall-through.
    _PRIORITY_HANDLERS = {
        "do": _prio_do,
        "dolist": _prio_dolist,
        "times": _prio_times,
        "while": _prio_while,
        "break": _prio_break,
        "cond": _prio_cond,
        "if": _prio_if,
        "ifelse": _prio_ifelse,
        "iferror": _prio_iferror,
        "set": _prio_set,
        "=": _prio_set,
        "global": _prio_global,
        "defun": _prio_defun,
        "defmacro": _prio_defmacro,
        "lambda": _prio_lambda,
        "eval": _prio_eval,
        "sub": _prio_sub,
        "subn": _prio_subn,
        "listn": _prio_listn,
        "read-from-string": _prio_read_from_string,
        "read": _prio_read,
        "split": _prio_split,
        "nth": _prio_nth,
        "expand": _prio_expand,
        "apply": _prio_apply,
        "include": _prio_include,
        "exit": _prio_exit,
    }
    def _exec_stack(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        op_args: list[object] = [stack]
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            op_args.insert(0, self._pop_and_eval(stack))
        if op["push_result_to_stack"]:
            result = op["func"](*op_args)  # type: ignore[operator]
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](*op_args)  # type: ignore[operator]

    def _exec_system(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        sys_args: list[object] = [stack, self]
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            sys_args.insert(0, self._pop_and_eval(stack))
        if op["push_result_to_stack"]:
            result = op["func"](*sys_args)  # type: ignore[operator]
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](*sys_args)  # type: ignore[operator]

    def _exec_regular(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        reg_args: list[object] = []
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            reg_args.insert(0, self._pop_and_eval(stack))
        if op["push_result_to_stack"]:
            result = op["func"](*reg_args)  # type: ignore[operator]
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](*reg_args)  # type: ignore[operator]
    def _exec_hof(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        if token in ["map", "filter"]:
            body = stack.pop()
            hof_args = stack.pop()
            args_org = copy.deepcopy(hof_args)
            func = self._get_hof_func(body, token)
            hof_args = hof_args.tokens if isinstance(hof_args, StackerCore) else hof_args
            if op["push_result_to_stack"]:
                lst = op["func"](func, hof_args)  # type: ignore[operator]
                if isinstance(args_org, list):
                    stack.append(list(lst))
                elif isinstance(args_org, tuple):
                    stack.append(tuple(lst))
                else:
                    self._substack_with_tokens(list(lst), stack)
            else:
                op["func"](func, hof_args)  # type: ignore[operator]
        elif token in ["reduce", "fold"]:
            body = stack.pop()
            symbol_x = stack.pop()  # Second variable name (element)
            symbol_acc = stack.pop()  # First variable name (accumulator)
            init = stack.pop()
            fold_args = stack.pop()

            # Extract variable names (same as dolist pattern)
            name_acc = self._dollar_to_var_name(symbol_acc)
            name_x = self._dollar_to_var_name(symbol_x)

            # Create binary function with variable binding
            def reduce_func(acc: object, x: object) -> object:
                # Create child scope for this reduction step
                original_parent_vars = self.variables
                original_parent_stack = self.stack
                result_stack: list[object] = []
                try:
                    self.variables = self.variables.create_child_scope()
                    # Bind accumulator and element to their variable names
                    self.variables[name_acc] = acc
                    self.variables[name_x] = x
                    # Evaluate the body using a temporary stack
                    self.stack = result_stack  # type: ignore[assignment]
                    self._evaluate(body.tokens, stack=result_stack)  # type: ignore[union-attr]
                finally:
                    # Restore parent scope and stack even if the body raised
                    self.stack = original_parent_stack
                    self.variables = original_parent_vars
                # Return the result
                if len(result_stack) == 1:
                    return result_stack[0]
                elif len(result_stack) == 0:
                    raise NoValueProducedError(token)
                return result_stack[0]

            fold_args = fold_args.tokens if isinstance(fold_args, StackerCore) else fold_args
            if op["push_result_to_stack"]:
                result = op["func"](reduce_func, init, fold_args)  # type: ignore[operator]
                stack.append(result)
            else:
                op["func"](reduce_func, init, fold_args)  # type: ignore[operator]
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
                lst = op["func"](xs1, xs2)  # type: ignore[operator]
                if isinstance(xs_org, list):
                    stack.append(list(lst))
                elif isinstance(xs_org, tuple):
                    stack.append(tuple(lst))
                else:
                    self._substack_with_tokens(list(lst), stack)
            else:
                op["func"](xs1, xs2)  # type: ignore[operator]
        else:
            ...
    def _exec_transform(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        tf_args = stack.pop()
        args_org = copy.deepcopy(tf_args)
        tf_args = (
            tf_args.tokens
            if isinstance(tf_args, StackerCore)
            else self._var_str_to_literal(tf_args)
        )
        if op["push_result_to_stack"]:
            lst = op["func"](tf_args)  # type: ignore[operator]
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
            op["func"](tf_args)  # type: ignore[operator]

    def _exec_aggregate(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        agg_args = stack.pop()
        agg_args = (
            list(map(self._literal_eval, agg_args.tokens))
            if isinstance(agg_args, StackerCore)
            else self._var_str_to_literal(agg_args)
        )
        if op["push_result_to_stack"]:
            result = op["func"](agg_args)  # type: ignore[operator]
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](agg_args)  # type: ignore[operator]

    def _exec_file(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        file_args: list[object] = []
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            file_args.insert(0, self._pop_and_eval(stack))
        if op["push_result_to_stack"]:
            result = op["func"](*file_args)  # type: ignore[operator]
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](*file_args)  # type: ignore[operator]

    def _exec_settings(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        if token == "disable_plugin":
            operator_name = stack.pop()
            op["func"](self, operator_name)  # type: ignore[operator]
        else:
            op["func"](self)  # type: ignore[operator]

    # Category -> executor. Keys must cover every category in
    # OperatorManager's dispatch table (_DISPATCH_ORDER).
    _CATEGORY_EXECUTORS = {
        "priority": _exec_priority,
        "stack": _exec_stack,
        "system": _exec_system,
        "regular": _exec_regular,
        "hof": _exec_hof,
        "transform": _exec_transform,
        "aggregate": _exec_aggregate,
        "file": _exec_file,
        "settings": _exec_settings,
    }

    def _dollar_to_var_name(self, symbol: object) -> str:
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
                    return symbol.tokens[0][1:]  # type: ignore[index]
                else:
                    return symbol.tokens[0]  # type: ignore[return-value]
        raise StackerSyntaxError(f"Expected a symbol, got {symbol}")

    def _get_hof_func(self, body: object, operator: str) -> Callable[..., object]:
        if isinstance(body, StackerCore):
            return lambda args: self._stacker_lambda(args, body.copy(), operator)
        elif isinstance(body, StackerLambda):
            return body
        else:
            if body in self.sfunctions:
                return self.sfunctions[body]["func"]  # type: ignore[index]
            elif body in self.plugins:
                return self.plugins[body]["func"]  # type: ignore[index]
            elif body in self.operator_manager.operators["regular"]:
                return self.operator_manager.operators["regular"][body]["func"]  # type: ignore[index]
            else:
                raise StackerSyntaxError(f"Unknown operator '{body}'")

    def _get_reduce_func(self, body: object) -> Callable[..., object]:
        """Get a binary function for reduce/fold operations."""
        if isinstance(body, StackerCore):
            def binary_func(acc: object, x: object) -> object:
                bstack: list[object] = []
                body_copy = body.copy()
                # Push accumulator and current element to stack
                body_copy.tokens.insert(0, acc)
                body_copy.tokens.insert(1, x)
                body_copy._evaluate(body_copy.tokens, stack=bstack)
                if len(bstack) == 1:
                    return bstack[0]
                elif len(bstack) == 0:
                    return self._substack("{}")
                return bstack[0]
            return binary_func
        elif isinstance(body, StackerLambda):
            return body
        else:
            if body in self.sfunctions:
                return self.sfunctions[body]["func"]  # type: ignore[index]
            elif body in self.plugins:
                return self.plugins[body]["func"]  # type: ignore[index]
            elif body in self.operator_manager.operators["regular"]:
                return self.operator_manager.operators["regular"][body]["func"]  # type: ignore[index]
            else:
                raise StackerSyntaxError(f"Unknown operator '{body}'")

    def _expand_macro(self, name: str, stack: stack_data[object]) -> None:
        """Executes a macro."""
        macro: StackerMacro = self.macros[name]  # type: ignore[assignment]
        self._evaluate(macro.blockstack.tokens, stack=stack)

    def _stacker_lambda(self, arg: object, body: StackerCore, operator: str) -> object:
        lstack: list[object] = []
        body.tokens.insert(0, arg)
        body._evaluate(body.tokens, stack=lstack)
        if len(lstack) == 1:
            return lstack[0]
        elif len(lstack) == 0:
            raise NoValueProducedError(operator)
        return lstack

    def copy(self) -> StackerCore:
        return copy.deepcopy(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StackerCore):
            return self.tokens == other.tokens
        else:
            if len(self.tokens) == 0:
                return other is None
            return self.tokens == other

    def __iter__(self) -> Iterator[object]:
        return iter(self.tokens)

    def __len__(self) -> int:
        return len(self.tokens)

    def __getitem__(self, index: int) -> object:
        return self.tokens[index]

    def __str__(self) -> str:
        def format_item(item: object) -> str:
            if isinstance(item, StackerCore):
                return str(item)
            elif is_list(item):
                return item.replace(",", " ")  # type: ignore[union-attr]
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

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(str(self))  # TODO Check if this is correct
