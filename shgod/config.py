import dataclasses
import pathlib
import tomllib
import os

import beartype

_CFG_PATH = pathlib.Path("~/.config/shgod/config.toml").expanduser()


@beartype.beartype
@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime options that rarely change between invocations.

    Attributes:
        api_key: Secret for your LLM backend (OpenAI / Anthropic / etc.). Default None -> fall back to env var `SHGOD_API_KEY` or backend-specific vars like `OPENAI_API_KEY`.
        model: Identifier sent to the provider, e.g. ``gpt-4o-mini``.
        history_lines: How many lines of tmux scrollback to include in the prompt.
    """

    api_key: str | None = None
    model: str = "gpt-4.1-mini"
    history_lines: int = 200  # reasonable default


@beartype.beartype
def load(cli: Config) -> Config:
    """Return a Config merged from TOML file + env vars + defaults + CLI options."""
    cfg_dict: dict = {}

    if _CFG_PATH.exists():
        cfg_dict.update(tomllib.loads(_CFG_PATH.read_text()))

    # Override with CLI options that differ from defaults
    default_cfg = Config()
    cli_dict = dataclasses.asdict(cli)
    for field_name, field_value in cli_dict.items():
        default_value = getattr(default_cfg, field_name)
        # Only override if the CLI value is not None and different from default
        if field_value is not None and field_value != default_value:
            cfg_dict[field_name] = field_value

    if env_key := os.getenv("SHGOD_API_KEY"):
        cfg_dict["api_key"] = env_key

    cfg = Config(**cfg_dict)

    return cfg
