"""
Lightweight Jinja2 alternative.

* *literal text*: everything not inside tags (unchanged)
* *variable*: `{{ expr }}` (any valid Python eval in the provided context; output str(expr))
* *for loops*: `{% for x in seq %} ... {% endfor %}` (nested allowed)
* *if/elif/else*: `{% if cond %} ... {% elif cond2 %} ... {% else %} ... {% endif %}` (nested allowed)
* *comment*: `{# ... #}` (discarded)
* *escaping*: `{{{` renders `{{`; raw block not supported
"""

from pathlib import Path

import beartype


@beartype.beartype
class Template:
    """Very small template engine."""

    def __init__(self, path_or_str: str):
        path = Path(path_or_str)
        text: str
        try:
            text = (
                path.read_text()
                if len(path_or_str) < 256 and path.is_file()
                else path_or_str
            )
        except OSError:
            text = path_or_str
        self._text = text
        self._code = self._compile(self._text)

    def _compile(self, src: str) -> str:
        lines: list[str] = ["__out = []"]
        indent = 0
        i = 0
        n = len(src)
        while i < n:
            if src.startswith("{{{", i):
                j = src.find("}}}", i + 3)
                if j != -1:
                    lit = "{" + src[i + 3 : j] + "}"
                    lines.append("    " * indent + f"__out.append({lit!r})")
                    i = j + 3
                else:
                    lines.append("    " * indent + "__out.append('{{')")
                    i += 3
                continue
            if src.startswith("{{", i):
                j = src.find("}}", i + 2)
                if j == -1:
                    lit = src[i:]
                    lines.append("    " * indent + f"__out.append({lit!r})")
                    break
                expr = src[i + 2 : j].strip()
                lines.append("    " * indent + f"__out.append(str({expr}))")
                i = j + 2
                continue
            if src.startswith("{#", i):
                j = src.find("#}", i + 2)
                if j == -1:
                    break
                i = j + 2
                continue
            if src.startswith("{%", i):
                j = src.find("%}", i + 2)
                if j == -1:
                    break
                inner = src[i + 2 : j].strip()
                if inner.startswith("for "):
                    lines.append("    " * indent + inner + ":")
                    indent += 1
                elif inner == "endfor":
                    indent -= 1
                elif inner.startswith("if "):
                    lines.append("    " * indent + inner + ":")
                    indent += 1
                elif inner.startswith("elif "):
                    indent -= 1
                    lines.append("    " * indent + inner + ":")
                    indent += 1
                elif inner == "else":
                    indent -= 1
                    lines.append("    " * indent + "else:")
                    indent += 1
                elif inner == "endif":
                    indent -= 1
                else:
                    raise SyntaxError(f"unknown tag: {inner}")
                i = j + 2
                continue
            next_brace = src.find("{", i)
            if next_brace == -1:
                lit = src[i:]
                lines.append("    " * indent + f"__out.append({lit!r})")
                break
            if next_brace > i:
                lit = src[i:next_brace]
                lines.append("    " * indent + f"__out.append({lit!r})")
            i = next_brace
        lines.append("__result = ''.join(__out)")
        return "\n".join(lines)

    def render(self, **kwargs) -> str:
        env = dict(kwargs)
        exec(self._code, {}, env)
        return env["__result"]
