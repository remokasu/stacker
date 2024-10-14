from __future__ import annotations

import itertools

from collections import deque
from typing import Any
from stacker.error import (
    DropError,
    DupError,
    OverError,
    SwapError,
    RollError,
    RotError,
    PickError,
    NipError,
    InsertError,
)
from stacker.util.disp import disp_stack


"""
Stack manipulation functions.

stack = ['a', 'b', 'c', 'd']

index: value
    4: 'a'
    3: 'b'
    2: 'c'
    1: 'd' <- top
"""


def _drop(stack: deque | list) -> None:
    """
    Drops the top element of the stack.
    Example:
        # 3: 'a'  |
        # 2: 'b'  | 2: 'a'
        # 1: 'c'  | 1: 'b'
    """
    if len(stack) == 0:
        raise DropError("Stack is empty")
    stack.pop()


def _drop2(stack: deque | list) -> None:
    """
    Drops the top two elements of the stack.
    Example:
        # 4: 'a'  |
        # 3: 'b'  |
        # 2: 'c'  | 2: 'a'
        # 1: 'd'  | 1: 'b'
    """
    if len(stack) < 2:
        raise DropError("Stack has less than 2 elements")
    stack.pop()
    stack.pop()


def _dropn(num: int, stack: deque | list) -> None:
    """
    Drops the top n elements of the stack.
    Example:
        # 6: 'a'  |
        # 5: 'b'  |
        # 4: 'c'  |
        # 3: 'd'  |
        # 2: 'e'  | 2: 'a'
        # 1: 3    | 1: 'b'
    """
    if len(stack) == 0:
        raise DropError("Stack is empty")
    if num > len(stack):
        raise DropError("Num is greater than stack size")
    for _ in range(num):
        stack.pop()


def _dup(stack: deque | list) -> None:
    """
    Duplicates the top element of the stack.
    Example:
        # 2:      | 2: 'a'
        # 1: 'a'  | 1: 'a'
    """
    if len(stack) == 0:
        raise DupError("Stack is empty")
    stack.append(stack[-1])


def _dup2(stack: deque | list) -> None:
    """
    Duplicates the top two elements of the stack.
    Example:
        # 4:      | 4: 'a'
        # 3:      | 3: 'b'
        # 2: 'a'  | 2: '1'
        # 1: 'b'  | 1: 'b'
    """
    if len(stack) < 2:
        raise DupError("Stack has less than 2 elements")
    start_index = len(stack) - 2
    end_index = len(stack)
    if isinstance(stack, list):
        stack.extend(stack[start_index:end_index])
    else:
        stack.extend(deque(itertools.islice(stack, start_index, end_index)))


def _dupn(num: int, stack: deque | list) -> None:
    """
    Duplicates the top n elements of the stack.
    Example:
        # 6:      | 6: 'a'
        # 5:      | 5: 'b'
        # 4: 'a'  | 4: 'c'
        # 3: 'b'  | 3: 'a'
        # 2: 'c'  | 2: 'b'
        # 1: 3    | 1: 'c'
    """
    if len(stack) == 0:
        raise DupError("Stack is empty")
    if num > len(stack):
        raise DupError("Index out of range")
    start_index = len(stack) - num
    end_index = len(stack)
    if isinstance(stack, list):
        stack.extend(stack[start_index:end_index])
    else:
        stack.extend(deque(itertools.islice(stack, start_index, end_index)))


def _over(stack: deque | list) -> None:
    """
    Copies the second element to the top of the stack.
    Example:
        # 3:     | 3: 'a'
        # 2: 'a' | 2: 'b'
        # 1: 'b' | 1: 'a'
    """
    if len(stack) < 2:
        raise OverError("Stack has less than 2 elements")
    stack.append(stack[-2])


def _swap(stack: deque | list):
    """
    Swaps the top two elements of the stack.
    Example:
        # 3: 'a'  | 3: 'a'
        # 2: 'b'  | 2: 'c'
        # 1: 'c'  | 1: 'b'
    """
    if len(stack) < 2:
        raise SwapError("Stack has less than 2 elements")
    stack[-1], stack[-2] = stack[-2], stack[-1]


def _roll(n: int, stack: deque | list) -> None:
    """
    Moves the nth element to the top of the stack.
    Example:
        # 5: 'a'  | 5: 'b'
        # 4: 'b'  | 4: 'c'
        # 3: 'c'  | 3: 'd'
        # 2: 'd'  | 2: 'a'
        # 1: 4
    """
    if len(stack) == 0:
        raise RollError("Stack is empty")
    if n > len(stack):
        raise RollError("Index out of range")
    item = stack[-n]
    stack.remove(item)
    stack.append(item)


def _rot(stack: deque | list) -> None:
    """
    Move the third element to the top of the stack.
    Example:
        # 3: 'a'  | 3: 'b'
        # 2: 'b'  | 2: 'c'
        # 1: 'c'  | 1: 'a'
    """
    if len(stack) < 3:
        raise RotError("Stack has less than 3 elements")
    stack[-1], stack[-2], stack[-3] = stack[-3], stack[-1], stack[-2]


