"""Track 1 — the pipeline does what it claims (A/B / synthetic-truth + planted-bug)."""

from __future__ import annotations

from research_pipeline.stats import permutation_ic_test
from research_pipeline.validation import (
    boundary_lookahead_discrepancy,
    detection_rate,
    false_positive_rate,
    leaky_signal,
    make_predictable_panel,
    signal_fn_from,
)


def test_detects_planted_alpha() -> None:
    # Strong planted alpha => the pipeline should flag it nearly always.
    assert detection_rate(beta=0.08, n_runs=20) > 0.9


def test_does_not_false_positive_on_noise() -> None:
    # No alpha (beta=0) => significance rate should be near the nominal 5%, well bounded.
    assert false_positive_rate(n_runs=40) < 0.25


def test_lookahead_guard_catches_a_planted_leak() -> None:
    panel, signal = make_predictable_panel(n_days=400, n_assets=20, beta=0.05, seed=7)
    clean = boundary_lookahead_discrepancy(signal_fn_from(signal), panel)
    leaky = boundary_lookahead_discrepancy(leaky_signal, panel)
    assert clean < 1e-9  # non-anticipating signal: no discrepancy
    assert leaky > 1e-9  # the bug is caught at the truncation boundary


def test_permutation_test_kills_signal() -> None:
    panel, signal = make_predictable_panel(n_days=500, n_assets=25, beta=0.08, seed=3)
    fwd = panel.forward_returns(1)
    obs_real, p_real = permutation_ic_test(signal_fn_from(signal)(panel), fwd, n_perm=200)
    assert p_real < 0.05  # real alpha is significant under the placebo null
    _, p_noise = permutation_ic_test(
        signal_fn_from(make_predictable_panel(500, 25, beta=0.0, seed=9)[1])(panel), fwd, n_perm=200
    )
    assert p_noise > 0.05  # unrelated signal is not
