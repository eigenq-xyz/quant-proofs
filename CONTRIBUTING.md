# Contributing Guide

Welcome to verified-options-backtest. This guide covers development setup, workflow, and conventions.

---

## Prerequisites

**Required:**

- **macOS or Linux** (Windows users: WSL 2 required)
- **Git** (version control)
- **Make** (build orchestration)
- **uv** (Python package manager): Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Installed by `make setup`:**

- **Lean 4** via elan (Lean toolchain manager)
- **Python 3.12** via uv
- **Python dependencies** (pytest, ruff, mypy, jupyterbook, etc.)

**Optional:**

- **direnv**: Auto-activate Python venv when entering project directory (`brew install direnv`)

---

## One-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/eigenq-xyz/verified-options-backtest.git
cd verified-options-backtest

# 2. Install all dependencies
make setup
# This takes ~5 minutes first time (downloads Lean toolchain + Python packages)

# 3. Verify installation
make test
# Expected: All Lean proofs compile, all Python tests pass

# 4. (Optional) Setup direnv for auto-activation
# Install: brew install direnv (macOS) or apt install direnv (Linux)
# Add to shell: eval "$(direnv hook bash)" in ~/.bashrc
# Create .envrc: echo "source python/.venv/bin/activate" > .envrc
# Allow: direnv allow

# 5. (Optional) Configure git-crypt for data access
# Request decryption key from project maintainer via secure channel
# Then run: git-crypt unlock /path/to/key
```

---

## Development Workflow

### Lean Development

```bash
cd lean

# Build proofs
lake build

# Run tests
lake build OptionHedge.Tests.UnitTests

# Watch mode (rebuild on file changes)
lake build --watch

# Check for sorry (must be zero)
grep -r "sorry" OptionHedge/

# Open in VSCode with Lean 4 extension
code .
```

**Lean Tips:**

- Install **Lean 4 VSCode extension**: `ms-vscode.lean4`
- Proofs show live feedback in editor
- Use `sorry` as placeholder during development, replace with actual proof
- Check CI before pushing: proofs must compile with no errors

### Python Development

```bash
cd python

# Install/update dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=verified_options_backtest --cov-report=term-missing

# Type checking
uv run mypy src/verified_options_backtest

# Linting
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Interactive Python shell
uv run ipython
```

**Python Tips:**

- Use basis-point integers for all values crossing the FFI boundary (never floats)
- Add type hints to all functions
- Write tests for new features (`tests/test_*.py`)
- Follow existing code style (enforced by ruff)

### Documentation

```bash
# Build JupyterBook
make docs-build

# Build and serve locally (http://localhost:8000)
make docs-serve
```

**Documentation Tips:**

- Document architectural decisions in [DECISIONS.md](DECISIONS.md)
- Update [RISKS.md](RISKS.md) if new risks identified

### Integration Testing

```bash
# Run full integration test
make integration
```

---

## Code Conventions

### Lean

```lean
-- Module naming: PascalCase under OptionHedge.*
-- OptionHedge/Basic.lean, OptionHedge/Invariants.lean

-- Structure names: PascalCase
structure Portfolio where
  cash : Int
  positions : List Position
  portfolioValue : Int
  value_valid : portfolioValue = cash + sumPositionValues positions

-- Function names: camelCase
def applyTrade (p : Portfolio) (t : Trade) : Portfolio := ...

-- Theorem names: camelCase with descriptive suffix
theorem valueUpdateFormula (p : Portfolio) (t : Trade) : ... := by ...

-- Proofs live inline in Invariants.lean / OptionInvariants.lean
-- Use rfl / simp / omega / native_decide where possible
```

### Python

```python
# Follow PEP 8, use type hints everywhere
# All monetary values crossing the FFI boundary are basis-point integers

from verified_options_backtest.pricer.conventions import to_bp, from_bp
from verified_options_backtest.ffi import apply_trade

result = apply_trade(
    cash=to_bp(100_000.0),
    positions=[],
    asset_id="SPY",
    delta_quantity=100,
    execution_price=to_bp(450.25),
    fee=to_bp(1.0),
)
print(from_bp(result["portfolio_value"]))
```

### Git Commit Messages

```text
[tag] Brief summary (50 chars)

- Detailed explanation if needed
- Use bullet points for multiple changes
- Reference issues: Fixes #123

