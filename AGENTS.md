# Code Style

- Keep code simple, explicit, typed, test-driven, and ready for automation.
- Source files are UTF-8 but must contain only ASCII characters. Do not use smart quotes, ellipses, em-dashes, emoji, or other non-ASCII glyphs.
- Docstrings are a single unwrapped paragraph. Rely on your editor's soft-wrap.
- Prefer explicit over implicit constructs. No wildcard imports.

```python
from . import tmux  # instead of from .tmux import Pane
```

Always reference modules by their alias. Never use `from X import *`.

- Decorate every public function or class with `@beartype.beartype`.
- Use frozen `@dataclasses.dataclass` for data containers such as `Config` or `Args`.
- Classes use `CamelCase`, for example `Dataset` or `FeatureExtractor`.
- Functions and variables use `snake_case`, for example `download_split` or `md5_of_file`.
- Constants are `UPPER_SNAKE`, defined at module top, for example `URLS = {...}`.
- File descriptors end in `fd`, for example `log_fd`.
- File paths end in `_fpath`; directories end in `_dpath`.
- Constructors follow verb prefixes:
  - `make_...` returns an object.
  - `get_...` returns a primitive value such as a string or path.
  - `setup_...` performs side effects and returns nothing.

# Testing

- Use pytest with fixtures and parameterization.
- Use Hypothesis for property-based tests, especially in helpers.
