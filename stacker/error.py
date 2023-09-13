from __future__ import annotations


"""
SyntaxError:
This error is thrown during syntax parsing when an unexpected token is found, or an expected token is not found.
Specifically, it occurs when the input expression does not follow the grammar of the language.

UnexpectedTokenError:
A subclass of SyntaxError, this error is thrown during syntax parsing when an unexpected token is encountered.
It is associated with a specific token.

SemanticError:
This error occurs during the evaluation of an expression.
It is thrown when an operation that is syntactically correct but semantically incorrect is performed,
such as referencing an undefined variable.

RuntimeError:
This error is thrown during the execution of the program when a problem occurs in the execution environment.
It includes situations such as memory shortage or failure to access external resources.

ResourceError:
This error is associated with the allocation and release of resources.
It is thrown when necessary resources are not adequately available.

ValidationError:
This error is thrown during the validation of input values when an invalid value is detected.
It applies when the input value is not of the expected type or is outside the allowable range.

Each of these errors occurs in specific situations, enabling appropriate handling and response.

------------------------------------------------------------------------------

SyntaxError:
本エラーは、構文解析中に予期しないトークンが発見された場合、または予期したトークンが見つからなかった場合に発生する。
具体的には、入力された式が言語の文法に従っていない場合にこのエラーが投げられる。

UnexpectedTokenError:
SyntaxErrorのサブクラスであり、構文解析中に予期しないトークンが出現した場合にこのエラーが投げられる。
このエラーは具体的なトークンに関連付けられる。

SemanticError:
このエラーは、式の評価中に発生する。構文的には正しいが、意味的に不正な操作が行われたときに投げられる。
例えば、未定義の変数の参照などが該当する。

RuntimeError:
プログラムの実行中に、実行環境上の問題が生じた場合にこのエラーが投げられる。
メモリの不足、外部リソースへのアクセス失敗などが該当する。

ResourceError:
リソースの確保、解放に関連するエラーである。
必要なリソースが十分に利用できない場合などに投げられる。

ValidationError:
入力値の検証中に不正な値が検出された場合にこのエラーが投げられる。
入力値が期待する型でない、あるいは許容範囲外である場合などが該当する。


このように、各エラーはそれぞれの特定の状況で発生するもので、適切な処理と対応を可能にします。
"""


class StackerError(Exception):
    pass


class StackerSyntaxError(StackerError):
    """Syntax error"""
    def __init__(self, message):
        if message is None:
            message = "Syntax error: An error occurred while parsing the expression."
        super().__init__(message)


class UnexpectedTokenError(SyntaxError):
    """Unexpected token error"""
    def __init__(self, token, message=None):
        if message is None:
            message = f"Unexpected token: {token}"
        super().__init__(message)


class SemanticError(StackerError):
    """Semantic error"""
    def __init__(self, message=None):
        if message is None:
            message = "Semantic error: An error occurred while evaluating the expression."
        super().__init__(message)


class StackerRuntimeError(StackerError):
    """Runtime error"""
    def __init__(self, message=None):
        if message is None:
            message = "Runtime error: An error occurred during execution."
        super().__init__(message)


class ResourceError(StackerError):
    """Resource error"""
    def __init__(self, message=None):
        if message is None:
            message = "Resource error: An error occurred while allocating resources."
        super().__init__(message)


class ValidationError(StackerError):
    """Validation error"""
    def __init__(self, message=None):
        if message is None:
            message = "Validation error: An error occurred while validating the input."
        super().__init__(message)
