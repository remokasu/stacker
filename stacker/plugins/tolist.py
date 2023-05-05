
def tolist(stacker_core, start, end):
    sublist = stacker_core.stack[start:end]
    new_stack = (stacker_core.stack[:start] + [sublist] + stacker_core.stack[end:])
    stacker_core.stack = new_stack


def unlist(stacker_core, index: int) -> None:
    if not stacker_core.stack:
        raise ValueError("Stack is empty")
    if index < 0 or index >= len(stacker_core.stack):
        raise IndexError("Invalid index")

    target = stacker_core.stack[index]
    if not isinstance(target, list):
        raise TypeError("Target element is not a list")

    stacker_core.stack = stacker_core.stack[:index] + target + stacker_core.stack[index + 1 :]


def setup(stacker_core):
    stacker_core.register_plugin(
        "tolist",
        tolist,
        push_result_to_stack=False,
        pass_core=True,
        description_en="Convert a specified range within the stack into a single list element",
        description_jp="スタック内の指定された範囲を1つのリスト要素に変換する",
    )
    stacker_core.register_plugin(
        operator_name="unlist",
        operator_func=unlist,
        push_result_to_stack=False,
        pass_core=True,
        description_en="Expand the list at the specified index of the stack",
        description_jp="スタックの指定されたインデックスにあるリストを展開する",
    )
