import dataclasses
import json
import os
import pathlib
import sys

import beartype
import tyro
from rich import print

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
        shell = shell or os.environ.get("SHELL", "")

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

    import litellm

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

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]

    while True:
        resp = litellm.completion(
            model=cfg.model,
            messages=messages,
            tools=tooling.get_tool_specs(),
            api_key=cfg.api_key,
        )

        msg = resp.choices[0].message
        tcs = msg.tool_calls or []

        # Print agent response.
        print(msg.content.strip())

        if not tcs:
            return 0

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": msg.tool_calls,
        })

        for tc in tcs:
            tool = tooling.get_tool(tc.function.name)
            if not tool.read_only:
                breakpoint()

            try:
                kwargs = json.loads(tc.function.arguments)
                print(f"Calling tool: [bold blue]{tool.name}[/bold blue]:")
                print(tool)
                result = tool(**kwargs)
                print(result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            except Exception as err:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(err),
                })
                print(f"[bold red]Error:[/bold red] {err}")
                if input("Do you want to continue? (y/n): ").lower() != "y":
                    return 1


def main():
    sys.exit(tyro.cli(cli))
