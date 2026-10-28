from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from stacker.engine.core import StackerCore
from stacker.engine.scope import ScopedVariables
from stacker.error import (
    BreakException,
    StackerSyntaxError,
    attach_include_location,
    copy_include_location,
)
from stacker.slib import load_prelude
from stacker.syntax.parser import parse_expression

if TYPE_CHECKING:
    from stacker.engine.sfunction import StackerFunction

from stacker.engine.data_type import stack_data


def _break_outside_a_loop(error: BreakException) -> StackerSyntaxError:
    """The error for a `break` that reached an entry point with no loop around it.

    A `break` raised inside an included file keeps the file's position.
    """
    replacement = StackerSyntaxError("`break` can only be used inside a loop")
    copy_include_location(error, replacement)
    return replacement


class Stacker(StackerCore):
    def __init__(
        self,
        expression: str | None = None,
        parent: StackerCore | None = None,
        prelude: bool = True,
    ) -> None:
        """Creates an interpreter.

        Args:
            expression: Source of a code block (child cores only).
            parent: Enclosing core when this is a code block's substack.
            prelude: Whether a root interpreter loads the prelude (the
                Stacker-written standard words). Ignored for child cores.
        """
        super().__init__(expression, parent)
        self.trace: list[object] = []
        self.plugin_descriptions: dict[str, str | None] = {}
        if parent is None:
            self._prelude["enabled"] = prelude
            if prelude:
                load_prelude(self)

    def include(self, filename: str) -> None:
        """Runs a script here, in the root scope, as the `include` word does.

        Args:
            filename: Path of the script.

        Raises:
            StackerSyntaxError: The file has a `break` outside a loop.
        """
        self._include(filename, once=False)

    def require(self, filename: str) -> None:
        """Runs a script once per interpreter, as the `require` word does.

        Args:
            filename: Path of the script.

        Raises:
            StackerSyntaxError: The file has a `break` outside a loop.
        """
        self._include(filename, once=True)

    def _include(self, filename: str, once: bool) -> None:
        from stacker.include.include import include_file

        try:
            include_file(self, filename, once=once)
        except BreakException as error:
            raise _break_outside_a_loop(error) from None

    def run_file(
        self,
        path: str | Path,
        *,
        main: bool = True,
        restore_location: bool = False,
        intercept: Callable[[str], bool] | None = None,
    ) -> None:
        """Runs a script file expression by expression on the root stack.

        Each expression is evaluated as a line typed at the prompt is: what
        it leaves stays on the stack, and `ans` sees it. While the file
        runs it is the current file (`script-path`, relative includes, and
        where a function it defines says it was defined), its lines are
        kept for error reports, and it is the outermost frame of the
        include stack, so a file that includes it is caught as circular.

        Args:
            path: The file to run, as written (quotes around it are not
                removed).
            main: Whether the file is the main script: the one
                `main-script-path` names and `main?` is true in.
            restore_location: Whether to put the current file, line and
                source lines back as they were once the file ends, as
                ``~/.stackerrc`` does so that what runs after it does not
                see it as its file. An error raised while the file runs
                then carries the file's position, since the report cannot
                read it back afterwards.
            intercept: A predicate given each expression's text before it
                is evaluated; an expression it returns True for is skipped.
                The REPL passes the commands it handles itself.

        Raises:
            ScriptReadError: The file cannot be read as text. Nothing has
                run and the current file is unchanged; with ``main`` the
                file is already `main-script-path`.
            OSError: The file cannot be opened (for example it does not
                exist); the same holds.
            UnterminatedTokenError: The file ends inside an open construct;
                ``current_line`` names the line it started on. The
                expressions before it have run.
            StackerSyntaxError: The file has a `break` outside a loop.
        """
        # Imported here, not at the top: the include module needs this class
        from stacker.include.include import (
            expressions_of,
            pop_entry_file,
            push_entry_file,
        )
        from stacker.include.stk_file_read import readtxt

        path = Path(path)
        if main:
            self.main_script = str(path.resolve())
        code = readtxt(path)
        before = (self.current_file, self.current_line, dict(self.source_lines)) if restore_location else None
        # Set before anything runs: a block or function the file defines
        # takes the current file as its own when it is made
        self.current_file = str(path.resolve())
        for line_number, text in enumerate(code.splitlines(), start=1):
            self.source_lines[line_number] = text

        def set_line(line: int | None) -> None:
            self.current_line = line

        push_entry_file(self, path)
        try:
            for expression in expressions_of(code, set_line):
                if intercept is not None and intercept(expression):
                    continue
                self.process_expression(expression)
        except Exception as error:
            if restore_location:
                # The position is put back below, and the report needs it;
                # an error inside a file this one includes keeps its own
                # (the first position attached wins). This is the outermost
                # file, so there are no including frames
                attach_include_location(
                    error,
                    self.current_file or str(path.resolve()),
                    self.current_line,
                    self.source_lines.get(self.current_line or 0),
                    [],
                )
            raise
        finally:
            pop_entry_file(self)
            if before is not None:
                self.current_file, self.current_line, source_lines = before
                self.source_lines.clear()
                self.source_lines.update(source_lines)

    def push(self, value: object) -> None:  # TODO: remove
        self.stack.append(value)

    def pop_and_eval(self, stack: stack_data[object]) -> object:
        return self._pop_and_eval(stack)

    def pop(self) -> object:
        return self.stack.pop()

    def process_expression(self, expression: str) -> None:
        tokens = parse_expression(expression)
        self._evaluate_outside_loops(tokens, self.stack)

    def _evaluate_outside_loops(
        self, tokens: list[object], stack: stack_data[object] | None
    ) -> stack_data[object]:
        """Evaluates code that no loop is running, as the entry points do.

        A ``break`` leaves the innermost running loop, wherever it is called
        from; one that reaches this level had no loop to leave. The top of
        the stack afterwards is the result ``ans`` pushes next time.

        Raises:
            StackerSyntaxError: If ``break`` is used outside a loop.
        """
        try:
            result = self.evaluate(tokens, stack=stack)
        except BreakException as error:
            raise _break_outside_a_loop(error) from None
        if result:
            self.last_result = result[-1]
            self.has_result = True
        return result

    def evaluate(self, tokens: list[object], stack: stack_data[object] | None = None) -> stack_data[object]:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.

        Not an entry point: a ``break`` with no loop around it escapes as
        ``BreakException``. Run top-level code with ``eval`` or
        ``process_expression``.
        """
        if stack is None:
            stack = stack_data()
        try:
            return self._evaluate(tokens, stack=stack)
        except Exception as e:
            if self.parent is not None:
                self.parent.trace = self.trace
            raise e

    def register_operator(
        self,
        operator_name: str,
        operator_func: Callable[..., object],
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
        defined_at: tuple[str | None, int | None] | None = None,
    ) -> None:
        """Registers a word that runs ``sfunction_func``.

        Args:
            sfunction_name: The word.
            sfunction_func: What it runs.
            arg_count: How many values it takes from the stack.
            push_result_to_stack: Whether what it returns is pushed.
            desc: Its line in the word listings.
            defined_at: The file and line that defined it (None for a word
                defined from the host, or in the REPL), shown when another
                file redefines it.
        """
        self.sfunctions[sfunction_name] = {
            "func": sfunction_func,
            "arg_count": arg_count,
            "push_result_to_stack": push_result_to_stack,
            "desc": desc,
            "defined_at": defined_at,
        }

    def register_macro(self, macro_name: str, macro_body: object) -> None:
        self.macros[macro_name] = macro_body

    def register_parameter(self, parameter_name: str, parameter_value: object) -> None:
        self.variables[parameter_name] = parameter_value

    def register_plugin(
        self,
        operator_name: str,
        operator_func: Callable[..., object],
        push_result_to_stack: bool = True,
        pass_core: bool = False,
        desc: str | None = None,
    ) -> None:
        if pass_core:
            original_operator_func = operator_func

            def wrapped_operator_func(*args: object, **kwargs: object) -> object:
                wraped = original_operator_func(self, *args, **kwargs)
                return wraped

            wrapped_operator_func.arg_count = (  # type: ignore[attr-defined]
                original_operator_func.__code__.co_argcount - 1  # type: ignore[union-attr]
            )
            operator_func = wrapped_operator_func
            arg_count = wrapped_operator_func.arg_count  # type: ignore[attr-defined]
        else:
            arg_count = operator_func.__code__.co_argcount  # type: ignore[union-attr]
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

    def get_stack_ref(self) -> stack_data[object]:
        return self.stack

    def get_stack_copy(self) -> stack_data[object]:
        return self.stack.copy()

    def get_stack_copy_as_list(self) -> list[object]:
        return list(self.stack.copy())

    def get_macros_ref(self) -> dict[str, object]:
        return self.macros

    def get_macros_copy(self) -> dict[str, object]:
        return self.macros.copy()

    def get_variables_ref(self) -> ScopedVariables:
        return self.variables

    def get_variables_copy(self) -> ScopedVariables:
        return self.variables.copy()

    def get_sfuntions_ref(self) -> dict[str, object]:
        return self.sfunctions

    def get_sfuntions_copy(self) -> dict[str, object]:
        return self.sfunctions.copy()

    def get_plugins_ref(self) -> dict[str, object]:
        return self.plugins

    def get_plugins_copy(self) -> dict[str, object]:
        return self.plugins.copy()

    def get_stack_length(self) -> int:
        return len(self.stack)

    def get_trace_ref(self) -> list[object]:
        return self.trace

    def get_trace_copy(self) -> list[object]:
        return self.trace.copy()

    def get_labels_ref(self) -> dict[str, int]:
        return self.labels

    def get_labels_copy(self) -> dict[str, int]:
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

    def get_plugin_descriptions(self) -> dict[str, str | None]:
        return self.plugin_descriptions

    # ========================
    # Clear
    # ========================

    def clear_trace(self) -> None:
        self.trace = []

    # ========================
    # Debug
    # ========================

    def eval(self, expression: str, stack: stack_data[object] | None = None) -> object:
        """Evaluates a given RPN expression.
        Returns the result of the evaluation.

        Example:
        ``` python
        stacker = Stacker()
        and = stacker.eval("1 2 +")
        ```
        """
        tokens = parse_expression(expression)
        return self._evaluate_outside_loops(tokens, stack)
