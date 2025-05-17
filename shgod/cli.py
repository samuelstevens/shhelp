import dataclasses

import beartype
import tyro

from . import tmux


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Query:
    msg: str


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Context:
    pane: tmux.Pane
    other_panes: tuple[tmux.Pane, ...]

    def __init__(self):
        pane, others = tmux.get_panes()
        object.__setattr__(self, "pane", pane)
        object.__setattr__(self, "other_panes", others)


@beartype.beartype
def ask(words: list[str], /):
    """
    Ask an LLM for help with shell commands.

    Args:
        words: Your query.
    """
    ctx = Context()
    breakpoint()


def main():
    tyro.cli(ask)
