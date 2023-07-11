from __future__ import annotations

import argparse
import ast
import cmath
import copy
import importlib
import logging
import math
import os
import random
import re
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

from pkg_resources import get_distribution, resource_stream
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

history_file = ".stacker_history"
history_file_path = Path.home() / history_file
plugins_dir_path = "plugins"

COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "lightgray": "\033[37m",
    "default": "\033[39m",
    "darkgray": "\033[90m",
    "lightred": "\033[91m",
    "lightgreen": "\033[92m",
    "lightyellow": "\033[93m",
    "lightblue": "\033[94m",
    "lightmagenta": "\033[95m",
    "lightcyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m",
}


def parse_string(s):
    result = []
    current_token = ""
    # brackets = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}
    brackets = {"[": "]", "(": ")", "{": "}"}
    bracket_stack = []
    for char in s:
        if char in brackets:
            if bracket_stack and brackets[bracket_stack[-1]] == char:
                current_token += char
                bracket_stack.pop()
                if not bracket_stack:
                    if current_token[0] == "'" or current_token[0] == '"':
                        result.append(current_token[1:-1])  # remove quotes
                    else:
                        result.append(current_token)
                    current_token = ""
            else:
                bracket_stack.append(char)
                current_token += char
        elif bracket_stack:
            current_token += char
            if char == brackets[bracket_stack[-1]]:
                bracket_stack.pop()
                if not bracket_stack:
                    if current_token[0] == "'" or current_token[0] == '"':
                        result.append(current_token[1:-1])  # remove quotes
                    else:
                        result.append(current_token)
                    current_token = ""
        elif char.isspace():
            if current_token:
                result.append(current_token)
                current_token = ""
        else:
            current_token += char
    if current_token:  # add the last token if any
        result.append(current_token)
    logging.debug(f"parse string: {s}")
    logging.debug(f"parsed: {result}")
    return result


def colored(text: str, color: Optional[str] = "default", end: str = "\n") -> None:
    """A context manager for setting and resetting the terminal color.
    Args:
        color (str, optional): The desired text color. Defaults to "default".
    Returns:
        None
    """
    ctext = COLORS[color] + text + COLORS["reset"]
    return ctext


def show_top() -> None:
    colors = ["red", "green", "yellow", "lightblue", "lightmagenta", "cyan"]
    with resource_stream(__name__, "data/top.txt") as f:
        messages = f.readlines()
        for i in range(len(messages)):
            print(colored(messages[i].decode('utf-8'), colors[i]), end="")
    print("")


