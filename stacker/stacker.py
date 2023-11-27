from __future__ import annotations

import ast
import copy
import logging
from typing import Any, Callable

from stacker.error import StackerSyntaxError
from stacker.function import math
from stacker import parameter
from stacker.function.base import convert_to_base
from stacker.util.string_parser import (
    parse_expression,
    convert_custom_string_tuple_to_proper_tuple,
    is_block
)
from stacker.include import include_stacker_script
from stacker.file import read_file, write_file
from stacker.compiler import py_eval


class Stacker:
    """ A class for evaluating RPN expressions.
    """
    depth_counter = 0

    def __init__(self, expression: str | None = None, parent: 'Stacker' | None = None):
        self.parent = parent
        self.depth = Stacker.depth_counter
        Stacker.depth_counter += 1
        self.sub_expression = expression
        self.child = None
        self.stack: list[Any] = []  # スタックを追加
        self.last_pop = None  # pop コマンド(ユーザー入力)で取り出した値を一時的に格納。演算でpopする場合は対象外
        self.operator = {
            "==": (lambda x1, x2: x1 == x2),    # Equal
            "!=": (lambda x1, x2: x1 != x2),    # Not equal
            "<=": (lambda x1, x2: x1 <= x2),    # Less than or equal to
            "<": (lambda x1, x2: x1 < x2),      # Less than
            ">=": (lambda x1, x2: x1 >= x2),    # Greater than or equal to
            ">": (lambda x1, x2: x1 > x2),      # Greater than
            "&&": (lambda x1, x2: x1 and x2),  # Logical and
            "||": (lambda x1, x2: x1 or x2),    # Logical or
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
            "^": (lambda x1, x2: math.pow(x1, x2)),  # Power
            "gcd": (lambda x1, x2: math.gcd(int(x1), int(x2))),  # Greatest common divisor
            "lcm": (lambda x1, x2: math.lcm(int(x1), int(x2))),  # 最小公倍数
            "neg": (lambda x: -x),           # Negate
            "abs": (lambda x: abs(x)),       # Absolute value
            "exp": (lambda x: math.exp(x)),  # Exponential
            "log10": (lambda x: math.log10(x)),  # Common logarithm (base 10)
            "log2": (lambda x: math.log2(x)),    # Logarithm base 2
            "log": (lambda x: math.log(x)),      # Natural logarithm
            "asinh": (lambda x: math.asinh(x)),  # Inverse hyperbolic sine
            "acosh": (lambda x: math.acosh(x)),  # Inverse hyperbolic cosine
            "atanh": (lambda x: math.atanh(x)),  # Inverse hyperbolic tangent
            "asin": (lambda x: math.asin(x)),  # Arcsine
            "acos": (lambda x: math.acos(x)),  # Arccosine
            "atan": (lambda x: math.atan(x)),  # Arctangent
            "sinh": (lambda x: math.sinh(x)),  # Hyperbolic sine
            "cosh": (lambda x: math.cosh(x)),  # Hyperbolic cosine
            "tanh": (lambda x: math.tanh(x)),  # Hyperbolic tangent
            "sin": (lambda x: math.sin(x)),    # Sine
            "cos": (lambda x: math.cos(x)),    # Cosine
            "tan": (lambda x: math.tan(x)),    # Tangent
            "sqrt": (lambda x: math.sqrt(x)),  # Square root
            "radians": (lambda deg: math.radians(deg)),  # Convert degrees to radians
            "!": (lambda x: math.factorial(int(x))),  # Factorial
            "cbrt": (lambda x: math.pow(x, 1/3)),  # 立方根
            "ncr": (lambda n, k: math.comb(int(n), int(k))),  # 組み合わせ (nCr)
            "npr": (lambda n, k: math.perm(int(n), int(k))),  # 順列 (nPr)
            "float": (lambda x: float(x)),  # Convert to floating-point number
            "int": (lambda x: int(x)),  # Convert to integer
            "str": (lambda x: str(x)),  # Convert to integer
            "ceil": (lambda x: math.ceil(x)),    # Ceiling
            "floor": (lambda x: math.floor(x)),  # Floor
            "roundn": (lambda x1, x2: round(x1, int(x2))),  # Round to specified decimal places
            "round": (lambda x: round(x)),  # Round
            "random": (lambda: math.rand()),  # Generate a random floating-point number between 0 and 1|
            "randint": (lambda x1, x2: math.randint(int(x1), int(x2))),  # Generate a random integer within a specified range
            "uniform": (lambda x1, x2: math.uniform(x1, x2)),  # Generate a random floating-point number within a specified range
            "dice": (lambda num_dice, num_faces: math.dice(num_dice, num_faces)),  # Roll dice (e.g., 3d6) 
            "delete": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index
            "pluck": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index and move it to the top of the stack
            "pick": (lambda index: self.stack.append((self.stack[index]))),  # Copy the element at the specified index to the top of the stack
            "push": (lambda value: self.stack.append(value)),  # push
            "pop": (lambda: self.pop()),  # pop
            "dup": (lambda: self.dup()),  # Duplicate the top element of the stack
            "swap": (lambda: self.swap()),  # # Swap the top two elements of the stack
            "peek": (lambda: self.peek()),  # Refer to the topmost element (the "top" of the stack) without deleting it
            "ppeek": (lambda: self.ppeek()),  # Refer to the topmost element of the parent stack without deleting it
            "insert": (lambda index, value: self.stack.insert(index, value)),  # insert
            "rev": (lambda: self.stack.reverse()),  # reverse
            "exec": (lambda command: exec(command, globals())),  # Execute the specified Python code
            "eval": (lambda command: self._eval(command)),  # Evaluate the specified Python expression
            "echo": (lambda value: print(value)),
            "ans": (lambda: self.get_last_ans()),
            "set": (lambda name, value: self._set(value, name)),
            "defun": (lambda func_name, fargs, body: self.fn_operator(func_name, fargs, body)),
            "alias": (lambda label, body: self.define_macro(label, body)),
            "seq": (lambda start_value, end_value: list(range(start_value, end_value + 1))),
            "for": (lambda sequence, block, loop_var_symbol: self.execute_for(sequence, block, loop_var_symbol)),
            "times": (lambda n_times, block: self.execute_times(block, n_times)),
            "if": (lambda condition, block: self.execute_if(condition, block)),
            "ifelse": (lambda condition, true_block, false_block: self.execute_if_else(condition, true_block, false_block)),
            # "cond": (lambda block: self.execute_cond(block)),
            "show": (lambda: self.show()),
            "clear": (lambda: self.clear_stack()),
            "include": (lambda filename: self.include(filename)),
            "read": (lambda filename, mode: self.raad(filename, mode)),
            "write": (lambda content, filename, mode: self.write(filename, content, mode)),
            # "ipy": (lambda code: py_eval(code, globals=globals())),
            # "py": (lambda code: py_eval(code)),
            # "sfunc": (lambda func, n_args: self.sfunc(func, n_args)),
            # "rf": (lambda func_name, func_body: self.register_function(func_name, func_body)), 
        }
        self.variables = {
            "pi": parameter.pi,
            "tau": parameter.tau,
            "e": parameter.e,
            "true": parameter.true,
            "false": parameter.false,
            "inf": parameter.inf,
            "nan": parameter.nan,
        }
        self.macros = {}
        self.plugins = {}
        self.functions = {}
        self.plugin_descriptions = {}
        self.reserved_word = [
            "help", "help-jp", "about", "exit",
            "delete_history", "last_pop", "end",
        ]
        # このコマンド実行時は戻り値をpushしない
        # forの場合、execute_for内でpushする
        # ifの場合、execute_if内でpushする
        # ifelseの場合、execute_if_else内でpushする
        # Note: execute_for, execute_if, execute_if_elseは、他の演算子の処理とは異なる.
        #       修正予定
        self.non_destructive_operator = {
            "exec", "delete", "pick", "rev", "echo", "show",
            "insert", "dup", "swap", "set", "push", "show_all_valiables",
            "whos", "alias", "defun", "for", "times", "ifelse", "if", "include",
            "write", "ipy"
        }

    def get_macros(self):
        return self.macros

    def get_variables(self):
        return self.variables

    def get_operator(self):
        return self.operator

    def raad(self, filename: str, mode: str) -> str:
        """ Reads a file.
        """
        logging.debug(f"read: {filename}")
        content = read_file(filename, mode=mode,interactive_mode=True)
        return content

    def write(self, filename: str, content, mode: str) -> None:
        """ Writes a file.
        """
        logging.debug(f"write: {filename}")
        write_file(filename, content, mode=mode, interactive_mode=True)

    def include(self, filename: str) -> None:
        """ Includes another stacker script.
        """
        logging.debug(f"include: {filename}")
        _stacker = include_stacker_script(filename)
        _operator = _stacker.get_operator()
        _macros = _stacker.get_macros()
        _variables = _stacker.get_variables()
        self.operator.update(_operator)
        self.macros.update(_macros)
        self.variables.update(_variables)

    def substack(self, token: str) -> None:
        """ Creates a substack.
        :param token: The token containing the substack.
        """
        logging.debug(f"sub block: {token}")
        self.child = Stacker(parent=self)
        self.child.sub_expression = token[1:-1]
        self.child.variables = self.variables  # TODO Refactoring
        if self.child.sub_expression == {}:
            self.stack.append(None)
        else:
            self.stack.append(self.child)

    def dup(self):
        self.stack.append(self.stack[-1])

    def swap(self):
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def peek(self) -> Any:
        return self.stack[-1]

    def ppeek(self):
        """ Pushes a duplicate of the parent stack onto the current stack.
        """
        if self.parent is not None:
            return self.parent.peek()
        else:
            raise StackerSyntaxError("Cannot pdup from root stacker")

    def _eval(self, expression: str):
        logging.debug(f"eval: {expression}")
        if isinstance(expression, str):
            return eval(expression)

    def _set(self, value, name):
        logging.debug(f"{name} {value} set")
        self.variables[name] = value

    def clear_stack(self):
        self.stack = []

    def pop(self, stack: list = None, evaluate_on_pop: bool = True):
        if stack is None:
            stack = self.stack
        value = stack.pop()
        if evaluate_on_pop is False:
            return value
        logging.debug("pop: %s", value)
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

    def push(self, value, stack=None):
        if stack is None:
            stack = self.stack
        stack.append(value)

    def define_macro(self, label: str, body: Stacker) -> None:
        """ Defines a macro.
        """
        self.macros[label] = body
        macro = StackerMacro(label, body)
        self.register_macro(label, macro)

    def expand_macro(self, label: str) -> None:
        """ Executes a macro.
        """
        macro = self.macros[label]
        expression = macro.blockstack.sub_expression
        tokens = parse_expression(expression)
        self.evaluate(tokens, stack=self.stack)

    def fn_operator(self, func_name, fargs, blockstack: Stacker):
        logging.debug(f"fn_operator: func_name:{func_name}, args: {fargs}, \
            expression: {blockstack.sub_expression}")
        # self.operator[func_name] = (lambda *args: self._debug(*args))
        function = StackerFunction(fargs, blockstack)
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

    def execute_times(self, n_times: int, blockstack: Stacker | Any) -> None:
        """ Executes a block of code a specified number of times.
        """
        if isinstance(blockstack, Stacker):
            loop_expression = blockstack.sub_expression
            tokens = parse_expression(loop_expression)
            i_count = 0
            self.stack.append(i_count)
            while self.peek() < n_times:
                self.pop()
                blockstack.evaluate(tokens, stack=blockstack.stack)
                sub_stack = blockstack.get_stack()
                if len(sub_stack) > 0:
                    self.stack += sub_stack
                blockstack.clear_stack()
                i_count = i_count + 1
                self.push(i_count)
            self.pop()
        else:  # e.g. a numeric object
            i_count = 0
            self.stack.append(i_count)
            while self.peek() < n_times:
                self.pop()
                self.push(blockstack)
                i_count = i_count + 1
                self.push(i_count)
            self.pop()

    def execute_if(self, condition: Stacker | bool, blockstack: Stacker | Any) -> None:
        """ Executes a block of code if a condition is true.
        """
        if isinstance(condition, Stacker):
            condition_expression = condition.sub_expression
            tokens = parse_expression(condition_expression)
            condition.evaluate(tokens, stack=condition.stack)
            sub_stack = condition.get_stack()
            if len(sub_stack) > 0:
                self.stack += sub_stack
            condition.clear_stack()
            condition = self.pop()
        logging.debug(f"execute_if: {condition}, {blockstack}")
        if condition:
            if isinstance(blockstack, Stacker):
                if_expression = blockstack.sub_expression
                tokens = parse_expression(if_expression)
                blockstack.evaluate(tokens, stack=blockstack.stack)
                sub_stack = blockstack.get_stack()
                if len(sub_stack) > 0:
                    self.stack += sub_stack
                blockstack.clear_stack()
            else:  # e.g. a numeric object
                self.stack.append(blockstack)

    def execute_if_else(
        self,
        condition: Stacker | bool,
        true_block: Stacker | Any,
        false_block: Stacker | Any
    ) -> None:
        """ Executes a block of code if a condition is true, otherwise executes another block of code.
        """
        if isinstance(condition, Stacker):
            condition_expression = condition.sub_expression
            tokens = parse_expression(condition_expression)
            condition.evaluate(tokens, stack=condition.stack)
            sub_stack = condition.get_stack()
            if len(sub_stack) > 0:
                self.stack += sub_stack
            condition.clear_stack()
            condition = self.pop()
        logging.debug(f"execute_if_else: {condition}, {true_block}, {false_block}")
        if condition:
            if isinstance(true_block, Stacker):
                true_expression = true_block.sub_expression
                tokens = parse_expression(true_expression)
                true_block.evaluate(tokens, stack=true_block.stack)
                sub_stack = true_block.get_stack()
                if len(sub_stack) > 0:
                    self.stack += sub_stack
                true_block.clear_stack()
            else:  # e.g. a numeric object
                self.stack.append(true_block)
        else:
            if isinstance(false_block, Stacker):
                false_expression = false_block.sub_expression
                tokens = parse_expression(false_expression)
                false_block.evaluate(tokens, stack=false_block.stack)
                sub_stack = false_block.get_stack()
                if len(sub_stack) > 0:
                    self.stack += sub_stack
                false_block.clear_stack()
            else:
                self.stack.append(false_block)

    # def execute_cond(self, block: Stacker) -> None:
    #     # print(block.sub_expression)
    #     if isinstance(block, Stacker):
    #         cond_expression = block.sub_expression
    #         tokens = parse_expression(cond_expression)
    #         block.evaluate(tokens, stack=block.stack)
    #         sub_stack = block.get_stack()
    #         if len(sub_stack) > 0:
    #             self.stack += sub_stack
    #         block.clear_stack()
    #     else:
    #         self.stack.append(block)

    def show(self) -> None:
        """ Prints the current stack.
        """
        print(self.get_stack())

    def get_stack(self) -> list:
        """ Returns the current stack.
        """
        return copy.deepcopy(self.stack)

    def length(self) -> int:
        """ Returns the length of the current stack.
        """
        return len(self.stack)

    def get_last_ans(self) -> Any:
        """ Returns the last answer.
        """
        return self.stack[-1]

    def get_n_args_for_operator(self, token: str) -> int:
        """ Returns the number of arguments required for a given operator.
        """
        # token(演算子)に必要な引数の数
        if token in self.operator:
            op = self.operator[token]
            arg_count = op.arg_count if hasattr(op, 'arg_count') else op.__code__.co_argcount
            return arg_count
            # return self.operator[token].__code__.co_argcount
        else:
            raise KeyError(f"Invalid token {token}")

    def process_expression(self, expression) -> None:
        tokens = parse_expression(expression)
        logging.debug(f"process_expression expression: {expression}")
        logging.debug(f"process_expression tokens: {tokens}")
        self.evaluate(tokens, stack=self.stack)

    def evaluate(self, tokens: list, stack=None) -> list:
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        if stack is None:
            stack = []

        # Ensure tokens is a list
        assert isinstance(tokens, list) is True
        logging.debug("evaluate tokens: %s", tokens)

        # Iterate over each token in the token list
        index = 0
        for token in tokens:
            logging.debug("tokens: %s, type: %s", token, type(token))
            next_token = None
            if index < len(tokens) - 1:
                next_token = tokens[index + 1]
            if isinstance(token, set):  # TODO Refactoring
                # {}
                logging.debug("Convert set to string")
                token = str(token)

            # If the token is not a string (e.g. it's a number), add it to the stack
            if not isinstance(token, str):
                stack.append(token)
            elif token in self.macros and next_token != "alias":
                self.expand_macro(token)
            elif token in self.operator and next_token != "defun":
                self.apply_operator(token, stack)
            elif token == "defun" or token == "alias":
                self.apply_operator(token, stack)
            # If the token is a block (substack), evaluate the substack
            elif is_block(token):
                self.substack(token)
            # If none of the above conditions are met, just add the token to the stack
            elif token in self.variables:
                stack.append(self.variables[token])
            else:
                # try:
                #     # execute python code
                #     token = eval(token)
                # except Exception as e:
                #     # just a string
                #     print(e)
                stack.append(token)
            logging.debug("stack: %s", str(stack))
            index += 1
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
            raise StackerSyntaxError(f"Not enough operands for operator '{token}'")
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
        elif token == "defun":
            args = []
            name = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            fargs = self.pop(stack)
            fargs = convert_custom_string_tuple_to_proper_tuple(fargs)  # TODO Refacotring
            fargs = ast.literal_eval(fargs)  # TODO Refacotring
            args.append(body)
            args.append(fargs)
            args.append(name)
        elif token == "alias":
            args = []
            label = self.pop(stack, evaluate_on_pop=False)
            body = self.pop(stack, evaluate_on_pop=False)
            args.append(body)
            args.append(label)
        elif token == "for":
            args = []
            loop_var_symbol = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            rng = self.pop()  # ???
            args.append(loop_var_symbol)
            args.append(body)
            args.append(rng)
        elif token == "times":
            args = []
            n_times = self.pop(stack)
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            args.append(n_times)
            args.append(body)
        elif token == "if":
            args = []
            condition = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            args.append(body)
            args.append(condition)
        elif token == "ifelse":
            args = []
            condition = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            false_block = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            true_block = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            args.append(false_block)
            args.append(true_block)
            args.append(condition)
        elif token == "rf":  # regisgter_function
            args = []
            func_name = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            func_body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
            args.append(func_body)
            args.append(func_name)
        elif token in ["py", "ipy"]:
            args = []
            code = self.pop(stack, evaluate_on_pop=False)
            if isinstance(code, Stacker):
                code = code.sub_expression 
            args.append(code)
        # elif token == "cond":
        #     args = []
        #     body = self.pop(stack, evaluate_on_pop=False)  # not evaluate
        #     args.append(body)
        else:
            args = [self.pop(stack) for _ in range(n_args)]
        args.reverse()  # 引数の順序を逆にする
        # if token in self.functions:
        #     ans = self.functions[token](*args)
        # else:
        #     ans = self.operator[token](*args)
        ans = self.operator[token](*args)
        if token in self.non_destructive_operator:
            return
        elif token == "pop":  # popの場合は戻り値を保存
            self.last_pop = ans
        else:
            stack.append(ans)  # stackは参照渡し

    def register_operator(
        self,
        operator_name: str,
        operator_func: Callable,
        push_result_to_stack: bool
    ) -> None:
        if not push_result_to_stack:
            self.non_destructive_operator.add(operator_name)
        self.operator[operator_name] = operator_func

    def register_macro(
        self,
        macro_name: str,
        macro_body: Callable
    ):
        if macro_name in self.macros:
            del self.macros[macro_name]
        self.macros[macro_name] = macro_body

    def register_parameter(
        self,
        parameter_name: str,
        parameter_value: Any
    ):
        if parameter_name in self.variables:
            del self.variables[parameter_name]
        self.variables[parameter_name] = parameter_value

    # def register_function(
    #     self,
    #     function_name: str,
    #     function_body: Callable
    # ):
    #     # if function_name in self.functions:
    #     #     del self.functions[function_name]
    #     # self.functions[function_name] = function_body
    #     print("function_name", function_name)
    #     print("function_body", function_body)
    #     if function_name in self.operator:
    #         del self.operator[function_name]
    #     self.operator[function_name] = function_body
    #     logging.debug(f"register function: {function_name}")

    def register_plugin(
        self,
        operator_name: str,
        operator_func: Callable,
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

    # def sfunc(self, func: Callable, n_args: int):
    #     def wrapped_operator_func(*args, **kwargs):
    #         wraped = func(self, *args, **kwargs)
    #         return wraped
    #     wrapped_operator_func.arg_count = n_args
    #     return wrapped_operator_func


class StackerFunction:
    """ A callable object that represents a function defined in Stacker.
    """
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


class StackerMacro:
    """ A callable object that represents a macro defined in Stacker.
    """
    def __init__(self, label: str, blockstack: Stacker):
        self.label = label
        self.blockstack = blockstack
        self.arg_count = 0

    def __call__(self):
        return self.blockstack
