import dataclasses

import beartype


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Pane:
    id: str
    cwd: str
    active: bool
    history: tuple[str, ...]
