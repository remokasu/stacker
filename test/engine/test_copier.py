"""Tests for the shallow copier of interpreter cores: the generated one and the dictionary update."""

import sys

import pytest

from stacker import Stacker
from stacker.engine import copier
from stacker.engine.data_type import String

WAYS = [copier.by_generated_copier, copier.by_dictionary_update]
#: how many attributes a core has; CPython shares the attribute keys of a class's instances only up to 30
CORE_ATTRIBUTES = 29


@pytest.fixture(autouse=True)
def fresh_copiers(monkeypatch):
    """Each test sees the generated copiers of its own shapes only."""
    monkeypatch.setattr(copier, "_copiers", {})


@pytest.fixture
def root():
    return Stacker()


@pytest.fixture
def child(root):
    """A block core: a child of the root, one attribute fewer than it."""
    return next(iter(root.eval("{1 2 +}")))


@pytest.fixture
def function_body(root):
    root.process_expression("{x} {x 1 +} :inc defun")
    return root.sfunctions["inc"]["func"].blockstack


@pytest.fixture
def lambda_body(root):
    return next(iter(root.eval("{x} {x 1 +} lambda"))).blockstack


def assert_same_as_dictionary_update(core, new):
    assert new is not core
    assert type(new) is type(core)
    assert new.__dict__.keys() == core.__dict__.keys()
    for name, value in core.__dict__.items():
        assert new.__dict__[name] is value, name


def add_nfkc_pair(core):
    core.file = 1
    setattr(core, "ﬁle", 2)  # noqa: B010  written as source, the ligature would be folded into `file`


RESHAPES = [
    pytest.param(lambda core: setattr(core, "added_by_a_plugin", object()), id="an attribute added later"),
    pytest.param(lambda core: delattr(core, "has_result"), id="an attribute removed"),
    pytest.param(lambda core: setattr(core, "not an identifier", 1), id="name that is not an identifier"),
    pytest.param(lambda core: setattr(core, "class", 2), id="keyword as a name"),
    pytest.param(lambda core: setattr(core, "__debug__", 1), id="name that cannot be assigned"),
    pytest.param(lambda core: core.__dict__.__setitem__("__dict__", {}), id="descriptor's name"),
    pytest.param(add_nfkc_pair, id="two spellings of one identifier"),
    pytest.param(lambda core: core.__dict__.__setitem__(1, "one"), id="key that is not a string"),
    pytest.param(lambda core: setattr(core, String("named"), 1), id="key of a string subclass"),
    pytest.param(lambda core: setattr(core, "process_expression", "shadowed"), id="a method's name"),
]


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("which", ["root", "child", "function_body", "lambda_body"])
def test_a_copy_holds_the_same_attributes_as_the_dictionary_update_would(way, which, request):
    core = request.getfixturevalue(which)
    assert_same_as_dictionary_update(core, way(core))


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("reshape", RESHAPES)
def test_a_shape_a_plugin_made_odd_is_copied_as_the_dictionary_update_would(way, reshape, child):
    reshape(child)
    assert_same_as_dictionary_update(child, way(child))


@pytest.mark.parametrize("way", WAYS)
def test_a_copy_shares_the_tokens_and_the_tables_but_is_a_distinct_object(way, child):
    new = way(child)
    assert new.tokens is child.tokens
    assert new.variables is child.variables
    assert new.sfunctions is child.sfunctions
    new.stack = object()  # the caller's own stack does not reach the original
    assert child.stack is not new.stack


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.skipif(not hasattr(sys, "getrefcount"), reason="no reference counts to look at")
@pytest.mark.skipif(not getattr(sys, "_is_gil_enabled", lambda: True)(), reason="reference counts are not exact")
def test_nothing_keeps_a_reference_to_the_copy(way, child):
    probe = object()
    new = way(child)
    assert sys.getrefcount(new) == sys.getrefcount(probe)


@pytest.mark.parametrize(
    ("implementation", "version", "gil_enabled", "generated"),
    [
        ("pypy", (3, 11), True, True),
        ("cpython", (3, 13), True, True),
        ("cpython", (3, 14), True, True),
        ("cpython", (3, 12), True, False),
        ("cpython", (3, 10), True, False),
        ("cpython", (3, 13), False, False),
    ],
)
def test_which_hosts_copy_by_the_generated_copier(implementation, version, gil_enabled, generated):
    assert copier.prefers_generated_copier(implementation, version, gil_enabled) is generated


def test_blocks_functions_and_lambdas_are_copied_through_the_module_attribute(monkeypatch):
    # the test session checks every copy by replacing that attribute: a call site
    # holding the function itself would slip past the check
    stacker = Stacker()
    copies = []
    original = copier.shallow_copy
    monkeypatch.setattr(copier, "shallow_copy", lambda core: copies.append(core) or original(core))
    for program in ("{x} {x} :f defun 1 f", "{x} {x} lambda :g set 1 g eval", "1 3 :i {i} do"):
        copies.clear()
        stacker.eval(program)
        assert copies, program


