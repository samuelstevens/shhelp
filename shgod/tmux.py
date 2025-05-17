import dataclasses
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


def get_panes() -> tuple[Pane, tuple[Pane, ...]]:
    active, panes = None, []
    fmt = "#{pane_id},#{pane_active},#{pane_current_path}"
    cmd = [
        "tmux",
        "list-panes",
        "-a",  # all sessions
        "-F",  # custom format
        fmt,
    ]
    for line in subprocess.check_output(cmd, text=True).splitlines():
        pane_id, active, cwd = line.split(",", 2)

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

        pane = Pane(id=pane_id, cwd=cwd, active=active == "1", history=history)
        if pane.active:
            active = pane
        else:
            panes.append(pane)

    return active, tuple(panes)
