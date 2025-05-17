import pytest

from .templating import Token, lex


def toks(src):
    """Helper → materialise iterator minus trailing EOF for brevity."""
    ts = list(lex(src))
    assert ts[-1] == Token("EOF", "")
    return ts[:-1]


def test_text_only():
    assert toks("hello") == [Token("TEXT", "hello")]


def test_mixed_text_and_var():
    src = "hi {{ name }}."
    expect = [
        Token("TEXT", "hi "),
        Token("VAR", " name "),
        Token("TEXT", "."),
    ]
    assert toks(src) == expect


def test_for_stmt_tokens():
    src = "{% for x in seq %}body{% endfor %}"
    expect = [
        Token("STMT", "for x in seq"),
        Token("TEXT", "body"),
        Token("STMT", "endfor"),
    ]
    assert toks(src) == expect


def test_comment_elided():
    src = "a{# skip #}b"
    assert toks(src) == [Token("TEXT", "a"), Token("TEXT", "b")]


def test_triple_brace_escape():
    src = "{{{ not_var }}"
    # lexer should output literal '{{' then the rest as text
    assert toks(src)[0] == Token("TEXT", "{{")


def test_unclosed_var_raises():
    with pytest.raises(SyntaxError):
        list(lex("{{ unclosed"))
