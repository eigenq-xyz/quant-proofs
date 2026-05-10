# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (FTAP,
Harrison-Pliska 1981):

> A finite-state, discrete-time market is arbitrage-free iff there exists an equivalent
> martingale measure (EMM).

**Target:** mathlib PR. Code style and naming should follow mathlib conventions from the
start (camelCase definitions, snake_case lemma names, `where` blocks for structures).

## Build & Test Commands

- `lake exe cache get` — fetch mathlib build cache (run after `lake update`)
- `lake build` — build the library
- `lake update` — refresh mathlib dependency to current master
- `lake build --watch` — rebuild on file changes

## Architecture

Single Lean library `Ftap`. Submodules to be added under `Ftap/` as the formalization
develops (e.g., `Ftap.Market`, `Ftap.Arbitrage`, `Ftap.MartingaleMeasure`, `Ftap.Theorem`).

## Constraints

- This is a **public repo.** Don't import private context from `~/ode/eigenq/` (transcript,
  internship strategy, etc.) into commits, READMEs, or PRs.
- Apache 2.0 license matches mathlib's so this work can flow upstream.
