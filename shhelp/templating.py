import pathlib

import beartype
import jinja2

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent),
    autoescape=jinja2.select_autoescape(),
)


@beartype.beartype
def load(path: str | pathlib.Path):
    template = env.get_template(str(path))
    return template
