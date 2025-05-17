from hypothesis import given
from hypothesis import strategies as st

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


# Property tests


# Any printable string that **does not** contain a tag opener.
plain_txt = st.text(
    alphabet=st.characters(
        blacklist_characters="",
        blacklist_categories=("Cs",),  # no surrogates
    )
).filter(lambda s: all(p not in s for p in ("{{", "{%", "{#")))


# simple python-evalable values
py_vals = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.text(min_size=0, max_size=30),
)

# literal text


@given(plain_txt)
def test_literal_roundtrip(txt):
    assert Template(txt).render() == txt


@given(plain_txt, plain_txt)
def test_literal_concat(a, b):
    tpl = f"{a}{b}"
    assert Template(tpl).render() == tpl


# variables


@given(py_vals)
def test_variable_direct(v):
    out = Template("{{ x }}").render(x=v)
    assert out == str(v)


@given(st.integers(), st.integers())
def test_variable_arithmetic(a, b):
    tpl = "{{ a + b }}"
    assert Template(tpl).render(a=a, b=b) == str(a + b)


# comments


@given(plain_txt, plain_txt)
def test_comment_elision(prefix, suffix):
    tpl = f"{prefix}{{# some comment #}}{suffix}"
    assert Template(tpl).render() == f"{prefix}{suffix}"


@given(plain_txt, plain_txt)
def test_nested_comment(prefix, suffix):
    # comments with braces inside
    tpl = f"{prefix}{{# {{}} weird #}}{suffix}"
    assert Template(tpl).render() == f"{prefix}{suffix}"


# escaping


@given(plain_txt)
def test_escape_triple_brace_random(inner):
    tpl = f"{{{{{{ {inner} }}}}}}"
    # produces "{{  ... }}" literally
    assert Template(tpl).render() == f"{{ {inner} }}"


@given(plain_txt)
def test_escape_not_interpreted(inner):
    # ensure escaped opener does NOT trigger variable parsing
    tpl = "prefix {{{{ foo }}} suffix"
    assert Template(tpl).render() == "prefix {{ foo } suffix"


# for-loops


@given(st.lists(py_vals, max_size=8))
def test_for_loop_iter(values):
    tpl = "{% for v in vals %}{{ v }} {% endfor %}"
    out = Template(tpl).render(vals=tuple(values))
    expected = " ".join(str(v) for v in values) + " " if values else ""
    assert out == expected


@given(st.lists(st.lists(st.integers(), max_size=4), max_size=4))
def test_nested_for_loops(matrix):
    tpl = "{% for row in mat %}[{% for n in row %}{{ n }}{% endfor %}]{% endfor %}"
    out = Template(tpl).render(mat=tuple(tuple(r) for r in matrix))
    expected = "".join("[" + "".join(str(n) for n in row) + "]" for row in matrix)
    assert out == expected


# if / elif / else


@given(st.integers())
def test_if_positive(n):
    tpl = "{% if n > 0 %}pos{% elif n == 0 %}zero{% else %}neg{% endif %}"
    result = Template(tpl).render(n=n)
    assert result == ("pos" if n > 0 else "zero" if n == 0 else "neg")


@given(st.tuples(st.integers(), st.integers()))
def test_if_without_else(vals):
    a, b = vals
    tpl = "{% if a == b %}equal{% endif %}"
    expected = "equal" if a == b else ""
    assert Template(tpl).render(a=a, b=b) == expected
