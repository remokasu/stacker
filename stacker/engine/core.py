from __future__ import annotations
import copy
import logging
from collections.abc import Callable, Iterator
import ast
from stacker.constant import constants
from stacker.error import (
    MacroExpansionError,
    NoValueProducedError,
    StackUnderflowError,
    StackerError,
    StackerSyntaxError,
    UndefinedSymbolError,
    attach_macro_context,
    # UnexpectedTokenError,
)
from stacker.syntax.parser import (
    convert_custom_array_to_proper_list,
    parse_expression,
)
from stacker.error import BreakException
from stacker.engine.boundary import value_to_token
from stacker.engine.data_type import String, Symbol, UndefinedSymbol, stack_data, VOID
from stacker.syntax.token_rules import (
    cached_literal_eval,
    is_bare_name,
    is_code_block,
    is_list,
    is_string_token,
    is_symbol,
    reads_as_name,
    strip_string_delimiters,
)
from stacker.engine.slambda import StackerLambda
from stacker.engine.scope import ScopedVariables
from stacker.engine import recursion
from stacker.engine.smacro import StackerMacro, gensym
from stacker.operators.manager import OperatorManager

_LOGGER = logging.getLogger("stacker")

_DEFMACRO_USAGE = (
    "`defmacro` takes three arguments: {args} {body} name defmacro. "
    "For a plain named code snippet use `alias`: {body} {name} alias."
)


# Commands that expect a symbol name as the preceding argument
_SYMBOL_CONSUMING_COMMANDS = frozenset({"set", "=", "defun", "defmacro", "global", "macroexpand"})
# Words of the form `... name {block} WORD`: the name before the block is bound
_DO_DOLIST = frozenset({"do", "dolist"})
# Words of the form `... name name {block} WORD`: both names are bound
_REDUCE_FOLD = frozenset({"reduce", "fold"})
_BLOCK_BINDING_WORDS = _DO_DOLIST | _REDUCE_FOLD
# Sentinel for single-lookup scope reads (None is a valid variable value)
_MISSING = object()


# Token classification kinds. Every decision below is a pure function of
# the token values (never of interpreter state), so a classification can be
# computed once per token list and reused across evaluations.
K_VALUE = 0  # non-str token: push as-is
K_STRING = 1  # quoted string literal: payload is the prebuilt String
K_LIST = 2  # list literal: payload is the parsed template (or None)
K_SYMBOL = 3  # $name: payload is the Symbol
K_BLOCK = 4  # code-block source: substack is created at evaluation time
K_LOOKAHEAD_SYMBOL = 5  # bare name right before a binding form (set/defun/...): payload is the Symbol
K_DYNAMIC = 6  # name resolved against runtime state on every evaluation
K_LOOP_VAR = 7  # bare name bound by do / dolist / reduce / fold (before their block): payload is the Symbol


def _classify_tokens(tokens: list[object]) -> list[tuple[int, object, object]]:
    """Classify tokens by the purely syntactic part of the evaluation chain.

    Mirrors the branch order of ``StackerCore._evaluate`` exactly, minus the
    macro check (macros are runtime state, so that check stays in the
    evaluation loop). A ``String`` object is always a string literal
    (``K_STRING``): blocks store their literals that way, and a literal must
    never be looked up as a name, whatever text it holds. Quote checks on raw
    source tokens go through ``is_string_token``.

    Args:
        tokens: Token list as produced by the parser / block formatter.

    Returns:
        One ``(kind, token, payload)`` entry per token.
    """
    entries: list[tuple[int, object, object]] = []
    n = len(tokens)
    for i, token in enumerate(tokens):
        if not isinstance(token, str):
            entries.append((K_VALUE, token, None))
        elif isinstance(token, String):
            entries.append((K_STRING, token, token))
        elif is_string_token(token):
            entries.append((K_STRING, token, String(strip_string_delimiters(token))))
        elif is_list(token):
            try:
                template = ast.literal_eval(
                    convert_custom_array_to_proper_list(token)
                )
            except Exception:
                # Malformed list token: leave the payload empty so the
                # evaluation loop re-parses (and raises) at the token's
                # execution position, exactly as before.
                template = None
            entries.append((K_LIST, token, template))
        elif is_symbol(token):
            entries.append((K_SYMBOL, token, Symbol(token[1:])))
        elif is_code_block(token):
            entries.append((K_BLOCK, token, None))
        else:
            next_token = tokens[i + 1] if i + 1 < n else None
            next_next_token = tokens[i + 2] if i + 2 < n else None
            third_token = tokens[i + 3] if i + 3 < n else None
            # Only raw source tokens are words; a String literal that reads
            # "set" or a list value must never be mistaken for one.
            word1 = next_token if type(next_token) is str else None
            word2 = next_next_token if type(next_next_token) is str else None
            word3 = third_token if type(third_token) is str else None
            if word1 in _SYMBOL_CONSUMING_COMMANDS:
                kind = K_LOOKAHEAD_SYMBOL
            elif word2 in _BLOCK_BINDING_WORDS and _is_block_token(next_token):
                # `name {block} do`, and the second name of `acc x {block} reduce`
                kind = K_LOOP_VAR
            elif (
                word3 in _REDUCE_FOLD
                and _is_block_token(next_next_token)
                and is_bare_name(next_token)
            ):
                # the first name of `acc x {block} reduce`
                kind = K_LOOP_VAR
            else:
                kind = K_DYNAMIC
            if kind != K_DYNAMIC and not reads_as_name(token):
                kind = K_DYNAMIC  # a literal (number, True, None, ...) is never a name
            entries.append((kind, token, None if kind == K_DYNAMIC else Symbol(token)))
    return entries


