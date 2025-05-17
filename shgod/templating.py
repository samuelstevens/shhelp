"""
Lightweight Jinja2 alternative.

* *literal text*: everything not inside tags (unchanged)
* *variable*: `{{ expr }}` (any valid Python eval in the provided context; output str(expr))
* *for loops*: `{% for x in seq %} ... {% endfor %}` (nested allowed)
* *if/elif/else*: `{% if cond %} ... {% elif cond2 %} ... {% else %} ... {% endif %}` (nested allowed)
* *comment*: `{# ... #}` (discarded)
* *escaping*: `{{{` renders `{{`; raw block not supported
"""

import collections.abc
import dataclasses
import pathlib
import beartype


@beartype.beartype
class Template:
    """Tiny subset-of-Jinja renderer.

    Parameters
    ----------
    path_or_str :
        Either raw template text or a filesystem path.
    """

    def __init__(self, path_or_str: str):
        path = pathlib.Path(path_or_str)
        txt = path.read_text() if path.exists() else path_or_str
        self._ast = Parser(lex(txt)).parse()

    def render(self, **kwargs) -> str:
        return "".join(n.render(dict(kwargs)) for n in self._ast)


# lexer


TOK_OPEN_VAR = "{{"
TOK_OPEN_STMT = "{%"
TOK_OPEN_COMM = "{#"
TOK_CLOSE_VAR = "}}"
TOK_CLOSE_STMT = "%}"
TOK_CLOSE_COMM = "#}"


@dataclasses.dataclass(frozen=True)
class Token:
    typ: str
    text: str


@beartype.beartype
def lex(src: str) -> collections.abc.Iterator[Token]:
    i, n = 0, len(src)
    while i < n:
        if src.startswith("{{{", i):  # escape
            yield Token("TEXT", "{{")
            i += 3
            continue

        if src.startswith(TOK_OPEN_VAR, i):
            j = src.find(TOK_CLOSE_VAR, i + 2)
            if j == -1:
                raise SyntaxError("unclosed {{")
            yield Token("VAR", src[i + 2 : j])
            i = j + 2
        elif src.startswith(TOK_OPEN_STMT, i):
            j = src.find(TOK_CLOSE_STMT, i + 2)
            if j == -1:
                raise SyntaxError("unclosed {%")
            yield Token("STMT", src[i + 2 : j].strip())
            i = j + 2
        elif src.startswith(TOK_OPEN_COMM, i):
            j = src.find(TOK_CLOSE_COMM, i + 2)
            if j == -1:
                raise SyntaxError("unclosed {#")
            i = j + 2  # discard
        else:  # literal
            j = src.find("{", i)
            yield Token("TEXT", src[i : j if j != -1 else n])
            i = j if j != -1 else n
    yield Token("EOF", "")


@beartype.beartype
class Node:
    # base class
    def render(self, ctx: dict[str, object]) -> str:
        raise NotImplementedError


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Text(Node):
    val: str

    def render(self, ctx):
        return self.val


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Var(Node):
    expr: str

    def render(self, ctx):
        return str(eval(self.expr, {}, ctx))


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class For(Node):
    var: str
    seq: str
    body: collections.abc.Sequence[Node]

    def render(self, ctx):
        out = []
        for item in eval(self.seq, {}, ctx):
            ctx[self.var] = item
            out.append("".join(n.render(ctx) for n in self.body))
        return "".join(out)


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class If(Node):
    branches: list[tuple[str | None, collections.abc.Sequence[Node]]] = (
        dataclasses.field(default_factory=list)
    )

    def render(self, ctx):
        for cond, body in self.branches:
            if cond is None or eval(cond, {}, ctx):
                return "".join(n.render(ctx) for n in body)
        return ""


@beartype.beartype
class Parser:
    def __init__(self, tokens: collections.abc.Iterable[Token]):
        self._toks = iter(tokens)
        self._next()

    def _next(self):
        self.cur = next(self._toks)

    def parse(self) -> list[Node]:
        nodes = []
        while self.cur.typ != "EOF":
            if self.cur.typ == "TEXT":
                nodes.append(Text(self.cur.text))
                self._next()
            elif self.cur.typ == "VAR":
                nodes.append(Var(self.cur.text.strip()))
                self._next()
            elif self.cur.typ == "STMT":
                cmd = self.cur.text
                if cmd.startswith("for "):
                    nodes.append(self._parse_for())
                elif cmd.startswith("if "):
                    nodes.append(self._parse_if())
                elif cmd == "endif" or cmd == "endfor":
                    break
                else:
                    raise SyntaxError(f"unknown stmt {cmd!r}")
            else:
                raise SyntaxError(f"unexpected token {self.cur}")
        return nodes

    # --- helpers ---
    def _parse_for(self):
        _, var, _, seq = self.cur.text.split(None, 3)  # "for x in seq"
        self._next()
        body = self.parse()
        if self.cur.text != "endfor":
            raise SyntaxError("missing endfor")
        self._next()
        return For(var, seq, body)

    def _parse_if(self):
        branches: list[tuple[str | None, collections.abc.Sequence[Node]]] = []
        cond = self.cur.text[3:].strip()  # after "if "
        self._next()
        branches.append((cond, self.parse()))
        while self.cur.text.startswith("elif "):
            cond = self.cur.text[5:].strip()
            self._next()
            branches.append((cond, self.parse()))
        if self.cur.text == "else":
            self._next()
            branches.append((None, self.parse()))
        if self.cur.text != "endif":
            raise SyntaxError("missing endif")
        self._next()
        return If(branches)
