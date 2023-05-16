from stacker.stacker import Stacker


def branch_command(true_block, false_block, condition: bool):
    if condition:
        return true_block
    else:
        return false_block


def setup(stacker: Stacker):
    stacker.register_plugin(
        "branch",
        branch_command,
        description_en="Execute true_block if condition is True, else execute false_block."
    )
