from __future__ import annotations

import ast
import cmath
import copy
import importlib
import math
import os
import random
import re
import shlex
import sys
from pathlib import Path
from typing import Optional

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


def colored(text: str, color: Optional[str] = "default", end: str = "\n") -> None:
    """A context manager for setting and resetting the terminal color.
    Args:
        color (str, optional): The desired text color. Defaults to "default".
    Returns:
        None
    """
    ctext = COLORS[color] + text + COLORS["reset"]
    return ctext


def show_top():
    colors = ["red", "green", "yellow", "lightblue", "lightmagenta", "cyan"]
    with resource_stream(__name__, "data/top.txt") as f:
        messages = f.readlines()
        for i in range(len(messages)):
            print(colored(messages[i].decode('utf-8'), colors[i]), end="")
    print("")


def show_about():
    with resource_stream(__name__, "data/about.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_help():
    with resource_stream(__name__, "data/help.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_help_jp():
    with resource_stream(__name__, "data/help-jp.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def delete_history():
    if history_file_path.exists():
        history_file_path.unlink()


# def evaluate_token_or_return_str(input_str: str) -> int | float | str:
#     try:
#         return eval(input_str)
#     except (SyntaxError, NameError, TypeError, ZeroDivisionError):
#         pass
#     return input_str
def evaluate_token_or_return_str(token):
    try:
        return ast.literal_eval(token)
    except (ValueError, SyntaxError):
        return token


def convert_to_base(value, base):
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
        raise ValueError("Invalid number format.")

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
def wrap(func, cfunc):
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
    def __init__(self, plugin_dir: str = plugins_dir_path):
        self.stack = []  # スタックを追加
        self.last_pop = None  # pop コマンド(ユーザー入力)で取り出した値を一時的に格納。演算でpopする場合は対象外
        self.operator = {
            "==": (lambda x1, x2: x1 == x2),    # Equal
            "!=": (lambda x1, x2: x1 != x2),    # Not equal
            "<": (lambda x1, x2: x1 < x2),      # Less than
            "<=": (lambda x1, x2: x1 <= x2),    # Less than or equal to
            ">": (lambda x1, x2: x1 > x2),      # Greater than
            ">=": (lambda x1, x2: x1 >= x2),    # Greater than or equal to
            "and": (lambda x1, x2: x1 and x2),  # Logical and
            "or": (lambda x1, x2: x1 or x2),    # Logical or
            "not": (lambda x: not x),           # Logical not
            "band": (lambda x1, x2: int(x1) & int(x2)),  # Bitwise and
            "bor": (lambda x1, x2: int(x1) | int(x2)),   # Bitwise or
            "bxor": (lambda x1, x2: int(x1) ^ int(x2)),  # Bitwise xor
            "bin": (lambda value: convert_to_base(value, 2)),   # Binary representation
            "oct": (lambda value: convert_to_base(value, 8)),   # Octal representation
            "dec": (lambda value: convert_to_base(value, 10)),  # Decimal representation
            "hex": (lambda value: convert_to_base(value, 16)),  # Hexadecimal representation
            "+": (lambda x1, x2: x1 + x2),    # Add
            "-": (lambda x1, x2: x1 - x2),    # Subtract
            "*": (lambda x1, x2: x1 * x2),    # Multiply
            "/": (lambda x1, x2: x1 / x2),    # Divide
            "//": (lambda x1, x2: x1 // x2),  # Integer divide
            "%": (lambda x1, x2: x1 % x2),    # Modulus
            "^": (lambda x1, x2: math_pow(x1, x2)),  # Power
            "gcd": (lambda x1, x2: math.gcd(int(x1), int(x2))),  # Greatest common divisor
            "lcm": (lambda x1, x2: math.lcm(int(x1), int(x2))),  # 最小公倍数
            "neg": (lambda x: -x),  # Negate
            "abs": (lambda x: abs(x)),  # Absolute value
            "exp": (lambda x: math_exp(x)),  # Exponential
            "log": (lambda x: math_log(x)),  # Natural logarithm
            "log10": (lambda x: math_log10(x)),  # Common logarithm (base 10)
            "log2": (lambda x: math_log2(x)),  # Logarithm base 2
            "sin": (lambda x: math_sin(x)),  # Sine
            "cos": (lambda x: math_cos(x)),  # Cosine
            "tan": (lambda x: math_tan(x)),  # Tangent
            "asin": (lambda x: math_asin(x)),  # Arcsine
            "acos": (lambda x: math_acos(x)),  # Arccosine
            "atan": (lambda x: math_atan(x)),  # Arctangent
            "sinh": (lambda x: math_sinh(x)),  # Hyperbolic sine
            "cosh": (lambda x: math_cosh(x)),  # Hyperbolic cosine
            "tanh": (lambda x: math_tanh(x)),  # Hyperbolic tangent
            "asinh": (lambda x: math_asinh(x)),  # Inverse hyperbolic sine
            "acosh": (lambda x: math_acosh(x)),  # Inverse hyperbolic cosine
            "atanh": (lambda x: math_atanh(x)),  # Inverse hyperbolic tangent
            "sqrt": (lambda x: math_sqrt(x)),  # Square root
            "radians": (lambda deg: math.radians(deg)),  # Convert degrees to radians
            "!": (lambda x: math.factorial(int(x))),  # Factorial
            "cbrt": (lambda x: pow(x, 1/3)),  # 立方根
            "ncr": (lambda n, k: math.comb(int(n), int(k))),  # 組み合わせ (nCr)
            "npr": (lambda n, k: math.perm(int(n), int(k))),  # 順列 (nPr)
            "float": (lambda x: float(x)),  # Convert to floating-point number
            "int": (lambda x: int(x)),  # Convert to integer
            "ceil": (lambda x: math.ceil(x)),    # Ceiling
            "floor": (lambda x: math.floor(x)),  # Floor
            "round": (lambda x: round(x)),  # Round
            "roundn": (lambda x1, x2: round(x1, int(x2))),  # Round to specified decimal places
            "random": (lambda: random.random()),  # Generate a random floating-point number between 0 and 1|
            "randint": (lambda x1, x2: random.randint(int(x1), int(x2))),  # Generate a random integer within a specified range
            "uniform": (lambda x1, x2: random.uniform(x1, x2)),  # Generate a random floating-point number within a specified range
            "dice": (lambda num_dice, num_faces: sum(random.randint(1, int(num_faces)) for _ in range(int(num_dice)))),  # Roll dice (e.g., 3d6) 
            "delete": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index
            "pluck": (lambda index: self.stack.pop(index)),  # Remove the element at the specified index and move it to the top of the stack
            "pick": (lambda index: self.stack.append((self.stack[index]))),  # Copy the element at the specified index to the top of the stack
            "pop": (lambda: self.stack.pop()),  # pop
            "exec": (lambda command: exec(command, globals())),  # Execute the specified Python code
            "eval": (lambda command: eval(command)),  # Evaluate the specified Python expression
        }
        self.plugins = {}
        self.plugin_descriptions = {}
        self.plugin_dir = plugin_dir

    def get_n_args_for_operator(self, token):
        # token(演算子)に必要な引数の数
        if token in self.operator:
            return self.operator[token].__code__.co_argcount
        else:
            raise KeyError(f"Invalid token {token}")

    def apply_operator(self, token, stack):
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        n_args = self.get_n_args_for_operator(token)
        if n_args is None:
            raise ValueError(f"Unknown operator '{token}'")

        if len(stack) < n_args:
            raise ValueError(f"Not enough operands for operator '{token}'")

        args = [stack.pop() for _ in range(n_args)]
        args.reverse()  # 引数の順序を逆にする

        ans = self.operator[token](*args)
        if token in {"exec", "delete", "pick"}:  # このコマンド実行時は戻り値NoneをStackしない
            return
        elif token == "pop":  # popの場合は戻り値を保存
            self.last_pop = ans
        else:
            stack.append(ans)  # stackは参照渡し

    def evaluate(self, expression, stack=None):
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        if stack is None:
            stack = []

        # List or Tuple
        try:
            value = ast.literal_eval(expression)
            if isinstance(value, (list, tuple)):
                stack.append(value)
                return stack
        except (ValueError, SyntaxError):
            pass  # 入力がリテラルではない場合、処理を継続

        tokens = shlex.split(expression)
        for token in tokens:
            # token: (str)
            if token in self.operator:
                self.apply_operator(token, stack)
            elif token == "=>":
                continue
            elif token == "last_pop":  # popコマンドでpopした値
                stack.append(self.last_pop)
            elif token in self.variables:
                stack.append(self.variables[token])  # 定数をスタックにプッシュ
            elif token in self.functions:
                if len(stack) < len(self.functions[token][0]):
                    raise ValueError(f"Not enough arguments for function '{token}'")
                args = [stack.pop() for _ in range(len(self.functions[token][0]))][::-1]
                stack.append(self.evaluate_function(token, *args))
            else:
                try:
                    stack.append(evaluate_token_or_return_str(token))
                except ValueError:
                    raise ValueError(f"Invalid token '{token}'")

        return stack

    def register_operator(self, operator_name, operator_func):
        self.operator[operator_name] = operator_func

    def register_plugin(self, operator_name, operator_func, description_en=None, description_jp=None):
        self.register_operator(operator_name, operator_func)
        self.plugin_descriptions[operator_name] = {"en": description_en, "jp": description_jp}


class Stacker(StackerCore):
    def __init__(self):
        super().__init__()
        self.variables = {
            "pi": math.pi,
            "tau": math.tau,
            "e": math.e,
            "true": True,
            "false": False,
            "inf": float("inf"),
            "nan": math.nan,
        }
        self.functions = {}
        self.reserved_word = ["help", "help-jp", "about", "exit", "delete_history", "last_pop"]
        self.stack_color = "white"

    def highlight_syntax(self, expression):
        """
        Highlights the syntax of the given RPN expression.
        Returns a colored string of the input expression.
        """
        tokens = expression.split()
        highlighted_tokens = []

        for token in tokens:
            if token in self.operator:
                color = "cyan"
                if token in {"==", "!=", "<", "<=", ">", ">="}:
                    color = "yellow"
                elif token in {"and", "or"}:
                    color = "green"
                highlighted_tokens.append(colored(token, color))
            else:
                try:
                    float(token)
                    highlighted_tokens.append(colored(token, "white"))
                except ValueError:
                    highlighted_tokens.append(colored(token, "red"))

        return " ".join(highlighted_tokens)

    def clear_stack(self):
        self.stack = []

    def define_function(self, name, arg_labels, expression):
        self.validate_name(name)
        self.functions[name] = (arg_labels, expression)

    def validate_name(self, name):
        """
        Validates if a given name is not a reserved word or an operator.
        Raises a ValueError if the name is invalid.
        """
        if name in self.operator or name.lower() in self.reserved_word:
            raise ValueError(f"Invalid name '{name}', it is a reserved word.")
        return name

    def assign_variable(self, name, value):
        """
        Assigns a value to a variable with the given name.
        """
        self.variables[name] = value

    def evaluate_function(self, name, *args):
        """
        Evaluates a function with the given name and arguments.
        Returns the result of the evaluation.
        """
        arg_labels, expression = self.functions[name]  # 引数のラベルと式を取得
        if len(arg_labels) != len(args):
            raise ValueError(f"Function '{name}' requires {len(arg_labels)} arguments, {len(args)} provided")
        for label, arg in zip(arg_labels, args):  # 引数の値を割り当てる
            self.assign_variable(label, arg)
        result = self.evaluate(expression)
        return result[-1]  # 評価された関数の結果だけを返す

    def process_function_definition(self, expression):
        tokens = expression.split()
        name = tokens[tokens.index("=>") - 1]
        self.validate_name(name)
        arg_labels = tokens[:tokens.index("=>") - 1]  # 引数のラベルを取得
        function_expression = " ".join(tokens[tokens.index("=>") + 1:])
        if name in self.operator:
            raise ValueError(f"Invalid function name '{name}'")
        self.define_function(name, arg_labels, function_expression)  # 引数を追加
        # return colored(f"Function '{name}' defined", "magenta")
        highlighted_function = self.highlight_syntax(function_expression)
        return colored(f"Function '{name}' defined: ", "magenta") + highlighted_function

    def process_variable_assignment(self, expression):
        name, value_expression = [s.strip() for s in expression.split("=", 1)]
        print(name, value_expression)
        if name in self.operator:
            raise ValueError(f"Invalid variable name '{name}'")
        self.validate_name(name)
        value = self.evaluate(value_expression)[0]
        self.assign_variable(name, value)
        # return colored(f"Variable '{name}' assigned with value {value}", "blue")
        highlighted_value_expression = self.highlight_syntax(value_expression)
        return colored(f"Variable '{name}' assigned with value {value}: ", "blue") + highlighted_value_expression

    def process_expression(self, expression):
        if "=>" in expression:  # 関数定義
            return self.process_function_definition(expression)
        elif re.search(r"\b\w+\s*=(?!=)", expression): # 代入処理
            return self.process_variable_assignment(expression)
        else:  # RPN式の評価と結果の表示
            ans = self.evaluate(expression, stack=self.stack)
            return colored(f"{ans}",  self.stack_color)


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


class InteractiveMode(ExecutionMode):
    def run(self):
        line_count = 0
        while True:
            try:
                expression = prompt(
                    f"stacker:{line_count}> ",
                    history=FileHistory(history_file_path),
                    completer=self.completer,
                )

                # ダブルコーテーションまたはシングルコーテーションで始まる入力が閉じられるまで継続する処理
                while (
                    (expression.startswith('"""') and expression.count('"""') % 2 != 0) or
                    (expression.startswith("'''") and expression.count("'''") % 2 != 0)
                ):
                    next_line = prompt(
                        f"stacker:{line_count}> ",
                        history=FileHistory(history_file_path),
                        completer=self.completer,
                    )
                    expression += "\n" + next_line

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

                stack_str = self.rpn_calculator.process_expression(expression)
                print(stack_str)  # stackを全表示

            except Exception as e:
                print(colored(f"[ERROR]: {e}", "red"))
                # print("Please enter a valid RPN expression, variable assignment, or function definition.")

            line_count += 1

# 機能拡張予定
# class ScriptMode(ExecutionMode):
#     def __init__(self, rpn_calculator, filename):
#         super().__init__(rpn_calculator)
#         self.filename = filename

#     def run(self):
#         with open(self.filename, 'r') as file:
#             for line in file:
#                 line = line.strip()
#                 if not line or line.startswith("#"):
#                     continue

#                 try:
#                     result = self.rpn_calculator.process_expression(line)
#                     print(result)
#                 except Exception as e:
#                     print(f"Error: {e}")


def main():
    show_top()

    stacker_version = get_distribution('pystacker').version
    print(f"Stacker {stacker_version} on {sys.platform}")
    print('Type "help" or "help-jp" to get more information.')

    rpn_calculator = Stacker()

    # 機能拡張予定
    # if len(sys.argv) > 1:  # 追加
    #     script_filename = sys.argv[1]
    #     # スクリプトモードの実行
    #     script_mode = ScriptMode(rpn_calculator, script_filename)
    #     script_mode.run()
    # else:
    #     # インタラクティブモードの実行
    #     interactive_mode = InteractiveMode(rpn_calculator)
    #     interactive_mode.run()

    # インタラクティブモードの実行
    load_plugins(rpn_calculator)  # プラグインの読み込み
    interactive_mode = InteractiveMode(rpn_calculator)
    interactive_mode.run()


if __name__ == "__main__":
    main()
