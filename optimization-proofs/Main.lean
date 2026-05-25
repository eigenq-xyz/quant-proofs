-- import must come first
import OptimizationProofs.PGD
open OptimizationProofs

/-!
# PGD Benchmark — August 2007 Reconstruction

Runs the Lean 4 PGD solver on the August 2007 stressed-covariance problem
(N=10 sector industries, T=5 day lookback, L=1.5 gross leverage cap) and
reports wall-clock time via `IO.monoMsNow`.

Parameters are the shrunk covariance Σ̂ = 0.1·F + 0.9·S and mean returns μ
from Ken French 10 Industry Portfolio daily VW returns, August 3–9, 2007,
embedded as Float literals.
-/

-- ── August 2007 problem data ────────────────────────────────────────────────

def sigma : Array (Array Float) := #[
  #[3.683368e-04, 3.328713e-04, 2.949957e-04, 3.906513e-04, 2.916090e-04,
    2.651904e-04, 3.974049e-04, 2.894922e-04, 4.525065e-04, 4.823073e-04],
  #[3.328713e-04, 5.626873e-04, 3.539313e-04, 5.741420e-04, 4.125600e-04,
    3.220866e-04, 4.972086e-04, 3.499083e-04, 5.539118e-04, 5.968962e-04],
  #[2.949957e-04, 3.539313e-04, 3.410938e-04, 4.140108e-04, 3.011198e-04,
    2.608142e-04, 3.926867e-04, 2.826207e-04, 4.417335e-04, 4.731386e-04],
  #[3.906513e-04, 5.741420e-04, 4.140108e-04, 7.612273e-04, 4.536405e-04,
    3.870283e-04, 5.712494e-04, 3.905096e-04, 6.653408e-04, 6.789785e-04],
  #[2.916090e-04, 4.125600e-04, 3.011198e-04, 4.536405e-04, 4.001581e-04,
    2.696738e-04, 4.194540e-04, 3.039053e-04, 4.482473e-04, 5.033115e-04],
  #[2.651904e-04, 3.220866e-04, 2.608142e-04, 3.870283e-04, 2.696738e-04,
    2.911249e-04, 3.547616e-04, 2.520032e-04, 4.066605e-04, 4.265474e-04],
  #[3.974049e-04, 4.972086e-04, 3.926867e-04, 5.712494e-04, 4.194540e-04,
    3.547616e-04, 5.917834e-04, 3.869807e-04, 6.059070e-04, 6.505461e-04],
  #[2.894922e-04, 3.499083e-04, 2.826207e-04, 3.905096e-04, 3.039053e-04,
    2.520032e-04, 3.869807e-04, 3.367243e-04, 4.200728e-04, 4.670546e-04],
  #[4.525065e-04, 5.539118e-04, 4.417335e-04, 6.653408e-04, 4.482473e-04,
    4.066605e-04, 6.059070e-04, 4.200728e-04, 7.913791e-04, 7.382880e-04],
  #[4.823073e-04, 5.968962e-04, 4.731386e-04, 6.789785e-04, 5.033115e-04,
    4.265474e-04, 6.505461e-04, 4.670546e-04, 7.382880e-04, 8.416468e-04]
]

def mu : Array Float := #[
   6.600e-04, -4.360e-03, -5.340e-03, -3.760e-03, -3.000e-03,
  -8.280e-03, -3.280e-03,  1.360e-03,  0.000e+00, -6.600e-04
]

-- λ_max(Σ̂) computed offline from numpy eigvalsh
def lambdaMax : Float := 4.568793713620237e-03

def industryNames : Array String :=
  #["NoDur", "Durbl", "Manuf", "Enrgy", "HiTec",
    "Telcm", "Shops", "Hlth ", "Utils", "Other"]

-- ── Objective evaluation ────────────────────────────────────────────────────

def evalObjective (w : Array Float) : Float :=
  let N := w.size
  let wSigmaW := (List.range N).foldl (fun acc i =>
    acc + w[i]! * (List.range N).foldl
      (fun s j => s + sigma[i]![j]! * w[j]!) 0.0) 0.0
  let muW := (List.range N).foldl (fun acc i => acc + mu[i]! * w[i]!) 0.0
  0.5 * wSigmaW - muW

-- ── Main ────────────────────────────────────────────────────────────────────

def main : IO Unit := do
  IO.println "=== Lean 4 PGD — August 2007 Reconstruction ==="
  IO.println s!"N = {mu.size}, lambda_max = {lambdaMax}, eta = {1.9/lambdaMax}"
  IO.println ""

  -- Single timed run
  let t0 ← IO.monoMsNow
  let (wStar, iters) := pgd sigma mu lambdaMax
  let t1 ← IO.monoMsNow

  IO.println "Optimal weights (nonzero):"
  for i in List.range mu.size do
    let wi := wStar[i]!
    if Float.abs wi > 1e-6 then
      IO.println s!"  {industryNames[i]!}  {wi}"

  let budgetErr := Float.abs (wStar.foldl (· + ·) 0.0 - 1.0)
  let leverage  := wStar.foldl (fun acc wi => acc + Float.abs wi) 0.0

  IO.println ""
  IO.println s!"Iterations   : {iters}"
  IO.println s!"Budget error : {budgetErr}"
  IO.println s!"Leverage     : {leverage}  (cap = 1.5)"
  IO.println s!"Objective    : {evalObjective wStar}"
  IO.println s!"Single run   : {t1 - t0} ms"

  -- 1000-run timing for stable estimate (nanosecond resolution)
  let t2 ← IO.monoNanosNow
  for _ in List.range 1000 do
    let _ := pgd sigma mu lambdaMax
    pure ()
  let t3 ← IO.monoNanosNow
  let avgNs := (t3 - t2).toFloat / 1000.0
  let avgMs := avgNs / 1_000_000.0
  IO.println s!"1000-run avg : {avgNs} ns/solve  ({avgMs} ms/solve)"
