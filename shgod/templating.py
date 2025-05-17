"""
Lightweight Jinja2 alternative.

* *literal text*: everything not inside tags (unchanged)
* *variable*: `{{ expr }}` (any valid Python eval in the provided context; output str(expr))
* *for loops*: `{% for x in seq %} ... {% endfor %}` (nested allowed)
* *if/elif/else*: `{% if cond %} ... {% elif cond2 %} ... {% else %} ... {% endif %}` (nested allowed)
* *comment*: `{# ... #}` (discarded)
* *escaping*: `{{{` renders `{{`; raw block not supported
"""

import beartype


@beartype.beartype
class Template:
    def __init__(self, path_or_str: str): ...

    def render(self, **kwargs) -> str: ...
