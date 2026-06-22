"""Stage 1 — data. Point-in-time price panel + a synthetic generator.

No-look-ahead is structural: ``PricePanel`` exposes prices/returns, and the only
forward-looking accessor (``forward_returns``) is named as such and is valid ONLY as an
evaluation target. ``as_of(t)`` materialises the information set available at ``t`` — the
runtime witness of the Lean ``AgreeUpTo`` / ``NonAnticipating`` spec
(``lean/ResearchPipeline/NoLookahead.lean``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PricePanel:
    """Prices as a DataFrame: index = dates (sorted ascending), columns = assets."""

    prices: pd.DataFrame

    def __post_init__(self) -> None:
        if not self.prices.index.is_monotonic_increasing:
            raise ValueError("prices index (dates) must be sorted ascending")

    @property
    def assets(self) -> list[str]:
        return list(self.prices.columns)

    def simple_returns(self) -> pd.DataFrame:
        return self.prices.pct_change(fill_method=None)

    def as_of(self, t: object) -> "PricePanel":
        """Information available at date ``t`` (inclusive). Use to witness no look-ahead."""
        return PricePanel(self.prices.loc[:t])

    def forward_returns(self, horizon: int = 1) -> pd.DataFrame:
        """Realised return over ``(t, t+horizon]``, indexed at ``t``.

        FUTURE information by construction — valid only as the evaluation target.
        """
        return self.prices.pct_change(horizon, fill_method=None).shift(-horizon)


def make_synthetic_panel(
    n_days: int = 1500,
    n_assets: int = 50,
    seed: int = 0,
    momentum_strength: float = 0.04,
) -> PricePanel:
    """Synthetic prices with a slow-moving drift, giving a mild *real* momentum effect.

    Per-asset drift follows an AR(1), so past returns predict near-future returns and the
    demo shows a positive IC. Deterministic given ``seed``. Clearly synthetic — real
    point-in-time loaders are available in ``data_sources.py``.
    """
    rng = np.random.default_rng(seed)
    drift = np.zeros(n_assets)
    rets = np.zeros((n_days, n_assets))
    phi = 0.97  # drift persistence => momentum
    for d in range(n_days):
        drift = phi * drift + (1.0 - phi) * rng.normal(0.0, momentum_strength, n_assets)
        rets[d] = drift + rng.normal(0.0, 0.01, n_assets)
    dates = pd.bdate_range("2015-01-01", periods=n_days)
    cols = [f"A{i:03d}" for i in range(n_assets)]
    prices = pd.DataFrame(100.0 * np.cumprod(1.0 + rets, axis=0), index=dates, columns=cols)
    return PricePanel(prices)
