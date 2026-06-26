/-!
# Projected Gradient Descent for Mean-Variance Portfolio Optimization

Main loop — no theorems yet, pure computation. No proof obligations.

Minimizes f(w) = ½ wᵀΣw − μᵀw subject to ∑wᵢ = 1, ∑|wᵢ| ≤ L using
projected gradient descent with the Duchi et al. (2008) O(N log N)
dual-bisection projection.
-/

namespace OptimizationProofs

-- ── Helpers ─────────────────────────────────────────────────────────────────

/-- ‖a − b‖₂ -/
def norm2diff (a b : Array Float) : Float :=
  let sq := (List.range a.size).foldl
    (fun acc i => acc + (a[i]! - b[i]!) ^ 2) 0.0
  Float.sqrt sq

/-- Matrix-vector product: (Σ w)[i] = ∑ⱼ Σ[i][j] · w[j] -/
def matVecMul (sigma : Array (Array Float)) (w : Array Float) : Array Float :=
  let N := w.size
  (List.range N).toArray.map fun i =>
    (List.range N).foldl (fun acc j => acc + sigma[i]![j]! * w[j]!) 0.0

-- ── Projection ─────────────────────────────────────────────────────────────

/-- Soft-thresholding: sign(a) · max(|a| − μ, 0) -/
private def softThresh (a mu : Float) : Float :=
  let absA := Float.abs a
  if absA ≤ mu then 0.0
  else if a > 0.0 then a - mu
  else a + mu

/-- xᵢ(θ, μ) = sign(yᵢ − θ) · max(|yᵢ − θ| − μ, 0) -/
private def primalFromDual (y : Array Float) (theta mu : Float) : Array Float :=
  y.map fun yi => softThresh (yi - theta) mu

/-- ∑ xᵢ(θ, μ) for budget bisection -/
private def budgetSum (y : Array Float) (theta mu : Float) : Float :=
  (primalFromDual y theta mu).foldl (· + ·) 0.0

/-- Bisect θ so that ∑ xᵢ(θ, μ) = B (for fixed μ) -/
private def bisectTheta (y : Array Float) (mu B : Float) (iters : Nat) : Float :=
  let yMin := y.foldl (fun acc yi => if yi < acc then yi else acc) 1e20
  let yMax := y.foldl (fun acc yi => if yi > acc then yi else acc) (-1e20)
  let lo0 := yMin - mu - 2.0
  let hi0 := yMax + mu + 2.0
  (List.range iters).foldl (fun (lo, hi) _ =>
    let mid := (lo + hi) / 2.0
    if budgetSum y mid mu > B then (mid, hi) else (lo, mid)) (lo0, hi0)
  |> fun (lo, hi) => (lo + hi) / 2.0

/-- Duchi et al. (2008) O(N log N) projection onto {∑x = B, ∑|x| ≤ L}. -/
def projectL1 (y : Array Float) (B L : Float) (iters : Nat := 80) : Array Float :=
  -- Try μ = 0 first (simplex projection)
  let theta0 := bisectTheta y 0.0 B iters
  let x0 := primalFromDual y theta0 0.0
  let lev0 := x0.foldl (fun acc xi => acc + Float.abs xi) 0.0
  if lev0 ≤ L then x0
  else
    -- L1 constraint active: bisect over μ ≥ 0
    let yAbsMax := y.foldl (fun acc yi => if Float.abs yi > acc then Float.abs yi else acc) 0.0
    let muHi0 := yAbsMax + Float.abs B + 2.0
    let (_, xFinal) := (List.range iters).foldl (fun (muLo, muHi, _) _ =>
      let mu := (muLo + muHi) / 2.0
      let theta := bisectTheta y mu B iters
      let xStar := primalFromDual y theta mu
      let lev := xStar.foldl (fun acc xi => acc + Float.abs xi) 0.0
      if Float.abs (lev - L) < 1e-11 then (muLo, muHi, xStar)
      else if lev > L then (mu, muHi, xStar)
      else (muLo, mu, xStar)) (0.0, muHi0, x0)
      |> fun (a, b, x) => ((a, b), x)
    xFinal

-- ── PGD main loop ──────────────────────────────────────────────────────────

/-- One projected gradient step: w_{k+1} = Π_C(w_k − η(Σwₖ − μ)) -/
def pgdStep (sigma : Array (Array Float)) (mu w : Array Float)
    (eta L : Float) : Array Float :=
  let g := matVecMul sigma w           -- Σw
  let gMinusMu := (List.range mu.size).toArray.map fun i =>
    g[i]! - mu[i]!                     -- Σw − μ
  let wHalf := (List.range w.size).toArray.map fun i =>
    w[i]! - eta * gMinusMu[i]!         -- gradient step
  projectL1 wHalf 1.0 L

/-- PGD solver. Returns (w*, iterations used).

    Uses `partial def` for the inner loop so Lean accepts early exit before
    `maxIter` steps. For the benchmark executable this is fine; the future
    Lean 4 proof will use a bounded-recursion variant with convergence proofs.
-/
partial def pgd (sigma : Array (Array Float)) (mu : Array Float)
    (lambdaMax : Float)
    (leverageCap : Float := 1.5)
    (tol : Float := 1e-8)
    (maxIter : Nat := 5000) : Array Float × Nat :=
  let N := mu.size
  let eta := 1.9 / lambdaMax
  let w0 : Array Float := (List.replicate N (1.0 / N.toFloat)).toArray
  let rec loop (w : Array Float) (k : Nat) : Array Float × Nat :=
    if k = 0 then (w, maxIter)
    else
      let wNew := pgdStep sigma mu w eta leverageCap
      if norm2diff wNew w < tol then (wNew, maxIter - k + 1)
      else loop wNew (k - 1)
  loop w0 maxIter

end OptimizationProofs
