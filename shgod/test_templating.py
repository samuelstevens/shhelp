import pytest

from .templating import Template

# literals


def test_literal_passthrough():
    src = "no tags here"
    assert Template(src).render() == "no tags here"


# variables


def test_variable_simple():
    out = Template("hello {{ name }}!").render(name="bob")
    assert out == "hello bob!"


def test_variable_expr_whitespace():
    src = "{{ 1 + 1 }}"
    assert Template(src).render() == "2"


def test_variable_undefined_raises():
    with pytest.raises(NameError):
        Template("{{ missing }}").render()


# comments


def test_comment_stripped():
    src = "a{# noisy #}b"
    assert Template(src).render() == "ab"


# escaping


def test_escape_triple_brace():
    src = "{{{ not_a_tag }}"
    assert Template(src).render() == "{{ not_a_tag }}"


# for-loops


def test_for_loop_basic():
    tpl = "{% for x in seq %}[{{ x }}]{% endfor %}"
    assert Template(tpl).render(seq=[1, 2, 3]) == "[1][2][3]"


def test_for_loop_nested_shadow():
    tpl = "{% for x in outer %}{% for x in inner %}{{ x }}{% endfor %}{% endfor %}"
    assert Template(tpl).render(outer=[0, 1], inner=["a"]) == "aa"
