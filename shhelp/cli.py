import asyncio
import contextlib
import json
import sys
import typing

import beartype
import mcp
import tyro

from . import config, llms, templating, tmux, ui


@beartype.beartype
async def cli(
    words: list[str],
    /,
    cfg: typing.Annotated[config.Config, tyro.conf.arg(name="")] = config.Config(),
    context: bool = True,
) -> int:
    """
    Ask an LLM for help with shell commands.

    Args:
        words: Your query.
        context: Whether to include any of your current shell context in your query.
    """
    cfg = config.load(cfg)

    import litellm

    if not litellm.supports_function_calling(cfg.model):
        print(f"Error: The model '{cfg.model}' does not support function calling.")
        print("Please choose a different model that supports this feature.")
        return 1

    query = " ".join(words)

    async with contextlib.AsyncExitStack() as stack:
        stdio = await stack.enter_async_context(
            mcp.client.stdio.stdio_client(
                mcp.StdioServerParameters(
                    command="/Users/samstevens/go/bin/voyager", args=[]
                )
            )
        )
        session = await stack.enter_async_context(mcp.ClientSession(*stdio))
        await session.initialize()

        conversation = llms.Conversation(model=cfg.model, api_key=cfg.api_key)

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

        conversation = llms.Conversation(model=cfg.model, api_key=cfg.api_key)
        conversation.system(system)
        conversation.user(query)

        response = await session.list_tools()
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        while True:
            toks, usd = conversation.get_costs()
            if not await ui.confirm_next_request(toks, usd):
                break

            msg = await conversation.send(tools=tools)

            # Print agent response.
            if msg.content is not None:
                ui.echo(msg.content.strip())
            if not msg.tool_calls:
                # Print total session cost.
                break

            deny_notes = []
            for tc in msg.tool_calls:
                try:
                    kwargs = json.loads(tc.function.arguments)
                    if await ui.confirm(
                        f"Run tool <cmd>{tc.function.name}</cmd> with args <cmd>{kwargs}</cmd>? [Y/n]:"
                    ):
                        result = await session.call_tool(tc.function.name, kwargs)
                        for content in result.content:
                            ui.echo(content.text)
                            conversation.tool(content.text, tool_call_id=tc.id)
                    else:
                        note = await ui.ask_tool_skip_reason(tc.function.name)
                        deny_notes.append(f"{tc.function.name}: {note}")
                        conversation.tool(f"denied by user: {note}", tool_call_id=tc.id)
                except Exception as err:
                    conversation.tool(str(err), tool_call_id=tc.id)
                    ui.echo(f"<warn>Error:</warn> {err}")

            if deny_notes:
                conversation.user("\n".join(deny_notes))

        await asyncio.sleep(0.1)

    await asyncio.sleep(0.1)
    return 0


@beartype.beartype
@typing.runtime_checkable
class McpSession(typing.Protocol):
    async def initialize(self) -> None: ...
    async def list_tools(self): ...  # returns .tools iterable
    async def call_tool(self, name: str, arguments: dict[str, object]): ...


def main():
    sys.exit(asyncio.run(tyro.cli(cli)))
