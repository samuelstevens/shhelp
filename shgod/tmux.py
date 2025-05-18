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
    active_id = os.environ.get("TMUX_PANE")
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
