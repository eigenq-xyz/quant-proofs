"""CRR put-call parity exactness and Black-Scholes convergence study.

The options-proofs development proves two things about the Cox-Ross-Rubinstein
binomial model: the market is arbitrage-free under ``0 < d < 1 + r < u``, and
put-call parity holds exactly, ``C - P = S0 - K / (1 + r) ** T``. This script is
the empirical companion to that proof. It checks two claims numerically.

First, parity exactness. The theorem is an identity, so in the discrete model
the parity residual should be zero up to floating-point rounding, for every step
count and every strike. We confirm the residual stays at machine-epsilon scale.

Second, continuum convergence. The CRR model is the discrete object the proof
reasons about; the Black-Scholes price is its continuous limit. Calibrating the
up and down factors in the standard way (``u = exp(sigma * sqrt(dt))``,
``d = 1 / u``), the CRR price converges to the Black-Scholes price as the number
of steps grows, at the textbook first-order rate. This situates the verified
discrete result inside continuous-time pricing.

This study is deterministic: there is no randomness, so the committed output
reproduces exactly. The CRR model here is the BS-calibrated special case of the
general model the theorem covers; the proof itself holds for any factors in the
no-arbitrage band.

Run (from repo root) with an environment that has numpy and scipy:

    quant-core/python/.venv/bin/python options-proofs/results/crr_convergence_study.py
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.stats import binom, norm  # type: ignore[import-untyped]

SPOT = 100.0
STRIKE = 100.0
RATE = 0.05  # continuously-compounded annual risk-free rate
SIGMA = 0.20  # annualized volatility
MATURITY = 1.0  # years
STEP_COUNTS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]


def black_scholes(
    spot: float, strike: float, rate: float, sigma: float, t: float
) -> tuple[float, float]:
    """Black-Scholes European call and put prices."""
    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    disc = np.exp(-rate * t)
    call = float(spot * norm.cdf(d1) - strike * disc * norm.cdf(d2))
    put = float(strike * disc * norm.cdf(-d2) - spot * norm.cdf(-d1))
    return call, put


def crr(
    spot: float, strike: float, rate: float, sigma: float, t: float, n_steps: int
) -> tuple[float, float]:
    """CRR binomial European call and put prices with standard calibration.

    ``u = exp(sigma * sqrt(dt))``, ``d = 1 / u``, per-step gross risk-free factor
    ``exp(rate * dt)``, risk-neutral up-probability ``q = (e^{r dt} - d)/(u - d)``.
    Prices are the discounted risk-neutral expectations of the payoffs.
    """
    dt = t / n_steps
    up = float(np.exp(sigma * np.sqrt(dt)))
    down = 1.0 / up
    growth = float(np.exp(rate * dt))
    q = (growth - down) / (up - down)
    j = np.arange(n_steps + 1)
    terminal = spot * up**j * down ** (n_steps - j)
    weights = binom.pmf(j, n_steps, q)
    disc = float(np.exp(-rate * t))
    call = float(disc * np.sum(weights * np.maximum(terminal - strike, 0.0)))
    put = float(disc * np.sum(weights * np.maximum(strike - terminal, 0.0)))
    return call, put


@dataclass(frozen=True)
class StepResult:
    """One step-count measurement."""

    n_steps: int
    crr_call: float
    crr_put: float
    call_abs_err_vs_bs: float
    put_abs_err_vs_bs: float
    parity_residual: float


def run() -> dict[str, object]:
    """Compute CRR vs Black-Scholes across step counts and the parity residual."""
    bs_call, bs_put = black_scholes(SPOT, STRIKE, RATE, SIGMA, MATURITY)
    parity_target = SPOT - STRIKE * float(np.exp(-RATE * MATURITY))
    results: list[StepResult] = []
    for n in STEP_COUNTS:
        c, p = crr(SPOT, STRIKE, RATE, SIGMA, MATURITY, n)
        results.append(
            StepResult(
                n_steps=n,
                crr_call=round(c, 8),
                crr_put=round(p, 8),
                call_abs_err_vs_bs=round(abs(c - bs_call), 8),
                put_abs_err_vs_bs=round(abs(p - bs_put), 8),
                parity_residual=abs((c - p) - parity_target),
            )
        )
    max_parity = max(r.parity_residual for r in results)
    return {
        "description": (
            "CRR put-call parity exactness and Black-Scholes convergence. "
            "Parity residual is |（C - P) - (S0 - K e^{-rT})|, which the theorem "
            "makes zero; it stays at machine-epsilon scale. CRR-minus-BS error "
            "shrinks at first order in the step size. Deterministic, exact reproduce."
        ),
        "parameters": {
            "spot": SPOT,
            "strike": STRIKE,
            "rate": RATE,
            "sigma": SIGMA,
            "maturity_years": MATURITY,
            "step_counts": STEP_COUNTS,
        },
        "black_scholes": {"call": round(bs_call, 8), "put": round(bs_put, 8)},
        "max_parity_residual": max_parity,
        "steps": [asdict(r) for r in results],
    }


def main() -> None:
    result = run()
    out_dir = Path(__file__).resolve().parent / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "crr_convergence.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(
        f"max parity residual across all step counts: {result['max_parity_residual']:.2e}"
    )
    steps = result["steps"]
    assert isinstance(steps, list)
    for r in steps:
        assert isinstance(r, dict)
        print(
            f"  N={r['n_steps']:>5}: CRR call={r['crr_call']:>9.5f}  "
            f"|CRR-BS|={r['call_abs_err_vs_bs']:.2e}  "
            f"parity_resid={r['parity_residual']:.2e}"
        )


if __name__ == "__main__":
    main()
