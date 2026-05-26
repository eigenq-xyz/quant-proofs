-- import must come first
import OptimizationProofs.PGDFlat
open OptimizationProofs

/-!
# PGD Benchmark — August 2007 Reconstruction (anti-fold edition)

Runs `pgdFlat` on the August 2007 stressed-covariance problem (N=10, cond≈86,
L=1.5) and reports wall-clock time via `IO.monoNanosNow`.

## Why the old timing was wrong

The previous version called `pgd sigma mu lambdaMax` 1000 times with identical
fixed arguments inside a pure loop.  LLVM constant-folds pure functions with
fixed arguments — each result is pre-computed at compile time, and the loop
measures only iteration overhead (~16 ns, not the algorithm).

Fix: vary `lambdaMax` by `i × 1e-9` per iteration.  At lambdaMax ≈ 4.6e-3 this
changes the value by one ULP per step, forcing LLVM to treat each call as a
distinct computation.  The accumulator `acc := acc + w.get! 0` prevents
dead-code elimination of the return value.  The result is the true algorithm
time.

## What is measured

- 5 warmup solves (cache and OS scheduler settle)
- 50 timed single solves with varying lambdaMax
- Output: median, Q1, Q3, min, max (nanoseconds and milliseconds)

The median is the defensible number.  Min is optimistic (best-case OS
scheduling).  Mean is misleading when GC pauses create outliers.
-/

-- ── Problem data: August 2007 (LW-shrunk covariance, flat row-major) ─────────

/-- Σ̂ = 0.1·F + 0.9·S, Ken French 10-industry, Aug 3–9 2007, flat row-major. -/
def sigmaFlat : FloatArray := FloatArray.mk #[
  3.683368e-04, 3.328713e-04, 2.949957e-04, 3.906513e-04, 2.916090e-04,
  2.651904e-04, 3.974049e-04, 2.894922e-04, 4.525065e-04, 4.823073e-04,
  3.328713e-04, 5.626873e-04, 3.539313e-04, 5.741420e-04, 4.125600e-04,
  3.220866e-04, 4.972086e-04, 3.499083e-04, 5.539118e-04, 5.968962e-04,
  2.949957e-04, 3.539313e-04, 3.410938e-04, 4.140108e-04, 3.011198e-04,
  2.608142e-04, 3.926867e-04, 2.826207e-04, 4.417335e-04, 4.731386e-04,
  3.906513e-04, 5.741420e-04, 4.140108e-04, 7.612273e-04, 4.536405e-04,
  3.870283e-04, 5.712494e-04, 3.905096e-04, 6.653408e-04, 6.789785e-04,
  2.916090e-04, 4.125600e-04, 3.011198e-04, 4.536405e-04, 4.001581e-04,
  2.696738e-04, 4.194540e-04, 3.039053e-04, 4.482473e-04, 5.033115e-04,
  2.651904e-04, 3.220866e-04, 2.608142e-04, 3.870283e-04, 2.696738e-04,
  2.911249e-04, 3.547616e-04, 2.520032e-04, 4.066605e-04, 4.265474e-04,
  3.974049e-04, 4.972086e-04, 3.926867e-04, 5.712494e-04, 4.194540e-04,
  3.547616e-04, 5.917834e-04, 3.869807e-04, 6.059070e-04, 6.505461e-04,
  2.894922e-04, 3.499083e-04, 2.826207e-04, 3.905096e-04, 3.039053e-04,
  2.520032e-04, 3.869807e-04, 3.367243e-04, 4.200728e-04, 4.670546e-04,
  4.525065e-04, 5.539118e-04, 4.417335e-04, 6.653408e-04, 4.482473e-04,
  4.066605e-04, 6.059070e-04, 4.200728e-04, 7.913791e-04, 7.382880e-04,
  4.823073e-04, 5.968962e-04, 4.731386e-04, 6.789785e-04, 5.033115e-04,
  4.265474e-04, 6.505461e-04, 4.670546e-04, 7.382880e-04, 8.416468e-04
]

/-- μ = mean daily returns, Ken French 10-industry, Aug 3–9 2007. -/
def muFlat : FloatArray := FloatArray.mk #[
   6.600e-04, -4.360e-03, -5.340e-03, -3.760e-03, -3.000e-03,
  -8.280e-03, -3.280e-03,  1.360e-03,  0.000e+00, -6.600e-04
]

/-- λ_max(Σ̂), computed offline from numpy `eigvalsh`. -/
def lambdaMax : Float := 4.568793713620237e-03

def leverageCap : Float := 1.5

def industryNames : Array String :=
  #["NoDur", "Durbl", "Manuf", "Enrgy", "HiTec",
    "Telcm", "Shops", "Hlth ", "Utils", "Other"]

-- ── Objective evaluation ─────────────────────────────────────────────────────

def evalObjectiveFlat (w : FloatArray) : Float := Id.run do
  let N := w.size
  let mut wSw : Float := 0.0
  for i in [:N] do
    let mut row : Float := 0.0
    for j in [:N] do
      row := row + sigmaFlat.get! (i * N + j) * w.get! j
    wSw := wSw + w.get! i * row
  let mut muw : Float := 0.0
  for i in [:N] do
    muw := muw + muFlat.get! i * w.get! i
  return 0.5 * wSw - muw

