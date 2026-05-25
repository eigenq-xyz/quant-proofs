import OptimizationProofs.PGD
import OptimizationProofs.PGDFlat
/-!
# FFI Exports — PGD Solver (two variants)

- `lean_pgd_solve`:      Array Float (boxed) — original, slower marshalling
- `lean_pgd_solve_flat`: FloatArray (unboxed) — fast path, memcpy marshalling
-/
namespace OptimizationProofs

/-- Original export: boxed Array Float.
    Marshalling cost: N² lean_box_float calls in Cython. -/
@[export lean_pgd_solve]
def pgdSolve (sigmaFlat : Array Float) (muArr : Array Float)
    (lambdaMax leverageCap : Float) : Array Float :=
  let N := muArr.size
  let sigma : Array (Array Float) :=
    (List.range N).toArray.map fun i =>
      (List.range N).toArray.map fun j =>
        sigmaFlat[i * N + j]!
  let (wStar, _) := pgd sigma muArr lambdaMax leverageCap
  wStar

/-- Fast export: unboxed FloatArray.
    Marshalling cost: single memcpy via lean_float_array_cptr in Cython. -/
@[export lean_pgd_solve_flat]
def pgdSolveFlat (sigmaFlat : FloatArray) (muArr : FloatArray)
    (lambdaMax leverageCap : Float) : FloatArray :=
  let (wStar, _) := pgdFlat sigmaFlat muArr lambdaMax leverageCap
  wStar

/-- Returns an empty FloatArray.  Needed by Cython to seed lean_float_array_push. -/
@[export lean_fa_empty]
def faEmpty : FloatArray := FloatArray.empty

end OptimizationProofs
