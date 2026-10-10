"""`eval` on strings, names and other values."""

from stacker.stacker import Stacker


def run(*expressions: str) -> list[object]:
    stacker = Stacker()
    result = None
    for expression in expressions:
        result = stacker.eval(expression, stack=stacker.stack)
    return list(result)


class TestStringEval:
    """`"..." eval` used to substitute variable values while tokenizing, so
    `"6 x set x" eval` failed when `x` already existed although the same
    text worked through `read-from-string eval`."""

    def test_assignment_inside_the_string_rebinds_an_existing_variable(self):
        assert run("5 x set", '"6 x set x" eval') == [6]

    def test_string_eval_matches_read_from_string_eval(self):
        assert run("5 x set", '"x 1 +" eval') == run("5 x set", '"x 1 +" read-from-string eval')

    def test_variables_are_still_resolved(self):
        assert run("5 x set", '"x x +" eval') == [10]

    def test_lambda_held_in_a_variable_is_called_inside_the_string(self):
        # The same as writing the name in a block.
        assert run("{a} {a 1 +} lambda f set", '"5 f" eval') == [6]


class TestEvalOnValues:
    def test_eval_of_a_list_pushes_it_back(self):
        # Used to raise TypeError: unhashable type: 'list'.
        assert run("[1 2] eval") == [[1, 2]]

    def test_eval_of_a_number_pushes_it_back(self):
        assert run("5 eval") == [5]
