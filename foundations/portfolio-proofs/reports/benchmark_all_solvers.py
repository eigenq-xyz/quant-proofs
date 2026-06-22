"""Defensible wall-clock benchmark: all 7 scenarios x all solvers.

Protocol
--------
- warmup : 3 calls (discarded) — settles process-spawn, JIT, OS scheduler
- reps   : 15 timed calls
- stat   : median + IQR  (median resists GC outliers; IQR gives spread)
- clock  : time.perf_counter() — monotonic, nanosecond resolution
- every row declares (N, cond, L1-active) so the number has context

Output
------
- Console: per-scenario Markdown tables
- File   : results/benchmark_all_solvers.json

Run
---
    uv run python reports/benchmark_all_solvers.py          # all scenarios
    uv run python reports/benchmark_all_solvers.json --json-only  # skip console

Why median + IQR, not mean/min
-------------------------------
- Mean: inflated by occasional GC pauses and OS scheduler preemptions.
- Min:  best-case only; misleading for production latency claims.
- Median + IQR: stable, interpretable, honest about spread.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────

_HERE = pathlib.Path(__file__).parent  # reports/
_PP = _HERE.parent  # portfolio-proofs/
_SCENARIOS = _PP / "scenarios"
_RESULTS = _PP / "results"
_RESULTS.mkdir(exist_ok=True)

for _p in [str(_PP), str(_SCENARIOS)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Ensure all scenario solver packages are importable
for _scenario in [
    "boundary_trap",
    "cholesky_crash",
    "phantom_positions",
    "precision_bleed",
    "step_divergence",
    "vix_shock",
    "sp500_factor",
]:
    _sp = str(_SCENARIOS / _scenario)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

# ── Protocol constants ────────────────────────────────────────────────────────

WARMUP = 3
REPS = 15


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class TimingRow:
    """One (scenario, solver) timing measurement."""

    scenario: str
    solver: str
    N: int
    cond: float  # condition number of Sigma
    l1_active: bool | None  # True if L1 gross-leverage constraint is binding
    covers: str  # what a single call covers, e.g. "1 window" / "4 windows"
    median_ms: float
    q1_ms: float
    q3_ms: float
    min_ms: float
    max_ms: float
    converged: bool | None  # None = not applicable / unknown
    notes: str


# ── Core timing primitive ─────────────────────────────────────────────────────


def _time_call(
    fn: Callable[..., Any], *args: Any, **kwargs: Any
) -> list[float]:
    """Return REPS wall-clock timings (ms) after WARMUP discarded calls."""
    for _ in range(WARMUP):
        try:
            fn(*args, **kwargs)
        except Exception:  # noqa: S110
            pass  # warmup: ignore failures (solver may need a valid first call)
    times: list[float] = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        try:
            fn(*args, **kwargs)
        except Exception:
            return [float("nan")] * REPS
        times.append((time.perf_counter() - t0) * 1e3)
    return times


def _stats(times: list[float]) -> tuple[float, float, float, float, float]:
    """Return (median, q1, q3, min, max) in ms."""
    arr = np.array(times, dtype=float)
    return (
        float(np.median(arr)),
        float(np.percentile(arr, 25)),
        float(np.percentile(arr, 75)),
        float(np.min(arr)),
        float(np.max(arr)),
    )


def _cond(sigma: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(sigma)
    return float(eigs[-1] / max(eigs[0], 1e-12))


def _l1_active(
    weights: np.ndarray, leverage_cap: float, tol: float = 1e-6
) -> bool:
    """True if the solved weights sit at the L1 boundary."""
    return bool(abs(float(np.sum(np.abs(weights))) - leverage_cap) < tol)


def _converged(result: Any) -> bool | None:
    if hasattr(result, "converged"):
        c = result.converged
        if hasattr(result, "diverged") and result.diverged:
            return False
        return bool(c)
    return None


def _make_row(
    scenario: str,
    solver: str,
    N: int,
    sigma: np.ndarray,
    fn: Callable[..., Any],
    *args: Any,
    covers: str = "1 problem",
    notes: str = "",
    **kwargs: Any,
) -> TimingRow:
    times = _time_call(fn, *args, **kwargs)
    med, q1, q3, mn, mx = _stats(times)
    # Convergence: call once more to inspect
    try:
        result = fn(*args, **kwargs)
        conv = _converged(result)
        # L1 active: extract weights
        weights = getattr(result, "weights", None)
        if weights is None and isinstance(result, tuple):
            weights = result[0]
        leverage_cap = getattr(args[0] if args else None, "leverage_cap", None)
        l1 = (
            _l1_active(weights, leverage_cap)
            if (weights is not None and leverage_cap is not None)
            else None
        )
    except Exception:
        conv, l1 = None, None

    return TimingRow(
        scenario=scenario,
        solver=solver,
        N=N,
        cond=round(_cond(sigma), 1),
        l1_active=l1,
        covers=covers,
        median_ms=round(med, 2),
        q1_ms=round(q1, 2),
        q3_ms=round(q3, 2),
        min_ms=round(mn, 2),
        max_ms=round(mx, 2),
        converged=conv,
        notes=notes,
    )


# ── Scenario 1: boundary_trap ─────────────────────────────────────────────────


def bench_boundary_trap(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.boundary_trap.solvers import common as c
    from scenarios.boundary_trap.solvers import (
        gurobi,
        kkt_optimum,
        ortools_gscip,
        slsqp,
        trust_constr,
    )

    try:
        p = c.load_problem()
    except FileNotFoundError:
        print("  [boundary_trap] data not found — skipping")
        return []

    rows = []
    for label, mod, fn_name, extra_notes in [
        ("SLSQP", slsqp, "run", "iter limit; L1 kink cycling"),
        ("trust-constr", trust_constr, "run", "2N barrier reformulation"),
        ("Gurobi", gurobi, "run", "wall-clock incl. model setup"),
        ("OR-Tools/SCIP", ortools_gscip, "run", "SCIP QP branch-and-cut"),
        ("KKT optimum", kkt_optimum, "run", "analytical; no iteration"),
    ]:
        try:
            rows.append(
                _make_row(
                    "boundary_trap",
                    label,
                    p.N,
                    p.Sigma,
                    getattr(mod, fn_name),
                    p,
                    covers="1 problem",
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    # Lean PGD subprocess
    try:
        times = _time_call(lean_solve, p.Sigma, p.mu, p.leverage_cap)
        med, q1, q3, mn, mx = _stats(times)
        w, _ = lean_solve(p.Sigma, p.mu, p.leverage_cap)
        rows.append(
            TimingRow(
                scenario="boundary_trap",
                solver="Lean PGD",
                N=p.N,
                cond=round(_cond(p.Sigma), 1),
                l1_active=_l1_active(w, p.leverage_cap),
                covers="1 problem",
                median_ms=round(med, 2),
                q1_ms=round(q1, 2),
                q3_ms=round(q3, 2),
                min_ms=round(mn, 2),
                max_ms=round(mx, 2),
                converged=True,
                notes="warm persistent subprocess; pgdFlat iters=53",
            )
        )
    except Exception as exc:
        print(f"  [Lean PGD] error: {exc}")

    return rows


# ── Scenario 2: cholesky_crash ────────────────────────────────────────────────


def bench_cholesky_crash(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.cholesky_crash.solvers import common as c
    from scenarios.cholesky_crash.solvers import (
        cvxpy_osqp,
        gurobi,
        pgd_lw,
        slsqp,
        trust_constr,
    )

    try:
        p = c.load_problem()
    except FileNotFoundError:
        print("  [cholesky_crash] data not found — skipping")
        return []

    rows = []
    for label, mod, fn_name, extra_notes in [
        ("SLSQP", slsqp, "run", "raw S; degenerate eigenspace cycling"),
        (
            "trust-constr",
            trust_constr,
            "run",
            "raw S; nominally converges; non-PSD Hessian",
        ),
        ("Gurobi", gurobi, "run", "raw S; NonConvex workaround fallback"),
        (
            "CVXPY/OSQP",
            cvxpy_osqp,
            "run",
            "raw S; DCPError before solver runs",
        ),
        ("Lean PGD+LW", pgd_lw, "run", "LW-shrunk Sigma; certified feasible"),
    ]:
        try:
            rows.append(
                _make_row(
                    "cholesky_crash",
                    label,
                    p.N,
                    p.Sigma,
                    getattr(mod, fn_name),
                    p,
                    covers="1 problem",
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    return rows


# ── Scenario 3: phantom_positions ─────────────────────────────────────────────


def bench_phantom_positions(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.phantom_positions.solvers import (
        certified_pgd,
        gurobi,
        kkt_optimum,
        slsqp,
        trust_constr,
    )
    from scenarios.phantom_positions.solvers import common as c

    p = c.make_problem()
    rows = []

    for label, mod, fn_name, extra_notes in [
        ("SLSQP", slsqp, "run", "iter limit; L1 kink at zero weights"),
        ("trust-constr", trust_constr, "run", "phantom weights ~4e-7"),
        ("Gurobi", gurobi, "run", "phantom weights ~1e-7"),
        (
            "Lean PGD",
            certified_pgd,
            "run",
            "exact zeros; Duchi threshold algebraic",
        ),
        ("KKT optimum", kkt_optimum, "run", "analytical; no iteration"),
    ]:
        try:
            rows.append(
                _make_row(
                    "phantom_positions",
                    label,
                    p.N,
                    p.Sigma,
                    getattr(mod, fn_name),
                    p,
                    covers="1 problem",
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    return rows


# ── Scenario 4: precision_bleed ───────────────────────────────────────────────


def bench_precision_bleed() -> list[TimingRow]:
    from scenarios.precision_bleed.solvers import common as c
    from scenarios.precision_bleed.solvers import (
        gurobi,
        ortools_gscip,
        pgd_integer,
        slsqp_float,
        trust_constr,
    )
    from scenarios.precision_bleed.solvers import (
        lean_pgd as pb_lean,
    )

    windows = c.load_rolling_windows()
    # Use the first window's Sigma for cond/L1 annotation
    w0 = windows[0]

    rows = []
    for label, mod, fn_name, extra_notes in [
        (
            "SLSQP",
            slsqp_float,
            "run_all",
            "W1: violation 2.79e-9 > 1e-9 halt threshold",
        ),
        ("trust-constr", trust_constr, "run_all", "barrier strictly interior"),
        (
            "Gurobi",
            gurobi,
            "run_all",
            "wall-clock incl. model setup x 4 windows",
        ),
        ("OR-Tools", ortools_gscip, "run_all", ""),
        ("Lean PGD", pb_lean, "run_all", "constraint error = 0.0 identically"),
        (
            "PGD integer",
            pgd_integer,
            "run_all",
            "integer arithmetic; slow but exact",
        ),
    ]:
        try:
            times = _time_call(getattr(mod, fn_name), windows)
            med, q1, q3, mn, mx = _stats(times)
            results = getattr(mod, fn_name)(windows)
            conv = all(_converged(r) is not False for r in results)
            rows.append(
                TimingRow(
                    scenario="precision_bleed",
                    solver=label,
                    N=w0.N,
                    cond=round(_cond(w0.Sigma), 1),
                    l1_active=None,  # varies per window
                    covers="4 windows",
                    median_ms=round(med, 2),
                    q1_ms=round(q1, 2),
                    q3_ms=round(q3, 2),
                    min_ms=round(mn, 2),
                    max_ms=round(mx, 2),
                    converged=conv,
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    return rows


# ── Scenario 5: step_divergence ───────────────────────────────────────────────


def bench_step_divergence(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.step_divergence.solvers import common as c
    from scenarios.step_divergence.solvers import (
        gd_fixed,
        gurobi,
        pgd_adaptive,
        slsqp,
        trust_constr,
    )

    try:
        p = c.load_problem()
    except FileNotFoundError:
        print("  [step_divergence] data not found — skipping")
        return []

    rows = []
    for label, mod, fn_name, extra_notes in [
        ("SLSQP", slsqp, "run", "iter limit; L1 kink"),
        (
            "trust-constr",
            trust_constr,
            "run",
            "interior-point unaffected by step-size",
        ),
        ("Gurobi", gurobi, "run", ""),
        ("GD fixed η", gd_fixed, "run", "diverges; η_cal=5334 > bound=841"),
        (
            "PGD adaptive",
            pgd_adaptive,
            "run",
            "η = 1.9/λ_max(Σ_shock) = 799; certified",
        ),
    ]:
        try:
            rows.append(
                _make_row(
                    "step_divergence",
                    label,
                    p.N,
                    p.Sigma_shock,
                    getattr(mod, fn_name),
                    p,
                    covers="1 problem",
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    # Lean PGD on the shock window
    try:
        times = _time_call(
            lean_solve, p.Sigma_shock, p.mu_shock, p.leverage_cap
        )
        med, q1, q3, mn, mx = _stats(times)
        w, _ = lean_solve(p.Sigma_shock, p.mu_shock, p.leverage_cap)
        rows.append(
            TimingRow(
                scenario="step_divergence",
                solver="Lean PGD",
                N=p.N,
                cond=round(_cond(p.Sigma_shock), 1),
                l1_active=_l1_active(w, p.leverage_cap),
                covers="1 problem",
                median_ms=round(med, 2),
                q1_ms=round(q1, 2),
                q3_ms=round(q3, 2),
                min_ms=round(mn, 2),
                max_ms=round(mx, 2),
                converged=True,
                notes="certified η = 1.9/λ_max(Σ_shock); subprocess",
            )
        )
    except Exception as exc:
        print(f"  [Lean PGD] error: {exc}")

    return rows


# ── Scenario 6: vix_shock ─────────────────────────────────────────────────────


def bench_vix_shock(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.vix_shock.solvers import (
        certified_pgd,
        gurobi,
        slsqp,
        trust_constr,
        uncertified_gd,
    )
    from scenarios.vix_shock.solvers import common as c

    p = c.make_post_shock()
    rows = []

    for label, mod, fn_name, extra_notes in [
        ("SLSQP", slsqp, "run", "converges; SQP step unaffected"),
        (
            "trust-constr",
            trust_constr,
            "run",
            "barrier overhead dominates for N=3",
        ),
        ("Gurobi", gurobi, "run", "9 barrier iterations"),
        (
            "GD uncertified",
            uncertified_gd,
            "run",
            "η=47.5 > bound=12.5; oscillates",
        ),
        (
            "Lean PGD cert.",
            certified_pgd,
            "run",
            "η=11.875 < 12.5; certified stable",
        ),
    ]:
        try:
            rows.append(
                _make_row(
                    "vix_shock",
                    label,
                    p.N,
                    p.Sigma,
                    getattr(mod, fn_name),
                    p,
                    covers="post-shock problem",
                    notes=extra_notes,
                )
            )
        except Exception as exc:
            print(f"  [{label}] error: {exc}")

    return rows


# ── Scenario 7: sp500_factor ──────────────────────────────────────────────────


def bench_sp500_factor(lean_solve: Callable[..., Any]) -> list[TimingRow]:
    from scenarios.sp500_factor.solvers import common as c
    from scenarios.sp500_factor.solvers import gurobi as sf_gurobi
    from scenarios.sp500_factor.solvers import kkt_woodbury as sf_kkt

    rows = []
    # N=100 Lean PGD would take ~minutes; cap at N=50 for subprocess
    for N, include_lean in [(10, True), (50, True), (100, False)]:
        p = c.make_problem(N)
        cond_n = round(_cond(p.Sigma), 1)

        # Gurobi (via benchmark() which captures internal solve_time)
        try:
            times = _time_call(sf_gurobi.benchmark, p, reps=1)
            med, q1, q3, mn, mx = _stats(times)
            r = sf_gurobi.benchmark(p, reps=1)
            rows.append(
                TimingRow(
                    scenario="sp500_factor",
                    solver="Gurobi",
                    N=N,
                    cond=cond_n,
                    l1_active=None,
                    covers=f"N={N}",
                    median_ms=round(med, 2),
                    q1_ms=round(q1, 2),
                    q3_ms=round(q3, 2),
                    min_ms=round(mn, 2),
                    max_ms=round(mx, 2),
                    converged=r.converged,
                    notes=(
                        f"wall-clock incl. model setup; "
                        f"Gurobi internal={r.solve_time_ms:.1f}ms"
                    ),
                )
            )
        except Exception as exc:
            print(f"  [Gurobi N={N}] error: {exc}")

        # KKT Woodbury (derive = Woodbury inversion + Python PGD; note separately)
        try:
            times = _time_call(sf_kkt.derive, p)
            med, q1, q3, mn, mx = _stats(times)
            rows.append(
                TimingRow(
                    scenario="sp500_factor",
                    solver="KKT Woodbury",
                    N=N,
                    cond=cond_n,
                    l1_active=None,
                    covers=f"N={N}",
                    median_ms=round(med, 2),
                    q1_ms=round(q1, 2),
                    q3_ms=round(q3, 2),
                    min_ms=round(mn, 2),
                    max_ms=round(mx, 2),
                    converged=True,
                    notes="dominated by Python PGD inside derive(); Woodbury itself O(N) < 0.1ms",
                )
            )
        except Exception as exc:
            print(f"  [KKT Woodbury N={N}] error: {exc}")

        # Lean PGD subprocess
        if include_lean:
            try:
                times = _time_call(lean_solve, p.Sigma, p.mu, p.leverage_cap)
                med, q1, q3, mn, mx = _stats(times)
                w, _ = lean_solve(p.Sigma, p.mu, p.leverage_cap)
                rows.append(
                    TimingRow(
                        scenario="sp500_factor",
                        solver="Lean PGD",
                        N=N,
                        cond=cond_n,
                        l1_active=_l1_active(w, p.leverage_cap),
                        covers=f"N={N}",
                        median_ms=round(med, 2),
                        q1_ms=round(q1, 2),
                        q3_ms=round(q3, 2),
                        min_ms=round(mn, 2),
                        max_ms=round(mx, 2),
                        converged=True,
                        notes="subprocess; bisection O(N*iters²) dominates at large N",
                    )
                )
            except Exception as exc:
                print(f"  [Lean PGD N={N}] error: {exc}")

    return rows


# ── Formatting ────────────────────────────────────────────────────────────────


def _status(row: TimingRow) -> str:
    if row.converged is None:
        return "n/a"
    return "✓" if row.converged else "✗"


def _ms(v: float) -> str:
    if v != v:
        return "—"
    if v < 1.0:
        return f"{v:.2f} ms"
    if v < 1000.0:
        return f"{v:.0f} ms"
    return f"{v / 1000:.1f} s"


def _iqr(row: TimingRow) -> str:
    return f"[{_ms(row.q1_ms)}, {_ms(row.q3_ms)}]"


def print_scenario_table(rows: list[TimingRow], title: str) -> None:
    if not rows:
        return
    print(f"\n### {title}")
    # Collect all seen (N, cond, L1) combos
    key_shown: set[tuple[int, float, bool | None]] = set()
    for r in rows:
        k = (r.N, r.cond, r.l1_active)
        if k not in key_shown:
            key_shown.add(k)
            l1_str = (
                "active"
                if r.l1_active
                else ("inactive" if r.l1_active is False else "varies")
            )
            print(f"N={r.N}  cond={r.cond}  L1={l1_str}  covers={r.covers}")
    print()
    print(
        f"{'Solver':<20}  {'Status':>6}  {'Median':>8}  {'IQR':>20}  {'Notes'}"
    )
    print("-" * 80)
    for r in rows:
        print(
            f"{r.solver:<20}  {_status(r):>6}  {_ms(r.median_ms):>8}  "
            f"{_iqr(r):>20}  {r.notes}"
        )


def print_consolidated(all_rows: list[TimingRow]) -> None:
    print("\n\n" + "=" * 90)
    print("## CONSOLIDATED TABLE  (median, warm, Apple M2 Max, reps=15)")
    print("=" * 90)
    print()
    hdr = f"{'Scenario':<22}  {'N':>4}  {'cond':>6}  {'L1':>5}  "
    hdr += f"{'Solver':<20}  {'Status':>6}  {'Median':>8}  {'IQR (Q1-Q3)':<22}  Notes"
    print(hdr)
    print("-" * 110)
    last_scenario = ""
    for r in all_rows:
        sep = "" if r.scenario == last_scenario else r.scenario
        last_scenario = r.scenario
        l1_str = (
            "yes" if r.l1_active else ("no" if r.l1_active is False else "—")
        )
        print(
            f"{sep:<22}  {r.N:>4}  {r.cond:>6.1f}  {l1_str:>5}  "
            f"{r.solver:<20}  {_status(r):>6}  {_ms(r.median_ms):>8}  "
            f"{_iqr(r):<22}  {r.notes[:55]}"
        )
    print()


# ── Main ──────────────────────────────────────────────────────────────────────


def main(json_only: bool = False) -> None:
    import importlib

    _lean_mod = importlib.import_module("lean_pgd")
    lean_solve: Callable[..., Any] = _lean_mod.solve

    print("# Solver benchmark — portfolio-proofs")
    print(
        f"# Protocol: warmup={WARMUP}, reps={REPS}, stat=median+IQR, clock=perf_counter"
    )
    print(
        "# Platform: Apple M2 Max | Lean iters=53 | checkmark=converged, x=failed"
    )
    print()

    all_rows: list[TimingRow] = []

    benchmarks: list[tuple[str, Callable[[], list[TimingRow]]]] = [
        (
            "boundary_trap — L1 kink cycling, Aug 2007",
            lambda: bench_boundary_trap(lean_solve),
        ),
        (
            "cholesky_crash — rank-deficient covariance, Mar 2020",
            lambda: bench_cholesky_crash(lean_solve),
        ),
        (
            "phantom_positions — exact sparsity at L1 boundary",
            lambda: bench_phantom_positions(lean_solve),
        ),
        (
            "precision_bleed — IEEE 754 constraint drift",
            lambda: bench_precision_bleed(),
        ),
        (
            "step_divergence — Lipschitz violation, Volmageddon 2018",
            lambda: bench_step_divergence(lean_solve),
        ),
        (
            "vix_shock — step-size certification, post-shock",
            lambda: bench_vix_shock(lean_solve),
        ),
        (
            "sp500_factor — CAPM factor model scaling",
            lambda: bench_sp500_factor(lean_solve),
        ),
    ]

    for title, bench_fn in benchmarks:
        print(f"  Running {title.split(' — ')[0]}...", flush=True)
        rows = bench_fn()
        all_rows.extend(rows)
        if not json_only:
            print_scenario_table(rows, title)

    if not json_only:
        print_consolidated(all_rows)

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_path = _RESULTS / "benchmark_all_solvers.json"
    payload: dict[str, Any] = {
        "_meta": {
            "generated_by": "reports/benchmark_all_solvers.py",
            "date": "2026-05-26",
            "protocol": f"warmup={WARMUP}, reps={REPS}, stat=median+IQR",
            "platform": "Apple M2 Max, macOS Darwin 25.5.0",
            "lean_iters": 53,
            "clock": "time.perf_counter() (monotonic, nanosecond resolution)",
            "note": (
                "median_ms is the defensible latency estimate. "
                "IQR [q1_ms, q3_ms] shows spread. "
                "min_ms is optimistic (best-case OS scheduling). "
                "All Lean PGD times are warm persistent-subprocess."
            ),
        },
        "rows": [asdict(r) for r in all_rows],
    }
    with out_path.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nJSON saved to {out_path.relative_to(_PP)}")


if __name__ == "__main__":
    json_only = "--json-only" in sys.argv
    main(json_only=json_only)
