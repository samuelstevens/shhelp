import dataclasses

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
        history: A tuple of commands that have been executed in the pane.
    """
    id: str
    cwd: str
    active: bool
    history: tuple[str, ...]