def show_about() -> None:
    with resource_stream(__name__, "data/about.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_help() -> None:
    with resource_stream(__name__, "data/help.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_help_jp() -> None:
    with resource_stream(__name__, "data/help-jp.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def delete_history() -> None:
    if history_file_path.exists():
        history_file_path.unlink()


def evaluate_token_or_return_str(token: str) -> Any:
    logging.debug(f"evaluate_token_or_return_str: {token}")
    try:
        return ast.literal_eval(token)
    except (ValueError, SyntaxError) as e:
        logging.debug(f"token ({token}) is str")
        logging.debug(f"{e}")
        return token


def starts_with_char(expression: str, char: str) -> bool:
    try:
        return expression.strip().startswith(char)
    except Exception:
        return False


def is_balanced(expression: str, open_char: str, close_char: str) -> bool:
    open_count = expression.count(open_char)
    close_count = expression.count(close_char)
    return open_count == close_count


def is_single(expression: str, open_char: str, close_char: str) -> bool:
    if is_balanced(expression, open_char, close_char):
        return expression.count(open_char) == 1 and expression.count(close_char) == 1
    return False


def is_array(expression: str) -> bool:
    return starts_with_char(expression, "[")


def is_tuple(expression: str) -> bool:
    return starts_with_char(expression, "(")


def is_brace(expression: str) -> bool:
    return starts_with_char(expression, "{")


def is_array_balanced(expression: str) -> bool:
    return is_balanced(expression, "[", "]")


def is_tuple_balanced(expression: str) -> bool:
    return is_balanced(expression, "(", ")")


def is_brace_balanced(expression: str) -> bool:
    return is_balanced(expression, "{", "}")


def is_single_array(expression: str) -> bool:
    return is_single(expression, "[", "]")


def is_single_tuple(expression: str) -> bool:
    return is_single(expression, "(", ")")


def is_single_brace(expression: str) -> bool:
    return is_single(expression, "{", "}")


def is_block(expression: str) -> bool:
    if not isinstance(expression, str):
        return False
    opener = expression.count('{')
    closer = expression.count('}')
    if opener == 0 and closer == 0:
        return False
    return opener == closer


def convert_custom_array_to_proper_list(token: str) -> str:
    """
    Converts a custom list token into a proper Python list.

    :param token: The custom list token to be converted.
    :return: The converted token as a proper Python list.

    Example:
    Input:  "[1 2 3; 4 5 6]"
    Output: "[[1, 2, 3], [4, 5, 6]]"
    """
    token = re.sub(r"(\d+(\.\d+)?)\s+", r"\1, ", token)
    token = re.sub(r";\s+", r"], [", token)

    open_brackets = token.count('[')
    close_brackets = token.count(']')
    if open_brackets > close_brackets:
        token += ']' * (open_brackets - close_brackets)
    if is_array(token) and not is_single_array(token):
        token = f"[{token}]"
    return token


def convert_custom_tuple_to_proper_tuple(token: str) -> str:
    """
    Converts a custom tuple token into a proper Python tuple.

    :param token: The custom tuple token to be converted.
    :return: The converted token as a proper Python tuple.

    Example:
    Input:  "(1 2 3; 4 5 6)"
    Output: "((1, 2, 3), (4, 5, 6))"
    """
    token = re.sub(r"(\d+(\.\d+)?)\s+", r"\1, ", token)
    token = re.sub(r";\s+", r"), (", token)

    open_parenthesis = token.count('(')
    close_parenthesis = token.count(')')
    if open_parenthesis > close_parenthesis:
        token += ')' * (open_parenthesis - close_parenthesis)
    if is_tuple(token) and not is_single_tuple(token):
        token = f"({token})"
    return token


def convert_custom_string_tuple_to_proper_tuple(token: str) -> str:
    """
    Converts a custom tuple token with string elements into a proper Python tuple.

    :param token: The custom tuple token to be converted.
    :return: The converted token as a proper Python tuple.

    Example:
    Input:  "(a b)"
    Output: "("a", "b")"
    """
    # Convert sequences of non-number, non-punctuation characters to
    #    use commas and surround with quotes
    token = re.sub(r"([a-zA-Z_]\w*)\s*", r'"\1", ', token)
    # Change semicolons to tuple separators
    token = re.sub(r";\s*", r"), (", token)

    open_parenthesis = token.count('(')
    close_parenthesis = token.count(')')
    if open_parenthesis > close_parenthesis:
        token += ')' * (open_parenthesis - close_parenthesis)
    if is_tuple(token) and not is_single_tuple(token):
        token = f"({token})"

    # Clean up any trailing commas and quotes
    token = re.sub(r", \)", r")", token)
    token = re.sub(r'", ', r'",', token)
    return token


def parse_expression(expression: str) -> list:
    """
        input(str)  : [1 2 3] 4 5 a
        output(list): [[1, 2, 3], 4, 5, 'a']
    """
    ignore_tokens = ['"""', "'''"]
    parsed_expressions = parse_string(expression)
    logging.debug(f"parsed_expressions: {parsed_expressions}")
    tokens = []
    for token in parsed_expressions:
        if token in ignore_tokens:
            continue
        elif is_array(token):
            token = convert_custom_array_to_proper_list(token)
            tokens.append(evaluate_token_or_return_str(token))
        elif is_tuple(token):
            token = convert_custom_tuple_to_proper_tuple(token)
            tokens.append(evaluate_token_or_return_str(token))
        else:
            tokens.append(evaluate_token_or_return_str(token))
    return tokens


def convert_to_base(value: str | int, base: int) -> str | int:
    value = str(value)

    # 2進数 (0b...)
    binary_pattern = re.compile(r'^0b[01]+$')
    # 8進数 (0o...)
    octal_pattern = re.compile(r'^0o[0-7]+$')
    # 10進数
    decimal_pattern = re.compile(r'^[-+]?\d+$')
    # 16進数 (0x...)
    hex_pattern = re.compile(r'^0x[\da-fA-F]+$')

    if not (binary_pattern.match(value) or octal_pattern.match(value) or decimal_pattern.match(value) or hex_pattern.match(value)):
        raise ValueError("Invalid number format.(convert_to_base)")

    # 文字列を整数に変換
    value_as_int = int(value, 0)  # 0は、2進数、8進数、16進数を自動的に検出して処理することを意味する

    if base == 2:
        return bin(value_as_int)
    elif base == 8:
        return oct(value_as_int)
    elif base == 10:
        return value_as_int
    elif base == 16:
        return hex(value_as_int)
    else:
        raise ValueError("Invalid base.")


# 入力が実数か虚数かで呼び出すモジュールを切り替える
def wrap(func: callable, cfunc: callable) -> callable:
    def wrapper(x):
        if isinstance(x, complex):
            return cfunc(x)
        return func(x)
    return wrapper


def math_pow(x1, x2):
    if isinstance(x1, complex) or isinstance(x2, complex):
        return cmath.exp(x2 * cmath.log(x1))
    else:
        return math.pow(x1, x2)


def math_log2(x):
    if isinstance(x, complex):
        return cmath.log(x) / cmath.log(2)
    else:
        return math.log2(x)


math_exp = wrap(math.exp, cmath.exp)
math_log = wrap(math.log, cmath.log)
math_log10 = wrap(math.log10, cmath.log10)
math_sin = wrap(math.sin, cmath.sin)
math_cos = wrap(math.cos, cmath.cos)
math_tan = wrap(math.tan, cmath.tan)
math_asin = wrap(math.asin, cmath.asin)
math_acos = wrap(math.acos, cmath.acos)
math_atan = wrap(math.atan, cmath.atan)
math_sinh = wrap(math.sinh, cmath.sinh)
math_cosh = wrap(math.cosh, cmath.cosh)
math_tanh = wrap(math.tanh, cmath.tanh)
math_asinh = wrap(math.asinh, cmath.asinh)
math_acosh = wrap(math.acosh, cmath.acosh)
math_atanh = wrap(math.atanh, cmath.atanh)
math_sqrt = wrap(math.sqrt, cmath.sqrt)


class StackerCore:
    def __init__(self):
        self.stack = []  # スタックを追加
        self.last_pop = None  # pop コマンド(ユーザー入力)で取り出した値を一時的に格納。演算でpopする場合は対象外
        self.operator = {
            "==": (lambda x1, x2: x1 == x2),    # Equal
            "!=": (lambda x1, x2: x1 != x2),    # Not equal
            "<=": (lambda x1, x2: x1 <= x2),    # Less than or equal to
            "<": (lambda x1, x2: x1 < x2),      # Less than
            ">=": (lambda x1, x2: x1 >= x2),    # Greater than or equal to
            ">": (lambda x1, x2: x1 > x2),      # Greater than
            "and": (lambda x1, x2: x1 and x2),  # Logical and
            "or": (lambda x1, x2: x1 or x2),    # Logical or
            "not": (lambda x: not x),           # Logical not
            "band": (lambda x1, x2: int(x1) & int(x2)),  # Bitwise and
            "bor": (lambda x1, x2: int(x1) | int(x2)),   # Bitwise or
            "bxor": (lambda x1, x2: int(x1) ^ int(x2)),  # Bitwise xor
            ">>": (lambda value, n: value >> n),  # bitshit right
            "<<": (lambda value, n: value << n),  # bitshift left
            "~": (lambda value: ~value),          # bit inversion
            "bin": (lambda value: convert_to_base(value, 2)),   # Binary representation
            "oct": (lambda value: convert_to_base(value, 8)),   # Octal representation
            "dec": (lambda value: convert_to_base(value, 10)),  # Decimal representation
            "hex": (lambda value: convert_to_base(value, 16)),  # Hexadecimal representation
            "++": (lambda x1: x1 + 1),        # Increment
            "--": (lambda x1: x1 - 1),        # Decrement
            "+": (lambda x1, x2: x1 + x2),    # Add
            "-": (lambda x1, x2: x1 - x2),    # Subtract
            "*": (lambda x1, x2: x1 * x2),    # Multiply
            "//": (lambda x1, x2: x1 // x2),  # Integer divide
            "/": (lambda x1, x2: x1 / x2),    # Divide
            "%": (lambda x1, x2: x1 % x2),    # Modulus
            "^": (lambda x1, x2: math_pow(x1, x2)),  # Power
            "gcd": (lambda x1, x2: math.gcd(int(x1), int(x2))),  # Greatest common divisor
            "lcm": (lambda x1, x2: math.lcm(int(x1), int(x2))),  # 最小公倍数
            "neg": (lambda x: -x),  # Negate
            "abs": (lambda x: abs(x)),  # Absolute value
            "exp": (lambda x: math_exp(x)),  # Exponential
            "log10": (lambda x: math_log10(x)),  # Common logarithm (base 10)
            "log2": (lambda x: math_log2(x)),  # Logarithm base 2
            "log": (lambda x: math_log(x)),  # Natural logarithm
            "asinh": (lambda x: math_asinh(x)),  # Inverse hyperbolic sine
            "acosh": (lambda x: math_acosh(x)),  # Inverse hyperbolic cosine
            "atanh": (lambda x: math_atanh(x)),  # Inverse hyperbolic tangent
            "asin": (lambda x: math_asin(x)),  # Arcsine
            "acos": (lambda x: math_acos(x)),  # Arccosine
            "atan": (lambda x: math_atan(x)),  # Arctangent
            "sinh": (lambda x: math_sinh(x)),  # Hyperbolic sine
            "cosh": (lambda x: math_cosh(x)),  # Hyperbolic cosine
            "tanh": (lambda x: math_tanh(x)),  # Hyperbolic tangent
            "sin": (lambda x: math_sin(x)),  # Sine
            "cos": (lambda x: math_cos(x)),  # Cosine
            "tan": (lambda x: math_tan(x)),  # Tangent
            "sqrt": (lambda x: math_sqrt(x)),  # Square root
            "radians": (lambda deg: math.radians(deg)),  # Convert degrees to radians
            "!": (lambda x: math.factorial(int(x))),  # Factorial
            "cbrt": (lambda x: pow(x, 1/3)),  # 立方根
            "ncr": (lambda n, k: math.comb(int(n), int(k))),  # 組み合わせ (nCr)
            "npr": (lambda n, k: math.perm(int(n), int(k))),  # 順列 (nPr)
            "float": (lambda x: float(x)),  # Convert to floating-point number
            "int": (lambda x: int(x)),  # Convert to integer
            "str": (lambda x: str(x)),  # Convert to integer
            "ceil": (lambda x: math.ceil(x)),    # Ceiling
            "floor": (lambda x: math.floor(x)),  # Floor
            "roundn": (lambda x1, x2: round(x1, int(x2))),  # Round to specified decimal places
            "random": (lambda: random.random()),  # Generate a random floating-point number between 0 and 1|
            "round": (lambda x: round(x)),  # Round
            "randint": (lambda x1, x2: random.randint(int(x1), int(x2))),  # Generate a random integer within a specified range
            "uniform": (lambda x1, x2: random.uniform(x1, x2)),  # Generate a random floating-point number within a specified range
            "dice": (lambda num_dice, num_faces: sum(random.randint(1, int(num_faces)) for _ in range(int(num_dice)))),  # Roll dice (e.g., 3d6) 
            "delete": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index
            "pluck": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index and move it to the top of the stack
            "pick": (lambda index: self.stack.append((self.stack[index]))),  # Copy the element at the specified index to the top of the stack
            # "pop": (lambda: self.stack.pop()),  # pop
            "pop": (lambda: self.pop()),  # pop
            "dup": (lambda: self.dup()),  # Duplicate the top element of the stack
            "swap": (lambda: self.swap()),  # # Swap the top two elements of the stack
            "peek": (lambda: self.peek()),  # Refer to the topmost element (the "top" of the stack) without deleting it
            "insert": (lambda index, value: self.stack.insert(index, value)),  # insert
            "rev": (lambda: self.stack.reverse()),  # reverse
            "exec": (lambda command: exec(command, globals())),  # Execute the specified Python code
            "eval": (lambda command: self._eval(command)),  # Evaluate the specified Python expression
            "echo": (lambda value: print(value)),
            "ans": (lambda: self.get_last_ans()),
            "set": (lambda name, value: self._set(value, name)),
            "fn": (lambda func_name, fargs, body: self.fn_operator(func_name, fargs, body)),
            "seq": (lambda start_value, end_value: list(range(start_value, end_value))),
            "for": (lambda sequence, block, loop_var_symbol: self.execute_for(sequence, block, loop_var_symbol)),
            "show": (lambda: self.show)
        }
        self.variables = {
            "pi": math.pi,
            "tau": math.tau,
            "e": math.e,
            "true": True,
            "false": False,
            "inf": float("inf"),
            "nan": math.nan,
        }
        self.reserved_word = [
            "help", "help-jp", "about", "exit",
            "delete_history", "last_pop", "end", "clear"
        ]
        # このコマンド実行時は戻り値をpushしない
        # forの場合、execute_for内でpushする
        self.non_destructive_operator = {
            "exec", "delete", "pick", "rev", "echo", "show",
            "insert", "dup", "swap", "set", "show_all_valiables", "whos", "fn", "for"}
        self.plugins = {}
        self.plugin_descriptions = {}

    def dup(self):
        self.stack.append(self.stack[-1])

    def swap(self):
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def peek(self):
        return self.stack[-1]

    def _eval(self, expression: str):
        logging.debug(f"eval: {expression}")
        if isinstance(expression, str):
            return eval(expression)

    def _set(self, value, name):
        logging.debug(f"{name} {value} set")
        self.variables[name] = value

    def clear_stack(self):
        self.stack = []

    def pop(self, stack: list = None):
        if stack is None:
            return self.stack.pop()
        else:
            return stack.pop()

    def push(self, value, stack=None):
        if stack is None:
            stack = self.stack
        stack.append(value)

    def fn_operator(self, func_name, fargs, blockstack: Stacker):
        logging.debug(f"fn_operator: func_name:{func_name}, args: {fargs}, expression: {blockstack.sub_expression}")
        # self.operator[func_name] = (lambda *args: self._debug(*args))
        function = StackerFunction(fargs, blockstack)
        if func_name in self.operator.keys():
            del self.operator[func_name]
        self.register_operator(func_name, function, push_result_to_stack=True)

    def execute_for(self, sequence: list, blockstack: Stacker, loop_var_symbol: str):
        for_expression = blockstack.sub_expression
        tokens = parse_expression(for_expression)
        for i in sequence:
            blockstack._set(i, loop_var_symbol)
            result = blockstack.evaluate(tokens, stack=blockstack.stack)
        if isinstance(result, list):
            # self.stack.append(result[-1])
            for i in range(len(result)):
                self.stack.append(result[i])
        else:
            self.stack.append(result)

    def show(self):
        print(self.get_stack())

    def get_stack(self):
        return copy.deepcopy(self.stack)

    def get_stack_length(self):
        return len(self.stack)

    def get_last_ans(self):
        return self.stack[-1]

    def get_n_args_for_operator(self, token: str) -> int:
        # token(演算子)に必要な引数の数
        if token in self.operator:
            op = self.operator[token]
            arg_count = op.arg_count if hasattr(op, 'arg_count') else op.__code__.co_argcount
            return arg_count
            # return self.operator[token].__code__.co_argcount
        else:
            raise KeyError(f"Invalid token {token}")

    def register_operator(
        self,
        operator_name: str,
        operator_func: callable,
        push_result_to_stack: bool
    ) -> None:
        if not push_result_to_stack:
            self.non_destructive_operator.add(operator_name)
        self.operator[operator_name] = operator_func

    def register_plugin(
            self,
            operator_name: str,
            operator_func: callable,
            push_result_to_stack: bool = True,
            pass_core: bool = False,
            description_en: str | None = None,
            description_jp: str | None = None
    ):
        if pass_core:
            original_operator_func = operator_func
            def wrapped_operator_func(*args, **kwargs):
                wraped = original_operator_func(self, *args, **kwargs)
                return wraped
            wrapped_operator_func.arg_count = original_operator_func.__code__.co_argcount - 1
            operator_func = wrapped_operator_func

        self.register_operator(operator_name, operator_func, push_result_to_stack)
        self.plugin_descriptions[operator_name] = {"en": description_en, "jp": description_jp}


class Stacker(StackerCore):
    depth_counter = 0

    def __init__(self, expression: str | None = None):
        super().__init__()
        self.depth = Stacker.depth_counter
        Stacker.depth_counter += 1
        self.sub_expression = expression
        self.child = None

    def substack(self, token: str) -> None:
        logging.debug(f"sub block: {token}")
        self.child = Stacker()
        self.child.sub_expression = token[1:-1]
        self.child.variables = self.variables  # TODO Refactoring
        if self.child.sub_expression == {}:
            self.stack.append(None)
        else:
            self.stack.append(self.child)

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        logging.debug(f"process_expression expression: {expression}")
        logging.debug(f"process_expression tokens: {tokens}")
        self.evaluate(tokens, stack=self.stack)

    def pop(self, stack: list = None, evaluate_on_pop: bool = True):
        if stack is None:
            stack = self.stack
        value = stack.pop()
        if evaluate_on_pop is False:
            return value
        logging.debug(f"pop: {value}")
        if not isinstance(value, Stacker):
            if isinstance(value, list) or isinstance(value, tuple):
                return value
            if value in self.variables.keys():  # TODO Fix
                logging.debug(f"variables {self.variables}")
                logging.debug(f"valiable {value}: {self.variables[value]}")
                return self.variables[value]
            return value
        # block
        expression = value.sub_expression  # {...}
        if expression == {}:
            stack.append(None)
        else:
            value.process_expression(expression)
            sub = value.get_stack()
            if len(sub) > 0:
                for i in range(len(sub)):
                    stack.append(sub[i])
            return stack.pop()

    def evaluate(self, tokens: list, stack=None) -> list:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        if stack is None:
            stack = []

        # Ensure tokens is a list
        assert isinstance(tokens, list) is True
        logging.debug(f"evaluate tokens: {tokens}")

        # Iterate over each token in the token list
        for token in tokens:
            logging.debug(f"tokens: {token}, type: {type(token)}")
            # If the token is not a string (e.g. it's a number), add it to the stack
            if not isinstance(token, str):
                stack.append(token)
            # If the token is an operator and we're not in a function definition ("fn" is not in the tokens)
            # apply the operator to the current stack
            elif token in self.operator and not "fn" in tokens:
                self.apply_operator(token, stack)
            # If we're defining a function (token is "fn"), also apply the operator
            elif token == "fn":
                self.apply_operator(token, stack)
            # If the token is a block (substack), evaluate the substack
            elif is_block(token):
                self.substack(token)
            # If none of the above conditions are met, just add the token to the stack
            else:
                stack.append(token)
            logging.debug(f"stack: {stack}")
        return stack

    def apply_operator(self, token: str, stack: list):
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        n_args = self.get_n_args_for_operator(token)
        if n_args is None:
            raise ValueError(f"Unknown operator '{token}'")
        if len(stack) < n_args:
            raise ValueError(f"Not enough operands for operator '{token}'")
        # args = [stack.pop() for _ in range(n_args)]
        if token == "set":
            # 代入操作の場合、self.pop()ではなく、stack.pop()する
            # self.pop()は, popと同時に評価するため、定義済み変数に再割当て時に
            # 変数値に対し代入してしまうため
            args = []
            name = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            value = self.pop(stack)
            args.append(value)
            args.append(name)
        elif token == "fn":
            args = []
            name = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            fargs = self.pop(stack)
            fargs = convert_custom_string_tuple_to_proper_tuple(fargs)  # TODO Refacotring
            fargs = ast.literal_eval(fargs)  # TODO Refacotring
            args.append(body)
            args.append(fargs)
            args.append(name)
        elif token == "for":
            args = []
            loop_var_symbol = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            rng = self.pop()
            args.append(loop_var_symbol)
            args.append(body)
            args.append(rng)
        else:
            args = [self.pop(stack) for _ in range(n_args)]
        args.reverse()  # 引数の順序を逆にする
        ans = self.operator[token](*args)
        if token in self.non_destructive_operator:
            return
        elif token == "pop":  # popの場合は戻り値を保存
            self.last_pop = ans
        else:
            stack.append(ans)  # stackは参照渡し


class StackerFunction:
    def __init__(self, args: list[str], blockstack: Stacker):
        self.args = args
        self.blockstack = blockstack
        self.arg_count = len(args)

    def __call__(self, *values):
        values = list(values)
        if len(values) != len(self.args):
            raise ValueError(f"Expected {len(self.args)} arguments, got {len(values)}")
        # Create a new stack for the function call
        # Bind the arguments to the values
        for arg, value in zip(self.args, values):
            # stacker.variables[arg] = value
            self.blockstack._set(value, arg)
            self.blockstack.stack.append(arg)
        self.blockstack.stack.append(self.blockstack)
        result = self.blockstack.pop()
        return result


def load_plugins(stacker_core: StackerCore):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(script_dir, plugins_dir_path)
    # プラグインディレクトリにパスを追加
    sys.path.insert(0, plugins_dir)

    try:
        # プラグインディレクトリ内のファイルを走査
        for filename in os.listdir(plugins_dir):
            try:
                if filename.endswith(".py") and not filename.startswith("__"):
                    # ファイル名から拡張子を除いた名前を取得
                    module_name = os.path.splitext(filename)[0]
                    # モジュールをインポート
                    plugin_module = importlib.import_module(module_name)
                    # プラグインのセットアップ関数を呼び出し
                    plugin_module.setup(stacker_core)
            except AttributeError as e:
                print(colored(f"[ERROR]{e}", "red"))
            finally:
                continue
    except FileNotFoundError:
        print("Warning: plugins folder not found. Skipping plugin loading.")
    finally:
        # プラグインディレクトリからパスを削除
        sys.path.pop(0)


class ExecutionMode:
    def __init__(self, rpn_calculator: Stacker):
        self.rpn_calculator = rpn_calculator
        self._operator_key = list(self.rpn_calculator.operator.keys())
        self._variable_key = list(self.rpn_calculator.variables.keys())
        self._reserved_word = copy.deepcopy(self.rpn_calculator.reserved_word)
        self._reserved_word = (self._reserved_word + self._operator_key + self._variable_key)
        self.completer = WordCompleter(self._reserved_word)
        self.color_print = True

    def get_multiline_input(prompt=""):
        lines = []
        while True:
            line = input(prompt)
            if line.endswith("\\"):
                line = line[:-1]  # バックスラッシュを取り除く
                lines.append(line)
                prompt = ""  # 2行目以降のプロンプトは空にする
            else:
                lines.append(line)
                break
        return "\n".join(lines)

    def run(self):
        raise NotImplementedError("Subclasses must implement the 'run' method")

    def print_colored_output(self, stack_list):
        stack_str = colored("[", 'yellow')
        for item in stack_list:
            item_str = str(item)
            # print(item_str)
            if item_str.startswith('[') or item_str.endswith(']'):
                stack_str += colored(item_str, 'red')
                stack_str += ", "
            elif item_str.startswith('(') or item_str.endswith(')'):
                stack_str += colored(item_str, 'green')
                stack_str += ", "
            elif item_str.replace('.', '', 1).isdigit() or (item_str.startswith('-') and item_str[1:].replace('.', '', 1).isdigit()):
                stack_str += colored(item_str, 'default')
                stack_str += ", "
            elif item_str in list(self.rpn_calculator.variables.keys()):
                stack_str += colored(item_str, 'lightblue')
                stack_str += ", "
            else:
                stack_str += colored(item_str, 'default')
                stack_str += ", "
        stack_str = stack_str[0:-2]
        stack_str += colored("]", 'yellow')
        print(stack_str)

    def show_stack(self) -> None:
        tokens = self.rpn_calculator.get_stack()
        if len(tokens) == 0:
            return
        stack = []
        for token in tokens:
            if isinstance(token, Stacker):
                stack.append(token.sub_expression)
            else:
                stack.append(token)

        if self.color_print is True:
            self.print_colored_output(stack)
        else:
            print(stack)


class InteractiveMode(ExecutionMode):

    def get_input(self, prompt_text: str, multiline: bool):
        try:
            return prompt(
                prompt_text,
                history=FileHistory(history_file_path),
                completer=self.completer,
                multiline=multiline
            )
        except EOFError:
            print("\nSee you!")
            sys.exit()

    def run(self):
        show_top()
        stacker_version = get_distribution('pystacker').version
        print(f"Stacker {stacker_version} on {sys.platform}")
        print('Type "help" or "help-jp" to get more information.')

        line_count = 0
        while True:
            try:
                expression = self.get_input(f"stacker:{line_count}> ", multiline=False)
                if expression[-2:] in {";]", ";)"}:
                    closer = expression[-1]
                    expression = expression[:-2] + closer

                if is_array(expression) or is_tuple(expression):
                    """
                        # List
                        stacker:0> [1 2 3
                                    3 4 5]
                        [1 2 3; 3 4 5]

                        # Tuple
                        stacker:0> (1 2 3
                                    3 4 5)
                        (1 2 3; 3 4 5)
                    """
                    while not is_array_balanced(expression) or not is_tuple_balanced(expression):
                        prompt_text = " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                        next_line = self.get_input(prompt_text, multiline=False)
                        if next_line.lower() == ('end'):
                            break
                        if next_line in {"]", ")"}:
                            expression += next_line
                            if is_array_balanced(expression) or is_tuple_balanced(expression):
                                if expression[-2:] in {";]", ";)"}:
                                    closer = expression[-1]
                                    expression = expression[:-2] + closer
                                break
                        if next_line[-2:] in {";]", ";)"}:
                            closer = next_line[-1]
                            next_line = next_line[:-2] + closer
                        if not expression.endswith(";"):
                            expression += "; " + next_line
                        else:
                            expression += " " + next_line

                # ダブルコーテーションまたはシングルコーテーションで始まる入力が閉じられるまで継続する処理
                while (
                    (expression.startswith('"""') and expression.count('"""') % 2 != 0) or
                    (expression.startswith("'''") and expression.count("'''") % 2 != 0)
                ):
                    """
                        stacker:0> '''
                        stacker:0> This is a multi-line
                        stacker:0> input example.
                        stacker:0> '''
                        ['\nThis is a multi-line\ninput example.\n']
                    """
                    prompt_text = " " * (len(f"stacker:{line_count}> ") - len("> ")) + "> "
                    next_line = self.get_input(prompt_text, multiline=False)
                    expression += "\n" + next_line

                # if (
                #     (expression.startswith('"""') and expression.endswith('"""')) or
                #     (expression.startswith("'''") and expression.endswith("'''"))
                # ):
                #     expression = expression.strip("\n")

                logging.debug(f"input expression: {expression}")

                if expression.lower() == "exit":
                    break
                if expression.lower() == "help":
                    show_help()
                    print("")
                    print("Plugin commands:")
                    for plugin_name, plugin_descriptions in self.rpn_calculator.plugin_descriptions.items():
                        en_description = plugin_descriptions.get("en", None)
                        if en_description:
                            print(f"  {plugin_name}: {en_description}")
                    continue
                if expression.lower() == "help-jp":
                    show_help_jp()
                    print("")
                    print("プラグインコマンド：")
                    for plugin_name, plugin_descriptions in self.rpn_calculator.plugin_descriptions.items():
                        jp_description = plugin_descriptions.get("jp", None)
                        if jp_description:
                            print(f"  {plugin_name}: {jp_description}")
                        else:
                            print(f"  {plugin_name}: {plugin_descriptions['en']} (日本語の説明はありません)")
                    continue
                if expression.lower() == "about":
                    show_about()
                    continue
                if expression.lower() == "delete_history":
                    delete_history()
                    continue
                if expression.lower() == "clear":
                    self.rpn_calculator.clear_stack()
                    continue

                self.rpn_calculator.process_expression(expression)
                self.show_stack()

            except EOFError:
                print("\nSee you!")
                break

            except Exception as e:
                print(colored(f"[ERROR]: {e}", "red"))
                traceback.print_exc()

            line_count += 1


class ScriptMode(ExecutionMode):
    def __init__(self, rpn_calculator: Stacker):
        super().__init__(rpn_calculator)

    def run(self, file_path: str):
        path = Path(file_path)
        if not path.is_file() or not path.suffix == '.sk':
            raise ValueError("Invalid file path or file type. Please provide a valid '.sk' file.")

        with path.open('r') as script_file:
            expression = ''
            for line in script_file:
                line = line.strip()
                if line.startswith('#') or not line:  # ignore comments and empty lines
                    continue
                expression += line + ' '
                if self._is_balanced(expression):
                    if expression[-2:] in {";]", ";)"}:
                        closer = expression[-1]
                        expression = expression[:-2] + closer
                    self.rpn_calculator.process_expression(expression)
                    expression = ''

    def _is_balanced(self, expression: str) -> bool:
        return (
            is_array_balanced(expression) and
            is_tuple_balanced(expression) and
            is_brace_balanced(expression) and
            (expression.count('"""') % 2 == 0) and
            (expression.count("'''") % 2 == 0)
        )


def copy_plugin_to_install_dir(plugin_path: str) -> None:
    try:
        # Get the installation directory of Stacker
        stacker_dist = get_distribution("pystacker")
        plugin_dir = stacker_dist.location + "/stacker/plugins"

        # Check if the plugin file exists
        if not os.path.isfile(plugin_path):
            print(f"Error: The file '{plugin_path}' does not exist.")
            return

        # Copy the plugin file to the Stacker's installation directory
        assert Path(plugin_dir).exists
        shutil.copy(plugin_path, plugin_dir)
        print(f"Successfully added the plugin '{plugin_path}' to Stacker.")
        print(plugin_dir)
    except Exception as e:
        print(f"An error occurred while adding the plugin: {str(e)}")
        traceback.print_exc()


def main():
    # add plugin
    parser = argparse.ArgumentParser(description='Stacker command line interface.')
    parser.add_argument('--addplugin', metavar='path', type=str, help='Path to the plugin to add.')
    parser.add_argument('--dmode', action='store_true', help='Enable debug mode')
    parser.add_argument('script', nargs='?', default=None, help='Script file to run.')
    args = parser.parse_args()

    """
        interactive:    stacker
        plugin install: stacker --addplugin <path>
        debug mode:     stacker --dmode
        script mode:    stacker ***.sk
    """

    if args.addplugin:
        copy_plugin_to_install_dir(args.addplugin)
        return

    if args.dmode:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    rpn_calculator = Stacker()
    load_plugins(rpn_calculator)

    if args.script:
        # Script Mode
        script_mode = ScriptMode(rpn_calculator)
        script_mode.run(args.script)
    else:
        # Interactive mode
        interactive_mode = InteractiveMode(rpn_calculator)
        interactive_mode.run()


if __name__ == "__main__":
    main()
