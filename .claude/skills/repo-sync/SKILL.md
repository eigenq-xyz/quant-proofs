---
name: repo-sync
description: >
  Audits the repo's own docs/skills for structural drift against DEPENDENCY_GRAPH.md
  (the ground truth, generated from Lean source). Triggered when adding, moving,
  archiving, or renaming a subproject, or when a doc/skill's project map, build-loop
  directory list, or subdir count is suspected stale. Fixes the exact failure mode
  found and corrected 2026-07-02: onboard-to-eigenq, work_queue_status.md, and 18
  skills all silently went stale after the foundations/extensions restructure and the
  backtest-proofs archival, some for multiple release cycles.
---

# Repo Sync Audit

This exists because multi-file drift happened and went unnoticed through several
doc-rewrite passes. On 2026-07-02: `onboard-to-eigenq` (the mandatory session-start
skill) still described `backtest-proofs/` as a live top-level project with 26 theorems
and Cython FFI — it had been archived, superseded by `research-pipeline`, the actual
flagship, which `onboard-to-eigenq` never mentioned at all. `work_queue_status.md`
described phases as "in progress" that had already shipped the same day per git log. 18
more skills had the same `backtest-proofs`-as-live-path bug; several had verification
loops that silently stopped covering entire subdirs (`optimization-proofs`,
`portfolio-proofs`, and others were missing from `verify-lean`'s build loop with no
error, just silent under-coverage). `DEPENDENCY_GRAPH.md`, dated the same day as some of
the stale files, was already correct. Staleness here isn't about age — it's about which
files get regenerated on a restructure and which get missed.

## Trigger

- A subproject is added, moved, renamed, or archived (`foundations/`/`extensions/`
  membership changes, or a directory is added/removed under either).
- Before merging any PR that touches repo structure (new `lakefile.lean`, new top-level
  dir, an `archive/` move).
- When asked "is this doc/skill still accurate," or when a build/verify command in a
  skill fails in a way that suggests a stale path (e.g., `cd: no such file or directory`).
- Periodically, if it's been a while since the last audit — check `DEPENDENCY_GRAPH.md`'s
  own "Status as of this audit" date against the most recent structural commit.

## Ground truth hierarchy

1. **The actual directory listing and Lean/Python source** — always wins.
2. **`DEPENDENCY_GRAPH.md`** — generated from source, regenerate-on-demand, trust this
   over any hand-written prose doc.
3. **`onboard-to-eigenq/SKILL.md`'s project map and "Build and test commands" table** —
   the canonical hand-written summary; every other skill's directory lists should match
   this table exactly, not redefine their own.
4. **Everything else** (root `CLAUDE.md`, subdir `CLAUDE.md` files, other skills) —
   defers to 1-3, never a competing source of truth for repo structure.

## Audit protocol

### 1. Get the real structure
```bash
find . -maxdepth 2 -type d -not -path "./.git*" -not -path "*/.lake*" -not -path "./.pi*" \
  -not -path "*/node_modules*" -not -path "*/.venv*" | sort
```
Cross-check against `DEPENDENCY_GRAPH.md`'s "Project topology" section (regenerate that
file first if it's plausibly stale — check its own "Status as of this audit" line's age
against recent structural commits).

### 2. Check onboard-to-eigenq against the real structure
Read `onboard-to-eigenq/SKILL.md`'s project map and build-command table. Every live
subdir from step 1 must appear; every subdir it lists must still exist; every
namespace/path it gives must be current (note: a Lean *namespace* like `BacktestProofs`
can correctly persist after a directory rename for historical continuity — check the
target subdir's own `CLAUDE.md` before assuming a namespace mismatch is a bug, it might
be intentional).

