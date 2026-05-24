# backtest-proofs

> **Educational Use Only**: This software is for research and educational purposes only. It is not intended for live trading or production use.

An options delta-hedging backtester with Lean 4 proof-checked accounting invariants, implemented in Python.

## What this does

Research paper: [Provably Correct Quantitative Backtesting (PDF)](https://eigenq-xyz.github.io/quant-proofs/paper/backtest-proofs.pdf)

The backtester simulates discrete delta-hedging strategies over historical or synthetic price paths. Portfolio bookkeeping (NAV identity, trade accounting, self-financing, option settlement) is implemented in Lean 4 and called from Python via Cython FFI.

At each weekly rebalancing step:

1. The option is marked to market at the new Black-Scholes price
2. The underlying hedge is rebalanced to the current delta
3. A `StepCertificate` is emitted verifying Lean's `valueUpdateFormula` held

A bug in the accounting logic raises `ValueError` immediately rather than silently producing incorrect numbers.

## Why formal proof?

A unit test checks one input. A Lean proof checks **all inputs**. The accounting theorems hold for every possible portfolio, every possible trade size, every possible option strike and spot price.

The key theorem, `settlement_value_formula`, unifies ITM and OTM option expiry into a single machine-checked statement:

$$\Delta\text{PV} = \text{qty} \times (\text{payoff} - \text{mark})$$

This holds whether the option expires in-the-money (ITM, `applyTrade` path) or out-of-the-money (OTM, `abandonPosition` path).

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs/backtest-proofs
make setup
make test
```

## Contents of this book

- **Formal Guarantees**: the theorems proven and the states made impossible by construction
- **Validation**: DerivaGem reference vectors, Monte Carlo convergence, BKL variance scaling, Carr-Madan decomposition
- **Delta-Hedging Demo**: Hull Table 19.2 replication with live step certificates and a deliberately broken example
- **Credibility Exhibits**: Leland (1985) rehedge-frequency sweep, QuantLib A-B comparison, four historical stress regimes
- **Architecture**: Lean accounting module, Python, and Cython FFI
- **Human-AI Collaboration**: how Lean acts as a development scaffold constraining AI-generated code

## References

- Hull, *Options, Futures, and Other Derivatives*, 9th Global ed. (2014), Tables 19.2, 19.3
- [Leland (1985)](https://doi.org/10.1111/j.1540-6261.1985.tb02383.x), *JF* 40(4): option pricing and replication with transaction costs
- [Bertsimas, Kogan & Lo (2000)](https://doi.org/10.1016/S0304-405X(99)00048-6), *JFE* 55(2): discrete hedging variance
- [Carr & Madan (1998)](https://ssrn.com/abstract=1691942): realized P&L decomposition via dollar gamma
- [de Moura & Ullrich (2021)](https://doi.org/10.1007/978-3-030-79876-5_37): Lean 4 theorem prover and programming language
