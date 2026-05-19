/-
Copyright (c) 2026 eigenq-xyz Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

/-!
# QuantCore

Shared pricing primitives for the quant-proofs monorepo.

This library provides types and theorems that are independent of any specific
backtester or pipeline, and can be imported by any sibling project.

## Module structure

```
QuantCore/Option.lean            — AssetId, OptionKind, EuropeanOption, payoff functions
QuantCore/OptionInvariants.lean  — 8 pure payoff theorems (no portfolio dependencies)
QuantCore/Tests/UnitTests.lean   — Concrete payoff tests via native_decide
```
-/
