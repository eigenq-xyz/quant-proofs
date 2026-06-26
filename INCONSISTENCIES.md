# Repo inconsistencies — audit notes (2026-06-14)

Findings from a "did you really prove it?" audit
([leanprover-community checklist](https://leanprover-community.github.io/did_you_prove_it.html)).
Ground truth was established from the Lean source and `#print axioms`, not from any README.

## Update 2026-06-26 (dependency-graph audit)

Re-verified against the live source. Resolved since the original notes:

- **TODO 2 (Jensen `sorry`) is RESOLVED.** `extensions/stopped-time-proofs/StoppedTimeProofs/Jensen.lean`
  has zero `sorry` (grep and `#print axioms` both clean). The abstract `geometricExpectation_jensen`
  (G2.2) was dropped and replaced by the targeted `geometricExpectation_strict_mono`, which is now
  load-bearing: it is the sole engine behind `perpetual-proofs` Theorem 3
  (`inverse_perp_convexity_discount`). It is NOT unused. The root `README.md` and the
  `StoppedTimeProofs.lean` docstring have been corrected to "Complete".
- **TODO 3 (stray nested duplicate dir) is RESOLVED.** `extensions/stopped-time-proofs/stopped-time-proofs/`
  no longer exists.
- **TODO 1 (toolchain divergence) is RESOLVED.** PR #171 unified all 8 projects to
  `leanprover/lean4:v4.30.0` and mathlib rev `5719ef278ac6921b1a68b558d9282377f93d0b80`. A fresh
  clone now builds without `incompatible header` errors.

Still open:

- **`perpetual-proofs`** imports `FtapProofs.Market` but cites no ftap
  declaration (the import is vestigial). Its `CLAUDE.md`/`SPEC.md` defer the real link to "once
  ftap-proofs Phase 4 is proved" via a `-- TODO: unify with FtapProofs.MartingaleMeasure.EMM` note.
  ftap-proofs is now Complete (`ftap`, clean axioms), so that unification is unblocked: either
  replace `OnePeriodEMM` with `FtapProofs.EquivalentMartingaleMeasure`, or drop the vestigial import.
  See `DEPENDENCY_GRAPH.md` section 9.

## Verified-good (no action)

- `FtapProofs.ftap` — axioms `[propext, Classical.choice, Quot.sound]`; faithful statement
  (no-arb ⟺ EMM, standard full-support hypothesis, real separating-hyperplane proof).
- `OptionsProofs.put_call_parity` — same clean axiom set; genuine CRR EMM + no-arb derivation.
- `PerpetualProofs.perp_futures_no_arb_price` and `inverse_perp_convexity_discount` — both
  clean axioms; they do **not** transitively use the open Jensen lemma.
- `native_decide` appears only in `quant-core` test `example`s (not load-bearing).

## Fixed this session

- **Root `README.md`** "Active projects" table: `ftap-proofs` was "In progress" (actually
  Complete), `options-proofs` was "Planned" (actually Complete); `optimization`, `stopped-time`,
  `perpetual`, `portfolio` were missing. Added a status legend and accurate per-module rows.
- **`docs/ftap-proofs.md`** and **`docs/options-proofs.md`**: removed stale
  "In progress — skeleton scaffolded"; now state Complete + verified axioms.
- **`perpetual-proofs`**: rebuilt under `v4.30.0` (was failing to load against rc2-built ftap
  oleans). Now builds clean (2652 jobs) and headline theorems are axiom-verified.

## TODO (still need to do)

1. **Align Lean toolchains. DONE (PR #171).** The modules previously diverged across
   `v4.30.0-rc2` (`ftap-proofs`, `options-proofs`, `quant-core`, `optimization-proofs`),
   `v4.30.0` (`stopped-time-proofs`, `perpetual-proofs`), and `v4.26.0` (`mortgage-proofs`),
   which caused `incompatible header` failures on a fresh clone because `perpetual-proofs`
   `require`s `ftap-proofs` by local path. PR #171 pinned all 8 projects to the single canonical
   `v4.30.0` + mathlib `5719ef27` and rebuilt, so a fresh clone / CI no longer hits this.

2. **`stopped-time-proofs` Jensen G2.2.** `geometricExpectation_jensen` (`StoppedTimeProofs/Jensen.lean:~92`)
   is an open `sorry` — confirmed via `#print axioms` (`sorryAx`). It's a mathlib-candidate file
   shipping with a `sorry`. Not used by perpetual's headline theorems, but the lemma itself is
   unproven. Prove it, or clearly mark the file as WIP so it isn't mistaken for complete.

3. **Remove the stray nested duplicate dir** (left for you — not deleted):
   `extensions/stopped-time-proofs/stopped-time-proofs/StoppedTimeProofs/Jensen.lean` — untracked accidental
   copy, has its own `sorry` (line 102), differs from the real file. Run:
   ```bash
   rm -rf extensions/stopped-time-proofs/stopped-time-proofs
   ```

4. **`.claude/skills/verify-lean/SKILL.md` is stale** — builds the **archived** `backtest-proofs/lean`
   and omits `stopped-time`, `optimization`, `perpetual`. My edit was blocked by the auto-permission
   classifier (it guards skill/config files), so **apply this manually**:
   - Module set / build order (deps respected):
     ```
     COMPLETE: foundations/quant-core/lean  ftap-proofs  options-proofs  optimization-proofs  extensions/mortgage-proofs/lean
     WIP:      stopped-time-proofs  perpetual-proofs
     ```
   - Drop `backtest-proofs/lean` entirely (archived).
   - Treat `stopped-time`/`perpetual` as report-only (stopped-time has the known Jensen `sorry`).
   - Add the authoritative gate: `#print axioms <headline thm>` must be ⊆
     `[propext, Classical.choice, Quot.sound]` (no `sorryAx`, no `Lean.ofReduceBool`).
   - The zero-sorry grep should `--exclude-dir=.lake`, skip `extensions/stopped-time-proofs/stopped-time-proofs/`,
     and strip `--` comments (docstrings saying "0 sorry" cause false positives).

5. **Same stale `backtest-proofs` reference** in `.claude/skills/write-lean4-proofs/ANTI_PATTERNS.md`
   (the `sorry`-on-main example) — update to a current module.

6. **Root `CLAUDE.md`** is modified/uncommitted — review for the same `backtest-proofs` / old
   module-list staleness while you're in there.

7. **Awareness only:** `docs/_toc.yml` lists `backtest-proofs` under Archive and `reports/` still
   has `backtest-proofs_files` — fine if intentional (archived), just confirm.
