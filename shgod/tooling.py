import collections.abc
import dataclasses
import pathlib
import subprocess

import beartype
import jsonschema


@beartype.beartype
@dataclasses.dataclass(frozen=True, slots=True)
class Tool:
    """Describe one JSON-function tool plus its Python executor.

    Parameters
    ----------
    name          : snake-case identifier shown to the model
    description   : human text
    parameters    : valid JSON-schema describing arguments
    function      : `func(**kwargs)->Any` that *runs* the tool
    read_only     : if False ask user confirmation before running
    """

    name: str
    description: str
    parameters: dict[str, object]
    function: collections.abc.Callable[..., object] = dataclasses.field(
        repr=False, hash=False, compare=False
    )
    read_only: bool = False

    def __post_init__(self):
        jsonschema.Draft202012Validator.check_schema(dict(self.parameters))
        if self.name not in _GLOBAL_TOOLS:
            _GLOBAL_TOOLS[self.name] = self

    def spec(self) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "strict": True,
            },
        }

    def __call__(self, **kwargs) -> object:
        return self.function(**kwargs)


_GLOBAL_TOOLS: dict[str, Tool] = {}


@beartype.beartype
def get_tools() -> list[Tool]:
    return list(_GLOBAL_TOOLS.values())


@beartype.beartype
def get_tool_specs() -> list[dict[str, object]]:
    return [tool.spec() for tool in get_tools()]


@beartype.beartype
def get_tool(name: str) -> Tool:
    if name not in _GLOBAL_TOOLS:
        raise ValueError(f"Tool {name} not registered.")
    return _GLOBAL_TOOLS[name]


def _run_ripgrep(pattern: str, path: str) -> str:
    base = pathlib.Path(path).expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)

    cmd = ["rg", "-n", "--color", "never", "-e", pattern, str(base)]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    if proc.returncode not in (0, 1):  # 1 = no matches
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout


ripgrep = Tool(
    name="ripgrep",
    description="Recursively look (grep) for PATTERN in a path PATH. Output path:line:match.",
    read_only=True,
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regex/text to search for",
            },
            "path": {"type": "string", "description": "Directory path (can be .)"},
        },
        "required": ["pattern", "path"],
        "additionalProperties": False,
    },
    function=_run_ripgrep,
)


def _run_find(*, regex: str | None = None, dir: str | None = None) -> str:
    base = pathlib.Path(dir or ".").expanduser().resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)

    cmd = ["fd", "--color", "never"]
    if regex:
        cmd.append(regex)
    cmd.append(str(base))

    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    if proc.returncode not in (0, 1):  # 1 = no matches
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout


Tool(
    name="find",
    description="Find filepaths with a regular expression. Omit regex to list everything; omit dir for CWD.",
    parameters={
        "type": "object",
        "properties": {
            "regex": {
                "type": ["string", "null"],
                "description": "Regex to match filenames; null or missing -> no filter",
            },
            "dir": {
                "type": ["string", "null"],
                "description": "Directory to search; null or missing -> current dir",
            },
        },
        "required": ["regex", "dir"],
        "additionalProperties": False,
    },
    function=_run_find,
    read_only=True,
)


# def _run_shell(*, cmd: str) -> str:
#     proc = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=60)
#     out = f"$ {cmd}\n{proc.stdout}"
#     if proc.stderr:
#         out += f"\n[stderr]\n{proc.stderr}"
#     out += f"\n[exit {proc.returncode}]"
#     return out


# shell_tool = Tool(
#     name="shell",
#     description="Execute an arbitrary shell command in the current working directory.",
#     parameters={
#         "type": "object",
#         "properties": {
#             "cmd": {"type": "string", "description": "Exact command line to run"},
#         },
#         "required": ["cmd"],
#         "additionalProperties": False,
#     },
#     function=_run_shell,
#     read_only=False,
# )
