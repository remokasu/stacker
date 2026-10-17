from __future__ import annotations
import copy
import logging
from collections.abc import Callable, Iterator
from typing import NoReturn
import ast
from stacker.constant import constants
from stacker.error import (
    MacroExpansionError,
    NoValueProducedError,
    StackUnderflowError,
    StackerError,
    StackerRuntimeError,
    StackerSyntaxError,
    StackerTypeError,
    UndefinedSymbolError,
    attach_macro_context,
    # UnexpectedTokenError,
)
from stacker.syntax.parser import (
    convert_custom_array_to_proper_list,
    parse_expression,
)
from stacker.error import BreakException
from stacker.engine.boundary import token_to_value, value_to_token
from stacker.util.disp import plain_text  # disp.py must not import core.py
from stacker.engine.data_type import String, Symbol, stack_data, VOID
from stacker.syntax.token_rules import (
    KEYWORD_LITERALS,
    OLD_SYMBOL_PREFIX,
    SYMBOL_PREFIX,
    cached_literal_eval,
    is_bare_name,
    is_code_block,
    is_list,
    is_string_token,
    is_symbol,
    is_symbol_name,
    not_a_symbol_message,
    strip_string_delimiters,
)
from stacker.engine.slambda import StackerLambda
from stacker.engine.scope import ScopedVariables
from stacker.engine import recursion
from stacker.engine.smacro import StackerMacro, gensym
from stacker.operators.manager import OperatorManager

_LOGGER = logging.getLogger("stacker")

_DEFMACRO_USAGE = (
    "`defmacro` takes three arguments: {args} {body} :name defmacro. "
    "For a plain named code snippet use `alias`: {body} {name} alias."
)


# Sentinel for single-lookup scope reads (None is a valid variable value)
_MISSING = object()


def _empty_stack_messages() -> frozenset[str]:
    """Returns what the stack type says when popped or indexed while empty."""
    messages = set()
    for touch in (lambda stack: stack.pop(), lambda stack: stack[-1]):
        try:
            touch(stack_data())
        except IndexError as error:
            messages.add(str(error))
    return frozenset(messages)


_EMPTY_STACK_MESSAGES = _empty_stack_messages()


def _name_in(value: object) -> str | None:
    """Returns the name ``value`` stands for, or None if it is not a name.

    A ``Symbol`` stands for its name; a one-token block ``{name}`` or
    ``{:name}`` (a quoted name) for the name inside. Shared by the words
    that take a name (``_name_of``) and by macro templates (``_interpolate``),
    so what counts as a name is decided in one place.
    """
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, StackerCore) and len(value.tokens) == 1:
        token = value.tokens[0]
        if is_symbol(token):
            return token[1:]  # type: ignore[index]
        if is_bare_name(token):
            return token  # type: ignore[return-value]
    return None


def _symbol_in(args: object) -> str | None:
    """Returns the name of the first ``Symbol`` among ``args``.

    Looks one container level deep (a symbol inside a list argument), which
    covers the host functions' own error messages; deeper nesting is left
    to Python's ``TypeError``.
    """
    for arg in args:  # type: ignore[attr-defined]
        if isinstance(arg, Symbol):
            return arg.name
        if isinstance(arg, (list, tuple)):
            for item in arg:
                if isinstance(item, Symbol):
                    return item.name
    return None


def _reraise_type_error(word: str, args: object, error: Exception) -> NoReturn:
    """Re-raises ``error``, as a ``StackerTypeError`` when a symbol caused it.

    Called from an ``except (TypeError, AttributeError)`` block in the
    operator executors, so the happy path carries no type checks. The error
    is attributed to a symbol only when one is among ``args`` and the
    message names the ``Symbol`` type (Python's own type and attribute
    errors do: ``'Symbol' object has no attribute 'upper'``); an error
    raised for another reason, such as ``"a" 1 +`` inside a ``map`` body,
    is re-raised unchanged.

    Args:
        word: The operator being executed.
        args: Its arguments (the values handed to the host function).
        error: The ``TypeError`` or ``AttributeError`` the host function raised.
    """
    name = None
    if not isinstance(error, StackerTypeError) and "Symbol" in str(error):
        name = _symbol_in(args)
    if name is None:
        raise error
    raise StackerTypeError(
        f"`{word}` cannot use the symbol `{name}` as a value. "
        f"Write `{name}` for the variable's value, or `:{name} str` for its name as text."
    ) from error


