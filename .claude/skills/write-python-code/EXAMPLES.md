# Python Code Examples — quant-proofs

Annotated good and bad examples. Each bad example is followed by the corrected version.

---

## Well-typed function with docstring

```python
from __future__ import annotations

from typing import Sequence, TypeAlias

PnlBps: TypeAlias = int


def compute_delta_pnl(
    deltas_bps: Sequence[int],
    price_moves_bps: Sequence[int],
) -> PnlBps:
    """Compute total delta-hedging PnL from per-leg deltas and price moves.

    Multiplies each delta by the corresponding price move and sums the results.
    Both inputs must be in basis points; the return value is also in basis points.

    Args:
        deltas_bps: Per-leg option deltas, each in basis points (e.g., 5000 = 0.50).
        price_moves_bps: Underlying price moves per leg, in basis points.

    Returns:
        Total PnL in basis points.

    Raises:
        ValueError: If the two sequences have different lengths.
    """
    if len(deltas_bps) != len(price_moves_bps):
        raise ValueError(
            f"deltas_bps length {len(deltas_bps)} != "
            f"price_moves_bps length {len(price_moves_bps)}"
        )
    return sum(d * m for d, m in zip(deltas_bps, price_moves_bps))
```

What makes this good:
- `from __future__ import annotations` at the top of the module.
- `TypeAlias` for the return type, which appears in multiple places.
- `Sequence[int]` rather than `list[int]` because the function only reads.
- Full docstring with Args / Returns / Raises.
- Validation at the function boundary, not inside the computation loop.
- Clear error message that includes the actual values.

---

## Under-typed function (bad)

```python
def compute_delta_pnl(deltas, price_moves):
    return sum(d * m for d, m in zip(deltas, price_moves))
```

Problems:
- No type annotations — mypy --strict will reject this.
- No docstring.
- No validation of equal lengths — silently produces wrong result if inputs differ.

---

## Protocol usage

Use `Protocol` when you need to accept any object that has a specific interface,
not just a specific class.

```python
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PricingModel(Protocol):
    """Any object that can price an option given strike and expiry."""

    def price_bps(self, strike_bps: int, expiry_days: int) -> int:
        """Return the option price in basis points."""
        ...


def run_backtest(model: PricingModel, strikes_bps: list[int]) -> list[int]:
    """Price each strike using the given model and return results."""
    return [model.price_bps(s, expiry_days=30) for s in strikes_bps]
```

Why this is better than `Union[BlackScholes, BinomialModel]`:
- Adding a new model doesn't require touching `run_backtest`.
- The `@runtime_checkable` decorator lets you use `isinstance(obj, PricingModel)`
  in tests.

---

## Pydantic model example

```python
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class RiskAssessment(BaseModel):
    """Structured output of the risk agent for a mortgage application.

    Args:
        ltv_bps: Loan-to-value ratio in basis points (e.g., 8000 = 80%).
        dti_bps: Debt-to-income ratio in basis points (e.g., 4300 = 43%).
        recommendation: Risk agent's routing recommendation.
        flags: List of risk flags raised (may be empty).
    """

    ltv_bps: int = Field(ge=0, le=10_000, description="Loan-to-value in bps")
    dti_bps: int = Field(ge=0, le=10_000, description="Debt-to-income in bps")
    recommendation: Literal["approve", "refer", "decline"]
    flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def high_ltv_must_flag(self) -> RiskAssessment:
        if self.ltv_bps > 9_500 and not self.flags:
            raise ValueError("LTV > 95% must include at least one risk flag")
        return self
```

---

## Bad example: bare `Any` and missing types

```python
from typing import Any

def process_application(data: Any) -> Any:
    result = {}
    result["ltv"] = data["loan_amount"] / data["property_value"]
    result["recommendation"] = "approve" if result["ltv"] < 0.8 else "refer"
    return result
```

Problems:
- `Any` on both input and output — mypy cannot check this at all.
- Ratios are computed as floats, not basis points — inconsistent with FFI rules.
- No validation that `data` has the required keys.
- No docstring.

Corrected version:

```python
from __future__ import annotations

from mortgage_proofs.models import ApplicationInput, RiskAssessment


def process_application(data: ApplicationInput) -> RiskAssessment:
    """Compute risk metrics and generate a routing recommendation.

    Args:
        data: Validated application input from the intake agent.

    Returns:
        Structured risk assessment with LTV, DTI, and recommendation.
    """
    ltv_bps = int(round(data.loan_amount_bps / data.property_value_bps * 10_000))
    return RiskAssessment(
        ltv_bps=ltv_bps,
        dti_bps=data.monthly_debt_bps * 12 * 10_000 // data.annual_income_bps,
        recommendation="approve" if ltv_bps <= 8_000 else "refer",
    )
```
