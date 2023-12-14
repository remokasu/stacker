from __future__ import annotations


def py_compile(code, filename: str = ""):
    obj = compile(code, filename, "exec")
    return obj


def py_eval(code: str, filename: str = "", globals=None, locals=None):
    obj = py_compile(code, filename)
    if globals is None and locals is None:
        return eval(obj)
    elif globals is None:
        return eval(obj, locals)
    elif locals is None:
        return eval(obj, globals)


if __name__ == "__main__":
    code = "import numpy as np"
    print(py_eval(code))
    code = "np.pi"
    print(py_eval(code))
