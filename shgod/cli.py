import dataclasses
import os
import pathlib
import sys

import beartype
import tyro

from . import config, templating, tmux, tooling


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Query:
    msg: str


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Context:
    active: tmux.Pane
    panes: tuple[tmux.Pane, ...]
    system: str
    shell: str
    aliases: tuple[str, ...]

    def __init__(self, shell: str | None = None):
        import subprocess

        active, panes = tmux.get_panes()
        system = subprocess.check_output(["uname", "-a"], text=True).strip()
        shell_value = shell or os.environ.get("SHELL", "")
        # Use $SHELL -ic alias to get the aliases available for use. AI!

        object.__setattr__(self, "active", active)
        object.__setattr__(self, "panes", panes)
        object.__setattr__(self, "system", system)
        object.__setattr__(self, "shell", shell_value)
        object.__setattr__(self, "aliases", aliases)


@beartype.beartype
def cli(words: list[str], /, cfg: config.Config = config.Config()) -> int:
    """
    Ask an LLM for help with shell commands.

    Args:
        words: Your query.
    """

    cfg = config.load(cfg)

    import litellm

    if not litellm.supports_function_calling(cfg.model):
        print(f"Error: The model '{cfg.model}' does not support function calling.")
        print("Please choose a different model that supports this feature.")
        return 1

    query = " ".join(words)
    ctx = Context()

    template = templating.Template(pathlib.Path(__file__).parent / "prompt.j2")

    system = template.render(active_pane=ctx.active, panes=ctx.panes)

    while True:
        completion = litellm.completion(
            model=cfg.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ],
            tools=tooling.get_tool_schemas(),
        )
        breakpoint()


def main():
    sys.exit(tyro.cli(cli))
