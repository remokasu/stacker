from __future__ import annotations

from typing import Callable

from stacker.error import StackerSyntaxError


from stacker.operators.algebra import alge_operators
from stacker.operators.arith import arith_operators
from stacker.operators.aggregate import aggregate_operators
from stacker.operators.transform import transform_operators
from stacker.operators.base import base_operators
from stacker.operators.bitwise import bitwise_operators
from stacker.operators.comparison import compare_operators
from stacker.operators.eval import eval_operators
from stacker.operators.file import file_operators
from stacker.operators.io import io_operators
from stacker.operators.list import list_operators
from stacker.operators.logic import logic_operators
from stacker.operators.math import math_operators
from stacker.operators.random import random_operators
from stacker.operators.stack import stack_operators
from stacker.operators.string import string_operators
from stacker.operators.time import time_operators
from stacker.operators.types import type_operators
from stacker.operators.loop import loop_operators
from stacker.operators.if_else import condition_operators
from stacker.operators.include import include_operators
from stacker.operators.setting import settings_operators
from stacker.operators.exit import exit_operators
from stacker.operators.defun import defun_operators
from stacker.operators.defmacro import macro_operators
from stacker.operators.hof import hof_operators
from stacker.operators.lmd import lambda_operators
from stacker.operators.collection import collection_operators
from stacker.operators.os import os_operators
from stacker.operators.system import system_operators


special_operators = {
    "ans": {
        "func": None,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Pushes again the result of the last input that left one: 3 4 +, then ans -> 7",
    },
    "set": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Binds a value to a name (a block is stored unevaluated): 3 :x set",
    },
    "=": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Same as set: 3 :x =",
    },
    "global": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Sets a variable in global scope.",
    },
    "collect": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Runs a block (or a symbol or a lambda) on an empty stack and pushes what it left as one list: {1 2 3} collect",
    },
    "eval": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Runs a code block, a symbol or a lambda (text: parse first).",
    },
    "break": {
        "func": None,
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Breaks a loop.",
    },
    "sub": {
        "func": None,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Wraps the top value in a one-token code block: :x sub -> {x}",
    },
    "subn": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Wraps the top n values in one code block: 1 2 2 subn -> {1 2}",
    },
    "parse": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Parses text into a code block: \"3 4 +\" parse -> {3 4 +}",
    },
    "read": {
        "func": None,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Reads one line from the console and pushes it as a code block: read eval runs it",
    },
    "split": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Splits the first string by the second string into a list: \"a,b\" \",\" split",
    },
    "nth": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Pushes the nth element of a list, string or block (a name in a block is a symbol); the container stays",
    },
    "expand": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Pushes the elements of a list, or each token of a code block as a one-token block.",
    },
    "gensym": {
        "func": None,
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Pushes a fresh unique symbol (for temporaries in macro-generated code).",
    },
    "symbol": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": 'Makes a symbol from a string or a quoted name: "x" symbol -> :x, {x} symbol -> :x',
    },
    "macroexpand": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Pushes a macro's expansion without evaluating it: <args> {name} macroexpand",
    },
    "concat-block": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Joins two code blocks into one: {a b} {c} concat-block -> {a b c}",
    },
    "listn": {
        "func": None,
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Makes a list of the top n values: 1 2 2 listn -> [1 2]",
    },
    "apply": {
        "func": None,
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Expands list elements onto the stack and applies the function.",
    },
    # REMOVED: "tuplen" operator - () now creates code blocks, not tuples
    # Use lists [] instead of tuples for data structures
}


# Category lookup order for the unified dispatch table. Must mirror the
# elif order of the dispatch chain in StackerCore._execute.
_DISPATCH_ORDER = (
    "priority",
    "stack",
    "system",
    "regular",
    "hof",
    "transform",
    "aggregate",
    "collection",
    "file",
    "settings",
)