Examples:
[v0.4] Prove settlement_value_formula (ITM/OTM unified)
[v0.5] Add binomial_replication_cost theorem
[docs] Rewrite CONTRIBUTING to reflect v0.4 layout
[fix] Handle edge case in bs_greeks near expiry
```

---

## Testing Requirements

### Before Pushing

```bash
# At project root
make test        # All tests must pass
make lint        # No linting errors
make integration # Integration test passes
```

### Test Coverage

- **Python**: Aim for 80%+ coverage (enforced in CI)
- **Lean**: All theorems must have proofs (no `sorry` in main code)
- **Integration**: At least one end-to-end test per milestone

### Writing Tests

**Python:**

```python
# tests/test_pricer.py
from verified_options_backtest.pricer.black_scholes import bs_price

def test_bs_price_hull_ex15_6():
    """Matches Hull Example 15.6 reference vector."""
    price = bs_price(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20, option_type="call")
    assert abs(price - 4.76) < 0.01
```

**Lean:**

```lean
-- Tests/UnitTests.lean
import OptionHedge.Accounting

-- Concrete computation test via native_decide
example : hedge_portfolio_value 500_000 [] = 500_000 := by native_decide
```

---

## Common Tasks

### Adding a New Invariant

1. **Document in DECISIONS.md**: Why is this invariant important?
2. **Define theorem in Lean** (`OptionHedge/Invariants.lean` or `OptionInvariants.lean`)
3. **Implement proof inline** (use `rfl`/`simp`/`omega`/`native_decide` where possible)
4. **Add concrete example** to `Tests/UnitTests.lean`
5. **Test in Python** if the invariant has a Python-observable effect

### Updating Dependencies

**Python:**

```bash
cd python
# Add new dependency
uv add package-name

# Update all dependencies
uv lock --upgrade

# Commit updated uv.lock
git add uv.lock && git commit -m "[deps] Update Python dependencies"
```

**Lean:**

```bash
cd lean
# Update Lean toolchain
lake update

# Commit updated lake-manifest.json
git add lake-manifest.json && git commit -m "[deps] Update Lean dependencies"
```

---

## Troubleshooting

### Lean Issues

**Problem**: `lake build` fails with "unknown package"

```bash
# Solution: Update dependencies
cd lean && lake update
```

**Problem**: Proofs compile slowly

```bash
# Solution: Increase parallelism
lake build -j 8  # Use 8 cores
```

**Problem**: VSCode Lean extension not working

```bash
# Solution: Restart Lean server
# Cmd+Shift+P → "Lean 4: Restart Server"
```

### Python Issues

**Problem**: `uv sync` fails

```bash
# Solution: Clear cache and retry
uv cache clean
uv sync
```

**Problem**: Import errors in tests

```bash
# Solution: Install package in editable mode
cd python
uv pip install -e .
```

**Problem**: `make docs-serve` fails

```bash
# Solution: Clean build and retry
rm -rf docs/_build
make docs-build
```

### Data Access

**Problem**: Need decryption key for `data/`

```text
# Solution: Request from project maintainer
# Send GPG public key or Signal contact
# Key will be provided via secure channel only
```

**Problem**: git-crypt not installed

```bash
# macOS
brew install git-crypt

# Linux
sudo apt install git-crypt
```

---

## CI Pipeline

GitHub Actions runs on every push:

1. **Lean Build** (`.github/workflows/lean.yml`) — compiles all proofs, checks for `sorry`
2. **Python Tests** (`.github/workflows/python.yml`) — lint, typecheck, unit tests with coverage
3. **Documentation** (`.github/workflows/docs.yml`) — builds JupyterBook, deploys to Pages (main only)

---

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/eigenq-xyz/verified-options-backtest/discussions)
- **Bugs**: Open an [Issue](https://github.com/eigenq-xyz/verified-options-backtest/issues)
- **Lean help**: [Lean Zulip](https://leanprover.zulipchat.com/)
- **Technical detail**: See [DEVELOPMENT.md](DEVELOPMENT.md)

---

## Code of Conduct

- Be respectful and constructive
- This is a research project; questions and discussions are welcome
- Document your reasoning (especially for design decisions)
- Prioritize correctness over cleverness

---

Contributions of all kinds are welcome.