### 3. Grep every skill for hardcoded subdir lists
```bash
grep -rlE "for dir in|backtest-proofs|foundations/[a-z-]+|extensions/[a-z-]+" .claude/skills/*/SKILL.md .claude/agents/*/agent.md
```
For every hit with a `for dir in ...` loop or an enumerated subdir list: count the
entries and compare against the real subdir count from step 1. A loop with fewer entries
than the real subdir count is silently under-covering — this is the failure mode that
hid an entire missing `optimization-proofs`/`portfolio-proofs` build check with no error
message.

### 4. Check for archived-but-still-described-as-live projects
```bash
ls archive/
```
For each archived project name, grep the rest of the repo's skills/docs for that name
appearing OUTSIDE a context that says "archived," "superseded," or "historical":
```bash
grep -rn "<archived-project-name>" .claude/ CLAUDE.md */CLAUDE.md 2>/dev/null | grep -viE "archiv|supersed|histor"
```
Any hit is either a stale live-path reference (fix it) or a legitimate namespace
reference in a resurrected module (verify against that module's own CLAUDE.md before
touching).

### 5. Check work_queue_status.md / any phase-tracker doc
If a phase/status-tracking doc exists (or is recreated in the future), cross-check its
described phase state against `git log --oneline -20` and `DEPENDENCY_GRAPH.md`'s module
statuses. A doc that says a module is "in progress" or "not started" when
`DEPENDENCY_GRAPH.md` shows it complete and zero-`sorry` is stale — prefer retiring such
docs in favor of `gh issue`/`gh api milestones` (the canonical planning system per root
`CLAUDE.md`) over maintaining a third parallel status tracker.

### 6. Produce a status block

```
┌─ REPO SYNC AUDIT ────────────────────────────────────────────┐
│ DEPENDENCY_GRAPH.md last regenerated: <date>                 │
│ Real subdir count: <N>                                       │
│ ─────────────────────────────────────────────────────────── │
│ IN SYNC                                                       │
│  • <file> — matches real structure                           │
│ STALE (flag, fix before proceeding)                           │
│  • <file> — <what's wrong> — <fix>                            │
│ UNDER-COVERING (silent, no error, but incomplete)              │
│  • <file>'s <loop/list> — has N entries, should have M         │
└────────────────────────────────────────────────────────────┘
```

## When you restructure the repo (add/move/archive a subproject)

Do these in the same PR, not as a follow-up:
1. Regenerate or hand-update `DEPENDENCY_GRAPH.md` to reflect the new topology.
2. Update `onboard-to-eigenq/SKILL.md`'s project map AND build-command table.
3. Re-run step 3's grep and fix every hardcoded subdir list found, including in
   `.claude/agents/*/agent.md`.
4. If archiving: confirm the archived name doesn't appear as a live reference anywhere
   (step 4). If a Lean namespace is being resurrected under a new directory name, note
   the historical-continuity reason in that subdir's own `CLAUDE.md` explicitly (see
   `extensions/hedge-proofs/CLAUDE.md`'s "Namespace: `BacktestProofs` (historical
   name...)" line as the pattern to follow).
5. If `.pi/skills/` exists, re-run `./setup_pi.sh` — it's generated, not hand-synced, and
   goes stale silently otherwise.
6. Re-run this skill's full audit once more to confirm zero stale/under-covering hits
   remain.

## What NOT to do

- Don't hand-edit `DEPENDENCY_GRAPH.md`'s topology sections without regenerating from
  source — it's supposed to be machine-generated ground truth; hand edits can drift from
  the Lean source the same way prose docs do.
- Don't fix a stale path by guessing the current one — check the actual directory
  listing and the target subdir's own `CLAUDE.md` first, the way the 2026-07-02 fix
  distinguished the basis-point Lean-export FFI boundary (`hedge-proofs`) from the
  separate float64 Cython FFI boundary (`optimization-proofs`/`portfolio-proofs`) rather
  than conflating them.
- Don't assume `backtest-proofs`-style path bugs are the only failure mode — the same
  under-coverage pattern (a hardcoded loop missing new subdirs) can recur with any
  future new module unless step 3's grep becomes a habit on every structural change.