def _is_block_token(token: object) -> bool:
    """True if ``token`` is a code block, as source text or already built."""
    return isinstance(token, StackerCore) or (type(token) is str and is_code_block(token))


class TokenList(list):
    """Token list carrying a lazily computed classification cache.

    The cache is invalidated by a length guard: every in-place tokens
    mutation in the codebase changes the list's length (lambda/reduce
    ``insert`` calls), and wholesale replacements create a fresh
    ``TokenList``. ``deepcopy`` intentionally drops the cache so copies
    reclassify after their own mutations.
    """

    def classification(self) -> list[tuple[int, object, object]]:
        """Return cached classification entries, recomputing when stale."""
        entries = getattr(self, "_cls_entries", None)
        if entries is None or self._cls_len != len(self):
            entries = _classify_tokens(self)
            self._cls_entries = entries
            self._cls_len = len(self)
        return entries

    def __deepcopy__(self, memo: dict[int, object]) -> "TokenList":
        new = TokenList()
        memo[id(self)] = new
        new.extend(copy.deepcopy(item, memo) for item in self)
        return new


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
        self.tokens: list[object] = TokenList()
        self.bracket_type: str = "{"  # Default bracket type for display ({} or ())

        # Source location tracking for error reporting
        self.current_file: str | None = None
        self.current_line: int | None = None
        self.source_lines: dict[int, str] = {}  # Map line number to source code

        # Macro expansion state: set only on the throwaway core that runs a
        # macro body. `_interp_scope` is the expansion scope whose own
        # bindings get interpolated into block literals; `_interp_target_vars`
        # is the caller's scope the interpolated copies must run in.
        self._interp_scope: ScopedVariables | None = None
        self._interp_target_vars: ScopedVariables | None = None

        if self.parent is not None:  # it is a substack of a parent stacker
            self.operator_manager = self.parent.operator_manager
            self.macros = self.parent.macros
            self.variables = self.parent.variables
            self.plugins = self.parent.plugins
            self.sfunctions = self.parent.sfunctions
            self.labels = self.parent.labels
            self._prelude = self.parent._prelude
            # Share source location tracking with parent
            self.current_file = self.parent.current_file
            self.current_line = self.parent.current_line
            self.source_lines = self.parent.source_lines
            if expression is not None:
                self.tokens = TokenList(
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
        # Prelude bookkeeping, shared by reference with every child core:
        # names defined by the prelude (for redefinition warnings), the very
        # objects it defined (so `include` can tell them from user
        # definitions), whether the prelude is being loaded right now, and
        # whether it is enabled.
        self._prelude: dict[str, object] = {
            "names": set(),
            "objects": {},
            "loading": False,
            "enabled": True,
        }

    def _block_token_format(self, token: str) -> object:
        """Converts one source token of a block into its stored form.

        Nested blocks become ``StackerCore`` instances, string literals become
        ``String`` values (which the classifier always treats as literals) and
        other Python literals become values. Everything else, including
        operator names and ``$x``, stays a raw token for lazy resolution.

        Args:
            token: One token of the block's source.

        Returns:
            The stored token.
        """
        if is_code_block(token):
            temp_stack: stack_data[object] = stack_data()
            self._substack(token, temp_stack)
            return temp_stack.pop()
        if is_string_token(token):
            return String(strip_string_delimiters(token))
        return cached_literal_eval(token)

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
        # Callers always pass freshly built lists, so wrapping copies no
        # shared state; the TokenList carries the classification cache.
        self.child.tokens = TokenList(tokens)
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
        """Pops an operator argument, evaluating a code block to its value.

        A ``String`` is handed to host functions as a plain ``str``. Every
        other value, a ``Symbol`` included, is returned as it is: a name is
        never looked up here, so ``$x`` stays the symbol ``x`` whether or
        not a variable ``x`` exists.

        Args:
            stack: Stack to pop from.

        Returns:
            The argument value.
        """
        value = stack.pop()

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
        if isinstance(value, String):
            return value.value
        return value

    def _pop_and_resolve(self, stack: stack_data[object]) -> object:
        """Pops a value for a binding form without evaluating it.

        ``=`` / ``set`` / ``global`` and the parameters of functions and
        lambdas are binding forms: a code block is bound raw ("code is
        data"), a ``String`` keeps its type and a ``Symbol`` stays a symbol.
        Nothing is looked up as a variable.

        Args:
            stack: Stack to pop the value from.

        Returns:
            The value, unevaluated.
        """
        value = stack.pop()

        if isinstance(value, UndefinedSymbol):
            raise UndefinedSymbolError(value.name)
        return value

    def _eval(self, expr: str, stack: stack_data[object] | None = None) -> stack_data[object]:
        if stack is None:
            stack = stack_data()
        # Same path as `read-from-string`: build block tokens and evaluate
        # them, so names resolve at evaluation time, not while tokenizing.
        tokens = TokenList(map(self._block_token_format, parse_expression(expr)))
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

        # Block/function bodies hold long-lived TokenLists whose
        # classification is computed once; top-level token lists are fresh
        # per call and classified in a single throwaway pass.
        if isinstance(tokens, TokenList):
            entries = tokens.classification()
        else:
            entries = _classify_tokens(tokens)
        macros = self.macros
        # Parameter interpolation applies only while a macro body (this
        # core's own token list) is being run; any other token list -- an
        # interpolated copy, a caller-supplied block, a runtime-built block --
        # is left untouched.
        interp = self._interp_scope if tokens is self.tokens else None
        kernel_words = self.operator_manager.built_in_operators
        plugins = self.plugins

        for kind, token, payload in entries:
            if kind == K_VALUE:
                if interp is not None and isinstance(token, StackerCore):
                    stack.append(self._interpolate(token, interp))
                else:
                    stack.append(token)  # Literal value
                continue
            if kind == K_STRING:
                stack.append(payload)  # a string literal is never a name
                continue
            if kind == K_LOOKAHEAD_SYMBOL:
                # Shadowing rule: only kernel words are protected. Any other
                # bare name before a binding form is the name being bound, so
                # user definitions can be rebound by their bare name.
                if token not in kernel_words and token not in plugins:
                    stack.append(payload)  # the Symbol
                    continue
            elif kind == K_LOOP_VAR:
                stack.append(payload)  # the Symbol
                continue
            # Macros take precedence over variables and operators. (At the
            # lookahead position only kernel-word names get this far; any
            # other name was just pushed as the name being bound.)
            if token in macros:
                self._expand_macro(token, stack)
            elif kind == K_DYNAMIC or kind == K_LOOKAHEAD_SYMBOL:
                if (value := self.variables.get(token, _MISSING)) is not _MISSING:
                    # A variable reference pushes the value, whatever it is:
                    # a lambda is a value too and is called with `eval`.
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
            elif kind == K_LIST:
                if payload is None:
                    # Malformed template: reproduce the original inline parse
                    # so the error is raised here, at execution position.
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
                else:
                    # Re-resolve top-level string elements on every
                    # evaluation and re-materialize nested containers so no
                    # state is shared between evaluations (same output as
                    # the former fresh ast.literal_eval per evaluation).
                    stack.append(
                        [
                            self._var_str_to_literal(element)
                            if isinstance(element, str)
                            else (
                                copy.deepcopy(element)
                                if isinstance(element, (list, tuple))
                                else element
                            )
                            for element in payload
                        ]
                    )
            elif kind == K_SYMBOL:
                stack.append(payload)  # the Symbol
            elif kind == K_BLOCK:
                self._substack(token, stack)
        return stack

    def _var_str_to_literal(self, value: object) -> object:
        if isinstance(value, UndefinedSymbol):
            # Popped from the stack: the same error every other consumer raises.
            raise UndefinedSymbolError(value.name)
        if isinstance(value, String):
            # A string literal popped from the stack is data; it must not be
            # looked up as a variable (`5 ab set "ab" list` listed 5).
            return value
        if isinstance(value, str) and is_string_token(value):
            return String(strip_string_delimiters(value))
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
        elif is_string_token(token):
            return String(strip_string_delimiters(token))
        else:
            # Check cache first for common literals
            if token in StackerCore._literal_cache:
                return StackerCore._literal_cache[token]
            try:
                return ast.literal_eval(token)
            except (ValueError, TypeError, SyntaxError):
                # Malformed literal: fall back to the raw token. Fatal errors
                # (MemoryError / RecursionError) must propagate.
                return token

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
            if category == "transform":
                # The former per-category walk never checked "transform",
                # so these operators always fell through to the default;
                # preserve that so StackUnderflowError text stays identical.
                return 1
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
                # Parameters are binding forms: block arguments bind
                # raw (code is data)
                args.insert(0, self._pop_and_resolve(stack))
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
        """Execute a priority operator via its per-name handler (see _PRIORITY_HANDLERS)."""
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
        name = self._name_of(symbol, "do")
        op["func"](start_value, end_value, name, body, self, stack)

    def _prio_dolist(self, op, stack) -> None:
        body = stack.pop()
        symbol = stack.pop()
        lst = self._pop_and_eval(stack)
        name = self._name_of(symbol, "dolist")
        op["func"](name, lst, body, self, stack)

    def _prio_times(self, op, stack) -> None:
        n_times = self._pop_and_eval(stack)
        body = stack.pop()
        op["func"](n_times, body, self, stack)

    def _prio_while(self, op, stack) -> None:
        body = stack.pop()
        condition = stack.pop()
        op["func"](condition, body, self, stack)

    def _prio_loop(self, op, stack) -> None:
        body = stack.pop()
        op["func"](body, self, stack)

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
        op["func"](condition, true_block, self, stack)

    def _prio_ifelse(self, op, stack) -> None:
        false_block = stack.pop()
        true_block = stack.pop()
        condition = stack.pop()
        op["func"](condition, true_block, false_block, self, stack)

    def _prio_iferror(self, op, stack) -> None:
        catch_block = stack.pop()
        try_block = stack.pop()
        op["func"](try_block, catch_block, self, stack)

    def _prio_set(self, op, stack) -> None:
        symbol = stack.pop()
        name = self._name_of(symbol, "set")
        value = self._pop_and_resolve(stack)
        if name in self._prelude["names"]:
            self._warn_prelude_redefinition(name)
        # Try to update existing variable in scope chain
        # If not found, create in local scope
        if not self.variables.update_existing(name, value):
            self.variables[name] = value

    def _prio_global(self, op, stack) -> None:
        # RPN: value varname global
        # Stack: [..., value, varname]
        symbol = stack.pop()  # Pop varname
        name = self._name_of(symbol, "global")
        value = self._pop_and_resolve(stack)  # Blocks bind raw (code is data)
        if name in self._prelude["names"]:
            self._warn_prelude_redefinition(name)
        # Always set in global (root) scope
        self.variables.set_global(name, value)

    def _warn_prelude_redefinition(self, name: str) -> None:
        """Logs a warning when user code redefines a word the prelude defined."""
        if not self._prelude["loading"]:
            _LOGGER.warning("redefining prelude word '%s'", name)

    def _prio_defun(self, op, stack) -> None:
        """``{args} {body} name defun`` -- the argument list is validated like ``defmacro``'s."""
        symbol = stack.pop()
        name = self._name_of(symbol, "defun")
        if name in self._prelude["names"]:
            self._warn_prelude_redefinition(name)
        body = stack.pop()
        fargs = self._parse_arg_names(stack.pop(), "defun")
        op["func"](self, name, fargs, body)

    def _prio_defmacro(self, op, stack) -> None:
        """``{args} {body} name defmacro`` -- validates the three parts at definition time."""
        symbol = stack.pop()
        body = stack.pop()
        try:
            fargs = stack.pop()
        except IndexError:
            # The pre-1.15 two-term form `{body} name defmacro` lands here.
            raise StackerSyntaxError(_DEFMACRO_USAGE) from None
        name = self._name_of(symbol, "defmacro")
        if not isinstance(body, StackerCore):
            raise StackerSyntaxError(
                f"`defmacro` expects a code block as the macro body, got {body}. {_DEFMACRO_USAGE}"
            )
        args = self._parse_arg_names(fargs, "defmacro")
        if name in self._prelude["names"]:
            self._warn_prelude_redefinition(name)
        op["func"](self, name, args, body)

    def _prio_macroexpand(self, op, stack) -> None:
        name = self._name_of(stack.pop(), "macroexpand")
        if name not in self.macros:
            raise StackerSyntaxError(f"`macroexpand` expects a macro name, `{name}` is not a macro")
        self._expand_macro(name, stack, evaluate=False)

    def _prio_gensym(self, op, stack) -> None:
        stack.append(gensym())

    def _prio_concat_block(self, op, stack) -> None:
        second = stack.pop()
        first = stack.pop()
        if not isinstance(first, StackerCore) or not isinstance(second, StackerCore):
            raise StackerSyntaxError(
                f"`concat-block` expects two code blocks, got {first} and {second}"
            )
        self._substack_with_tokens(list(first.tokens) + list(second.tokens), stack)

    def _prio_lambda(self, op, stack) -> None:
        """``{args} {body} lambda`` -- the argument list is validated like ``defmacro``'s."""
        body = stack.pop()
        fargs = self._parse_arg_names(stack.pop(), "lambda")
        if op["push_result_to_stack"]:
            result = op["func"](fargs, body)
            if result is not VOID:
                stack.append(result)
        else:
            op["func"](fargs, body)

    def _prio_eval(self, op, stack) -> None:
        """Evaluates the top value.

        - a ``Symbol`` is evaluated as its name, exactly as if the bare name
          had been written here (macro, variable, function or operator)
        - a string is evaluated as source code
        - a code block is evaluated on this stack
        - a lambda is called with arguments taken from this stack
        - anything else is pushed back
        """
        expression = stack.pop()
        if isinstance(expression, Symbol):
            self._evaluate([expression.name], stack=stack)
        elif isinstance(expression, UndefinedSymbol):
            stack.append(expression)
        elif isinstance(expression, str):
            self._eval(str(expression), stack=stack)
        elif isinstance(expression, StackerCore):
            self._eval_block(expression, stack=stack)
        elif isinstance(expression, StackerLambda):
            self._call_lambda(expression, stack)
        else:
            stack.append(expression)

    def _call_lambda(self, fn: StackerLambda, stack: stack_data[object]) -> None:
        """Calls a lambda value with arguments popped from ``stack``.

        Parameters are binding forms, so a code-block argument is bound raw
        (code is data), like a function parameter. A ``VOID`` result is not
        pushed.

        Args:
            fn: The lambda to call.
            stack: Stack holding the arguments; the result is pushed here.

        Raises:
            StackUnderflowError: Fewer than ``fn.arg_count`` values on ``stack``.
        """
        args: list[object] = []
        try:
            for _ in range(fn.arg_count):
                args.insert(0, self._pop_and_resolve(stack))
        except IndexError:
            raise StackUnderflowError("lambda", fn.arg_count) from None
        result = fn(*args)
        if result is not VOID:
            stack.append(result)

    def _prio_sub(self, op, stack) -> None:
        self._substack_with_tokens([self._as_token(stack.pop())], stack)

    def _prio_subn(self, op, stack) -> None:
        n = stack.pop()
        elms = [self._as_token(stack.pop()) for _ in range(n)]  # type: ignore[arg-type]
        elms.reverse()
        self._substack_with_tokens(elms, stack)

    @staticmethod
    def _as_token(value: object) -> object:
        """``value_to_token`` that still lets an ``UndefinedSymbol`` through as a bare name."""
        if isinstance(value, UndefinedSymbol):
            return value.name
        return value_to_token(value)

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
            # Each token becomes a one-token code block, so the pieces stay
            # code (`{+}`) rather than leaking the raw token representation.
            for token in iterable.tokens:
                self._substack_with_tokens([token], stack)
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
            self._call_lambda(func, stack)
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
        "loop": _prio_loop,
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
        "macroexpand": _prio_macroexpand,
        "gensym": _prio_gensym,
        "concat-block": _prio_concat_block,
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
        """Execute a stack-category operator; the stack itself is the last argument."""
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
        """Execute a system-category operator; receives the stack and interpreter as trailing arguments."""
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
        """Execute a regular operator: pop arg_count evaluated arguments, push non-VOID results."""
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
        """Execute a higher-order operator (map/filter, reduce/fold, zip) with per-name argument shapes."""
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
            name_acc = self._name_of(symbol_acc, token)
            name_x = self._name_of(symbol_x, token)

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
        """Execute a transform operator, preserving the input's container type on push."""
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
        """Execute an aggregate operator over a literal-evaluated block or list argument."""
        agg_args = stack.pop()
        agg_args = (
            # A String token is already a literal; re-evaluating its text
            # would read `{"a"} max` as the variable `a`.
            [t if isinstance(t, String) else self._literal_eval(t) for t in agg_args.tokens]
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
        """Execute a file operator: pop arg_count evaluated arguments, push non-VOID results."""
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
        """Execute a settings operator; disable_plugin additionally pops the target name."""
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

    def _name_of(self, symbol: object, word: str) -> str:
        """Normalizes the forms a name can be written in to the bare name.

        - a ``Symbol`` (``$name``, ``gensym``, a bare name read at a name
          position) -> its name
        - ``{name}`` / ``{$name}`` (quoted name: a one-token block) -> ``name``
        - a string (temporarily, until strings stop naming things) -> its text
        - anything else (a multi-token block, a number, ...) -> ``StackerSyntaxError``

        Args:
            symbol: Value popped from the stack at a name position.
            word: The word reading the name (for the error message).

        Returns:
            The bare name, the key used in the variable scopes.

        Raises:
            StackerSyntaxError: If ``symbol`` cannot denote a name.
        """
        if isinstance(symbol, Symbol):
            return symbol.name
        if isinstance(symbol, StackerCore) and len(symbol.tokens) == 1:
            token = symbol.tokens[0]
            if isinstance(token, str):
                return token[1:] if is_symbol(token) else token
        elif isinstance(symbol, str):
            return symbol[1:] if is_symbol(symbol) else str(symbol)
        raise StackerSyntaxError(f"Expected a symbol, got {symbol}")

    def _parse_arg_names(self, fargs: object, word: str) -> list[str]:
        """Validates an argument list ``{a b ...}`` and returns the names.

        Shared by ``defun``, ``lambda`` and ``defmacro``: the list must be a
        code block whose tokens are distinct bare names (no ``$a``, string,
        literal or nested block).

        Args:
            fargs: The value written where the argument list goes.
            word: The defining word (for the error messages).

        Returns:
            The argument names in order.

        Raises:
            StackerSyntaxError: If ``fargs`` is not a valid argument list.
        """
        if not isinstance(fargs, StackerCore):
            hint = f" {_DEFMACRO_USAGE}" if word == "defmacro" else ""
            raise StackerSyntaxError(
                f"`{word}` expects a code block of argument names, got {fargs}.{hint}"
            )
        names: list[str] = []
        for token in fargs.tokens:
            if type(token) is not str or is_symbol(token) or not is_bare_name(token):
                raise StackerSyntaxError(f"`{word}` argument names must be bare names, got {token}")
            names.append(token)
        if len(set(names)) != len(names):
            raise StackerSyntaxError(f"`{word}` argument names must be unique: {{{' '.join(names)}}}")
        return names

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

    def _pop_macro_arg(self, stack: stack_data[object]) -> object:
        """Pops a macro argument without evaluating it.

        Like ``_pop_and_resolve``: blocks stay raw, a ``String`` keeps its
        type and a ``Symbol`` stays a symbol. An undefined bare name (still
        pushed as ``UndefinedSymbol`` for now) is handed over as a symbol.

        Args:
            stack: Stack to pop from.

        Returns:
            The argument value.
        """
        value = stack.pop()
        if isinstance(value, UndefinedSymbol):
            return Symbol(value.name)
        return value

    def _interpolate(self, block: StackerCore, scope: ScopedVariables) -> StackerCore:
        """Copies ``block`` with the expansion scope's own bindings spliced in.

        Only the template tree is walked: values spliced in are never
        re-scanned, so caller-supplied code is left exactly as written.
        Bare-name tokens bound in ``scope`` are replaced by their values;
        ``$name``, string literals and list literals are untouched.

        Args:
            block: Block literal from the macro body.
            scope: Expansion scope; only its own bindings are consulted.

        Returns:
            A fresh block whose scope is the caller's.
        """
        bindings = scope.own_bindings()

        def substitute(token: object) -> object:
            if isinstance(token, StackerCore):
                return build(token)
            if type(token) is not str or is_symbol(token) or token not in bindings:
                return token  # literals, `$name` and unbound names stay as written
            # A symbol becomes a bare name, a string a string literal,
            # anything else is spliced as a value (see engine/boundary.py).
            return value_to_token(bindings[token])

        def build(template: StackerCore) -> StackerCore:
            copy_core = type(self)(parent=self)
            copy_core.tokens = TokenList([substitute(token) for token in template.tokens])
            copy_core.bracket_type = template.bracket_type
            copy_core.variables = self._interp_target_vars  # type: ignore[assignment]
            return copy_core

        return build(block)

    def _expand_macro(self, name: str, stack: stack_data[object], *, evaluate: bool = True) -> None:
        """Expands a macro call and (by default) evaluates the expansion.

        The body runs on a throwaway stack in a child scope of the caller
        where the arguments are bound and assignments stay local. Exactly one
        value must remain: a code block is evaluated on ``stack`` in the
        caller's scope, any other value is pushed.

        Args:
            name: Macro name (already known to be in ``self.macros``).
            stack: Caller's evaluation stack.
            evaluate: When False (``macroexpand``), push the expansion instead
                of evaluating it.

        Raises:
            StackUnderflowError: Not enough arguments on ``stack``.
            NoValueProducedError: The body left nothing.
            MacroExpansionError: The body left more than one value.
        """
        macro: StackerMacro = self.macros[name]  # type: ignore[assignment]
        recursion.enter(name, kind="macro")
        try:
            args: list[object] = []
            for _ in range(macro.arg_count):
                try:
                    args.insert(0, self._pop_macro_arg(stack))
                except IndexError:
                    raise StackUnderflowError(name, macro.arg_count) from None

            scope = self.variables.create_child_scope()
            scope._write_barrier = True
            for arg_name, value in zip(macro.args, args):
                scope[arg_name] = value

            expander = type(self)(parent=self)
            expander.tokens = macro.body.tokens  # shared, read-only
            expander.bracket_type = macro.body.bracket_type
            expander.variables = scope
            expander._interp_scope = scope
            expander._interp_target_vars = self.variables
            expansion_stack: stack_data[object] = stack_data()
            try:
                expander._evaluate(expander.tokens, stack=expansion_stack)
            except StackerError as error:
                attach_macro_context(error, f"while expanding macro '{name}'")
                raise

            if len(expansion_stack) == 0:
                raise NoValueProducedError(
                    name, f"Macro `{name}` left no value to use as its expansion."
                )
            if len(expansion_stack) > 1:
                raise MacroExpansionError(name, len(expansion_stack))
            result = expansion_stack.pop()

            if not evaluate or not isinstance(result, StackerCore):
                stack.append(result)
                return
            try:
                self._eval_block(result, stack)
            except StackerError as error:
                attach_macro_context(error, f"in code generated by macro '{name}'")
                raise
        finally:
            recursion.leave()

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
            elif isinstance(item, String):
                # A string literal, quotes and all (single quotes if the text has double ones).
                quote = "'" if '"' in item.value and "'" not in item.value else '"'
                return f"{quote}{item.value}{quote}"
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
        # Must agree with __eq__ (token comparison): str(self) includes
        # the bracket type, which made equal {…} and (…) blocks hash
        # differently and violate the eq/hash contract
        return hash(str(self.tokens))
