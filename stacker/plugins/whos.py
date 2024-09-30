# from stacker.stacker import Stacker


# def whos(stacker):
#     labels = ["Name", "Size", "Class"]
#     names = stacker.variables.keys()
#     for label in labels:
#         print(f"{label}\t", end="")
#     print("")
#     for name in names:
#         _value = stacker.variables[name]
#         _type = str(type(_value))
#         _size = 1
#         if isinstance(_value, list) or isinstance(_value, tuple):
#             try:
#                 # n dim (n > 1)
#                 _size = [len(v) for v in _value]
#             except TypeError:
#                 # 1 dim
#                 _size = len(_value)
#         print(f"{name}\t{_size}\t{_type}")


# def setup(stacker: Stacker):
#     stacker.register_plugin(
#         operator_name="whos",
#         operator_func=whos,
#         push_result_to_stack=False,
#         pass_core=True,
#         desc="Show the variables in the stacker",
#     )


def setup(stacker):
    pass