class OperatorManager:
    def __init__(self) -> None:
        self._regular_operators = {}
        self._regular_operators.update(alge_operators)
        self._regular_operators.update(arith_operators)
        self._regular_operators.update(base_operators)
        self._regular_operators.update(bitwise_operators)
        self._regular_operators.update(compare_operators)
        self._regular_operators.update(file_operators)
        self._regular_operators.update(io_operators)
        self._regular_operators.update(logic_operators)
        self._regular_operators.update(math_operators)
        self._regular_operators.update(random_operators)
        self._regular_operators.update(type_operators)
        self._regular_operators.update(list_operators)
        self._regular_operators.update(eval_operators)
        self._regular_operators.update(string_operators)
        self._regular_operators.update(time_operators)
        self._regular_operators.update(os_operators)

        self._priority_operators = {}
        self._priority_operators.update(loop_operators)
        self._priority_operators.update(condition_operators)
        self._priority_operators.update(special_operators)
        self._priority_operators.update(include_operators)
        self._priority_operators.update(defun_operators)
        self._priority_operators.update(macro_operators)
        self._priority_operators.update(lambda_operators)
        self._priority_operators.update(exit_operators)

        self._collection_operators = collection_operators
        self._file_operators = file_operators
        self._hof_operators = hof_operators
        self._aggregate_operators = aggregate_operators
        self._transform_operators = transform_operators
        self._stack_operators = stack_operators
        self._settings_operators = settings_operators
        self._system_operators = system_operators

        self.operators = {
            "priority": self._priority_operators,
            "regular": self._regular_operators,
            "hof": self._hof_operators,
            "aggregate": self._aggregate_operators,
            "collection": self._collection_operators,
            "transform": self._transform_operators,
            "stack": self._stack_operators,
            "file": self._file_operators,
            "settings": self._settings_operators,
            "system": self._system_operators,
        }

        self.built_in_operators = set()
        for kind in self.operators.keys():
            self.built_in_operators.update(self.operators[kind].keys())

        self._rebuild_dispatch_table()

    def _rebuild_dispatch_table(self) -> None:
        """Build the unified operator lookup table.

        Maps each operator name to its ``(category, definition)`` pair.
        Categories are visited in the same order as the dispatch chain in
        ``StackerCore._execute``; first match wins, so a name present
        in several categories (e.g. file operators, which are also merged
        into ``regular``) resolves to the same category as before.

        Must be called again whenever a category dict is mutated
        (see ``register_operator``).
        """
        table: dict[str, tuple[str, dict[str, object]]] = {}
        for category in _DISPATCH_ORDER:
            for name, opdef in self.operators[category].items():
                if name not in table:
                    table[name] = (category, opdef)
        self.dispatch_table = table

    def get_all_keys_for_completer(self) -> list[str]:
        return list(
            set(
                self.get_regular_keys()
                + self.get_priority_keys()
                + self.get_hof_keys()
                + self.get_aggregate_keys()
                + self.get_transform_keys()
                + self.get_collection_keys()
                + self.get_stack_keys()
                + self.get_system_keys()
                # + list(self.get_settings_keys())
            )
        )

    def get_any_operator_arg_count(self, operator: str) -> int:
        if operator in self._priority_operators:
            return self._priority_operators[operator]["arg_count"]
        if operator in self._regular_operators:
            return self._regular_operators[operator]["arg_count"]
        if operator in special_operators:
            return special_operators[operator]["arg_count"]
        if operator in hof_operators:
            return hof_operators[operator]["arg_count"]
        if operator in aggregate_operators:
            return aggregate_operators[operator]["arg_count"]
        if operator in transform_operators:
            return transform_operators[operator]["arg_count"]
        if operator in stack_operators:
            return stack_operators[operator]["arg_count"]
        if operator in file_operators:
            return file_operators[operator]["arg_count"]
        if operator in settings_operators:
            return settings_operators[operator]["arg_count"]
        if operator in system_operators:
            return system_operators[operator]["arg_count"]
        raise StackerSyntaxError(f"Unknown operator '{operator}'")

    ############################
    # Regular operators
    ############################
    def get_regular_ref(self) -> dict[str, object]:
        return self._regular_operators

    def get_regular_copy(self) -> dict[str, object]:
        return self._regular_operators.copy()

    def get_regular_keys(self) -> list[str]:
        return list(self._regular_operators.keys())

    ############################
    # Priority operators
    ############################
    def get_priority_ref(self) -> dict[str, object]:
        return self._priority_operators

    def get_priority_copy(self) -> dict[str, object]:
        return self._priority_operators.copy()

    def get_priority_keys(self) -> list[str]:
        return list(self._priority_operators.keys())

    ############################
    # Special operators
    ############################
    def get_special_ref(self) -> dict[str, object]:
        return special_operators

    def get_special_copy(self) -> dict[str, object]:
        return special_operators.copy()

    def get_special_keys(self) -> list[str]:
        return list(special_operators.keys())

    ############################
    # HOF operators
    ############################
    def get_hof_ref(self) -> dict[str, object]:
        return self._hof_operators

    def get_hof_copy(self) -> dict[str, object]:
        return self._hof_operators.copy()

    def get_hof_keys(self) -> list[str]:
        return list(self._hof_operators.keys())

    ############################
    # Aggregate operators
    ############################
    def get_aggregate_ref(self) -> dict[str, object]:
        return self._aggregate_operators

    def get_aggregate_copy(self) -> dict[str, object]:
        return self._aggregate_operators.copy()

    def get_aggregate_keys(self) -> list[str]:
        return list(self._aggregate_operators.keys())

    ############################
    # Transform operators
    ############################
    def get_transform_ref(self) -> dict[str, object]:
        return self._transform_operators

    def get_transform_copy(self) -> dict[str, object]:
        return self._transform_operators.copy()

    def get_transform_keys(self) -> list[str]:
        return list(self._transform_operators.keys())

    def get_collection_keys(self) -> list[str]:
        return list(self._collection_operators.keys())

    ############################
    # Stack operators
    ############################
    def get_stack_ref(self) -> dict[str, object]:
        return self._stack_operators

    def get_stack_copy(self) -> dict[str, object]:
        return self._stack_operators.copy()

    def get_stack_keys(self) -> list[str]:
        return list(self._stack_operators.keys())

    ############################
    # File operators
    ############################
    def get_file_ref(self) -> dict[str, object]:
        return self._file_operators

    def get_file_copy(self) -> dict[str, object]:
        return self._file_operators.copy()

    def get_file_keys(self) -> list[str]:
        return list(self._file_operators.keys())

    ############################
    # Settings operators
    ############################
    def get_settings_ref(self) -> dict[str, object]:
        return self._settings_operators

    def get_settings_copy(self) -> dict[str, object]:
        return self._settings_operators.copy()

    def get_settings_keys(self) -> list[str]:
        return list(self._settings_operators.keys())

    ############################
    # System operators
    ############################
    def get_system_ref(self) -> dict[str, object]:
        return self._system_operators

    def get_system_copy(self) -> dict[str, object]:
        return self._system_operators.copy()

    def get_system_keys(self) -> list[str]:
        return list(self._system_operators.keys())

    ############################
    # Descriptions
    ############################
    def get_priority_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._priority_operators:
            descriptions[operator] = self._priority_operators[operator]["desc"]
        return descriptions

    def get_hof_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._hof_operators:
            descriptions[operator] = self._hof_operators[operator]["desc"]
        return descriptions

    def get_aggregate_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._aggregate_operators:
            descriptions[operator] = self._aggregate_operators[operator]["desc"]
        return descriptions

    def get_transform_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._transform_operators:
            descriptions[operator] = self._transform_operators[operator]["desc"]
        return descriptions

    def get_collection_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._collection_operators:
            descriptions[operator] = self._collection_operators[operator]["desc"]
        return descriptions

    def get_stack_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._stack_operators:
            descriptions[operator] = self._stack_operators[operator]["desc"]
        return descriptions

    def get_file_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._file_operators:
            descriptions[operator] = self._file_operators[operator]["desc"]
        return descriptions

    def get_settings_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._settings_operators:
            descriptions[operator] = self._settings_operators[operator]["desc"]
        return descriptions

    def get_system_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._system_operators:
            descriptions[operator] = self._system_operators[operator]["desc"]
        return descriptions

    def get_regular_descriptions(self) -> dict[str, object]:
        descriptions = {}
        for operator in self._regular_operators:
            descriptions[operator] = self._regular_operators[operator]["desc"]
        return descriptions

    def get_regular_and_priority_operator_descriptions(self) -> dict[str, object]:
        descriptions = {}
        descriptions.update(self.get_regular_descriptions())
        descriptions.update(self.get_priority_descriptions())
        return descriptions

    ############################
    # Register
    ############################
    def register_operator(
        self,
        operator_name: str,
        operator_func: Callable[..., object],
        arg_count: int,
        push_result_to_stack: bool,
        desc: str | None = None,
    ) -> None:
        for item in self.operators:
            if operator_name in self.operators[item]:
                del self.operators[item][operator_name]
                self.operators[item][operator_name] = {
                    "func": operator_func,
                    "arg_count": arg_count,
                    "push_result_to_stack": push_result_to_stack,
                    "desc": desc,
                }
                # The definition dict is replaced (not mutated), so the
                # dispatch table must be rebuilt to point at the new one.
                self._rebuild_dispatch_table()
                return
        return
