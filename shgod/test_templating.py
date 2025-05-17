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


# if / elif / else


def test_if_true_branch():
    tpl = "{% if ok %}yes{% else %}no{% endif %}"
    assert Template(tpl).render(ok=True) == "yes"


def test_if_false_no_else():
    tpl = "{% if ok %}yes{% endif %}done"
    assert Template(tpl).render(ok=False) == "done"


def test_if_elif_else_chain():
    tpl = "{% if n==0 %}zero{% elif n==1 %}one{% else %}many{% endif %}"
    assert Template(tpl).render(n=7) == "many"


# interaction of loops and conditionals


def test_loop_with_inner_if_else():
    tpl = "{% for x in seq %}{% if x > 1 %}{{ x }}{% else %}-{% endif %}{% endfor %}"
    assert Template(tpl).render(seq=[0, 1, 2]) == "--2"


def test_loop_in_each_if_branch():
    tpl = "{% if show %}{% for x in seq %}{{ x }}{% endfor %}{% else %}{% for x in other %}{{ x }}{% endfor %}{% endif %}"
    assert Template(tpl).render(show=True, seq=[1], other=[2]) == "1"
    assert Template(tpl).render(show=False, seq=[1], other=[2]) == "2"


def test_loop_variable_scope_with_if():
    tpl = "{{ x }}{% for x in seq %}{% if True %}{{ x }}{% endif %}{% endfor %}{{ x }}"
    assert Template(tpl).render(x="a", seq=["b"]) == "abba"


def test_nested_loops_with_if():
    tpl = "{% for x in outer %}{% if x %}{% for y in inner %}{{ y }}{% endfor %}{% else %}x{% endif %}{% endfor %}"
    assert Template(tpl).render(outer=[0, 1], inner=["z"]) == "xz"


def test_if_around_loop_and_else_loop():
    tpl = "{% if ok %}{% for x in seq %}{{ x }}{% endfor %}{% else %}{% for x in seq %}-{% endfor %}{% endif %}"
    assert Template(tpl).render(ok=True, seq=[1, 2]) == "12"
    assert Template(tpl).render(ok=False, seq=[1, 2]) == "--"
