from __future__ import annotations


list_operators = {
    "seq": {
        "func": (lambda x1, x2: list(range(x1, x2 + 1))),
        "arg_count": 2,
        "push_result_to_stack": True,
        "desc": "Generate sequence from x1 to x2",
    },
    # "range": {
    #     "func": (lambda x1, x2: range(x1, x2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Generate range from x1 to x2",
    # },
    # "append": {
    #     "func": (lambda xs, x: xs.append(x)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Append value to list",
    # },
    # "extend": {
    #     "func": (lambda xs1, xs2: xs1.extend(xs2)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Extend list",
    # },
    # "insert": {
    #     "func": (lambda xs, i, x: xs.insert(i, x)),
    #     "arg_count": 3,
    #     "push_result_to_stack": True,
    #     "desc": "Insert value into list",
    # },
    # "reverse": {
    #     "func": (lambda xs: xs.reverse()),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "Reverse list",
    # },
    # "sort": {
    #     "func": (lambda xs: xs.sort()),
    #     "arg_count": 1,
    #     "push_result_to_stack": True,
    #     "desc": "Sort list",
    # },
    # "count": {
    #     "func": (lambda xs, x: xs.count(x)),
    #     "arg_count": 2,
    #     "push_result_to_stack": True,
    #     "desc": "Count value in list",
    # },
}
