import OptimizationProofs.PGD
/-!
# PGD with FloatArray (unboxed) — allocation-free inner loops

Replaces `Array Float` (boxed, per-element heap allocation) with `FloatArray`
(unboxed flat doubles).

## Key change from original implementation

All inner loops use `for i in [:N] do` (Std.Range, zero linked-list allocation)
instead of `(List.range N).foldl` (allocates N linked-list nodes per call).

The original `List.range N + foldl` pattern allocated ≈ 438 000 linked-list nodes
per solve for N = 10 with iters = 80 (6 PGD steps × 80² bisection steps × N nodes
per `budgetSumF` call).  At ≈ 60 ns/alloc+free this adds ≈ 26 ms of overhead.
The Std.Range rewrite eliminates all transient list allocations.

## Performance notes (measured, Apple M-series, warm persistent subprocess)

The dominant cost is the Duchi projection bisection, not the pipe I/O or matrix-vector
multiply.  Measured medians across 15 warm reps:

| Problem (L1 constraint active?)    | Subprocess | FFI-flat | FFI-boxed |
|------------------------------------|-----------|----------|-----------|
| N=2 diag, L1 inactive (pipe floor) |    2.4 ms |   2.5 ms |    6.7 ms |
| N=5 diag, L1 active (phantom_pos)  |    4.8 ms |   4.9 ms |    4.9 ms |
| N=3 diag, L1 active (vix shock)    |    7.6 ms |   7.5 ms |   24.5 ms |
| N=10 CAPM, cond≈36 (sp500)         |   83.3 ms |  82.5 ms |  122.1 ms |
| N=10 rand, cond≈204 (bound.trap)   |  343.7 ms | 344.0 ms |  231.6 ms |

Key takeaways:
- **FFI-flat ≈ subprocess** — the Cython path eliminates pipe overhead (~0.2 ms)
  but the compute cost is identical (same Lean code, same `FloatArray.get!` bounds
  checks).
- **FFI-boxed** is faster than FFI-flat only for large high-condition problems (cond ≥ 200).
  For small or well-conditioned problems it is slower due to N² `lean_box_float` calls
  in the marshalling layer.
- The bisection dominates.  Per-step cost (L1 active, N=10, iters=53):
    ~43 active outer iters × 53 inner iters × N ops × ~60 ns/FloatArray.get! ≈ 1.4 ms.
- `pgd_bench` reports ~16 ns (1 000-run loop, fixed args, no I/O) — this figure is
  unreliable due to compiler constant-folding of the pure, fixed-argument call.

## Bisection step count: why 53

IEEE 754 `Float` has a 53-bit mantissa.  After k bisection steps the search interval
shrinks by 2^(-k):
  - Inner bisect (theta s.t. Σ softThresh(yᵢ - θ, μ) = B):
      range ≈ 8; need precision ≤ tol_pgd/N ≈ 1e-9; k ≥ 33.
  - Outer bisect (μ ≥ 0 s.t. leverage = L, tol 1e-11):
      range ≈ 4; need 4/2^k × N < 1e-11; k ≥ 43.
Using `iters = 53` satisfies both with a ~10-step safety margin and equals the
machine-precision ceiling.  Previously 80; reduction eliminates 37.5% of bisection
work while preserving full float64 accuracy.

## Further optimisation opportunities

1. **Separate outer/inner iters**: outer only needs ~43 steps; inner only ~33. Splitting
   them (e.g., `outerIters=50, innerIters=40`) would save another 25% of bisection work.
2. **Unsafe array indexing**: Replace `FloatArray.get!` (bounds-checked) with unchecked
   access in the proven-safe inner loops.  In v4.30.0-rc2, `FloatArray.uget` still
   requires a proof argument; a custom `@[extern]` wrapper to `lean_float_array_cptr`
   would eliminate the ~60 ns/op bounds-check overhead.
3. **Cython FFI for large N**: For problems where marshalling is cheap relative to
   computation (N ≥ 50 with many PGD steps), the FFI-boxed path is faster.
-/
namespace OptimizationProofs

-- ── Helpers ──────────────────────────────────────────────────────────────────

private def norm2diffF (a b : FloatArray) : Float :=
  let sq := Id.run do
    let mut acc : Float := 0.0
    for i in [:a.size] do
      let d := a.get! i - b.get! i
      acc := acc + d * d
    return acc
  Float.sqrt sq

/-- Row-major dense matrix-vector multiply: (sigma * w)[i] = Σⱼ sigma[i*N+j] * w[j] -/
def matVecFlat (sigma w : FloatArray) (N : Nat) : FloatArray := Id.run do
  let n := N.toUSize
  let mut res := FloatArray.empty
  for i in [:N] do
    let iu := i.toUSize
    let mut s : Float := 0.0
    for j in [:N] do
      s := s + sigma.get! (iu * n + j.toUSize).toNat * w.get! j
    res := res.push s
  return res

