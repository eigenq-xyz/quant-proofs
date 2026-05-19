# Python Code Reference — quant-proofs

Full conventions for naming, tooling configuration, test structure, and Pydantic usage.
This file is the authoritative reference; SKILL.md is the summary.

---

## Naming conventions

| Construct | Style | Example |
|-----------|-------|---------|
| Functions and methods | `snake_case` | `compute_delta_hedge()` |
| Variables | `snake_case` | `implied_vol_bps` |
| Classes | `PascalCase` | `DecisionRecord`, `HedgePosition` |
| Constants (module-level) | `UPPER_SNAKE_CASE` | `MAX_STRIKES = 500` |
| Private functions/methods | leading underscore `_snake_case` | `_validate_strike()` |
| Private class attributes | leading underscore | `self._cache: dict[str, float]` |
| Type aliases | `PascalCase` or `UPPER_SNAKE_CASE` | `PnlBps: TypeAlias = int` |
| Lean FFI wrapper functions | prefix `lean_` | `lean_compute_pnl()` |
| Test functions | `test_<what>_<condition>` | `test_delta_hedge_at_expiry()` |
| Test fixtures | descriptive noun phrase | `sample_option_chain`, `mock_wrds_session` |

Do not use abbreviations unless they are standard in quantitative finance
(e.g., `pnl`, `vol`, `bps`, `atm`, `itm`, `otm`) or in the Python ecosystem
(`cls`, `fn`, `cfg`).

---

## ruff configuration

`ruff` is configured in `pyproject.toml` under `[tool.ruff]`. The active rule sets are:

| Code | Rule set | Why enabled |
|------|----------|-------------|
| `E` | pycodestyle errors | PEP 8 compliance |
| `F` | pyflakes | Unused imports, undefined names |
| `I` | isort | Import ordering |
| `UP` | pyupgrade | Enforce modern Python 3.12+ syntax |
| `B` | flake8-bugbear | Common bug patterns |
| `SIM` | flake8-simplify | Unnecessary complexity |
| `ANN` | flake8-annotations | Annotation completeness (subset) |

The `line-length` is set to `88` (Black-compatible). Do not override this per-file.

To auto-fix safe issues:
```
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

To check without modifying:
```
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

---

## mypy configuration

mypy runs with `--strict`, which enables:

- `--disallow-any-generics` — `list` must be `list[T]`, not bare `list`
- `--disallow-untyped-defs` — all functions must have annotations
- `--disallow-incomplete-defs` — partial annotations not allowed
- `--no-implicit-optional` — `Optional[T]` must be explicit
- `--warn-return-any` — returning `Any` from a typed function is an error
- `--warn-unused-ignores` — stale `# type: ignore` comments are errors

Configuration in `pyproject.toml` under `[tool.mypy]`:
```toml
[tool.mypy]
strict = true
python_version = "3.12"
warn_unused_configs = true
```

For third-party libraries without stubs, add an explicit ignore in `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = ["wrds.*", "fredapi.*"]
ignore_missing_imports = true
```

Do not use `# type: ignore` without specifying the error code. Prefer
`# type: ignore[import-untyped]` over bare `# type: ignore`.

---

## uv commands

| Task | Command |
|------|---------|
| Install all deps + dev extras | `uv sync --extra dev` |
| Add a new dependency | `uv add <package>` |
| Add a dev-only dependency | `uv add --optional dev <package>` |
| Remove a dependency | `uv remove <package>` |
| Run a command in the venv | `uv run <command>` |
| Show installed packages | `uv pip list` |
| Update lockfile | `uv lock --upgrade` |

The lockfile (`uv.lock`) is committed to the repository. Do not delete or
manually edit it.

`pyproject.toml` structure for optional dev dependencies:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "ruff>=0.4",
    "pre-commit>=3.7",
]
```

---

## Test structure

### Directory layout

```
tests/
  conftest.py          # shared fixtures
  unit/
    test_<module>.py   # one file per source module
  integration/
    test_ffi.py        # Cython FFI integration (backtest-proofs)
    test_agents.py     # LangGraph agent integration (mortgage-proofs)
```

### conftest.py patterns

Use `conftest.py` for fixtures shared across multiple test files. Keep
module-specific fixtures in the test file itself.

```python
# conftest.py
from __future__ import annotations

import pytest

@pytest.fixture
def sample_option_chain() -> list[dict[str, int]]:
    """Minimal option chain with strikes in basis points."""
    return [
        {"strike_bps": 100_0000, "expiry_days": 30, "delta_bps": 5000},
        {"strike_bps": 105_0000, "expiry_days": 30, "delta_bps": 2500},
    ]
```

### Fixture naming

- Use descriptive noun phrases: `sample_option_chain`, `mock_wrds_session`
- Prefix mocks with `mock_`: `mock_polygon_client`
- Prefix minimal/small fixtures with `minimal_`: `minimal_decision_record`

### Parametrize usage

Use `@pytest.mark.parametrize` for testing multiple inputs to the same logic.
Give each case an `id` for readable output:

```python
@pytest.mark.parametrize(
    ("delta_bps", "expected_bps"),
    [
        (5000, 5000),
        (0, 0),
        (-5000, -5000),
    ],
    ids=["positive-delta", "zero-delta", "negative-delta"],
)
def test_hedge_pnl(delta_bps: int, expected_bps: int) -> None:
    ...
```

### Coverage

New code must reach at least 80% test coverage. Check with:
```
uv run pytest --cov=src/ --cov-report=term-missing
```

---

## Pydantic model conventions (mortgage-proofs)

Use Pydantic v2 (`pydantic>=2.0`).

```python
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class DecisionRecord(BaseModel):
    """Record of a single routing decision by a mortgage pipeline agent.

    Args:
        agent: Name of the agent that made the decision.
        action: Routing action taken.
        rationale: Human-readable explanation for the decision.
        confidence_bps: Agent's confidence in basis points (0–10000).
    """

    agent: Literal["intake", "risk", "compliance", "underwriter"]
    action: str
    rationale: str
    confidence_bps: int = Field(ge=0, le=10_000)

    @model_validator(mode="after")
    def rationale_non_empty(self) -> DecisionRecord:
        if not self.rationale.strip():
            raise ValueError("rationale must not be blank")
        return self
```

Rules:
- Use `Field(ge=..., le=...)` for range constraints — do not validate in an `if` block.
- Use `Literal` for fixed-choice string fields.
- Use `model_validator(mode="after")` for cross-field validation.
- Always use `model.model_dump()` (not `.dict()`) and `Model.model_validate()` (not
  `.parse_obj()`) — these are the v2 APIs.
- JSON round-trip: `Model.model_validate_json(json_str)` and `model.model_dump_json()`.