# Token classification kinds. Every decision below is a pure function of
# the token values (never of interpreter state), so a classification can be
# computed once per token list and reused across evaluations.
K_VALUE = 0  # non-str token: push as-is
K_STRING = 1  # quoted string literal: payload is the prebuilt String
K_LIST = 2  # list literal: payload is the parsed template (or None)
K_SYMBOL = 3  # :name: payload is the Symbol
K_BLOCK = 4  # code-block source: substack is created at evaluation time
K_BLOCK_VALUE = 5  # prebuilt code block (nested in a block): bound to the current scope when pushed
K_DYNAMIC = 6  # name resolved against runtime state on every evaluation
# 7 was a bare name a lookahead read as the name being bound; gone
K_INVALID = 8  # a `:` or `$` token that is not a symbol: payload is the error message, raised when executed


def _classify_token(token: object) -> tuple[int, object, object]:
    """Classifies one token; the result depends on this token alone.

    Mirrors the branch order of ``StackerCore._evaluate`` exactly, minus the
    macro check (macros are runtime state, so that check stays in the
    evaluation loop). A ``String`` object is always a string literal
    (``K_STRING``): blocks store their literals that way, and a literal must
    never be looked up as a name, whatever text it holds. Quote checks on raw
    source tokens go through ``is_string_token``. A bare name is ``K_DYNAMIC``
    wherever it stands: it is read as a reference, never as the name being
    bound, so the tokens around it are not consulted.

    Args:
        token: One token as produced by the parser / block formatter.

    Returns:
        A ``(kind, token, payload)`` entry.
    """
    if isinstance(token, StackerCore):
        return (K_BLOCK_VALUE, token, None)
    if not isinstance(token, str):
        return (K_VALUE, token, None)
    if isinstance(token, String):
        return (K_STRING, token, token)
    if is_string_token(token):
        return (K_STRING, token, String(strip_string_delimiters(token)))
    if is_list(token):
        try:
            template = _compile_list_template(token)
        except Exception:
            # Malformed list token: leave the payload empty so the
            # evaluation loop re-parses (and raises) at the token's
            # execution position, exactly as before.
            template = None
        return (K_LIST, token, template)
    if token.startswith((SYMBOL_PREFIX, OLD_SYMBOL_PREFIX)):
        if is_symbol(token):
            return (K_SYMBOL, token, Symbol(token[1:]))
        return (K_INVALID, token, not_a_symbol_message(token))
    if is_code_block(token):
        return (K_BLOCK, token, None)
    if token in KEYWORD_LITERALS:
        return (K_VALUE, KEYWORD_LITERALS[token], None)  # true / false / null are values
    return (K_DYNAMIC, token, None)


def _classify_tokens(tokens: list[object]) -> list[tuple[int, object, object]]:
    """Classifies every token of ``tokens``, each on its own.

    Every entry is a pure function of its token (see ``_classify_token``),
    so a classification can be computed once per token list and reused
    across evaluations, and ``_classify_tokens(T)[i]`` is always
    ``_classify_token(T[i])``.
    """
    return [_classify_token(token) for token in tokens]


def _compile_list_template(token: str) -> list[object]:
    """Compiles a list-literal token into a template (done once per token).

    String literals become ``String``, ``:name`` becomes a ``Symbol``,
    ``true`` / ``false`` / ``null`` become values, numbers stay numbers and
    nested lists are compiled recursively. A bare name stays a plain
    ``str``: it is looked up every time the literal is evaluated
    (``_build_list``). A code block is not allowed inside a list literal.

    Args:
        token: The ``[...]`` source token.

    Returns:
        The template, a nested list of values and plain-str names.

    Raises:
        StackerSyntaxError: A code block is written inside the literal.
    """
    parsed = ast.literal_eval(convert_custom_array_to_proper_list(token))
    return _compile_list_elements(parsed if isinstance(parsed, list) else [parsed])


