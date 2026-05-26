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

## Performance notes

- Warm subprocess call (persistent lean_pgd.py):  ≈ 3 ms  (N = 10, full covariance)
- Dominant cost:  `matVecFlat` — N² multiply-adds per PGD step, 6 steps total
- Pipe + string-parse overhead:  ≈ 0.2 ms  (measured with diagonal sigma where
  the fast-path projection skips the bisection entirely)
- True algorithmic floor (no I/O):  pgd_bench reports 16 ns, but this figure is
  likely optimistic due to compiler constant-folding of the pure, fixed-argument
  call in the timing loop.

## Further optimisation opportunities

1. Replace `FloatArray.get!` (bounds-checked) with unsafe indexing in the proven-safe
   inner loops — `FloatArray.uget` in v4.30.0-rc2 still requires a proof argument,
   so this needs a custom unsafe wrapper.
2. Use the existing Cython FFI (`ffi/pgd_ffi.pyx`) to eliminate pipe + parse overhead
   entirely; estimated warm latency ≈ 0.3 ms via FFI vs 3 ms via subprocess.
3. Reduce bisection iters from 80 to 40 (53 steps give full float64 precision;
   40 gives ≈ 12 significant figures, far beyond the 1e-8 convergence criterion).
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
def projectL1F (y : FloatArray) (B L : Float) (iters : Nat := 80) : FloatArray := Id.run do
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
