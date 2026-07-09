---
name: setup-lean4
description: >
  First-time and recurring Lean 4 environment setup for a quant-proofs subproject.
  Use when installing or diagnosing elan/lake, fetching the mathlib cache,
  building a subproject for the first time, or troubleshooting VS Code InfoView.
  Also use when a lake build fails due to environment or cache issues.
paths:
  - "**/*.lean"
  - "**/lakefile.*"
  - "**/lean-toolchain"
allowed-tools: >
  Bash(lake build *)
  Bash(lake exe *)
  Bash(lake clean)
  Read
  Grep
  Glob
---

# Setting up Lean 4

## Prerequisites

Three things must be in place before building any subproject:

1. **elan** — the Lean version manager (like `rustup` for Rust). Manages Lean toolchains.
2. **lake** — the Lean build system, bundled with elan.
3. **An editor** — VS Code with the `lean4` extension is standard. JetBrains works too,
   but InfoView is VS Code-first.

## Installing elan

```bash
curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y
# Then restart your shell or:
source ~/.elan/env
```

Verify: `elan --version` and `lake --version` should both print version strings.

`elan` not on PATH after install? Add `~/.elan/bin` to your `PATH` in `~/.zshrc` or
`~/.bashrc`.

## First-time setup for a subproject

Work always happens inside a specific subdir. Replace `<subdir>` with one of
`research-pipeline/lean`, `foundations/quant-core/lean`, `foundations/ftap-proofs`,
`foundations/options-proofs`, `foundations/portfolio-proofs/lean`, `extensions/vrp-proofs`,
`extensions/hedge-proofs`, `extensions/perpetual-proofs`, `extensions/stopped-time-proofs`,
or `extensions/mortgage-proofs`.

```bash
cd /Users/akhilkarra/ode/eigenq/quant-proofs/<subdir>
```

**Step 1 — Fetch the mathlib cache (CRITICAL, run first):**

```bash
lake exe cache get
```

Downloads pre-compiled `.olean` files for the mathlib version pinned in `lakefile.toml`.
Skip this and you trigger a full mathlib rebuild — 30-60 minutes.

**Step 2 — Build the subproject:**

```bash
lake build
```

Must exit 0. If not, see "Common issues" below.

**Step 3 — Verify zero sorry (for main branch):**

```bash
grep -rn sorry --include="*.lean" .
```

Must produce no output on `main`. Any `sorry` is a CI failure.

## VS Code setup

1. Install the `lean4` extension (identifier: `leanprover.lean4`).
2. Open the subproject directory as the workspace root, not the monorepo root.
3. Open a `.lean` file. The extension reads `lean-toolchain` to select the Lean version.

**InfoView:** shows the current proof goal and type information.
- Open/close: `Ctrl+Shift+Enter` (macOS: `Cmd+Shift+Enter`)
- Place the cursor inside a `by` block to see the goal at that point.
- `#check Nat.add_comm` — prints the type of any term in InfoView.
- `#eval 2 + 2` — evaluates an expression and prints the result.

## Mathlib search tactics

Use these inside a proof to discover what mathlib already has:

| Tactic | What it does |
|--------|-------------|
| `exact?` | Searches for a term that closes the goal exactly |
| `apply?` | Searches for lemmas that unify with the goal |
| `simp?` | Runs simp and reports which lemmas it used |
| `decide?` | Checks if the goal is decidable and suggests `decide` |

Also search [loogle.lean-lang.org](https://loogle.lean-lang.org) by type signature, and
[mathlib4 docs](https://leanprover-community.github.io/mathlib4_docs/) by name.

## CI checks

Two mandatory checks:

```bash
# 1. No sorry
grep -rn sorry --include="*.lean" <subdir>/
# Expected output: (none)

# 2. Clean build
cd <subdir> && lake build
# Expected exit code: 0
```

Both run automatically in pre-commit hooks. Do not disable them.

## Common issues

**Mathlib cache miss (slow rebuild):**
Symptom: `lake build` starts compiling `Mathlib.*` files one by one.
Fix: `lake exe cache get` — you skipped step 1, or the cache server was temporarily
unavailable. If `cache get` itself fails, check internet access and retry; builds still
succeed, just slowly.

**`elan` not on PATH:**
Symptom: `command not found: lake` or `command not found: elan`.
Fix: `source ~/.elan/env` or add `~/.elan/bin` to your shell's PATH permanently.

**Wrong toolchain version:**
Symptom: `error: toolchain 'leanprover/lean4:v4.x.x' is not installed`.
Fix: `elan toolchain install leanprover/lean4:v4.27.0-rc1` (or the version in
`lean-toolchain`). elan reads the `lean-toolchain` file automatically once the toolchain
is installed.

**Lake package resolution failure:**
Symptom: `error: unknown package 'Mathlib'` or similar.
Fix:
```bash
lake update   # re-resolves dependencies from lakefile.toml
lake exe cache get
lake build
```

**`options-proofs` fails to build:**
This subproject imports `FtapProofs`. Build `ftap-proofs` first:
```bash
cd /Users/akhilkarra/ode/eigenq/quant-proofs/foundations/ftap-proofs && lake build
cd /Users/akhilkarra/ode/eigenq/quant-proofs/foundations/options-proofs && lake build
```

## Quick reference

```bash
# One-liner: clean slate for a subproject
cd <subdir> && lake clean && lake exe cache get && lake build
```

See REFERENCE.md for the full lake command listing and VS Code InfoView reading guide.