-- ── Median of a sorted array ─────────────────────────────────────────────────

def sortedMedian (xs : Array Nat) : Float :=
  let n := xs.size
  if n == 0 then 0.0
  else if n % 2 == 1 then xs[n / 2]!.toFloat
  else (xs[n / 2 - 1]!.toFloat + xs[n / 2]!.toFloat) / 2.0

-- insertion sort for small arrays
def insertionSort (xs : Array Nat) : Array Nat := Id.run do
  let mut a := xs
  for i in [1:a.size] do
    let key := a[i]!
    let mut j := i
    while j > 0 && a[j - 1]! > key do
      a := a.set! j a[j - 1]!
      j := j - 1
    a := a.set! j key
  return a

-- ── Main ─────────────────────────────────────────────────────────────────────

def main : IO Unit := do
  let N := muFlat.size  -- 10
  IO.println "=== Lean 4 PGD Benchmark — August 2007 (anti-fold edition) ==="
  IO.println s!"N = {N},  cond ≈ 86,  L1-active = true"
  IO.println s!"λ_max = {lambdaMax},  η = {1.9 / lambdaMax}"
  IO.println ""

  -- ── Single correctness run ────────────────────────────────────────────────
  let t0 ← IO.monoMsNow
  let (wStar, iters) := pgdFlat sigmaFlat muFlat lambdaMax leverageCap
  let t1 ← IO.monoMsNow

  IO.println "Optimal weights (nonzero, |w| > 1e-6):"
  for i in [:N] do
    let wi := wStar.get! i
    if Float.abs wi > 1e-6 then
      IO.println s!"  {industryNames[i]!}  {wi}"

  let budgetSum : Float := Id.run do
    let mut s : Float := 0.0
    for i in [:N] do
      s := s + wStar.get! i
    return s
  let budgetErr := Float.abs (budgetSum - 1.0)
  let leverage : Float := Id.run do
    let mut s : Float := 0.0
    for i in [:N] do
      s := s + Float.abs (wStar.get! i)
    return s

  IO.println ""
  IO.println s!"PGD iters    : {iters}"
  IO.println s!"Budget err   : {budgetErr}"
  IO.println s!"Leverage     : {leverage}  (cap = {leverageCap})"
  IO.println s!"Objective    : {evalObjectiveFlat wStar}"
  IO.println s!"Single run   : {t1 - t0} ms  (coarse ms timer)"
  IO.println ""

  -- ── Anti-fold timing: vary lambdaMax by i×1e-9 per iteration ─────────────
  -- Warmup: 5 calls, results discarded.  Warms I-cache, branch predictor,
  -- and OS scheduler quantum.
  let mut warmAcc : Float := 0.0
  for i in [:5] do
    let lam := lambdaMax + Float.ofNat i * 1e-9
    let (w, _) := pgdFlat sigmaFlat muFlat lam leverageCap
    warmAcc := warmAcc + w.get! 0
  -- prevent DCE of warmup
  if warmAcc > 1e10 then IO.println "unexpected warmup result"

  -- Timed runs: 50 solves, each with a distinct lambdaMax.
  -- The i×1e-9 shift (~2e-7 relative) is smaller than PGD tolerance (1e-8
  -- absolute), so all 50 solutions are identical to 8 significant figures.
  -- The shift is large enough (> 1 ULP at this scale) that LLVM cannot fold.
  let REPS := 50
  let mut times : Array Nat := #[]
  let mut acc : Float := 0.0
  for i in [:REPS] do
    let lam := lambdaMax + Float.ofNat i * 1e-9
    let t_start ← IO.monoNanosNow
    let (w, _) := pgdFlat sigmaFlat muFlat lam leverageCap
    let t_end ← IO.monoNanosNow
    acc := acc + w.get! 0   -- prevent DCE
    times := times.push (t_end - t_start)

  -- prevent DCE of accumulator
  if acc > 1e10 then IO.println "unexpected acc"

  let sorted := insertionSort times
  let medNs  := sortedMedian sorted
  let q1Ns   := (sorted[REPS / 4]!).toFloat
  let q3Ns   := (sorted[3 * REPS / 4]!).toFloat
  let minNs  := (sorted[0]!).toFloat
  let maxNs  := (sorted[REPS - 1]!).toFloat

  IO.println s!"Timing ({REPS} anti-fold reps, nanoseconds):"
  IO.println s!"  Median  : {medNs} ns  ({medNs / 1_000_000.0} ms)"
  IO.println s!"  Q1–Q3   : {q1Ns}–{q3Ns} ns  ({q1Ns / 1_000_000.0}–{q3Ns / 1_000_000.0} ms)"
  IO.println s!"  Min/Max : {minNs} ns / {maxNs} ns"
  IO.println ""
  IO.println "NOTE: 'single run' above uses the coarse ms timer (IO.monoMsNow)."
  IO.println "The anti-fold median is the defensible number."
  IO.println "Previously reported '~16 ns' was constant-folded loop overhead."
