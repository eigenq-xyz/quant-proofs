import OptimizationProofs.PGD
/-!
# PGD with FloatArray (unboxed) — FFI-optimised variant

Replaces `Array Float` (boxed, per-element heap allocation) with `FloatArray`
(unboxed flat doubles).  On the Lean side `FloatArray.get!` and `FloatArray.push`
operate directly on the underlying `double[]` buffer.  On the Cython side the
marshalling reduces to a single `memcpy` via `lean_float_array_cptr`.
-/
namespace OptimizationProofs

-- ── Helpers ─────────────────────────────────────────────────────────────────

private def norm2diffF (a b : FloatArray) : Float :=
  let sq := (List.range a.size).foldl
    (fun acc i => acc + (a.get! i - b.get! i) ^ 2) (0.0 : Float)
  Float.sqrt sq

/-- Row-major dense matrix-vector multiply: (sigma * w)[i] = Σⱼ sigma[i*N+j] * w[j] -/
def matVecFlat (sigma w : FloatArray) (N : Nat) : FloatArray :=
  (List.range N).foldl (fun res i =>
    let s := (List.range N).foldl (fun acc j =>
      acc + sigma.get! (i * N + j) * w.get! j) (0.0 : Float)
    res.push s)
    FloatArray.empty

-- ── Projection (FloatArray variant) ─────────────────────────────────────────

private def softThreshF (a mu : Float) : Float :=
  let absA := Float.abs a
  if absA ≤ mu then 0.0
  else if a > 0.0 then a - mu else a + mu

private def primalFromDualF (y : FloatArray) (theta mu : Float) : FloatArray :=
  (List.range y.size).foldl (fun res i =>
    res.push (softThreshF (y.get! i - theta) mu))
    FloatArray.empty

private def budgetSumF (y : FloatArray) (theta mu : Float) : Float :=
  (List.range y.size).foldl (fun acc i =>
    acc + softThreshF (y.get! i - theta) mu) (0.0 : Float)

private def bisectThetaF (y : FloatArray) (mu B : Float) (iters : Nat) : Float :=
  let yMin := (List.range y.size).foldl (fun acc i =>
    let yi := y.get! i; if yi < acc then yi else acc) (1e20 : Float)
  let yMax := (List.range y.size).foldl (fun acc i =>
    let yi := y.get! i; if yi > acc then yi else acc) (-1e20 : Float)
  let lo0 := yMin - mu - 2.0
  let hi0 := yMax + mu + 2.0
  (List.range iters).foldl (fun (lo, hi) _ =>
    let mid := (lo + hi) / 2.0
    if budgetSumF y mid mu > B then (mid, hi) else (lo, mid)) (lo0, hi0)
  |> fun (lo, hi) => (lo + hi) / 2.0

/-- Duchi et al. (2008) projection onto { x | Σxᵢ = B, Σ|xᵢ| ≤ L } using FloatArray. -/
def projectL1F (y : FloatArray) (B L : Float) (iters : Nat := 80) : FloatArray :=
  let θ₀ := bisectThetaF y 0.0 B iters
  let x₀ := primalFromDualF y θ₀ 0.0
  let lev₀ := (List.range x₀.size).foldl
    (fun acc i => acc + Float.abs (x₀.get! i)) (0.0 : Float)
  if lev₀ ≤ L then x₀
  else
    let yAbsMax := (List.range y.size).foldl (fun acc i =>
      let a := Float.abs (y.get! i); if a > acc then a else acc) (0.0 : Float)
    let muHi0 := yAbsMax + Float.abs B + 2.0
    let (_, xFinal) := (List.range iters).foldl (fun (muLo, muHi, _) _ =>
      let mu := (muLo + muHi) / 2.0
      let θ  := bisectThetaF y mu B iters
      let x  := primalFromDualF y θ mu
      let lev := (List.range x.size).foldl
        (fun acc i => acc + Float.abs (x.get! i)) (0.0 : Float)
      if Float.abs (lev - L) < 1e-11 then (muLo, muHi, x)
      else if lev > L then (mu, muHi, x)
      else (muLo, mu, x)) (0.0, muHi0, x₀)
      |> fun (a, b, x) => ((a, b), x)
    xFinal

-- ── PGD main loop (FloatArray) ───────────────────────────────────────────────

/-- One PGD step on FloatArrays:  w_{k+1} = Π_C(w_k − η(Σ wₖ − μ)) -/
def pgdStepF (sigma mu w : FloatArray) (N : Nat) (eta L : Float) : FloatArray :=
  let sigmaW := matVecFlat sigma w N
  let wHalf  := (List.range N).foldl (fun res i =>
    res.push (w.get! i - eta * (sigmaW.get! i - mu.get! i)))
    FloatArray.empty
  projectL1F wHalf 1.0 L

/-- PGD solver operating entirely on FloatArrays (no boxing). Returns (w*, iters). -/
partial def pgdFlat (sigma mu : FloatArray) (lambdaMax : Float)
    (leverageCap : Float := 1.5)
    (tol : Float := 1e-8)
    (maxIter : Nat := 5000) : FloatArray × Nat :=
  let N := mu.size
  let eta := 1.9 / lambdaMax
  let w0 : FloatArray := (List.range N).foldl
    (fun a _ => a.push (1.0 / Nat.toFloat N)) FloatArray.empty
  let rec loop (w : FloatArray) (k : Nat) : FloatArray × Nat :=
    if k = 0 then (w, maxIter)
    else
      let wNew := pgdStepF sigma mu w N eta leverageCap
      if norm2diffF wNew w < tol then (wNew, maxIter - k + 1)
      else loop wNew (k - 1)
  loop w0 maxIter

end OptimizationProofs
