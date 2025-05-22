import abc
import pathlib
import subprocess

import beartype
import jsonschema


@beartype.beartype
class Tool(abc.ABC):
    """Describes a JSON-function tool plus its Python function."""

    name: str
    """snake-case identifier shown to the model"""
    description: str
    """natural langauage description of the tool."""
    parameters: dict[str, object]
    """valid JSON-schema describing arguments"""
    read_only: bool
    """Whether the function makes any changes to disk."""

    def __init_subclass__(cls):
        jsonschema.Draft202012Validator.check_schema(cls.parameters)
        _GLOBAL_REGISTRY[cls.name] = cls()  # auto-register

    def spec(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "strict": True,
            },
        }

    @abc.abstractmethod
    def run(self, **kw):
        """`run(**kwargs)->Any` that *runs* the tool"""
        raise NotImplementedError()

    @abc.abstractmethod
    def fmt(self, **kw):
        """`fmt(**kwargs)->str` that formats the tool about to be called."""
        raise NotImplementedError()

    def __call__(self, **kw):
        return self.run(**kw)


_GLOBAL_REGISTRY: dict[str, Tool] = {}


@beartype.beartype
def get_tools() -> list[Tool]:
    return list(_GLOBAL_REGISTRY.values())


@beartype.beartype
def get_tool_specs() -> list[dict[str, object]]:
    return [tool.spec() for tool in get_tools()]


@beartype.beartype
def get_tool(name: str) -> Tool:
    if name not in _GLOBAL_REGISTRY:
        raise ValueError(f"Tool {name} not registered.")
    return _GLOBAL_REGISTRY[name]


@beartype.beartype
class Grep(Tool):
    name = "ripgrep"
    description = (
        "Recursively look (grep) for REGEX in a path PATH. Output path:line:match."
    )
    read_only = True
    parameters = {
        "type": "object",
        "properties": {
            "regex": {
                "type": "string",
                "description": "Regex/text to search for",
            },
            "path": {"type": "string", "description": "Directory path (can be .)"},
        },
        "required": ["regex", "path"],
        "additionalProperties": False,
    }

    def run(self, *, regex: str, path: str) -> str:
        base = pathlib.Path(path).expanduser().resolve()
        if not base.is_dir():
            raise NotADirectoryError(base)

        cmd = ["rg", "-n", "--color", "never", "-e", regex, str(base)]
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
        if proc.returncode not in (0, 1):  # 1 = no matches
            raise RuntimeError(proc.stderr.strip())
        return proc.stdout

    def fmt(self, *, regex: str, path: str) -> str:
        return f"rg {regex} {path}"


@beartype.beartype
class Find(Tool):
    name = "find"
    description = "Find filepaths with a regular expression. Omit regex to list everything; omit path for CWD."
    parameters = {
        "type": "object",
        "properties": {
            "regex": {
                "type": ["string", "null"],
                "description": "Regex to match filenames; null or missing -> no filter",
            },
            "path": {
                "type": ["string", "null"],
                "description": "Directory to search; null or missing -> current dir",
            },
        },
        "required": ["regex", "path"],
        "additionalProperties": False,
    }
    read_only = True

    def run(self, *, regex: str | None = None, path: str | None = None) -> str:
        base = pathlib.Path(path or ".").expanduser().resolve()
        if not base.is_dir():
            raise NotADirectoryError(base)

        cmd = ["fd", "--hidden", "--no-ignore", "--color", "never"]
        if regex:
            cmd.append(regex)
        cmd.append(str(base))

        print(" ".join(cmd))
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
        if proc.returncode not in (0, 1):  # 1 = no matches
            raise RuntimeError(proc.stderr.strip())
        return proc.stdout

    def fmt(self, regex: str, path: str) -> str:
        return f"fd --hidden --no-ignore {regex} {path}"


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
