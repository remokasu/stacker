# Description is optional.
# descriptionの指定は任意です。

description_en = (
    "Change the output color to any desired color\n"
    "\tSupported colors:\n"
    "\tblack, red, green, yellow, blue, magenta, cyan, lightgray\n"
    "\tdarkgray, lightred, lightgreen, lightyellow, lightblue\n"
    "\tlightmagenta, lightcyan, white\n"
    "\t(example) > red set_color"
)

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
