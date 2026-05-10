# verified-ftap

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing
(FTAP, Harrison-Pliska 1981).

> **Theorem (FTAP, discrete-time, finite-state).** A market is arbitrage-free
> if and only if there exists an equivalent martingale measure (EMM).

This is a **work-in-progress skeleton.** The intended endpoint is a mathlib PR.

## Build

```bash
lake exe cache get   # fetch mathlib build cache (first run)
lake build           # build the library
```

The first cache fetch + build takes several minutes.

## License

Apache License 2.0 — matches mathlib's licensing so contributions can flow upstream.
