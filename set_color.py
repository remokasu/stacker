# To create a plugin for Stacker, follow these steps:

# 1. Create a new Python file (e.g., `my_plugin.py`) in the `plugins` directory.
# 2. Define any functions or classes required for your plugin.
# 3. Define a `setup` function in your plugin file that takes a single argument: `stacker_core`.
# 4. In the `setup` function, use the `register_plugin` method of `stacker_core` to register your custom commands. For example:

# description_en = "Returns the Collatz sequence for the given number."
# description_jp = "与えられた数値のコラッツ数列を返します。"

# def collatz_sequence(n):
#     seq = [n]
#     while n != 1:
#         if n % 2 == 0:
#             n //= 2
#         else:
#             n = n * 3 + 1
#         seq.append(n)
#     return seq

# def setup(stacker_core):
#     stacker_core.register_plugin(
#         "collatz", lambda x: collatz_sequence(x),
#         description_en=description_en,  #  Please comment out if not necessary.
#         description_jp=description_jp   #  不要な場合はコメントアウト
#     )

# 5. Reinstall Stacker by running the following command:

# python setup.py install

# 5. Save your plugin file in the plugins directory.
# 6. When Stacker starts, it will automatically load your plugin, and your custom command will be available for use.
# =================================================================================



# Description is optional.
description_en = (
    "Change the output color to any desired color\n"
    "\tSupported colors:\n"
    "\tblack, red, green, yellow, blue, magenta, cyan, lightgray\n"
    "\tdarkgray, lightred, lightgreen, lightyellow, lightblue\n"
    "\tlightmagenta, lightcyan, white\n"
    "\t(example) > red set_color"
)

# descriptionの指定は任意です。
description_jp = (
    "出力の色を任意の色に変更\n"
    "\t対応している色：\n"
    "\tblack, red, green, yellow blue magenta cyan lightgray \n"
    "\ttdarkgray lightred lightgreen lightyellow lightblue \n"
    "\tlightmagenta lightcyan white\n"
    "\t(example) > red set_color"
)


def setup(stacker_core):
    def _set_color(color):
        stacker_core.stack_color = color
    stacker_core.register_plugin(
        "set_color", lambda color: _set_color(color),
        description_en=description_en,  #  Please comment out if not necessary.
        description_jp=description_jp   #  不要な場合はコメントアウト
    )
