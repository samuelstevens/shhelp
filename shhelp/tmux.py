import dataclasses
import os
import subprocess

import beartype


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Pane:
    """Represents a tmux pane.

    A tmux pane is a rectangular section of a tmux window where commands
    can be executed.

    Attributes:
        id: The unique identifier of the pane.
        cwd: The current working directory of the pane.
        active: Whether the pane is currently active.
        history: All lines of history in the pane.
    """

    id: str
    cwd: str
    active: bool
    history: str


@beartype.beartype
def get_panes() -> tuple[Pane, list[Pane]]:
    active_pane, other_panes = None, []
    active_id = os.getenv("TMUX_PANE")
    fmt = "#{pane_id},#{pane_current_path}"
    cmd = [
        "tmux",
        "list-panes",
        "-F",  # custom format
        fmt,
    ]
    for line in subprocess.check_output(cmd, text=True).splitlines():
        pane_id, cwd = line.split(",", 2)

        hist_cmd = [
            "tmux",
            "capture-pane",
            "-p",  # print to stdout
            "-J",  # join wrapped lines
            "-S",
            "-100",  # start 100 lines from bottom
            "-t",  # target this pane
            pane_id,
        ]
        history = subprocess.check_output(hist_cmd, text=True).strip()

        pane = Pane(id=pane_id, cwd=cwd, active=pane_id == active_id, history=history)
        if pane.active:
            active_pane = pane
        else:
            other_panes.append(pane)

    return active_pane, other_panes


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Context:
    active: Pane
    panes: tuple[Pane, ...]
    system: str
    shell: str
    aliases: tuple[str, ...]

    def __init__(self, shell: str | None = None):
        import subprocess

        active, panes = get_panes()
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