def _unrot(stack: deque | list) -> None:
    """
    Moves the top element to the third position of the stack.
    Example:
        # 3: 'a'  | 3: 'b'
        # 2: 'b'  | 2: 'c'
        # 1: 'c'  | 1: 'a'
    """
    if len(stack) < 3:
        raise RotError("Stack has less than 3 elements")
    stack[-1], stack[-2], stack[-3] = stack[-2], stack[-3], stack[-1]


def _pick(num: int, stack: deque | list) -> None:
    """
    Copies the nth element to the top of the stack.
    Example:
        # 5: 'a'  | 5: 'a'
        # 4: 'b'  | 4: 'b'
        # 3: 'c'  | 3: 'c'
        # 2: 'd'  | 2: 'd'
        # 1: 2    | 1: 'c'
    """
    if len(stack) == 0:
        raise PickError("Stack is empty")
    elif num >= len(stack):
        raise PickError("Index out of range")
    if num < 0:
        num = len(stack) + num + 1
    index = len(stack) - num
    stack.append(stack[index])


def _nip(stack: deque | list) -> None:
    """
    Removes the second element from the top of the stack.
    Example:
        # 3: 'a'  | 3:
        # 2: 'b'  | 2: 'a'
        # 1: 'c'  | 1: 'c'
    """
    if len(stack) < 2:
        raise NipError("Stack has less than 2 elements")
    stack.remove(stack[-2])


def _depth(stack: deque | list) -> int:
    """
    Returns the depth of the stack.
    Example:
        # 4:      | 4: 'a'
        # 3: 'a'  | 3: 'b'
        # 2: 'b'  | 2: 'c'
        # 1: 'c'  | 1: 3
    """
    return len(stack)


def _insert(index: int, value: Any, stack: deque | list) -> None:
    """
    Inserts a value at the specified index.
    Example:
        # 6: 'a'  | 6:
        # 5: 'b'  | 5: 'a'
        # 4: 'c'  | 4: 'b'
        # 3: 'd'  | 3: 'e'
        # 2: 2    | 2: 'c'
        # 1: 'e'  | 1: 'd'
    """
    index = len(stack) - index
    if index > len(stack):
        raise InsertError("index out of range")
    stack.insert(index, value)


def _rev(stack: deque | list) -> None:
    """
    Reverses the stack.
    Example:
        # 4: 'a'  | 4: 'd'
        # 3: 'b'  | 3: 'c'
        # 2: 'c'  | 2: 'b'
        # 1: 'd'  | 1: 'a'
    """
    stack.reverse()


def _count(
    value: Any,
    stack: deque | list,
) -> int:
    """
    Counts the number of occurrences of a value in the stack.
    """
    return stack.count(value)


def _clear(stack: deque | list) -> None:
    """
    Clears the stack.
    """
    stack.clear()


def _disp(stack: deque | list) -> None:
    """
    Prints the stack.
    """
    if isinstance(stack, deque):
        # print(list(stack))
        disp_stack(list(stack))
    else:
        # print(stack)
        disp_stack(stack)


stack_operators = {
    "drop": {
        "func": (lambda stack: _drop(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Drops the top element of the stack.",
    },
    "drop2": {
        "func": (lambda stack: _drop2(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Drops the top two elements of the stack.",
    },
    "dropn": {
        "func": (lambda num, stack: _dropn(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Drops the top n elements of the stack.",
    },
    "dup": {
        "func": (lambda stack: _dup(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Duplicates the top element of the stack.",
    },
    "dup2": {
        "func": (lambda stack: _dup2(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Duplicates the top two elements of the stack.",
    },
    "dupn": {
        "func": (lambda num, stack: _dupn(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Duplicates the top n elements of the stack.",
    },
    "over": {
        "func": (lambda stack: _over(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Copies the second element to the top of the stack.",
    },
    "swap": {
        "func": (lambda stack: _swap(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Swaps the top two elements of the stack.",
    },
    "pick": {
        "func": (lambda num, stack: _pick(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Copies the nth element to the top of the stack.",
    },
    "roll": {
        "func": (lambda num, stack: _roll(num, stack)),
        "arg_count": 1,
        "push_result_to_stack": False,
        "desc": "Moves the nth element to the top of the stack.",
    },
    "rot": {
        "func": (lambda stack: _rot(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Move the third element to the top of the stack.",
    },
    "unrot": {
        "func": (lambda stack: _unrot(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Moves the top element to the third position of the stack.",
    },
    "nip": {
        "func": (lambda stack: _nip(stack)),
        "arg_count": 0,
        "push_result_to_stack": False,
        "desc": "Removes the second element from the top of the stack.",
    },
    "depth": {
        "func": (lambda stack: _depth(stack)),
        "arg_count": 0,
        "push_result_to_stack": True,
        "desc": "Returns the depth of the stack.",
    },
    "ins": {
        "func": (lambda index, value, stack: _insert(index, value, stack)),
        "arg_count": 2,
        "push_result_to_stack": False,
        "desc": "Inserts a element at the specified index.",
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
