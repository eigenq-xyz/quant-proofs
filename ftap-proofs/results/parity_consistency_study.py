"""Controlled put-call parity consistency study for the FTAP paper.

The Fundamental Theorem of Asset Pricing says a frictionless arbitrage-free
market admits a single consistent pricing measure. Put-call parity,
``C - P = S - K * exp(-r * T)``, is a model-free consequence of that
consistency: it holds for every strike regardless of the volatility model. Real
quotes carry microstructure friction (bid-ask spreads, quote noise,
non-synchronicity), so observed prices satisfy parity only approximately.

This script measures that approximation gap in a controlled setting. We build an
arbitrage-free Black-Scholes cross-section (parity holds exactly by
construction), perturb each leg with multiplicative quote noise at several
friction levels, and report the parity deviation in basis points of spot. The
deviation is the operational shadow of "prices admit a single pricing measure":
near zero when quotes are tight, widening as friction grows, and amplified in
high-volatility regimes because option price levels (and hence the absolute
effect of a given relative noise) are larger.

The generator here is synthetic, so this is a controlled study, not a
real-market claim. The same harness runs on real quotes by replacing
``arbitrage_free_chain`` with a loader for a committable option snapshot.

Run (from repo root) with an environment that has numpy and scipy:

    quant-core/python/.venv/bin/python ftap-proofs/results/parity_consistency_study.py

Reproducible: all randomness is drawn from a seeded generator.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm  # type: ignore[import-untyped]

SEED = 20260530
SPOT = 100.0
RATE = 0.03
MATURITY = 0.25  # three months
STRIKES = np.arange(80.0, 120.0 + 1e-9, 2.5)
N_TRIALS = 20_000

# Friction levels: relative quote-noise standard deviation, calm to stress.
FRICTION_LEVELS: dict[str, float] = {
    "tight": 0.0005,
    "normal": 0.0025,
    "wide": 0.0100,
    "stressed": 0.0300,
}
# Volatility regimes (annualized).
VOL_REGIMES: dict[str, float] = {
    "low_vol": 0.15,
    "mid_vol": 0.30,
    "high_vol": 0.60,
}


def bs_call_put(
    spot: float,
    strikes: NDArray[np.float64],
    rate: float,
    sigma: float,
    maturity: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Black-Scholes call and put prices for a vector of strikes."""
    sqrt_t = np.sqrt(maturity)
    d1 = (np.log(spot / strikes) + (rate + 0.5 * sigma**2) * maturity) / (
        sigma * sqrt_t
    )
    d2 = d1 - sigma * sqrt_t
    disc = np.exp(-rate * maturity)
    call = np.asarray(
        spot * norm.cdf(d1) - strikes * disc * norm.cdf(d2), dtype=np.float64
    )
    put = np.asarray(
        strikes * disc * norm.cdf(-d2) - spot * norm.cdf(-d1), dtype=np.float64
    )
    return call, put


def parity_target(
    spot: float, strikes: NDArray[np.float64], rate: float, maturity: float
) -> NDArray[np.float64]:
    """The model-free parity right-hand side ``S - K * exp(-r * T)``."""
    return np.asarray(spot - strikes * np.exp(-rate * maturity), dtype=np.float64)


@dataclass(frozen=True)
class Cell:
    """One (volatility regime, friction level) measurement."""

    vol_regime: str
    friction: str
    sigma: float
    noise_std: float
    mean_dev_bps: float
    p95_dev_bps: float
    max_dev_bps: float


def measure(
    sigma: float, noise_std: float, rng: np.random.Generator
) -> tuple[float, float, float]:
    """Mean, 95th percentile, and max parity deviation in bps of spot.

    Each trial perturbs the exact call and put on every strike with independent
    multiplicative Gaussian noise, then measures the per-strike parity gap.
    """
    call, put = bs_call_put(SPOT, STRIKES, RATE, sigma, MATURITY)
    target = parity_target(SPOT, STRIKES, RATE, MATURITY)
    n_strikes = STRIKES.shape[0]
    # A quote is a positive multiple of the true price. The multiplicative noise
    # factor 1 + N(0, noise_std) is therefore floored at a small positive value:
    # at the friction levels used here a negative draw is effectively impossible
    # (the stressed level is ~33 sigma away), but the clamp keeps the model
    # well-defined if the harness is ever pushed to extreme stress (noise_std > ~0.1).
    floor = 1.0e-6
    call_noise = np.maximum(
        1.0 + rng.normal(0.0, noise_std, size=(N_TRIALS, n_strikes)), floor
    )
    put_noise = np.maximum(
        1.0 + rng.normal(0.0, noise_std, size=(N_TRIALS, n_strikes)), floor
    )
    obs_call = call[None, :] * call_noise
    obs_put = put[None, :] * put_noise
    dev_bps = np.abs((obs_call - obs_put) - target[None, :]) / SPOT * 1.0e4
    return (
        float(np.mean(dev_bps)),
        float(np.percentile(dev_bps, 95.0)),
        float(np.max(dev_bps)),
    )


def run() -> dict[str, object]:
    """Run the full grid of regimes and friction levels."""
    rng = np.random.default_rng(SEED)
    cells: list[Cell] = []
    for vol_name, sigma in VOL_REGIMES.items():
        for fric_name, noise_std in FRICTION_LEVELS.items():
            mean_bps, p95_bps, max_bps = measure(sigma, noise_std, rng)
            cells.append(
                Cell(
                    vol_regime=vol_name,
                    friction=fric_name,
                    sigma=sigma,
                    noise_std=noise_std,
                    mean_dev_bps=round(mean_bps, 4),
                    p95_dev_bps=round(p95_bps, 4),
                    max_dev_bps=round(max_bps, 4),
                )
            )
    return {
        "description": (
            "Controlled put-call parity consistency study. Parity deviation in "
            "basis points of spot, on an arbitrage-free Black-Scholes "
            "cross-section perturbed by multiplicative quote noise. Synthetic "
            "generator; the harness runs on real quotes unchanged."
        ),
        "parameters": {
            "seed": SEED,
            "spot": SPOT,
            "rate": RATE,
            "maturity_years": MATURITY,
            "strikes": STRIKES.tolist(),
            "n_trials": N_TRIALS,
        },
        "cells": [asdict(c) for c in cells],
    }


def main() -> None:
    result = run()
    out_dir = Path(__file__).resolve().parent / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "parity_consistency.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    cells = result["cells"]
    assert isinstance(cells, list)
    print(f"wrote {out_path} with {len(cells)} cells")
    for c in cells:
        assert isinstance(c, dict)
        print(
            f"  {c['vol_regime']:>9} / {c['friction']:>8}: "
            f"mean={c['mean_dev_bps']:>8.3f} bps  p95={c['p95_dev_bps']:>8.3f} bps"
        )


if __name__ == "__main__":
    main()
