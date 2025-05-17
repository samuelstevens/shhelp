import dataclasses
import pathlib

import beartype
import tyro

from . import tmux, templating, config


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Query:
    msg: str


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Context:
    active: tmux.Pane
    panes: tuple[tmux.Pane, ...]

    def __init__(self):
        active, panes = tmux.get_panes()
        object.__setattr__(self, "active", active)
        object.__setattr__(self, "panes", panes)


@beartype.beartype
def cli(words: list[str], /, cfg: config.Config = config.Config()) -> int:
    """
    Ask an LLM for help with shell commands.

    Args:
        words: Your query.
    """
    import litellm

    cfg = config.load(cfg)

    if not litellm.supports_function_calling(cfg.model):
        print(f"Error: The model '{cfg.model}' does not support function calling.")
        print("Please choose a different model that supports this feature.")
        return 1

    query = " ".join(words)
    ctx = Context()

    template = templating.Template(pathlib.Path(__file__).parent / "prompt.j2")

    prompt = template.render(
        query=query,
        active_pane=ctx.active,
        panes=ctx.panes,
    )
    breakpoint()

    # while True:
    #     output, tool_calls = llm(prompt)
    #     print(


def main():
    sys.exit(tyro.cli(cli))
