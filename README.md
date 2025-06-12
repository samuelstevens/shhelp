# shhelp

shhelp is a tool for answering shell-related questions directly from the command line.

You can ask it how to do something in your shell, or for explanations of specific command-line options.

# TODO

* Markdown formatting in terminal
* ptk.HTML blows up on & in input.
* Streaming??
* https://github.com/JohannesKaufmann/html-to-markdown for fetch as `.md`.

## Example Usage

### Problem solving

```sh
shh where is my OPENROUTER_API_KEY being set?
```

### Explanation

```sh
shh "can you explain what -a and -F are in tmux list-panes?"
```

```sh
shh whats the difference between os.environ.get and os.getenv in python
````

```sh
shh where do typical unix programs store REPL history on unix?
```

# Example Interactions

```sh
[I] samstevens@localhoster ~> shh "sshelp is a tool I'm working on at /Users/samstevens/Development/shhelp. What's the default model according to the source code, and what model do I have set by default in my config file?"
Next request: 1043 tok  $0.00
continue? [Y/n]:
I'll help you find the default model in your shhelp source code and check your config file settings.

**Plan:**
- Look for source code files that might contain default model configuration
- Find and examine your config file to see what model you have set

Let me start by exploring the shhelp directory structure:
Run tool find with args {'path': '/Users/samstevens/Development/shhelp', 'pattern': '.'}? [Y/n]:
/Users/samstevens/Development/shhelp/AGENTS.md
/Users/samstevens/Development/shhelp/README.md
/Users/samstevens/Development/shhelp/docs/
/Users/samstevens/Development/shhelp/docs/llms.txt
/Users/samstevens/Development/shhelp/docs/todo/
/Users/samstevens/Development/shhelp/docs/todo/0001_skip_tools.md
/Users/samstevens/Development/shhelp/docs/todo/0002_findall.md
/Users/samstevens/Development/shhelp/justfile
/Users/samstevens/Development/shhelp/pyproject.toml
/Users/samstevens/Development/shhelp/shhelp/
/Users/samstevens/Development/shhelp/shhelp/__init__.py
/Users/samstevens/Development/shhelp/shhelp/__main__.py
/Users/samstevens/Development/shhelp/shhelp/cli.py
/Users/samstevens/Development/shhelp/shhelp/config.py
/Users/samstevens/Development/shhelp/shhelp/llms.py
/Users/samstevens/Development/shhelp/shhelp/prompt.j2
/Users/samstevens/Development/shhelp/shhelp/templating.py
/Users/samstevens/Development/shhelp/shhelp/test_e2e.py
/Users/samstevens/Development/shhelp/shhelp/test_lex.py
/Users/samstevens/Development/shhelp/shhelp/test_templating.py
/Users/samstevens/Development/shhelp/shhelp/test_tooling.py
/Users/samstevens/Development/shhelp/shhelp/tmux.py
/Users/samstevens/Development/shhelp/shhelp/tooling.py
/Users/samstevens/Development/shhelp/shhelp/ui.py
/Users/samstevens/Development/shhelp/shhelp/unix.py

Next request: 1669 tok  $0.01
continue? [Y/n]:
Now let me check the config.py file first, as it's likely to contain default model settings:
Run tool cat with args {'path': '/Users/samstevens/Development/shhelp/shhelp/config.py'}? [Y/n]:
1: import dataclasses
2: import os
3: import pathlib
4: import tomllib
5:
6: import beartype
7:
8: _CFG_PATH = pathlib.Path("~/.config/shhelp/config.toml").expanduser()
9:
10:
11: @beartype.beartype
12: @dataclasses.dataclass(frozen=True)
13: class Config:
14:     """Runtime options that rarely change between invocations.
15:
16:     Attributes:
17:         api_key: Secret for your LLM backend (OpenAI / Anthropic / etc.). Default None, which falls back to env var `SHHELP_API_KEY` or backend-specific vars like `OPENAI_API_KEY`.
18:         model: Identifier sent to the provider, e.g. ``gpt-4o-mini``.
19:         history_lines: How many lines of tmux scrollback to include in the prompt.
20:     """
21:
22:     api_key: str = ""
23:     model: str = "gpt-4.1-mini"
24:     history_lines: int = 200  # reasonable default
25:     mcp_servers: list[str] = dataclasses.field(default_factory=list)
26:
27:
28: @beartype.beartype
29: def _write_default_cfg() -> None:
30:     """Write default config to `~/.config/shhelp/config.toml`."""
31:     # TODO: include TOML comments with the parsed attribute comments from Config. We can adjust the comments to be under each variable instead of the docstring if that's easier.
32:     _CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
33:     with _CFG_PATH.open("w") as fh:
34:         for k, v in dataclasses.asdict(Config()).items():
35:             fh.write(f"{k} = {v!r}\n")
36:
37:
38: @beartype.beartype
39: def load(cli: Config) -> Config:
40:     """Return a Config merged from TOML file + env vars + defaults + CLI options."""
41:     cfg_dict: dict = {}
42:
43:     if not _CFG_PATH.exists():
44:         _write_default_cfg()
45:
46:     cfg_dict.update(tomllib.loads(_CFG_PATH.read_text()))
47:
48:     # Override with CLI options that differ from defaults
49:     default_cfg = Config()
50:     cli_dict = dataclasses.asdict(cli)
51:     for field_name, field_value in cli_dict.items():
52:         default_value = getattr(default_cfg, field_name)
53:         # Only override if the CLI value is not None and different from default
54:         if field_value is not None and field_value != default_value:
55:             cfg_dict[field_name] = field_value
56:
57:     if env_key := os.getenv("SHHELP_API_KEY"):
58:         cfg_dict["api_key"] = env_key
59:
60:     cfg = Config(**cfg_dict)
61:
62:     return cfg
63:

Next request: 2545 tok  $0.01
continue? [Y/n]:
Great! I found the default model in the source code. Now let me check your actual config file:
Run tool cat with args {'path': '~/.config/shhelp/config.toml'}? [Y/n]:
Error reading file: open ~/.config/shhelp/config.toml: no such file or directory
Next request: 2637 tok  $0.01
continue? [Y/n]:
Let me try the expanded path:
Run tool cat with args {'path': '/Users/samstevens/.config/shhelp/config.toml'}? [Y/n]:
1: api_key = REDACTED
2: model = "claude-sonnet-4-20250514"
3: history_lines = 100
4:

Next request: 2810 tok  $0.01
continue? [Y/n]:
Perfect! Here's what I found:

## Default Model in Source Code
According to `/Users/samstevens/Development/shhelp/shhelp/config.py` line 23, the **default model** is:
```
gpt-4.1-mini
```

## Your Current Config
In your config file at `~/.config/shhelp/config.toml`, you have set the model to:
```
claude-sonnet-4-20250514
```

So while the source code defaults to `gpt-4.1-mini`, you've overridden it in your config to use `claude-sonnet-4-20250514` instead. Your config also sets `history_lines` to 100 (vs the default 200) and includes an API key.
Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x10bf0b050>
Unclosed connector
connections: ['deque([(<aiohttp.client_proto.ResponseHandler object at 0x10bea8d70>, 1074687.206860791)])']
connector: <aiohttp.connector.TCPConnector object at 0x10bf08110>
[I] samstevens@localhoster ~>
```
