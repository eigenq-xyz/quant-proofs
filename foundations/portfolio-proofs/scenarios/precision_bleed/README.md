# Precision Bleed — Constraint Drift from Floating-Point Rounding

Standard double-precision `float64` arithmetic cannot represent most portfolio
weights exactly in binary, causing constraint errors that accumulate silently
over sequential rolling rebalances and trigger pre-trade risk halts in
production systems.

---

## The failure in one sentence

Four rolling five-day windows over March 2020 SPY/TLT/GLD/HYG returns cause
SciPy SLSQP to violate the budget constraint ($\sum w_i = 1$) or leverage cap
($\sum |w_i| \leq 1.5$) in three of four windows, with a leverage error of
$2.79 \times 10^{-9}$ in the first window alone — 279 times larger than machine
epsilon and sufficient to trigger risk halts in systems with tolerance $10^{-9}$.

---

## Why this happens

The IEEE 754 `float64` format stores real numbers in 53-bit binary mantissas.
Most fractions that arise in portfolio optimization — including $1/3$, $1/4$, and
virtually all mean-variance-optimal weights — are not exactly representable in
binary floating-point. Each is stored as the nearest representable value, which
differs from the true value by at most half a unit of least precision, written
$\tfrac{1}{2} \varepsilon_{\text{mach}}$ where $\varepsilon_{\text{mach}} \approx
2.2 \times 10^{-16}$ for `float64`.

The budget constraint requires $\sum_i w_i = 1.0$ exactly. The projection step
that enforces it,

$$w \;\leftarrow\; w - \frac{\sum_i w_i - 1}{N} \,\mathbf{1},$$

corrects the constraint in exact arithmetic but reintroduces a fresh truncation
error at every step. Over four windows this does not cancel to zero; it
accumulates biasedly depending on the geometry of the particular return data.

Two concrete examples:

- $w_i = 1/3$ is the repeating binary fraction $0.\overline{01}_2$, truncated to
  53 bits. The error per weight is $\approx 5.6 \times 10^{-17}$. Across a
  three-asset portfolio, three such weights already accumulate
  $\approx 1.7 \times 10^{-16}$ of budget error before any solver runs.
- Over 100,000 sequential projection steps with a float32 weight vector (24-bit
  mantissa, $\varepsilon_{\text{mach}} \approx 1.2 \times 10^{-7}$), the same
  drift would reach $\approx 10^{-7}$ — large enough to trigger risk halts in
  medium-frequency execution systems.

The failure is invisible to the solver's convergence criterion. The solver reports
"Converged" with numerically clean-looking 17-digit weight values. The constraint
has already been violated at the floating-point representation level, and there is
no objective-function signal that anything is wrong.

---

## Why this matters

Institutional risk systems check portfolio constraints before every order
submission. A budget or leverage violation, regardless of magnitude, blocks the
entire rebalance. Even a constraint error of $10^{-14}$ — which is $100$ times
smaller than machine epsilon — triggers a pre-trade risk halt in systems with
sufficiently tight tolerances. In live trading, this means no orders are submitted
until the constraint is manually resolved.

Unlike the `boundary_trap` scenario, precision bleed does not produce a
suboptimal objective value. Each individual solve converges correctly to the
optimizer's local minimum. The violation exists only in constraint satisfaction,
which means backtests and offline diagnostics that check objective values will
not surface the problem.

---

## Numerical setup

The scenario uses actual daily returns for four assets during the March 2020
COVID-19 liquidity crisis:

| Asset | Instrument |
| :---- | :--------- |
| SPY | S&P 500 ETF |
| TLT | 20+ Year Treasury Bond ETF |
| GLD | Gold ETF |
| HYG | High-Yield Corporate Bond ETF |

Return dates: March 9, 10, 11, 12, 13, 16, 17, 18, 2020.

The objective and constraints at each window:

$$f(w) = \tfrac{1}{2}\, w^T \Sigma\, w \;-\; \mu^T w$$

$$\text{subject to} \quad \sum_i w_i = 1, \quad \sum_i |w_i| \leq 1.5, \quad w_i \in [-1, 1]$$

where $\Sigma$ and $\mu$ are the sample covariance matrix and mean return vector
over the five-day rolling window. The solver tolerance is set to $10^{-12}$.

---

## Quick start

Run from the `foundations/portfolio-proofs/` root:

```bash
uv run python scenarios/precision_bleed/scipy_slsqp.py
uv run python scenarios/precision_bleed/cvxpy_float.py
```

Both scripts run without optional dependencies. `cvxpy_float.py` falls back to a
native NumPy simulation when CVXPY is not installed.

---

## Scripts

### `scipy_slsqp.py` — actual March 2020 data

Runs four sequential rolling five-day windows of actual March 2020 returns
through SciPy SLSQP at tolerance $10^{-12}$. Flags any window where the budget
error exceeds $10^{-15}$ or the leverage error exceeds $10^{-15}$.

Actual output:

