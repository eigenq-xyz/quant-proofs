# Setting up Lean 4 — Reference

## elan: toolchain management

elan manages multiple Lean 4 toolchains side-by-side, similar to `rustup`.

```bash
elan --version                              # verify install
elan toolchain list                         # list installed toolchains
elan toolchain install leanprover/lean4:v4.27.0-rc1   # install a specific version
elan toolchain uninstall leanprover/lean4:v4.24.0     # remove an old version
elan show                                  # show active toolchain for cwd
elan override set leanprover/lean4:v4.27.0-rc1        # pin a directory's toolchain
```

The `lean-toolchain` file in each subproject root overrides the global default.
Its contents are a single line, e.g. `leanprover/lean4:v4.27.0-rc1`.
elan reads this file automatically; you should not need to set overrides manually.

## Lake commands

`lake` is the Lean 4 build system. All commands run from the subproject root
(the directory containing `lakefile.toml`).

| Command | Purpose |
|---------|---------|
| `lake build` | Build the whole project and its dependencies |
| `lake build BacktestProofs.Basic` | Build a single module |
| `lake clean` | Delete all build artifacts (forces full rebuild) |
| `lake update` | Re-resolve package dependencies from `lakefile.toml` |
| `lake exe cache get` | Download pre-compiled mathlib `.olean` files |
| `lake exe cache put` | Upload local build artifacts to the cache (CI use) |
| `lake exe verify-trace <file.json>` | Run the mortgage-proofs trace checker |
| `lake env` | Print environment variables lake sets for its subprocesses |
| `lake --help` | Full command listing |

**Order matters for first-time setup:**
`lake update` → `lake exe cache get` → `lake build`

If you skip `lake exe cache get`, mathlib compiles from source (~30-60 min).

## VS Code InfoView: reading goals

The InfoView panel (open with `Ctrl+Shift+Enter`) shows:

```
⊢ n + 0 = n
```

The `⊢` symbol is the "turnstile" — everything to its right is the current goal.
Above it, local hypotheses are listed by name and type:

```
n : ℕ
h : n > 0
⊢ n + 0 = n
```

**Reading a tactic proof in InfoView:**
- Place the cursor *before* a tactic to see the goal it is applied to.
- Place the cursor *after* a tactic to see the goal it produces (or `Goals accomplished` if done).
- Use `#check` to inspect any term's type without being in a proof:
  ```lean
  #check Nat.add_zero   -- Nat.add_zero : ∀ (n : ℕ), n + 0 = n
  ```
- Use `#eval` to run pure computation:
  ```lean
  #eval Finset.sum (Finset.range 5) id   -- 10
  ```

## Key mathlib tactics

| Tactic | When to use |
|--------|-------------|
| `simp [lemma1, lemma2]` | Simplification; always name the lemmas — bare `simp` is fragile |
| `ring` | Closes goals that are ring equalities (e.g., `a * b + b * a = 2 * a * b`) |
| `omega` | Closes linear arithmetic goals over `ℤ` or `ℕ` |
| `norm_num` | Evaluates numeric expressions (`2 ^ 10 = 1024`) |
| `decide` | Closes decidable propositions by evaluation; avoid for non-trivial props |
| `exact?` | Search for a term that closes the exact goal |
| `apply?` | Search for a lemma whose conclusion unifies with the goal |
| `simp?` | Run simp, then report which simp lemmas were needed |
| `constructor` | Splits an `And` or `Iff` goal into its two parts |
| `cases h` | Case-splits on an inductive type or proposition `h` |
| `induction n` | Proof by induction on a natural number or inductive type |
| `linarith` | Closes linear arithmetic goals; can use hypotheses automatically |
| `field_simp` | Simplifies field expressions, clearing denominators |
| `push_neg` | Pushes negations inward (`¬ ∀ x, P x` → `∃ x, ¬ P x`) |
| `contrapose` | Switches to the contrapositive of the goal |
| `by_contra h` | Introduces `h : ¬ goal` and changes goal to `False` |
| `rcases h with ⟨a, b⟩` | Destructs existentials and products cleanly |
| `obtain ⟨a, ha⟩ := h` | Destructs and names components simultaneously |
| `ext` | Proves function/set equality by extensionality |
| `funext x` | Proves function equality by showing equality at each `x` |
| `gcongr` | Congruence lemma for inequalities in a structured way |
| `positivity` | Proves positivity goals (`0 < expr`, `0 ≤ expr`) |

## Import patterns

Always import specific mathlib modules, never the whole library:

```lean
-- CORRECT
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Data.Real.Basic

-- WRONG — imports everything, causes slow builds, rejected upstream
import Mathlib
```

Finding the right import:
1. Search [mathlib4 docs](https://leanprover-community.github.io/mathlib4_docs/) by lemma name.
2. Use `#check` in a file that already `import Mathlib` (a scratch file) to find the module.
3. The module path mirrors the import path: `Mathlib.Data.Finset.Basic` is in
   `Mathlib/Data/Finset/Basic.lean` in the mathlib4 repository.

## lakefile.toml structure

Each subproject has a `lakefile.toml`. The key sections:

```toml
name = "backtest-proofs"          # package name
defaultTargets = ["BacktestProofs"]  # default build target

[[require]]
name = "mathlib"
from = git "https://github.com/leanprover-community/mathlib4"
rev = "v4.27.0"                   # must match or be compatible with lean-toolchain

[[lean_lib]]
name = "BacktestProofs"           # Lean 4 library name = namespace root
```

After editing `lakefile.toml` (e.g., to pin a new mathlib rev), run:
```bash
lake update && lake exe cache get && lake build
```

## Subproject build roots

| Subdir | `lakefile.toml` location | Default `lake build` target |
|--------|--------------------------|-----------------------------|
| `backtest-proofs/` | `backtest-proofs/lean/lakefile.toml` | `BacktestProofs` |
| `ftap-proofs/` | `ftap-proofs/lakefile.toml` | `FtapProofs` |
| `options-proofs/` | `options-proofs/lakefile.toml` | `OptionsProofs` |
| `mortgage-proofs/` | `mortgage-proofs/lakefile.toml` | `MortgageProofs` |

Always `cd` to the directory containing `lakefile.toml` before running `lake` commands.
