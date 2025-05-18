import os
import pathlib

import beartype


@beartype.beartype
def get_history_path() -> pathlib.Path:
    base = pathlib.Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser()
    path = base / "shgod" / "history"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
