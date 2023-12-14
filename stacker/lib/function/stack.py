from __future__ import annotations

from collections import deque

from stacker.error import StackerSyntaxError


def _drop(stack: deque):
    if len(stack) == 0:
        raise StackerSyntaxError("drop failed: stack is empty")
    stack.pop()


def _dup(stack: deque):
    if len(stack) == 0:
        raise StackerSyntaxError("dup failed: stack is empty")
    stack.append(stack[-1])


def _swap(stack: deque):
    if len(stack) < 2:
        raise StackerSyntaxError("swap failed: stack has less than 2 elements")
    stack[-1], stack[-2] = stack[-2], stack[-1]


# def _pluck(index: int, stack: list):
#     if len(stack) == 0:
#         raise StackerSyntaxError("pluck failed: stack is empty")
#     elif index >= len(stack):
#         raise StackerSyntaxError("pluck failed: index out of range")
#     value = stack.pop(index)
#     stack.append(value)


def _rot(num: int, stack: deque):
    stack.rotate(num)


def _rotl(num: int, stack: deque):
    stack.rotate(-num)


def _pick(num: int, stack: deque):
    stack.append(stack[num])


def _insert(index: int, value: Any, stack: deque):
    stack.insert(index, value)


def _rev(stack: deque):
    stack.reverse()


def _count(
    value: Any,
    stack: deque,
):
    return stack.count(value)


def _clear(stack: deque):
    stack.clear()


def _disp(stack: deque):
    print(list(stack))


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
    # "pluck": {
    #     "func": (lambda index, stack: _pluck(index, stack)),
    #     "arg_count": 1,
    #     "push_result_to_stack": False,
    #     "desc": "Removes the element at the specified index and moves it to the top of the stack.",
    # },
    "pick": {
        "func": (lambda num, stack: _pick(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Copies the nth element to the top of the stack.",
    },
    "rot": {
        "func": (lambda num, stack: _rot(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Rotates the top n elements of the stack.",
    },
    "rotl": {
        "func": (lambda num, stack: _rotl(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Rotates the top n elements of the stack to the left.",
    },
    "ins": {
        "func": (lambda index, value, stack: _insert(index, value, stack)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Inserts a value at the specified index.",
    },
    "rev": {
        "func": (lambda stack: _rev(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Reverses the stack.",
    },
    "count": {
        "func": (lambda stack, value: _count(stack, value)),
        "arg_count": 1,
        "push_result_to_stack": True,
        "desc": "Counts the number of occurrences of a value in the stack.",
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
