import OptimizationProofs.PGD
/-!
# FFI Exports — PGD Solver

Thin wrappers that expose the PGD solver via @[export] so Lake generates
C-compatible entry points that Cython can link against.

The exported function takes flat Float arrays (row-major for sigma) and
returns the optimal weight vector as a Float array.  All marshalling
between Lean's Array Float and C doubles is handled via lean_box_float /
lean_unbox_float in the Cython layer.
-/
namespace OptimizationProofs

/-- FFI entry point: flat sigma (N×N, row-major) + mu (N) → weights (N).

    Called from Cython via `lean_pgd_solve(sigmaFlat, muArr, lambdaMax, leverageCap)`.
    The caller owns all returned objects and must manage RC.
-/
@[export lean_pgd_solve]
def pgdSolve (sigmaFlat : Array Float) (muArr : Array Float)
    (lambdaMax leverageCap : Float) : Array Float :=
  let N := muArr.size
  -- Reconstruct row-major 2D sigma from flat array
  let sigma : Array (Array Float) :=
    (List.range N).toArray.map fun i =>
      (List.range N).toArray.map fun j =>
        sigmaFlat[i * N + j]!
  let (wStar, _) := pgd sigma muArr lambdaMax leverageCap
  wStar

end OptimizationProofs