# --- the generated copier ---


def test_the_root_and_a_child_have_the_same_shape_and_share_one_copier(root, child):
    copier.by_generated_copier(root)
    copier.by_generated_copier(child)
    assert len(root.__dict__) == len(child.__dict__) == CORE_ATTRIBUTES
    shapes = copier._copiers[Stacker]
    assert list(shapes) == [CORE_ATTRIBUTES] and shapes[CORE_ATTRIBUTES] is not None


def test_two_shapes_with_as_many_attributes_get_copiers_by_count(root, child):
    child.added = 1
    copier.by_generated_copier(root)
    copier.by_generated_copier(child)
    shapes = copier._copiers[Stacker]
    assert sorted(shapes) == [CORE_ATTRIBUTES, CORE_ATTRIBUTES + 1] and shapes[CORE_ATTRIBUTES] is not shapes[CORE_ATTRIBUTES + 1]


@pytest.mark.parametrize("which", ["root", "child"])
def test_the_generated_copier_copies_its_own_shape_without_falling_back(which, request):
    core = request.getfixturevalue(which)
    copier.by_generated_copier(core)
    new = object.__new__(Stacker)
    copier._copiers[Stacker][len(core.__dict__)](core, new)  # an AttributeError here means every copy falls back
    assert_same_as_dictionary_update(core, new)


def test_a_shape_with_as_many_attributes_under_other_names_falls_back_to_the_dictionary_update(child):
    copier.by_generated_copier(child)  # the child's shape has its copier
    del child.has_result
    child.other = 1  # as many attributes, one of them unknown to that copier
    assert_same_as_dictionary_update(child, copier.by_generated_copier(child))


def test_a_shape_naming_a_method_does_not_lend_the_method_to_another_shape(root):
    # with as many attributes, a block holding a method's name would otherwise give the
    # other block's copy that method in place of the attribute it lacks
    first, second = next(iter(root.eval("{1}"))), next(iter(root.eval("{2}")))
    first.process_expression = "shadowed"
    second.other = 1
    assert len(first.__dict__) == len(second.__dict__)
    copier.by_generated_copier(first)
    assert_same_as_dictionary_update(second, copier.by_generated_copier(second))


def test_a_shape_is_generated_once_whether_or_not_it_got_a_copier(child, monkeypatch):
    odd = next(iter(Stacker().eval("{1}")))
    odd.__dict__[1] = "one"
    copier._copiers.clear()  # whatever making the cores copied is forgotten
    calls = []
    generate = copier._generate
    monkeypatch.setattr(copier, "_generate", lambda cls, names: calls.append(names) or generate(cls, names))
    for _ in range(3):
        copier.by_generated_copier(child)
        copier.by_generated_copier(odd)
    assert len(calls) == 2


def test_a_shape_without_attributes_gets_a_copier_that_does_nothing(child):
    new = object.__new__(Stacker)
    copier._generate(Stacker, ())(child, new)
    assert new.__dict__ == {}


@pytest.mark.parametrize(
    ("name", "writable"),
    [
        ("tokens", True),
        ("_bound_cache", True),
        ("a.b", False),
        ("x; y", False),
        ("1x", False),
        ("class", False),
        ("match", True),
        ("__dict__", False),
        ("__debug__", False),
        ("ﬁle", False),
        ("process_expression", False),
        (1, False),
        (String("tokens"), False),
    ],
)
def test_which_names_the_generated_source_may_hold(name, writable):
    assert copier._writable(name, Stacker) is writable


# --- the check the test session runs on every copy ---


def test_every_copy_of_the_session_goes_through_the_check():
    assert copier.shallow_copy.__name__ == "checked"


def test_the_check_catches_a_copy_that_lacks_an_attribute(child, shallow_copy_check):
    new = copier.by_dictionary_update(child)
    del new.trace
    with pytest.raises(pytest.fail.Exception, match=r"lacks \['trace'\]"):
        shallow_copy_check(child, new)


def test_the_check_catches_a_copy_whose_attribute_is_another_object(child, shallow_copy_check):
    new = copier.by_dictionary_update(child)
    new.trace = list(child.trace)
    with pytest.raises(pytest.fail.Exception, match="`trace` is not the original's object"):
        shallow_copy_check(child, new)


def test_functions_and_bound_blocks_still_compute_the_same_values():
    stacker = Stacker()
    assert list(stacker.eval("{n} {n 2 < {n} {n 1 - fib n 2 - fib +} ifelse} :fib defun 10 fib")) == [55]
    assert list(stacker.eval("0 :acc set 1 10 :i {acc i + :acc set} do acc")) == [55]
    closures = "[] array :fs set 1 3 :i {{i} fs append!} do fs {eval} map 0 :acc :x {acc x +} reduce"
    assert list(stacker.eval(closures)) == [6]
