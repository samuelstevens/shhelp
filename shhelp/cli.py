import sys
import typing

import beartype
import tyro

from . import config


@beartype.beartype
def cli(
    words: list[str],
    /,
    cfg: typing.Annotated[config.Config, tyro.conf.arg(name="")] = config.Config(),
    context: bool = True,
) -> int:
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
    # Need templating
    from . import templating, tmux

    template = templating.load("prompt.j2")
    ctx = tmux.Context()

    system = template.render(
        active_pane=ctx.active,
        panes=ctx.panes,
        system=ctx.system,
        shell=ctx.shell,
        aliases=ctx.aliases,
        context=context,
    )

    # Need llms
    from . import llms

    conversation = llms.Conversation(model=cfg.model, api_key=cfg.api_key)
    conversation.system(system)
    conversation.user(query)

    # Need ui.
    from . import ui

    while True:
        toks, usd = conversation.get_costs()
        if not ui.confirm_next_request(toks, usd):
            return 0

        msg = conversation.send(tools=[])

        # Print agent response.
        ui.echo(msg.content.strip())

        if not msg.tool_calls:
            return 0


def main():
    sys.exit(tyro.cli(cli))
