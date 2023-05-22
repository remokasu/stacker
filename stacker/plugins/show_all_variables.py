from stacker.stacker import Stacker


def show_all_valiables(stacker):
    for key in stacker.variables.keys():
        print(f"{key} = {stacker.variables[key]}")


def setup(stacker: Stacker):
    stacker.register_plugin(
        operator_name="show_all_valiables",
        operator_func=show_all_valiables,
        push_result_to_stack=False,
        pass_core=True
    )
