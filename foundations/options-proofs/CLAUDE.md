# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein (CRR) binomial model. The CRR
model is a finite-state, discrete-time market where the FTAP from `ftap-proofs` applies,
giving an explicit risk-neutral measure. Put-call parity is a corollary.

## Build & Test Commands

- `lake exe cache get` — fetch mathlib build cache (run after `lake update`)
- `lake build` — build the library
- `lake update` — refresh dependencies (mathlib; later `ftap-proofs`)
- `lake build --watch` — rebuild on file changes

## Architecture

Single Lean library `OptionsProofs`. Submodules to be added under `OptionsProofs/` as the
formalization develops (e.g., `OptionsProofs.Tree`, `OptionsProofs.RiskNeutral`,
`OptionsProofs.PutCallParity`).

## Dependencies

- `quant-core` — shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems).
- `mathlib` — measure theory, expectation, finite probability.
- `ftap-proofs` (planned) — once it exposes a stable interface for EMMs and no-arbitrage.

## Constraints

- This is a **public repo.** Don't import private context from `~/ode/eigenq/` (transcript,
  internship strategy, etc.) into commits, READMEs, or PRs.
- Apache 2.0 license matches mathlib's so the FTAP work can flow upstream.
