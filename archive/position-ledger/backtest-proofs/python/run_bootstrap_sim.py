"""Bootstrap specification-test simulation.

Generates raw hedging cost arrays at 20 log-spaced rebalancing frequencies
with 5,000 paths each (100,000 total simulations) for the bootstrap
specification test in backtest-proofs.

Outputs
-------
../results/bootstrap_paths_5000.pkl  — {N: list[float]} raw hedging costs
../results/bootstrap_paths_5000_summary.json  — parameter metadata
"""

from __future__ import annotations

import concurrent.futures
import json
import pickle
import time
from pathlib import Path

import numpy as np

from backtest_proofs.backtest.leland import _simulate_one_frequency

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
S0 = 49.0
K = 50.0
R = 0.05
SIGMA = 0.20
T = 20 / 52
N_CONTRACTS = 100_000
SEED = 20260519 + 99_999_999  # = 120260518
N_PATHS = 5_000
MAX_WORKERS = 8

# 20 log-spaced frequencies from N=3 to N=400
_raw = sorted(
    set(int(round(x)) for x in np.logspace(np.log10(3), np.log10(400), 22))
)
_indices = np.round(np.linspace(0, len(_raw) - 1, 20)).astype(int)
FREQUENCIES: list[int] = [_raw[i] for i in _indices]

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
_results_dir = Path(__file__).parent.parent / "results"
_results_dir.mkdir(exist_ok=True)

PKL_PATH = _results_dir / "bootstrap_paths_5000.pkl"
JSON_PATH = _results_dir / "bootstrap_paths_5000_summary.json"

# ---------------------------------------------------------------------------
# Run simulation
# ---------------------------------------------------------------------------
print(
    f"Bootstrap simulation — {len(FREQUENCIES)} frequencies × {N_PATHS} paths"
)
print(f"Total simulations: {len(FREQUENCIES) * N_PATHS:,}")
print(f"Frequencies: {FREQUENCIES}")
print(f"Seed: {SEED}, max_workers: {MAX_WORKERS}")
print()

result: dict[int, list[float]] = {}
t0 = time.perf_counter()

with concurrent.futures.ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:
    futures_map: dict[
        concurrent.futures.Future[tuple[int, list[float]]], int
    ] = {}
    for n_steps in FREQUENCIES:
        fut = executor.submit(
            _simulate_one_frequency,
            n_steps,
            S0,
            K,
            R,
            SIGMA,
            T,
            N_PATHS,
            SEED,
            N_CONTRACTS,
        )
        futures_map[fut] = n_steps

    completed = 0
    for fut in concurrent.futures.as_completed(futures_map):
        n_steps_done, costs = fut.result()
        result[n_steps_done] = costs
        completed += 1
        elapsed = time.perf_counter() - t0
        print(
            f"  [{completed:2d}/{len(FREQUENCIES)}] N={n_steps_done:4d} done"
            f" — {len(costs)} paths"
            f" — elapsed {elapsed:.1f}s"
        )

wall = time.perf_counter() - t0
print(f"\nAll frequencies complete. Wall-clock time: {wall:.2f}s")

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
with open(PKL_PATH, "wb") as fh:
    pickle.dump(result, fh, protocol=pickle.HIGHEST_PROTOCOL)
print(f"Saved pickle: {PKL_PATH}")

summary = {
    "n_paths": N_PATHS,
    "frequencies": FREQUENCIES,
    "n_freqs": len(FREQUENCIES),
    "seed": SEED,
    "s0": S0,
    "k": K,
    "r": R,
    "sigma": SIGMA,
    "t": round(T, 4),
}
with open(JSON_PATH, "w") as fh:
    json.dump(summary, fh, indent=2)
print(f"Saved summary: {JSON_PATH}")

# ---------------------------------------------------------------------------
# Verification round-trip
# ---------------------------------------------------------------------------
print("\nVerification — reloading pickle...")
with open(PKL_PATH, "rb") as fh:
    loaded: dict[int, list[float]] = pickle.load(fh)

freqs_loaded = sorted(loaded.keys())
total_paths = sum(len(v) for v in loaded.values())
print(f"Frequencies loaded ({len(freqs_loaded)}): {freqs_loaded}")
print(f"Total paths in pickle: {total_paths:,}")
assert freqs_loaded == sorted(FREQUENCIES), "Frequency mismatch!"
assert total_paths == len(FREQUENCIES) * N_PATHS, "Path count mismatch!"
print("Verification passed.")
