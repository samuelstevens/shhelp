import beartype
import rich.console
import rich.markdown
import rich.theme

# theme for console markup styles
_THEME = rich.theme.Theme({
    "highlight": "cyan",
    "cost": "green",
    "warn": "bold red",
    "prompt": "bold",
    "cmd": "italic yellow",
})

_CONSOLE = rich.console.Console(theme=_THEME)

###########
# Generic #
###########


@beartype.beartype
def echo(md: str) -> None:
    """Write a line to the console."""
    _CONSOLE.print(rich.markdown.Markdown(md))


@beartype.beartype
def confirm(markup: str, *, default_yes: bool = True) -> bool:
    """Prompt the user for a yes/no answer, returning True if yes."""
    yes_set = {"y", "yes"}
    if default_yes:
        yes_set.add("")
    prompt_text = f"[prompt]{markup}[/prompt] "
    try:
        ans = _CONSOLE.input(prompt_text)
    except EOFError:
        return False

    return ans.strip().lower() in yes_set


# shhelp-specific


@beartype.beartype
def confirm_next_request(tokens: int, cost_usd: float) -> bool:
    """Ask the user to confirm proceeding with the next request cost."""
    msg = (
        f"[highlight]Next request[/highlight]: [cost]{tokens} tok  ${cost_usd:.2f}[/cost]\n"
        "continue? [Y/n]:"
    )
    return confirm(msg)


@beartype.beartype
def ask_tool_skip_reason(tool: str) -> str:
    """Return the user's reason for denying a tool."""
    prompt_text = "[prompt]Why?[/prompt] "
    try:
        ans = _CONSOLE.input(prompt_text)
    except EOFError:
        return ""
    return ans.strip()
