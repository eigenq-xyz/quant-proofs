"""Strategy abstraction + registry — the alpha-agnostic extension point.

A ``Strategy`` maps the information set available up to a date ``t`` to a target
portfolio at ``t``. The engine only ever hands a strategy ``panel.as_of(t)`` (prices at
dates ``<= t``), so **non-anticipation is structural for any strategy**, not a property
each alpha must re-establish: this is the runtime face of the engine-level Lean guarantee
``ResearchPipeline.decision_uses_no_future`` (which is fully type-generic over the alpha).

``SignalStrategy`` adapts the existing cross-sectional ``SignalFn`` + portfolio-constructor
pair into a ``Strategy``, so momentum / reversal plug in unchanged. The registry lets the
CLI resolve a strategy by name with parameter overrides (``get_strategy("momentum", lookback=126)``).

Keeping the abstraction at the *target-portfolio* level (not orders / fills / execution) is
deliberate: this is a research backtester, not a production trading system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

import pandas as pd

from .data import PricePanel
from .portfolio import PortfolioConstructor, get_portfolio, signal_to_weights
from .signals import momentum_signal, reversal_signal, ts_momentum_signal

# A signal maps a (point-in-time) panel to a dates x assets score frame.
SignalFn = Callable[[PricePanel], pd.DataFrame]


@runtime_checkable
class Strategy(Protocol):
    """An alpha-agnostic strategy: information up to ``t`` -> target weights at ``t``."""

    @property
    def name(self) -> str:
        """Human-readable strategy name (also the registry key)."""
        ...

    def signals(self, panel: PricePanel) -> pd.DataFrame:
        """Vectorised, non-anticipating score frame (dates x assets) over the whole panel."""
        ...

    def decide(self, info: PricePanel) -> pd.Series:
        """Target weights at the last date of ``info``, using only ``info`` (data <= t)."""
        ...


@dataclass(frozen=True)
class SignalStrategy:
    """Adapt a cross-sectional ``SignalFn`` + portfolio constructor into a ``Strategy``.

    ``signal_fn`` must be non-anticipating (value at ``t`` uses prices ``<= t`` only); this
    is witnessed at runtime by ``validation.boundary_lookahead_discrepancy``.
    """

    name: str
    signal_fn: SignalFn
    weight_fn: PortfolioConstructor = field(default=signal_to_weights)

    def signals(self, panel: PricePanel) -> pd.DataFrame:
        return self.signal_fn(panel)

    def decide(self, info: PricePanel) -> pd.Series:
        sig = self.signal_fn(info)
        if sig.empty:
            return pd.Series(dtype=float)
        return self.weight_fn(sig.iloc[-1])


# --- registry ---------------------------------------------------------------

StrategyFactory = Callable[..., Strategy]
_REGISTRY: dict[str, StrategyFactory] = {}


def register(name: str, factory: StrategyFactory) -> None:
    """Register a strategy factory under ``name`` (overwrites an existing entry)."""
    _REGISTRY[name] = factory


def available_strategies() -> list[str]:
    """Names of all registered strategies, sorted."""
    return sorted(_REGISTRY)


def get_strategy(name: str, **params: object) -> Strategy:
    """Instantiate a registered strategy by name, passing ``params`` to its factory."""
    if name not in _REGISTRY:
        raise KeyError(f"unknown strategy {name!r}; available: {available_strategies()}")
    return _REGISTRY[name](**params)


# --- built-in strategies (known controls) -----------------------------------


def _momentum(lookback: int = 252, skip: int = 21, portfolio: str = "dollar_neutral") -> Strategy:
    return SignalStrategy(
        "momentum",
        lambda p: momentum_signal(p, lookback=lookback, skip=skip),
        get_portfolio(portfolio),
    )


def _reversal(lookback: int = 21, portfolio: str = "dollar_neutral") -> Strategy:
    return SignalStrategy(
        "reversal", lambda p: reversal_signal(p, lookback=lookback), get_portfolio(portfolio)
    )


def _ts_momentum(lookback: int = 252, skip: int = 21, portfolio: str = "directional") -> Strategy:
    """Time-series momentum: directional by default (single-asset capable)."""
    return SignalStrategy(
        "ts_momentum",
        lambda p: ts_momentum_signal(p, lookback=lookback, skip=skip),
        get_portfolio(portfolio),
    )


register("momentum", _momentum)
register("reversal", _reversal)
register("ts_momentum", _ts_momentum)