-- ── Projection (FloatArray variant) ──────────────────────────────────────────

private def softThreshF (a mu : Float) : Float :=
  let absA := Float.abs a
  if absA ≤ mu then 0.0
  else if a > 0.0 then a - mu else a + mu

private def primalFromDualF (y : FloatArray) (theta mu : Float) : FloatArray := Id.run do
  let mut res := FloatArray.empty
  for i in [:y.size] do
    res := res.push (softThreshF (y.get! i - theta) mu)
  return res

private def budgetSumF (y : FloatArray) (theta mu : Float) : Float := Id.run do
  let mut acc : Float := 0.0
  for i in [:y.size] do
    acc := acc + softThreshF (y.get! i - theta) mu
  return acc

private def bisectThetaF (y : FloatArray) (mu B : Float) (iters : Nat) : Float := Id.run do
  let mut yMin : Float := 1e20
  let mut yMax : Float := -1e20
  for i in [:y.size] do
    let yi := y.get! i
    if yi < yMin then yMin := yi
    if yi > yMax then yMax := yi
  let mut lo := yMin - mu - 2.0
  let mut hi := yMax + mu + 2.0
  for _ in [:iters] do
    let mid := (lo + hi) / 2.0
    if budgetSumF y mid mu > B then lo := mid else hi := mid
  return (lo + hi) / 2.0

/-- Duchi et al. (2008) projection onto { x | Σxᵢ = B, Σ|xᵢ| ≤ L } using FloatArray. -/
def projectL1F (y : FloatArray) (B L : Float) (iters : Nat := 53) : FloatArray := Id.run do
  let θ₀ := bisectThetaF y 0.0 B iters
  let x₀ := primalFromDualF y θ₀ 0.0
  let mut lev₀ : Float := 0.0
  for i in [:x₀.size] do
    lev₀ := lev₀ + Float.abs (x₀.get! i)
  if lev₀ ≤ L then return x₀
  -- L1 constraint is active: bisect over μ ≥ 0
  let mut yAbsMax : Float := 0.0
  for i in [:y.size] do
    let a := Float.abs (y.get! i)
    if a > yAbsMax then yAbsMax := a
  let muHi0 := yAbsMax + Float.abs B + 2.0
  let mut muLo : Float := 0.0
  let mut muHi  := muHi0
  let mut xFinal := x₀
  let mut converged := false
  for _ in [:iters] do
    if !converged then
      let muMid := (muLo + muHi) / 2.0
      let θ     := bisectThetaF y muMid B iters
      let x     := primalFromDualF y θ muMid
      let mut lev : Float := 0.0
      for i in [:x.size] do
        lev := lev + Float.abs (x.get! i)
      xFinal := x
      if Float.abs (lev - L) < 1e-11 then
        converged := true
      else if lev > L then
        muLo := muMid
      else
        muHi := muMid
  return xFinal

-- ── PGD main loop (FloatArray) ────────────────────────────────────────────────

/-- One PGD step on FloatArrays:  w_{k+1} = Π_C(w_k − η(Σ wₖ − μ)) -/
def pgdStepF (sigma mu w : FloatArray) (N : Nat) (eta L : Float) : FloatArray := Id.run do
  let sigmaW := matVecFlat sigma w N
  let mut wHalf := FloatArray.empty
  for i in [:N] do
    wHalf := wHalf.push (w.get! i - eta * (sigmaW.get! i - mu.get! i))
  return projectL1F wHalf 1.0 L

/-- PGD solver operating entirely on FloatArrays (no boxing). Returns (w*, iters). -/
partial def pgdFlat (sigma mu : FloatArray) (lambdaMax : Float)
    (leverageCap : Float := 1.5)
    (tol : Float := 1e-8)
    (maxIter : Nat := 5000) : FloatArray × Nat :=
  let N := mu.size
  let eta := 1.9 / lambdaMax
  let w0 : FloatArray := Id.run do
    let mut a := FloatArray.empty
    for _ in [:N] do
      a := a.push (1.0 / Nat.toFloat N)
    return a
  let rec loop (w : FloatArray) (k : Nat) : FloatArray × Nat :=
    if k = 0 then (w, maxIter)
    else
      let wNew := pgdStepF sigma mu w N eta leverageCap
      if norm2diffF wNew w < tol then (wNew, maxIter - k + 1)
      else loop wNew (k - 1)
  loop w0 maxIter

end OptimizationProofs
