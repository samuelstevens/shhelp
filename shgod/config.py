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

    # Can you make this automatic, so that when we add new fields to the config, we don't have to update this? Maybe with dataclasses.asdict or something? AI!
    if cli.api_key is not None:
        cfg_dict["api_key"] = cli.api_key
    if cli.model != Config().model:  # If CLI model differs from default
        cfg_dict["model"] = cli.model
    if (
        cli.history_lines != Config().history_lines
    ):  # If CLI history_lines differs from default
        cfg_dict["history_lines"] = cli.history_lines

    if env_key := os.getenv("SHGOD_API_KEY"):
        cfg_dict["api_key"] = env_key

    cfg = Config(**cfg_dict)

    return cfg