def _compile_list_elements(elements: list[object]) -> list[object]:
    compiled: list[object] = []
    for element in elements:
        if isinstance(element, (list, tuple)):
            compiled.append(_compile_list_elements(list(element)))
        elif type(element) is str:
            if is_string_token(element):
                compiled.append(String(strip_string_delimiters(element)))
            elif element.startswith(SYMBOL_PREFIX):
                compiled.append(Symbol(element[1:]))  # checked by the array lexer
            elif element in KEYWORD_LITERALS:
                compiled.append(KEYWORD_LITERALS[element])
            elif is_code_block(element):
                raise StackerSyntaxError(
                    "a code block cannot be written inside a list literal; "
                    "use {x} 1 listn, or [:x] for a symbol"
                )
            else:
                compiled.append(element)  # a name, referenced on evaluation
        else:
            compiled.append(element)
    return compiled


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

    def __init__(
        self, expression: str | None = None, parent: StackerCore | None = None
    ) -> None:
        self.parent = parent
        self.child: StackerCore | None = None
        self.trace: list[object] = []  # for error trace
        self.stack: stack_data[object] = stack_data()
        self.tokens: list[object] = TokenList()
        # The latest (scope, copy) made by _bound_to, reused for that scope.
        # It keeps that scope alive until the block is pushed from another one
        self._bound_cache: tuple[ScopedVariables, StackerCore] | None = None
        self.bracket_type: str = "{"  # Default bracket type for display ({} or ())

        # Source location tracking for error reporting
        self.current_file: str | None = None
        self.current_line: int | None = None
        self.source_lines: dict[int, str] = {}  # Map line number to source code
        # Top of the stack after the latest top-level expression that left
        # one, for `ans`. Only the root core (the one the entry points run
        # on) records it. A flag rather than a sentinel: copy() deep-copies
        # the core, and a copied sentinel is no longer `is` the original.
        self.has_result = False
        self.last_result: object = None

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
        operator names and ``:x``, stays a raw token for lazy resolution.

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
        stack.append(self._block_of(tokens))

    def _block_of(self, tokens: list[object]) -> StackerCore:
        """Builds a code block holding ``tokens`` (a freshly built list)."""
        self.child = type(self)(parent=self)
        # Callers always pass freshly built lists, so wrapping copies no
        # shared state; the TokenList carries the classification cache.
        self.child.tokens = TokenList(tokens)
        return self.child

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
        never looked up here, so ``:x`` stays the symbol ``x`` whether or
        not a variable ``x`` exists.

        Args:
            stack: Stack to pop from.

        Returns:
            The argument value.
        """
        value = stack.pop()

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
        return stack.pop()

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

        for kind, token, payload in entries:
            if kind == K_VALUE:
                stack.append(token)  # Literal value
                continue
            if kind == K_BLOCK_VALUE:
                if interp is not None:
                    stack.append(self._interpolate(token, interp))
                else:
                    # The block object is shared by every evaluation of this
                    # token list; what is pushed is the block bound to the
                    # scope it is pushed from, so a lambda or a `map` body
                    # made here keeps this scope (closure)
                    stack.append(token._bound_to(self.variables))
                continue
            if kind == K_STRING:
                stack.append(payload)  # a string literal is never a name
                continue
            # Macros take precedence over variables and operators.
            if token in macros:
                self._expand_macro(token, stack)
            elif kind == K_DYNAMIC:
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
                    # A literal (classified as a name only when the literal
                    # check was skipped or deferred) pushes its value; any
                    # other name is undefined, and that is an error here.
                    evaluated = cached_literal_eval(token)
                    if isinstance(evaluated, str):
                        raise UndefinedSymbolError(token)
                    stack.append(evaluated)
            elif kind == K_LIST:
                if payload is None:
                    # Malformed literal: compile it again here so the error
                    # is raised at the token's execution position.
                    payload = _compile_list_template(token)
                stack.append(self._build_list(payload))
            elif kind == K_SYMBOL:
                stack.append(payload)  # the Symbol
            elif kind == K_BLOCK:
                self._substack(token, stack)
            elif kind == K_INVALID:
                raise StackerSyntaxError(payload)
        return stack

    def _build_list(self, template: list[object]) -> list[object]:
        """Builds a fresh list from a compiled list-literal template.

        Names are looked up now (the value of the variable, or
        ``UndefinedSymbolError``); nested lists are built fresh so no
        state is shared between evaluations.
        """
        return [
            self._lookup_name(element)
            if type(element) is str
            else (self._build_list(element) if isinstance(element, list) else element)
            for element in template
        ]

    def _execute(self, token: str, stack: stack_data[object]) -> None:
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        try:
            self._execute_impl(token, stack)
        except IndexError as e:
            # Only a pop or peek past the bottom of a stack means the operator
            # ran out of arguments. A list, string or format index out of
            # range is the operator's own error and stays as is.
            if str(e) not in _EMPTY_STACK_MESSAGES:
                raise
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
            try:
                if op["push_result_to_stack"]:  # type: ignore[index]
                    result = op["func"](*args)  # type: ignore[index]
                    if result is not VOID:
                        stack.append(result)
                else:
                    op["func"](*args)  # type: ignore[index]
            except (TypeError, AttributeError) as error:
                _reraise_type_error(token, args, error)
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
        try:
            op["func"](start_value, end_value, name, body, self, stack)
        except (TypeError, AttributeError) as error:
            _reraise_type_error("do", [start_value, end_value], error)

    def _prio_dolist(self, op, stack) -> None:
        body = stack.pop()
        symbol = stack.pop()
        lst = self._pop_and_eval(stack)
        name = self._name_of(symbol, "dolist")
        try:
            op["func"](name, lst, body, self, stack)
        except (TypeError, AttributeError) as error:
            _reraise_type_error("dolist", [lst], error)

    def _prio_times(self, op, stack) -> None:
        n_times = self._pop_and_eval(stack)
        body = stack.pop()
        try:
            op["func"](n_times, body, self, stack)
        except (TypeError, AttributeError) as error:
            _reraise_type_error("times", [n_times], error)

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
        try:
            count = range(n)  # type: ignore[arg-type]
        except (TypeError, AttributeError) as error:
            _reraise_type_error("cond", [n], error)
        for _ in count:
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
        """``{args} {body} :name defun`` -- the argument list is validated like ``defmacro``'s."""
        symbol = stack.pop()
        name = self._name_of(symbol, "defun")
        if name in self._prelude["names"]:
            self._warn_prelude_redefinition(name)
        body = stack.pop()
        fargs = self._parse_arg_names(stack.pop(), "defun")
        op["func"](self, name, fargs, body)

    def _prio_defmacro(self, op, stack) -> None:
        """``{args} {body} :name defmacro`` -- validates the three parts at definition time."""
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

    def _prio_ans(self, op, stack) -> None:
        root = self
        while root.parent is not None:
            root = root.parent
        if not root.has_result:
            raise StackerRuntimeError("`ans` has no result yet: no expression has left a value")
        stack.append(root.last_result)

    def _prio_symbol(self, op, stack) -> None:
        """``x symbol`` -- a symbol from a string, a quoted name or a symbol (identity)."""
        value = stack.pop()
        if isinstance(value, Symbol):
            stack.append(value)
        elif isinstance(value, str):
            name = str(value)
            if not is_symbol_name(name):
                raise StackerSyntaxError(
                    f"`symbol` expects a string that reads as a name, got {name!r}"
                )
            stack.append(Symbol(name))
        elif isinstance(value, StackerCore) and len(value.tokens) == 1 and is_symbol(value.tokens[0]):
            stack.append(Symbol(value.tokens[0][1:]))  # type: ignore[index]
        elif isinstance(value, StackerCore) and len(value.tokens) == 1 and is_bare_name(value.tokens[0]):
            stack.append(Symbol(value.tokens[0]))  # type: ignore[arg-type]
        else:
            raise StackerSyntaxError(f"`symbol` expects a string or a quoted name, got {value}")

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
        """Evaluates the top value: code, never text.

        - a code block is evaluated on this stack
        - a ``Symbol`` is evaluated as its name, exactly as if the bare name
          had been written here (macro, variable, function or operator)
        - a lambda is called with arguments taken from this stack
        - a string is data, not code: ``StackerTypeError`` (parse text with
          ``parse`` first)
        - anything else is pushed back
        """
        expression = stack.pop()
        if isinstance(expression, Symbol):
            self._evaluate([expression.name], stack=stack)
        elif isinstance(expression, str):
            raise StackerTypeError(
                f"`eval` expects a code block, a symbol or a lambda, got the string {str(expression)!r}. "
                "A string is text, not code: turn it into a block with `parse` first, "
                'e.g. "3 4 +" parse eval'
            )
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
        self._substack_with_tokens([value_to_token(stack.pop())], stack)

    def _prio_subn(self, op, stack) -> None:
        n = stack.pop()
        try:
            count = range(n)  # type: ignore[arg-type]
        except (TypeError, AttributeError) as error:
            _reraise_type_error("subn", [n], error)
        elms = [value_to_token(stack.pop()) for _ in count]
        elms.reverse()
        self._substack_with_tokens(elms, stack)

    def _prio_listn(self, op, stack) -> None:
        n = stack.pop()
        try:
            count = range(n)  # type: ignore[arg-type]
        except (TypeError, AttributeError) as error:
            _reraise_type_error("listn", [n], error)
        elms = [stack.pop() for _ in count]
        elms.reverse()
        stack.append(elms)

    def _prio_parse(self, op, stack) -> None:
        self._substack_with_expression(stack.pop(), stack)  # type: ignore[arg-type]

    def _prio_read(self, op, stack) -> None:
        self._substack_with_expression(input(), stack)

    def _prio_split(self, op, stack) -> None:
        sep = stack.pop()
        word = stack.pop()
        try:
            parts = word.split(sep)  # type: ignore[union-attr]
        except (TypeError, AttributeError) as error:
            _reraise_type_error("split", [word, sep], error)
        stack.extend(parts)

    def _prio_nth(self, op, stack) -> None:
        n = stack.pop()
        lst = stack[-1]
        try:
            if isinstance(lst, String):
                stack.append(String(lst[n]))  # type: ignore[index]
            elif isinstance(lst, StackerCore):
                stack.append(token_to_value(lst.tokens[n]))  # type: ignore[index]
            else:
                stack.append(lst[n])  # type: ignore[index]
        except (TypeError, AttributeError) as error:
            _reraise_type_error("nth", [lst, n], error)

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
                stack.append(token_to_value(tok))
        else:
            stack.append(args_list)
        if isinstance(func, StackerCore):
            self._eval_block(func, stack=stack)
        elif isinstance(func, StackerLambda):
            self._call_lambda(func, stack)
        elif isinstance(func, Symbol):
            self._evaluate([func.name], stack=stack)
        else:
            raise StackerTypeError(self._function_spec_message("apply", func))

    def _prio_include(self, op, stack) -> None:
        filename = stack.pop()
        if not isinstance(filename, str):
            raise StackerTypeError(
                f'`include` expects the file path as a string, e.g. "lib.stk" include; got {filename}'
            )
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
        "ans": _prio_ans,
        "symbol": _prio_symbol,
        "concat-block": _prio_concat_block,
        "lambda": _prio_lambda,
        "eval": _prio_eval,
        "sub": _prio_sub,
        "subn": _prio_subn,
        "listn": _prio_listn,
        "parse": _prio_parse,
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
        try:
            if op["push_result_to_stack"]:
                result = op["func"](*op_args)  # type: ignore[operator]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*op_args)  # type: ignore[operator]
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, op_args, error)

    def _exec_system(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a system-category operator; receives the stack and interpreter as trailing arguments."""
        sys_args: list[object] = [stack, self]
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            sys_args.insert(0, self._pop_and_eval(stack))
        try:
            if op["push_result_to_stack"]:
                result = op["func"](*sys_args)  # type: ignore[operator]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*sys_args)  # type: ignore[operator]
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, sys_args, error)

    def _exec_regular(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a regular operator: pop arg_count evaluated arguments, push non-VOID results."""
        reg_args: list[object] = []
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            reg_args.insert(0, self._pop_and_eval(stack))
        try:
            if op["push_result_to_stack"]:
                result = op["func"](*reg_args)  # type: ignore[operator]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*reg_args)  # type: ignore[operator]
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, reg_args, error)
    def _exec_hof(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a higher-order operator (map/filter, reduce/fold, zip) with per-name argument shapes."""
        if token in ["map", "filter"]:
            body = stack.pop()
            hof_args = stack.pop()
            func = self._resolve_function_spec(body, token)
            items = self._data_items(hof_args)
            try:
                self._push_like(hof_args, op["func"](func, items), stack)  # type: ignore[operator]
            except (TypeError, AttributeError) as error:
                _reraise_type_error(token, [items], error)
        elif token in ["reduce", "fold"]:
            body = stack.pop()
            symbol_x = stack.pop()  # Second variable name (element)
            symbol_acc = stack.pop()  # First variable name (accumulator)
            init = stack.pop()
            fold_args = stack.pop()
            if isinstance(body, Symbol):
                body = self._block_of([body.name])
            if not isinstance(body, StackerCore):
                raise StackerTypeError(
                    f"`{token}` expects a code block as the function, got {body!r}"
                )

            # Extract variable names (same as dolist pattern)
            name_acc = self._name_of(symbol_acc, token)
            name_x = self._name_of(symbol_x, token)

            # Create binary function with variable binding
            def reduce_func(acc: object, x: object) -> object:
                # Create child scope for this reduction step
                original_parent_vars = self.variables
                original_parent_stack = self.stack
                result_stack: stack_data[object] = stack_data()
                try:
                    # A loop scope: it holds the two names, and a name the
                    # body is first to set goes to the caller's scope
                    self.variables = ScopedVariables.loop_scope(self.variables)
                    self.variables.bind(name_acc, acc)
                    self.variables.bind(name_x, x)
                    # Evaluate the body using a temporary stack
                    self.stack = result_stack
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

            items = self._data_items(fold_args)
            try:
                stack.append(op["func"](reduce_func, init, items))  # type: ignore[operator]
            except (TypeError, AttributeError) as error:
                _reraise_type_error(token, [init, items], error)
        elif token in ["zip"]:
            xs2 = stack.pop()
            xs1 = stack.pop()
            items1, items2 = self._data_items(xs1), self._data_items(xs2)
            try:
                self._push_like(xs1, op["func"](items1, items2), stack)  # type: ignore[operator]
            except (TypeError, AttributeError) as error:
                _reraise_type_error(token, [items1, items2], error)

    def _data_items(self, value: object) -> object:
        """Returns the items a data word iterates over.

        A code block is read as data: each name token becomes a ``Symbol``
        (see ``engine/boundary.py``); lists and other iterables are used as
        they are.
        """
        if isinstance(value, StackerCore):
            return [token_to_value(token) for token in value.tokens]
        return value

    def _push_like(self, source: object, result: object, stack: stack_data[object]) -> None:
        """Pushes ``result`` in the container type of ``source``.

        A block in gives a block out (values are converted back to tokens),
        a tuple gives a tuple, anything else a list.
        """
        if isinstance(source, StackerCore):
            self._substack_with_tokens([value_to_token(v) for v in result], stack)  # type: ignore[union-attr]
        elif isinstance(source, tuple):
            stack.append(tuple(result))  # type: ignore[arg-type]
        else:
            stack.append(list(result))  # type: ignore[arg-type]
    def _exec_transform(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a transform operator, preserving the input's container type on push."""
        tf_args = stack.pop()
        items = self._data_items(tf_args)
        try:
            lst = op["func"](items)  # type: ignore[operator]
            if token == "list":
                stack.append(list(lst))
            else:
                self._push_like(tf_args, lst, stack)
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, [items], error)

    def _exec_aggregate(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute an aggregate operator over a block (names are referenced) or a list."""
        agg_args = stack.pop()
        if isinstance(agg_args, StackerCore):
            if token == "len":
                # `len` counts tokens so `dup len` works on any block
                stack.append(len(agg_args.tokens))
                return
            agg_args = [self._block_token_value(t) for t in agg_args.tokens]
        try:
            if op["push_result_to_stack"]:
                result = op["func"](agg_args)  # type: ignore[operator]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](agg_args)  # type: ignore[operator]
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, [agg_args], error)

    def _exec_file(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a file operator: pop arg_count evaluated arguments, push non-VOID results."""
        file_args: list[object] = []
        for _ in range(op["arg_count"]):  # type: ignore[arg-type]
            file_args.insert(0, self._pop_and_eval(stack))
        try:
            if op["push_result_to_stack"]:
                result = op["func"](*file_args)  # type: ignore[operator]
                if result is not VOID:
                    stack.append(result)
            else:
                op["func"](*file_args)  # type: ignore[operator]
        except (TypeError, AttributeError) as error:
            _reraise_type_error(token, file_args, error)

    def _exec_settings(
        self, token: str, op: dict[str, object], stack: stack_data[object]
    ) -> None:
        """Execute a settings operator; disable_plugin additionally pops the target name."""
        if token == "disable_plugin":
            operator_name = stack.pop()
            if not isinstance(operator_name, str):
                raise StackerTypeError(
                    '`disable_plugin` expects the plugin name as a string, '
                    f'e.g. "name" disable_plugin; got {operator_name}'
                )
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

        - a ``Symbol`` (``:name``, ``gensym``, ``symbol``) -> its name
        - ``{name}`` / ``{:name}`` (quoted name: a one-token block) -> ``name``
        - a string is data, never a name -> ``StackerSyntaxError`` (the
          message shows ``:name``, ``{name}`` and ``symbol``)
        - anything else (a multi-token block, a number, ...) -> ``StackerSyntaxError``

        Args:
            symbol: Value popped from the stack where a name is expected.
            word: The word reading the name (for the error message).

        Returns:
            The bare name, the key used in the variable scopes.

        Raises:
            StackerSyntaxError: If ``symbol`` cannot denote a name.
        """
        name = _name_in(symbol)
        if name is not None:
            return name
        # A one-token block that is not a name: pull a string literal out of
        # it (`{"x"}`) so the message below says it is a string, not a block.
        if isinstance(symbol, StackerCore) and len(symbol.tokens) == 1:
            token = symbol.tokens[0]
            if isinstance(token, String):
                symbol = token
        if isinstance(symbol, str):
            raise StackerSyntaxError(
                f"`{word}` expects a name, got the string {str(symbol)!r}. "
                f"Write :{symbol} or {{{symbol}}}, or convert a string with `symbol`."
            )
        raise StackerSyntaxError(
            f"`{word}` expects a name, got {symbol}. A bare name pushes what it "
            "refers to; write the name itself as `:name` or `{name}`."
        )

    def _parse_arg_names(self, fargs: object, word: str) -> list[str]:
        """Validates an argument list ``{a b ...}`` and returns the names.

        Shared by ``defun``, ``lambda`` and ``defmacro``: the list must be a
        code block whose tokens are distinct bare names (no ``:a``, string,
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
            if not is_bare_name(token):
                raise StackerSyntaxError(f"`{word}` argument names must be bare names, got {token}")
            names.append(token)
        if len(set(names)) != len(names):
            raise StackerSyntaxError(f"`{word}` argument names must be unique: {{{' '.join(names)}}}")
        return names

    @staticmethod
    def _function_spec_message(word: str, spec: object) -> str:
        return f"`{word}` expects a code block, a lambda or a symbol as the function, got {spec!r}"

    def _resolve_function_spec(self, spec: object, word: str) -> Callable[[object], object]:
        """Turns the function argument of ``map`` / ``filter`` into a callable.

        A code block is run once per element with the element on its stack.
        A lambda is called as it is. A symbol means the same as the quoted
        name ``{name}``: the name is resolved like a bare name (macro,
        variable, function, operator). As a shortcut, a symbol naming a
        one-argument host word that is not shadowed by a macro or a
        variable is called directly; the result is the same.

        Args:
            spec: The function argument as popped from the stack.
            word: The calling word (for the error message).

        Returns:
            A one-argument callable.

        Raises:
            StackerTypeError: ``spec`` is none of the above (a string, a number, ...).
        """
        if isinstance(spec, StackerCore):
            # The block runs as it is, in the scope it is bound to (the
            # caller's): what it assigns stays assigned, and nothing is copied
            return lambda element: self._stacker_lambda(element, spec, word)
        if isinstance(spec, StackerLambda):
            return spec
        if isinstance(spec, Symbol):
            name = spec.name
            if name not in self.macros and self.variables.get(name, _MISSING) is _MISSING:
                sfunc = self.sfunctions.get(name)
                if sfunc is not None and sfunc["arg_count"] == 1 and sfunc["push_result_to_stack"]:  # type: ignore[index]
                    return sfunc["func"]  # type: ignore[index, return-value]
                host = self.plugins.get(name)
                if host is None:
                    entry = self.operator_manager.dispatch_table.get(name)
                    if entry is not None and entry[0] == "regular":
                        host = entry[1]
                if host is not None and host["arg_count"] == 1 and host["push_result_to_stack"]:  # type: ignore[index]
                    func = host["func"]  # type: ignore[index]

                    def call(element: object) -> object:
                        # The element is prepared as `_execute` would (a block
                        # is evaluated, a String literal is unwrapped), and a
                        # type error names the word, as `_execute` would.
                        try:
                            return func(self._pop_and_eval(stack_data([element])))
                        except (TypeError, AttributeError) as error:
                            _reraise_type_error(name, [element], error)

                    return call
            block = self._block_of([name])
            return lambda element: self._stacker_lambda(element, block, word)
        raise StackerTypeError(self._function_spec_message(word, spec))

    def _lookup_name(self, name: str) -> object:
        """Returns the value bound to ``name``, or raises ``UndefinedSymbolError``."""
        value = self.variables.get(name, _MISSING)
        if value is _MISSING:
            raise UndefinedSymbolError(name)
        return value

    def _block_token_value(self, token: object) -> object:
        """Reads a block token the way an aggregate does: names are referenced.

        A bare name token is the value of that variable, ``:name`` is the
        symbol, and literal tokens are themselves.
        """
        if type(token) is str:
            if is_symbol(token):
                return Symbol(token[1:])
            if is_list(token):
                return self._build_list(_compile_list_template(token))
            return self._lookup_name(token)
        return token

    def _interpolate(self, block: StackerCore, scope: ScopedVariables) -> StackerCore:
        """Copies ``block`` with the expansion scope's own bindings spliced in.

        Only the template tree is walked: values spliced in are never
        re-scanned, so caller-supplied code is left exactly as written.
        Bare-name tokens bound in ``scope`` are replaced by their values and
        ``:name`` tokens by the symbol of the name the binding holds, so a
        template can bind the name an argument or ``gensym`` stands for
        (``{ x eval :t set t t + }``). String and list literals and unbound
        names are untouched.

        Args:
            block: Block literal from the macro body.
            scope: Expansion scope; only its own bindings are consulted.

        Returns:
            A fresh block whose scope is the caller's.

        Raises:
            StackerSyntaxError: A ``:name`` whose binding is not a name.
        """
        bindings = scope.own_bindings()

        def substitute(token: object) -> object:
            if isinstance(token, StackerCore):
                return build(token)
            if type(token) is not str:
                return token  # literals stay as written
            if token.startswith(SYMBOL_PREFIX):
                name = token[1:]
                if name not in bindings:
                    return token  # an unbound `:name` (or a stray `:`) stays as written
                return SYMBOL_PREFIX + self._template_name(name, bindings[name])
            if token not in bindings:
                return token
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

    @staticmethod
    def _template_name(name: str, value: object) -> str:
        """Returns the name ``value`` stands for, for a ``:name`` in a template.

        Raises:
            StackerSyntaxError: If ``value`` is not a name that can be written
                back as ``:name`` (a number, a string, a longer block, ...).
        """
        held = _name_in(value)
        if held is not None and is_symbol_name(held):
            return held
        if held is not None:  # a Symbol built from Python with text no `:name` can spell
            shown = f"the invalid name {held!r}"
        elif isinstance(value, str):  # a String literal or a plain str value
            shown = f"the string {str(value)!r}"
        else:
            shown = str(value)
        raise StackerSyntaxError(
            f"`:{name}` in a macro template needs a name, but `{name}` holds {shown}"
        )

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
                    args.insert(0, self._pop_and_resolve(stack))  # blocks stay raw, symbols stay symbols
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
        """Runs ``body`` once with ``arg`` as the only value on its stack.

        The element is pushed as a value, never spliced into the token
        list, so a string element stays a string and a symbol a symbol.
        """
        lstack: stack_data[object] = stack_data([arg])
        body._evaluate(body.tokens, stack=lstack)
        if len(lstack) == 1:
            return lstack[0]
        elif len(lstack) == 0:
            raise NoValueProducedError(operator)
        return list(lstack)

    def copy(self) -> StackerCore:
        return copy.deepcopy(self)

    def _bound_to(self, scope: ScopedVariables) -> StackerCore:
        """Returns this block bound to ``scope``: itself when already bound there.

        The copy shares the tokens (and their classification cache) and gets
        a stack of its own, so evaluating it never touches the original.

        Args:
            scope: The scope the block is being pushed from.

        Returns:
            A block whose names resolve in ``scope``.
        """
        if self.variables is scope:
            return self
        # A loop pushes the same block once per iteration in one scope: the
        # bound copy is kept for as long as the scope asking for it is the
        # same one, so the copy is made once per scope, not once per push
        cached = self._bound_cache
        if cached is not None and cached[0] is scope:
            return cached[1]
        bound = object.__new__(type(self))  # a shallow copy, without copy.copy's overhead
        bound.__dict__.update(self.__dict__)
        bound.variables = scope
        bound.stack = stack_data()
        bound._bound_cache = None
        self._bound_cache = (scope, bound)
        return bound

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
            elif isinstance(item, str):
                # A raw token is a name, an operator or `:name`: shown as written,
                # whether or not the name is bound right now.
                return item
            # A value spliced in by sub / subn / a block-returning word: shown
            # as the stack display shows it (`[1 2]`, `true`), not as Python does
            return plain_text(item)

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
