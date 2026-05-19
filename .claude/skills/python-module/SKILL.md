---
name: python-module
description: >
  Scaffolds a new Python module in backtest-proofs or mortgage-proofs following
  eigenq-xyz conventions: typed signatures, NumPy-style docstrings, input
  validation mirroring Lean proof assumptions, and a unit test file.
paths:
  - "**/*.py"
  - "**/pyproject.toml"
allowed-tools: Bash(uv run *) Read Write Edit Glob
---

# Python Module — Scaffold

## Where modules go

```
backtest-proofs/python/src/backtest_proofs/<subpackage>/<module>.py
mortgage-proofs/src/mortgage_proofs/<subpackage>/<module>.py
```

## Required file header

```python
from __future__ import annotations

"""One-line summary of what this module does.

Longer description if needed. Reference the corresponding Lean theorem
or invariant that this module implements or validates against.
"""
```

## Function template

```python
def function_name(param: int, other: str) -> int:
    """One-line summary.

    Parameters
    ----------
    param : int
        Description. Units if applicable (e.g., basis points).
    other : str
        Description.

    Returns
    -------
    int
        Description. Units if applicable.

    Raises
    ------
    ValueError
        If `param` is negative. (Mirror of Lean's `param_pos` invariant.)

    Notes
    -----
    Corresponds to `BacktestProofs.Invariants.valueIdentity`.
    """
    if param < 0:
        raise ValueError(f"param must be non-negative (Lean: param_pos), got {param}")
    # implementation
```

## Validation mirrors Lean

Every Lean type invariant becomes a Python `ValueError`:
- Lean: `markPrice_pos : position.markPrice > 0` → Python: `if mark_price <= 0: raise ValueError(...)`
- Lean: `fee_nonneg : trade.fee ≥ 0` → Python: `if fee < 0: raise ValueError(...)`

## FFI boundary rule (backtest-proofs only)

All values crossing to/from Lean FFI are `int` in basis points. Use `to_bp` / `from_bp`:
```python
from backtest_proofs.pricer.conventions import to_bp, from_bp
mark_bps = to_bp(mark_price_float)   # float → int, at the boundary
result = from_bp(result_bps)          # int → float, after the FFI call
```
Never multiply by `10_000` inline — use the named helpers.

## Test file template

```python
# tests/unit/test_<module>.py
import pytest
from backtest_proofs.<subpackage>.<module> import function_name

def test_function_name_basic():
    assert function_name(100, "x") == expected

def test_function_name_validates_negative():
    with pytest.raises(ValueError, match="non-negative"):
        function_name(-1, "x")

def test_function_name_matches_lean_model():
    """Model consistency: Python result must match Lean on synthetic input."""
    # Use the FFI to get the Lean result, compare to Python
    ...
```

## Checklist before handing back

- [ ] `uv run mypy src/ --strict` exits 0
- [ ] `uv run pytest tests/unit/test_<module>.py -v` exits 0
- [ ] `uv run ruff check src/` exits 0
- [ ] `from __future__ import annotations` present
- [ ] Validation for every Lean invariant on the corresponding type
