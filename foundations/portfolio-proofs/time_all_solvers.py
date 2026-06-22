"""Comprehensive wall-clock timing benchmark across all 7 scenarios x all solvers.

Run from portfolio-proofs/:
    uv run python time_all_solvers.py

Prints a Markdown table per scenario and a consolidated summary at the end.
"""

from __future__ import annotations

import contextlib
import importlib
import sys
import time
from pathlib import Path

import numpy as np

# ── Path setup ───────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_SCENARIOS = _HERE / "scenarios"
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


# ── Helpers ───────────────────────────────────────────────────────────────────

WARMUP = 1
REPS = 5


def _median_ms(fn, *args, **kwargs) -> float:
    """Return median wall-clock ms over REPS calls (after WARMUP calls)."""
    for _ in range(WARMUP):
        with contextlib.suppress(Exception):
            fn(*args, **kwargs)
    times = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        try:
            fn(*args, **kwargs)
        except Exception:
            return float("nan")
        times.append((time.perf_counter() - t0) * 1e3)
    return float(np.median(times))


def _load(scenario: str, module: str):
    """Import scenarios/<scenario>/solvers/<module>.py."""
    pkg = f"scenarios.{scenario}.solvers.{module}"
    spec_path = _SCENARIOS / scenario / "solvers" / f"{module}.py"
    # Use importlib with file path to avoid __init__ issues
    spec = importlib.util.spec_from_file_location(pkg, spec_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find {spec_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    # Ensure the solvers package is importable
    pkg_init = _SCENARIOS / scenario / "solvers" / "__init__.py"
    pkg_name = f"scenarios.{scenario}.solvers"
    if pkg_name not in sys.modules:
        init_spec = importlib.util.spec_from_file_location(pkg_name, pkg_init)
        if init_spec and init_spec.loader:
            init_mod = importlib.util.module_from_spec(init_spec)
            sys.modules[pkg_name] = init_mod
            init_spec.loader.exec_module(init_mod)
    spec.loader.exec_module(mod)
    return mod


def fmt(ms: float, converged: bool | None = None) -> str:
    """Format a timing with optional fail marker."""
    if ms != ms:  # nan
        return "ERROR"
    suffix = "" if converged is None else ("" if converged else " ✗")
    if ms < 1:
        return f"{ms:.2f} ms{suffix}"
    if ms < 1000:
        return f"{ms:.0f} ms{suffix}"
    return f"{ms / 1000:.1f} s{suffix}"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. boundary_trap
# ═══════════════════════════════════════════════════════════════════════════════


def bench_boundary_trap():
    print("\n## boundary_trap — L1 kink cycling, August 2007 (N=10, cond≈204)")
    print("(warm subprocess medians, 5 reps)\n")

    # Add scenario solvers to path
    solvers_path = str(_SCENARIOS / "boundary_trap" / "solvers")
    if solvers_path not in sys.path:
        sys.path.insert(0, str(_SCENARIOS / "boundary_trap"))

    from scenarios.boundary_trap.solvers import (
        common as bt_common,  # type: ignore[import-not-found]
    )

    try:
        p = bt_common.load_problem()
    except FileNotFoundError as e:
        print(f"  ⚠ Data not found: {e}")
        return []

    rows = []
    solver_list = [
        ("SLSQP", "slsqp", "run"),
        ("trust-constr", "trust_constr", "run"),
        ("Gurobi", "gurobi", "run"),
        ("OR-Tools", "ortools_gscip", "run"),
        ("KKT optimum", "kkt_optimum", "run"),
    ]
    # Also time Lean PGD subprocess
    try:
        from lean_pgd import (
            solve as lean_solve,  # type: ignore[import-not-found]
        )

        lean_ok = True
    except Exception:
        lean_ok = False

    for label, modname, fn_name in solver_list:
        try:
            mod = _load("boundary_trap", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, p)
            # Convergence
            try:
                result = fn(p)
                conv = getattr(result, "converged", None)
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}")

    if lean_ok:
        try:
            ms = _median_ms(lean_solve, p.Sigma, p.mu, p.leverage_cap)
            rows.append(("Lean PGD", ms, True))
            print(f"  {'Lean PGD':<18}  {fmt(ms, True)}")
        except Exception as exc:
            print(f"  [Lean PGD] ERROR: {exc}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 2. cholesky_crash
# ═══════════════════════════════════════════════════════════════════════════════


def bench_cholesky_crash():
    print(
        "\n## cholesky_crash — rank-deficient covariance, March 2020 (N=10, T=5)"
    )
    print("(warm subprocess medians, 5 reps)\n")

    from scenarios.cholesky_crash.solvers import (
        common as cc_common,  # type: ignore[import-not-found]
    )

    try:
        p = cc_common.load_problem()
    except FileNotFoundError as e:
        print(f"  ⚠ Data not found: {e}")
        return []

    rows = []
    solver_list = [
        ("SLSQP", "slsqp", "run"),
        ("trust-constr", "trust_constr", "run"),
        ("Gurobi", "gurobi", "run"),
        ("CVXPY/OSQP", "cvxpy_osqp", "run"),
        ("Lean PGD+LW", "pgd_lw", "run"),
    ]
    for label, modname, fn_name in solver_list:
        try:
            mod = _load("cholesky_crash", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, p)
            try:
                result = fn(p)
                conv = getattr(result, "converged", None)
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 3. phantom_positions
# ═══════════════════════════════════════════════════════════════════════════════


def bench_phantom_positions():
    print(
        "\n## phantom_positions — exact sparsity at L1 boundary (N=5, L=1.5)"
    )
    print("(warm subprocess medians, 5 reps)\n")

    from scenarios.phantom_positions.solvers import (
        common as pp_common,  # type: ignore[import-not-found]
    )

    p = pp_common.make_problem()

    rows = []
    solver_list = [
        ("SLSQP", "slsqp", "run"),
        ("trust-constr", "trust_constr", "run"),
        ("Gurobi", "gurobi", "run"),
        ("Lean PGD", "certified_pgd", "run"),
        ("KKT optimum", "kkt_optimum", "run"),
    ]
    for label, modname, fn_name in solver_list:
        try:
            mod = _load("phantom_positions", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, p)
            try:
                result = fn(p)
                conv = getattr(result, "converged", None)
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 4. precision_bleed
# ═══════════════════════════════════════════════════════════════════════════════


def bench_precision_bleed():
    print(
        "\n## precision_bleed — IEEE 754 constraint drift, March 2020 (N=4, 4 windows)"
    )
    print(
        "(median over all windows, 5 reps; time = total for all 4 windows)\n"
    )

    from scenarios.precision_bleed.solvers import (
        common as pb_common,  # type: ignore[import-not-found]
    )

    windows = pb_common.load_rolling_windows()

    rows = []
    solver_list = [
        ("SLSQP", "slsqp_float", "run_all"),
        ("trust-constr", "trust_constr", "run_all"),
        ("Gurobi", "gurobi", "run_all"),
        ("OR-Tools", "ortools_gscip", "run_all"),
        ("Lean PGD", "lean_pgd", "run_all"),
        ("PGD integer", "pgd_integer", "run_all"),
    ]
    for label, modname, fn_name in solver_list:
        try:
            mod = _load("precision_bleed", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, windows)
            try:
                results = fn(windows)
                conv = all(getattr(r, "converged", True) for r in results)
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}  (4 windows)")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 5. step_divergence
# ═══════════════════════════════════════════════════════════════════════════════


def bench_step_divergence():
    print(
        "\n## step_divergence — Lipschitz stability violation, Volmageddon 2018 (N=10)"
    )
    print("(warm subprocess medians, 5 reps)\n")

    from scenarios.step_divergence.solvers import (
        common as sd_common,  # type: ignore[import-not-found]
    )

    try:
        p = sd_common.load_problem()
    except FileNotFoundError as e:
        print(f"  ⚠ Data not found: {e}")
        return []

    rows = []
    solver_list = [
        ("SLSQP", "slsqp", "run"),
        ("trust-constr", "trust_constr", "run"),
        ("Gurobi", "gurobi", "run"),
        ("GD fixed eta", "gd_fixed", "run"),
        ("PGD adaptive", "pgd_adaptive", "run"),
    ]
    for label, modname, fn_name in solver_list:
        try:
            mod = _load("step_divergence", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, p)
            try:
                result = fn(p)
                conv = getattr(result, "converged", None)
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 6. vix_shock — post-shock variant (the interesting one)
# ═══════════════════════════════════════════════════════════════════════════════


def bench_vix_shock():
    print(
        "\n## vix_shock — step-size certification, post-VIX-doubling (N=3, L=1)"
    )
    print("(post-shock problem; warm subprocess medians, 5 reps)\n")

    from scenarios.vix_shock.solvers import (
        common as vs_common,  # type: ignore[import-not-found]
    )

    p = vs_common.make_post_shock()

    rows = []
    solver_list = [
        ("SLSQP", "slsqp", "run"),
        ("trust-constr", "trust_constr", "run"),
        ("Gurobi", "gurobi", "run"),
        ("GD uncertified", "uncertified_gd", "run"),
        ("Lean PGD cert.", "certified_pgd", "run"),
        ("KKT optimum", "kkt_optimum", "run"),
    ]
    for label, modname, fn_name in solver_list:
        try:
            mod = _load("vix_shock", modname)
            fn = getattr(mod, fn_name)
            ms = _median_ms(fn, p)
            try:
                result = fn(p)
                conv = getattr(result, "converged", None)
                if hasattr(result, "diverged") and result.diverged:
                    conv = False
            except Exception:
                conv = None
        except Exception as exc:
            print(f"  [{label}] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append((label, ms, conv))
        print(f"  {label:<18}  {fmt(ms, conv)}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 7. sp500_factor — N=10 and N=50 only (N=100+ is very slow for Gurobi/trust-constr)
# ═══════════════════════════════════════════════════════════════════════════════


def bench_sp500_factor():
    print("\n## sp500_factor — CAPM factor scaling (N=10, N=50)")
    print("(warm subprocess medians, 5 reps per N)\n")

    from scenarios.sp500_factor.solvers import (
        common as sf_common,  # type: ignore[import-not-found]
    )
    from scenarios.sp500_factor.solvers import (  # type: ignore[import-not-found]
        gurobi,
        pgd_reference,
    )

    rows: list[tuple[str, int, float, bool | None]] = []

    for N in [10, 50]:
        p = sf_common.make_problem(N)
        print(f"  --- N={N} ---")

        # Lean PGD (pgd_reference.run_pgd)
        try:
            ms = _median_ms(pgd_reference.run_pgd, p)
            result = pgd_reference.run_pgd(p)
            conv: bool | None = getattr(result, "converged", True)
        except Exception as exc:
            print(f"    [Lean PGD] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append(("Lean PGD", N, ms, conv))
        print(f"    {'Lean PGD':<20}  {fmt(ms, conv)}")

        # Gurobi (gurobi.run)
        try:
            ms = _median_ms(gurobi.run, p)
            gresult = gurobi.run(p)
            conv = getattr(gresult, "converged", None)
            if getattr(gresult, "timed_out", False):
                conv = None
        except Exception as exc:
            print(f"    [Gurobi] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append(("Gurobi", N, ms, conv))
        print(f"    {'Gurobi':<20}  {fmt(ms, conv)}")

        # KKT Woodbury (kkt_woodbury.run)
        try:
            kmod = _load("sp500_factor", "kkt_woodbury")
            # Check if it has a run() function
            if hasattr(kmod, "run"):
                ms = _median_ms(kmod.run, p)
                kresult = kmod.run(p)
                conv = getattr(kresult, "converged", True)
            else:
                ms, conv = float("nan"), None
                print("    [KKT Woodbury] no run() function")
        except Exception as exc:
            print(f"    [KKT Woodbury] ERROR: {exc}")
            ms, conv = float("nan"), None
        rows.append(("KKT Woodbury", N, ms, conv))
        print(f"    {'KKT Woodbury':<20}  {fmt(ms, conv)}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    print("# Wall-clock timing: all scenarios x all solvers")
    print(f"# Platform: Apple M-series | Reps: {REPS} (median) | iters=53")
    print("# ✗ = did not converge\n")

    # Add all scenario parent dirs to sys.path
    for scenario in [
        "boundary_trap",
        "cholesky_crash",
        "phantom_positions",
        "precision_bleed",
        "step_divergence",
        "vix_shock",
        "sp500_factor",
    ]:
        p = str(_SCENARIOS / scenario)
        if p not in sys.path:
            sys.path.insert(0, p)

    results = {}
    results["boundary_trap"] = bench_boundary_trap()
    results["cholesky_crash"] = bench_cholesky_crash()
    results["phantom_positions"] = bench_phantom_positions()
    results["precision_bleed"] = bench_precision_bleed()
    results["step_divergence"] = bench_step_divergence()
    results["vix_shock"] = bench_vix_shock()
    results["sp500_factor"] = bench_sp500_factor()

    # ── Consolidated summary table ────────────────────────────────────────────
    print("\n\n" + "=" * 80)
    print("## CONSOLIDATED SUMMARY TABLE (median ms, ✗ = did not converge)")
    print("=" * 80)
    print()
    print(
        f"{'Scenario':<22}  {'N':>4}  {'SLSQP':>10}  {'trust-constr':>13}  {'Gurobi':>10}  {'Lean PGD':>10}  {'Other':>10}"
    )
    print("-" * 90)

    scenario_labels = {
        "boundary_trap": ("boundary_trap", 10),
        "cholesky_crash": ("cholesky_crash", 10),
        "phantom_positions": ("phantom_pos", 5),
        "precision_bleed": ("precision_bleed", 4),
        "step_divergence": ("step_diverge", 10),
        "vix_shock": ("vix_shock", 3),
    }

    for key, (label, N) in scenario_labels.items():
        rows = results.get(key, [])
        d = {r[0]: (r[1], r[2]) for r in rows}

        def cell(solver_key, _d=d):
            if solver_key in _d:
                ms, conv = _d[solver_key]
                return fmt(ms, conv)
            return "—"

        # Find "Other" (non-standard solvers)
        standard = {
            "SLSQP",
            "trust-constr",
            "Gurobi",
            "Lean PGD",
            "Lean PGD+LW",
            "Lean PGD cert.",
            "trust_constr",
        }
        other_entries = [
            (k, v)
            for k, v in d.items()
            if k not in standard and "constr" not in k.lower()
        ]
        other_str = (
            ", ".join(f"{k}={fmt(v[0], v[1])}" for k, v in other_entries[:2])
            or "—"
        )

        slsqp_str = cell("SLSQP")
        tc_str = cell("trust-constr")
        gurobi_str = cell("Gurobi")
        lean_str = next(
            (
                fmt(v[0], v[1])
                for k, v in d.items()
                if "Lean" in k or "PGD" in k.lower()
            ),
            "—",
        )

        print(
            f"{label:<22}  {N:>4}  {slsqp_str:>10}  {tc_str:>13}  "
            f"{gurobi_str:>10}  {lean_str:>10}  {other_str}"
        )

    # sp500_factor separately (multi-N)
    sp500_rows = results.get("sp500_factor", [])
    for N in [10, 50]:
        label = f"sp500 N={N}"
        d_sp = {r[0]: (r[2], r[3]) for r in sp500_rows if r[1] == N}
        lean_str = next(
            (fmt(v[0], v[1]) for k, v in d_sp.items() if "Lean" in k), "—"
        )
        gurobi_str = fmt(*d_sp["Gurobi"]) if "Gurobi" in d_sp else "—"
        kkt_str = fmt(*d_sp["KKT Woodbury"]) if "KKT Woodbury" in d_sp else "—"
        print(
            f"{label:<22}  {N:>4}  {'—':>10}  {'—':>13}  "
            f"{gurobi_str:>10}  {lean_str:>10}  KKT={kkt_str}"
        )

    print()


if __name__ == "__main__":
    main()