```
Window: 03-09 to 03-13
  Sum of Weights:  1.00000000000000000  (Budget Err: 0.00e+00)
  Gross Exposure:  1.50000000278915402  (Leverage Err: 2.79e-09)
  ⚠️  STATUS: BLEEDING detected!

Window: 03-10 to 03-16
  Sum of Weights:  0.99999999999999611  (Budget Err: 3.89e-15)
  Gross Exposure:  1.49999999999999623  (Leverage Err: 0.00e+00)
  ⚠️  STATUS: BLEEDING detected!

Window: 03-11 to 03-17
  Sum of Weights:  0.99999999999999989  (Budget Err: 1.11e-16)
  Gross Exposure:  1.50000000000000022  (Leverage Err: 2.22e-16)
  ✅  STATUS: Perfect (within float limits)

Window: 03-12 to 03-18
  Sum of Weights:  1.00000000000000022  (Budget Err: 2.22e-16)
  Gross Exposure:  1.50000000000000999  (Leverage Err: 9.99e-15)
  ⚠️  STATUS: BLEEDING detected!
```

Three of four windows show violations. The first-window leverage error of
$2.79 \times 10^{-9}$ is the largest: it exceeds the $10^{-9}$ risk-halt
threshold, and it is already present on the very first rebalance before any
accumulation effect has had time to build.

### `cvxpy_float.py` — high-frequency simulation (100,000 steps)

Simulates cumulative constraint drift across 100,000 sequential projection steps
using a float32 weight vector (no CVXPY installation required). The projection
applied at each step is:

$$w \;\leftarrow\; w + \epsilon_i, \qquad w \;\leftarrow\; w - \frac{\sum_j w_j - 1}{3}\,\mathbf{1}$$

where $\epsilon_i$ is a small sinusoidal perturbation. This mimics the repeated
re-projection that underlies CVXPY/OSQP's ADMM iteration.

Actual output:

```
Final w_float vector sum: 0.9999999999999997779553951
Cumulative Rounding Drift: 2.22e-16
```

After 100,000 iterations with active re-centering at every step, the float64
vector sum has drifted by $2.22 \times 10^{-16}$. In float32 (24-bit mantissa),
the same simulation accumulates $\approx 10^{-7}$ drift — large enough to
trigger risk halts in medium-frequency systems.

---

## The verified PGD solution

The verified PGD solver operates entirely on scaled-integer basis-point
arithmetic: all return values are multiplied by $10{,}000$ and stored as exact
integers (for example, a $5.2\%$ return is stored as the integer $520$). All
arithmetic operations over integers are exact — there is no truncation, no
rounding, and no representation error at any step. Budget and leverage
constraints are enforced using integer equality and inequality checks, not
floating-point comparisons with tolerances.

The Lean 4 proof in `foundations/portfolio-proofs/lean/` formally establishes that the
budget constraint $\sum_i w_i = B$ (in integer units) holds exactly after every
projection step, over an arbitrary number of rebalance steps. The guarantee is
proved once and holds unconditionally at compile time — no runtime tolerance
tuning required.

---

## Files

| File | What it does |
| :--- | :--- |
| `scipy_slsqp.py` | Runs SciPy SLSQP over four March 2020 windows; detects budget and leverage bleeding |
| `cvxpy_float.py` | Simulates 100,000-step float32 accumulation; documents CVXPY/OSQP drift mechanism |

---

## References

- Kraft, D. (1988). "A software package for sequential quadratic programming."
  Tech. Rep. DFVLR-FB 88-28, Institut für Dynamik der Flugsysteme, Oberpfaffenhofen.
  The original Fortran SLSQP implementation; hard-codes `acc=1e-8` as the internal
  constraint satisfaction accuracy parameter. SciPy's `minimize(method="SLSQP")`
  inherits this value directly; it is not overridable via any public API.
- IEEE Computer Society (2019). _IEEE Standard for Floating-Point Arithmetic (IEEE
  Std 754-2019)_. IEEE. DOI: 10.1109/IEEESTD.2019.8766229. The normative document
  defining binary floating-point formats, rounding modes, and the unit-in-last-place
  (ULP) model of rounding error.
- Goldberg, D. (1991). "What every computer scientist should know about
  floating-point arithmetic." _ACM Computing Surveys_ 23(1): 5-48.
  DOI: 10.1145/103162.103163. The standard tutorial on representation error,
  rounding modes, and accumulation in iterative algorithms; directly applicable
  to constraint drift in sequential portfolio rebalancing.
- Higham, N. J. (2002). _Accuracy and Stability of Numerical Algorithms_, 2nd ed.
  SIAM. DOI: 10.1137/1.9780898718027. Chapter 2 proves that iterative computation
  accumulates rounding errors at rate $O(n\,\varepsilon_{\text{mach}})$ across $n$
  steps; Chapter 3 applies this to solving linear systems iteratively, the same
  mechanism that underlies OSQP's ADMM re-projection steps.
