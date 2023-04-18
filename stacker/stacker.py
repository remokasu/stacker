import math
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import readline
except ImportError:
    import pyreadline as readline

import pkg_resources

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
    with pkg_resources.resource_stream(__name__, "data/top.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_about():
    with pkg_resources.resource_stream(__name__, "data/about.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


def show_help():
    with pkg_resources.resource_stream(__name__, "data/help.txt") as f:
        message = f.read().decode('utf-8')
    print(message)


class Stacker:
    def __init__(self):
        self.stack = []  # スタックを追加
        self.operator = {
            "==": (lambda x1, x2: x1 == x2),  # 等しい
            "!=": (lambda x1, x2: x1 != x2),  # 等しくない
            "<": (lambda x1, x2: x1 < x2),  # より小さい
            "<=": (lambda x1, x2: x1 <= x2),  # 以下
            ">": (lambda x1, x2: x1 > x2),  # より大きい
            ">=": (lambda x1, x2: x1 >= x2),  # 以上
            "and": (lambda x1, x2: x1 and x2),  # 論理積
            "or": (lambda x1, x2: x1 or x2),  # 論理和
            "not": (lambda x: not x),  # 否定
            "band": (lambda x1, x2: int(x1) & int(x2)),  # ビット毎の and
            "bor": (lambda x1, x2: int(x1) | int(x2)),  # ビット毎の or
            "bxor": (lambda x1, x2: int(x1) ^ int(x2)),  # ビット毎の xor
            "+": (lambda x1, x2: x1 + x2),  # 加算
            "-": (lambda x1, x2: x1 - x2),  # 減算
            "*": (lambda x1, x2: x1 * x2),  # 乗算
            "/": (lambda x1, x2: x1 / x2),  # 除算
            "//": (lambda x1, x2: x1 // x2),  # 整数除算
            "%": (lambda x1, x2: x1 % x2),  # 剰余
            "^": (lambda x1, x2: math.pow(x1, x2)),  # べき乗
            "gcd": (lambda x1, x2: math.gcd(int(x1), int(x2))),  # 最大公約数
            "neg": (lambda x: -x),  # 符号反転
            "abs": (lambda x: abs(x)),  # 絶対値
            "exp": (lambda x: math.exp(x)),  # 指数関数
            "log": (lambda x: math.log(x)),  # 自然対数
            "log10": (lambda x: math.log10(x)),  # 常用対数（底が10）
            "log2": (lambda x: math.log2(x)),  # 常用対数（底が10）
            "sin": (lambda x: math.sin(x)),  # 正弦関数
            "cos": (lambda x: math.cos(x)),  # 余弦関数
            "tan": (lambda x: math.tan(x)),  # 正接関数
            "asin": (lambda x: math.asin(x)),  # アークサイン
            "acos": (lambda x: math.acos(x)),  # アークコサイン
            "atan": (lambda x: math.atan(x)),  # アークタンジェント
            "sinh": (lambda x: math.sinh(x)),  # 双曲線正弦
            "cosh": (lambda x: math.cosh(x)),  # 双曲線余弦
            "tanh": (lambda x: math.tanh(x)),  # 双曲線正接
            "asinh": (lambda x: math.asinh(x)),  # 双曲線正弦の逆関数
            "acosh": (lambda x: math.acosh(x)),  # 双曲線余弦の逆関数
            "atanh": (lambda x: math.atanh(x)),  # 双曲線正接の逆関数
            "!": (lambda x: math.factorial(int(x))),  # 階乗
            "cbrt": (lambda x: pow(x, 1/3)),  # 立方根
            "ncr": (lambda n, k: math.comb(int(n), int(k))),  # 組み合わせ (nCr)
            "npr": (lambda n, k: math.perm(int(n), int(k))),  # 順列 (nPr)
            "int2float": (lambda x: float(x)),  # 整数を浮動小数点数に変換
            "float2int": (lambda x: int(x)),  # 浮動小数点数を整数に変換
            "sqrt": (lambda x: math.sqrt(x)),  # 平方根
            "ceil": (lambda x: math.ceil(x)),    # 小数点以下を切り上げた最小の整数
            "floor": (lambda x: math.floor(x)),  # 小数点以下を切り捨てた最大の整数
            "round": (lambda x: round(x)),  # 最も近い整数に四捨五入
            "roundn": (lambda x1, x2: round(x1, int(x2))),  # 任意の桁数で丸める
        }
        self.variables = {
            "pi": math.pi,
            "e": math.e,
            "true": True,
            "false": False,
        }
        self.functions = {}
        self.reserved_word = ["help", "about", "exit"]

    def get_operators_with_n_args(self, n: int):
        # 任意の引数の数に対応する演算子の一覧を取得
        matching_operators = []

        for label, func in self.operator.items():
            if func.__code__.co_argcount == n:
                matching_operators.append(label)

        return matching_operators

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

    def apply_operator(self, token, stack):
        """
        Applies an operator to the top elements on the stack.
        Modifies the stack in-place.
        """
        if token in self.get_operators_with_n_args(n=1):
            # 引数の数nが1の演算
            if len(stack) < 1:
                raise ValueError(f"Not enough operands for operator '{token}'")
            value = stack.pop()
            stack.append(self.operator[token](value))
        else:
            if len(stack) < 2:
                raise ValueError(f"Not enough operands for operator '{token}'")
            value_2 = stack.pop()
            value_1 = stack.pop()
            stack.append(self.operator[token](value_1, value_2))

    def evaluate(self, expression, stack=None):
        """
        Evaluates a given RPN expression.
        Returns the result of the evaluation.
        """
        if stack is None:
            stack = []

        tokens = expression.split()
        for token in tokens:
            if token in self.operator:
                self.apply_operator(token, stack)
            elif token == "=>":
                continue
            elif token in self.variables:
                stack.append(self.variables[token])  # 定数をスタックにプッシュ
            elif token in self.functions:
                if len(stack) < len(self.functions[token][0]):
                    raise ValueError(f"Not enough arguments for function '{token}'")
                args = [stack.pop() for _ in range(len(self.functions[token][0]))][::-1]
                stack.append(self.evaluate_function(token, *args))
            else:
                try:
                    stack.append(float(token))
                except ValueError:
                    raise ValueError(f"Invalid token '{token}'")

        return stack

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
            return colored(f"{ans}", "green")


class ExecutionMode:
    def __init__(self, rpn_calculator):
        self.rpn_calculator = rpn_calculator

    def run(self):
        raise NotImplementedError("Subclasses must implement the 'run' method")


class InteractiveMode(ExecutionMode):
    def run(self):
        line_count = 0
        while True:
            try:
                expression = input(f"stacker:{line_count}> ")

                if expression.lower() == "exit":
                    break

                if expression.lower() == "help":
                    show_help()
                    continue

                if expression.lower() == "about":
                    show_about()
                    continue

                if expression.lower() == "clear":
                    self.rpn_calculator.clear_stack()
                    continue

                result = self.rpn_calculator.process_expression(expression)
                print(result)

            except Exception as e:
                print(colored(f"[ERROR]: {e}", "red"))
                # print("Please enter a valid RPN expression, variable assignment, or function definition.")

            line_count += 1


class ScriptMode(ExecutionMode):
    def __init__(self, rpn_calculator, filename):
        super().__init__(rpn_calculator)
        self.filename = filename

    def run(self):
        with open(self.filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    result = self.rpn_calculator.process_expression(line)
                    print(result)
                except Exception as e:
                    print(f"Error: {e}")


def main():
    show_top()

    rpn_calculator = Stacker()

    if len(sys.argv) > 1:  # 追加
        script_filename = sys.argv[1]
        # スクリプトモードの実行
        script_mode = ScriptMode(rpn_calculator, script_filename)
        script_mode.run()
    else:
        # インタラクティブモードの実行
        interactive_mode = InteractiveMode(rpn_calculator)
        interactive_mode.run()


if __name__ == "__main__":
    main()
