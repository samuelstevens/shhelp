import abc
import pathlib
import subprocess

import beartype


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
        import jsonschema

        jsonschema.Draft202012Validator.check_schema(cls.parameters)
        _GLOBAL_REGISTRY[cls.name] = cls

    @classmethod
    def spec(cls):
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": cls.parameters,
                "strict": True,
            },
        }

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def fmt(self):
        raise NotImplementedError()

    def __call__(self):
        return self.run()

    def __str__(self):
        return self.fmt()


_GLOBAL_REGISTRY: dict[str, type[Tool]] = {}


@beartype.beartype
def get_tools() -> list[type[Tool]]:
    return list(_GLOBAL_REGISTRY.values())


@beartype.beartype
def get_tool_specs() -> list[dict[str, object]]:
    return [tool.spec() for tool in get_tools()]


@beartype.beartype
def get_tool(name: str) -> type[Tool]:
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

    def __init__(self, *, regex: str, path: str):
        self.regex = regex
        self.path = pathlib.Path(path).expanduser().resolve()

        self._cmd = [
            "rg",
            "--line-number",
            "--color",
            "never",
            self.regex,
            str(self.path),
        ]

    def run(self) -> str:
        proc = subprocess.run(self._cmd, text=True, capture_output=True, timeout=15)
        if proc.returncode not in (0, 1):  # 1 = no matches
            raise RuntimeError(proc.stderr.strip())
        return proc.stdout

    def fmt(self) -> str:
        return " ".join(self._cmd)


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

    def __init__(self, *, regex: str | None = None, path: str | None = None):
        self._regex = regex
        self._path = pathlib.Path(path or ".").expanduser().resolve()

        if not self._path.is_dir():
            raise NotADirectoryError(self._path)

        cmd = ["fd", "--hidden", "--no-ignore", "--color", "never", "--full-path"]
        if regex:
            cmd.append(regex)
        cmd.append(str(self._path))

        self._cmd = cmd

    def run(self) -> str:
        proc = subprocess.run(self._cmd, text=True, capture_output=True, timeout=15)
        if proc.returncode not in (0, 1):  # 1 = no matches
            raise RuntimeError(proc.stderr.strip())
        return proc.stdout

    def fmt(self) -> str:
        return " ".join(self._cmd)
