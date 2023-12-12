from __future__ import annotations

from stacker.error import StackerSyntaxError


def _drop(stack: list):
    if len(stack) == 0:
        raise StackerSyntaxError("drop failed: stack is empty")
    stack.pop()


def _dup(stack: list):
    if len(stack) == 0:
        raise StackerSyntaxError("dup failed: stack is empty")
    stack.append(stack[-1])


def _copy(index: int, stack: list):
    if len(stack) == 0:
        raise StackerSyntaxError("copy failed: stack is empty")
    elif index >= len(stack):
        raise StackerSyntaxError("copy failed: index out of range")
    stack.append(stack[index])


def _swap(stack: list):
    if len(stack) < 2:
        raise StackerSyntaxError("swap failed: stack has less than 2 elements")
    stack[-1], stack[-2] = stack[-2], stack[-1]


def _pluck(index: int, stack: list):
    if len(stack) == 0:
        raise StackerSyntaxError("pluck failed: stack is empty")
    elif index >= len(stack):
        raise StackerSyntaxError("pluck failed: index out of range")
    value = stack.pop(index)
    stack.append(value)


def _insert(index: int, value: Any, stack: list):
    if len(stack) == 0 and index > 0:
        raise StackerSyntaxError("insert failed: stack is empty")
    elif index > len(stack):
        raise StackerSyntaxError("insert failed: index out of range")
    stack.insert(index, value)


def _rev(stack: list):
    stack.reverse()


def _delete(index: int, stack: list):
    if len(stack) == 0:
        raise StackerSyntaxError("delete failed: stack is empty")
    elif index >= len(stack):
        raise StackerSyntaxError("delete failed: index out of range")
    stack.pop(index)


def _clear(stack: list):
    stack.clear()


def _disp(stack: list):
    print(stack)


stack_operators = {
    "drop": {
        "func": (lambda stack: _drop(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Drops the top element of the stack.",
    },
    "dup": {
        "func": (lambda stack: _dup(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Duplicates the top element of the stack.",
    },
    "swap": {
        "func": (lambda stack: _swap(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Swaps the top two elements of the stack.",
    },
    "copy": {
        "func": (lambda index, stack: _copy(index, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Copies the element at the specified index to the top of the stack.",
    },
    "pluck": {
        "func": (lambda index, stack: _pluck(index, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Removes the element at the specified index and moves it to the top of the stack.",
    },
    "insert": {
        "func": (lambda index, value, stack: _insert(index, value, stack)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Inserts a value at the specified index.",
    },
    "delete": {
        "func": (lambda index, stack: _delete(index, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Deletes the element at the specified index.",
    },
    "rev": {
        "func": (lambda stack: _rev(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Reverses the stack.",
    },
    "clear": {
        "func": (lambda stack: _clear(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Clears the stack.",
    },
    "disp": {
        "func": (lambda stack: _disp(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Prints the stack.",
    },
}
