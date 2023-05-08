from stacker.stacker import Stacker


def branch_command(condition, true_block, false_block):
    if condition:
        return true_block
    else:
        return false_block


def setup(stacker_core: Stacker):
    stacker_core.register_plugin(
        "branch",
        branch_command,
        description_en="Execute true_block if condition is True, else execute false_block."
    )
