# Python Anti-Patterns — quant-proofs

Patterns banned in this codebase. Most are caught by ruff or mypy; all are caught
in code review. Each entry shows the fix.

---

## 1. `import *`

**Why it's prohibited:** pollutes the namespace, hides where a name comes from,
breaks mypy's type tracking.

```python
# Bad
from backtest_proofs.models import *
from numpy import *
```

```python
# Good
from backtest_proofs.models import HedgePosition, PnlBps
import numpy as np
```

ruff rule: `F403` (import star), `F401` (unused import after star import).

---

## 2. `Any` as a type annotation shortcut

**Why it's prohibited:** `Any` turns off mypy's type checking for that value.
Every use is a hole in the type-safety guarantee.

```python
# Bad
from typing import Any

def load_data(path: str) -> Any:
    ...

def transform(record: Any, config: Any) -> Any:
    ...
```

```python
# Good — use a concrete type, Protocol, or TypedDict
from typing import TypedDict

class OptionRecord(TypedDict):
    strike_bps: int
    expiry_days: int
    price_bps: int

def load_data(path: str) -> list[OptionRecord]:
    ...
```

If `Any` is genuinely unavoidable (e.g., wrapping a dynamically-typed third-party
library), add a comment:
```python
result: Any  # wrds.Connection returns untyped cursor results; narrowed below
```

---

## 3. Floats across the Lean FFI boundary

**Why it's prohibited:** the Lean 4 accounting kernel uses integer arithmetic to
maintain formally verified invariants. Floats introduce rounding errors that
silently invalidate those guarantees.

```python
# Bad — passing float to FFI function
from backtest_proofs._ffi import compute_pnl
pnl = compute_pnl(delta=0.4823, price_move=0.0212)
```

```python
# Good — convert to basis points before the boundary
from backtest_proofs._ffi import compute_pnl
delta_bps = int(round(0.4823 * 10_000))    # 4823
price_move_bps = int(round(0.0212 * 10_000))  # 212
pnl_bps = compute_pnl(delta_bps=delta_bps, price_move_bps=price_move_bps)
```

---

## 4. Catching bare `Exception`

**Why it's prohibited:** catches everything, including `KeyboardInterrupt`,
`SystemExit`, and programming errors that should propagate. Makes debugging
impossible and hides real failures.

```python
# Bad
try:
    result = call_lean_kernel(inputs)
except Exception:
    result = default_value
```

```python
# Good — catch the specific exception you expect
try:
    result = call_lean_kernel(inputs)
except ValueError as exc:
    logger.warning("Lean kernel returned invalid value: %s", exc)
    result = default_value
```

A broad catch is sometimes needed (e.g., a top-level agent entry point). Use
`except Exception as exc` (not bare `except`), log the full traceback, then
re-raise or return a structured error. Never swallow the exception silently.

---

## 5. Mutable default arguments

**Why it's prohibited:** the default is evaluated once, at function-definition time.
Every call using the default shares the same mutable object — state leaks between calls.

```python
# Bad
def add_flag(flags: list[str] = []) -> list[str]:
    flags.append("new_flag")
    return flags

add_flag()  # ["new_flag"]
add_flag()  # ["new_flag", "new_flag"]  ← shared mutable state
```

```python
# Good — use None as default and create a new object inside
def add_flag(flags: list[str] | None = None) -> list[str]:
    if flags is None:
        flags = []
    flags.append("new_flag")
    return flags
```

For Pydantic models, use `Field(default_factory=list)`:
```python
flags: list[str] = Field(default_factory=list)
```

ruff rule: `B006`.

---

## 6. `os.system()` instead of `subprocess.run()`

**Why it's prohibited:** `os.system()` doesn't capture output, doesn't raise on
failure, and shells out (injection risk). `subprocess.run()` is explicit, safe,
and captures output.

```python
# Bad
import os
os.system("lake build")
```

```python
# Good
import subprocess
result = subprocess.run(
    ["lake", "build"],
    cwd="/path/to/lean/project",
    capture_output=True,
    text=True,
    check=True,          # raises CalledProcessError on non-zero exit
)
```

`check=True` unless you intentionally handle non-zero exits yourself.
`capture_output=True` unless you want output streamed to the terminal.

ruff rule: `S605` (os.system with shell=True).

---

## 7. Magic numeric literals

**Why it's prohibited:** a bare number carries no semantic meaning. `502500` is
opaque; `to_bp(50.25)` documents the unit and makes the conversion explicit. This
matters most where basis-point integers cross the Lean FFI boundary — a wrong unit
silently produces incorrect results no type checker catches.

```python
# Bad — what does 10_000 mean? Basis-point factor? Days? A fee cap?
position_value = quantity * 10_000
if fee > 50:
    raise ValueError("fee too high")
```

```python
# Good — use the project's conversion helpers or named constants
from backtest_proofs.pricer.conventions import to_bp, from_bp

BP_FACTOR = 10_000           # module-level constant with a name
MAX_FEE_BPS = to_bp(0.005)  # 0.5% fee cap, explicit conversion

position_value = quantity * BP_FACTOR
if fee > MAX_FEE_BPS:
    raise ValueError(
        f"fee {from_bp(fee):.4f} exceeds cap {from_bp(MAX_FEE_BPS):.4f}"
    )
```

Rules:
- Domain constants at module level, `ALL_CAPS` names.
- `to_bp` / `from_bp` at every float↔int conversion — never multiply by `10_000` inline.
- Prefer named keyword arguments over positional literals in function calls.

No automatic ruff rule — catch this in review. Pay extra attention near FFI call sites.
