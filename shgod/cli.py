import dataclasses
import json
import os
import pathlib
import sys

import beartype
import litellm
import tyro

from . import config, llms, templating, tmux, tooling, ui


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
        shell = shell or os.getenv("SHELL", "")

        # Get shell aliases
        aliases = ()
        try:
            # Run shell in interactive mode to get aliases
            alias_cmd = [shell, "-ic", "alias"]
            alias_output = subprocess.check_output(
                alias_cmd, text=True, stderr=subprocess.DEVNULL
            ).strip()
            if alias_output:
                aliases = tuple(alias_output.splitlines())
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fallback if getting aliases fails
            pass

        object.__setattr__(self, "active", active)
        object.__setattr__(self, "panes", panes)
        object.__setattr__(self, "system", system)
        object.__setattr__(self, "shell", shell)
        object.__setattr__(self, "aliases", aliases)


@beartype.beartype
def cli(words: list[str], /, cfg: config.Config = config.Config()) -> int:
    """
    Ask an LLM for help with shell commands.

    Args:
        words: Your query.
    """

    cfg = config.load(cfg)

    if not litellm.supports_function_calling(cfg.model):
        print(f"Error: The model '{cfg.model}' does not support function calling.")
        print("Please choose a different model that supports this feature.")
        return 1

    query = " ".join(words)
    ctx = Context()
    template = templating.Template(pathlib.Path(__file__).parent / "prompt.j2")

    system = template.render(
        active_pane=ctx.active,
        # panes=ctx.panes,
        system=ctx.system,
        shell=ctx.shell,
        aliases=ctx.aliases,
    )

    conversation = llms.Conversation(model=cfg.model, api_key=cfg.api_key)
    conversation.system(system)
    conversation.user(query)

    while True:
        toks, usd = conversation.get_costs()
        if not ui.confirm_next_request(toks, usd):
            return 0

        msg = conversation.send(
            tools=tooling.get_tool_specs(),
        )

        # Print agent response.
        ui.echo(msg.content.strip())

        if not msg.tool_calls:
            # Print total session cost.
            return 0

        deny_notes = []
        for tc in msg.tool_calls:
            try:
                kwargs = json.loads(tc.function.arguments)
                tool = tooling.get_tool(tc.function.name)(**kwargs)
                if ui.confirm(f"Run tool {tc.function.name}: <cmd>{tool}</cmd>?"):
                    result = tool()
                    ui.echo(result)
                    conversation.tool(result, tool_call_id=tc.id)
                else:
                    note = ui.ask_tool_skip_reason(tc.function.name)
                    deny_notes.append(f"{tc.function.name}: {note}")
                    conversation.tool(f"denied by user: {note}", tool_call_id=tc.id)
            except Exception as err:
                conversation.tool(str(err), tool_call_id=tc.id)
                ui.echo(f"<warn>Error:</warn> {err}")

        if deny_notes:
            conversation.user("\n".join(deny_notes))


def main():
    sys.exit(tyro.cli(cli))
