import beartype
import prompt_toolkit as ptk

from . import unix

_STYLE = ptk.styles.Style.from_dict({
    "hl": "ansicyan",
    "cost": "ansigreen",
    "warn": "bold ansired",
    "prompt": "bold",
    "cmd": "italic ansiyellow",
})

_SESSION = ptk.PromptSession(
    history=ptk.history.FileHistory(str(unix.get_history_path())),
    style=_STYLE,
)

###########
# Generic #
###########


@beartype.beartype
def echo(html: str) -> None:
    """Write a line outside the input buffer (non-blocking)."""
    ptk.print_formatted_text(ptk.HTML(html), style=_STYLE)  # safe with PTK


@beartype.beartype
def confirm(html: str, *, default_yes: bool = True) -> bool:
    yes_set = {"y", "yes"}
    if default_yes:
        yes_set.add("")
    try:
        ans = _SESSION.prompt(ptk.HTML(f"<prompt>{html}</prompt> ")).strip().lower()
    except EOFError:  # Ctrl-D
        return False

    return ans in yes_set


# shgod-specific


@beartype.beartype
def confirm_next_request(tokens: int, cost_usd: float) -> bool:
    msg = (
        f"<highlight>Next request</highlight>: <cost>{tokens} tok  ${cost_usd:.2f}</cost>\n"
        "continue? [Y/n]:"
    )
    return confirm(msg)


@beartype.beartype
def ask_tool_skip_reason(tool: str) -> str:
    """Return the user's reason for denying a tool."""
    try:
        ans = _SESSION.prompt(ptk.HTML("<prompt>Why? </prompt> "))
    except EOFError:
        return ""
    return ans.strip()
