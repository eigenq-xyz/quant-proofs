# cython: language_level=3
"""
Cython FFI bindings to the Lean 4 PGD solver (OptimizationProofs).

Exposes lean_pgd_solve from OptimizationProofs.FFI.
Input/output: numpy float64 arrays.

Reference-counting rules (Lean deterministic RC):
- Objects created here start at rc=1 (caller owns).
- Passing to an FFI function transfers ownership — do NOT lean_dec after.
- Return values from FFI are owned by caller — lean_dec when done.
- lean_array_get_core returns a BORROWED reference — lean_inc to keep past parent.
"""

import numpy as np
cimport numpy as np
from libc.stdint cimport uint8_t
from libc.stddef cimport size_t

np.import_array()

# ── C declarations: lean.h exact signatures ─────────────────────────────────

cdef extern from "lean/lean.h":
    ctypedef void* lean_object

    # Lifecycle
    void lean_io_mark_end_initialization()
    bint lean_io_result_is_error(lean_object* r)

    # Reference counting
    void lean_inc(lean_object* o)
    void lean_dec(lean_object* o)

    # Scalars (tagged pointers — no RC needed)
    lean_object* lean_box(size_t n)
    size_t lean_unbox(lean_object* o)

    # Float boxing
    lean_object* lean_box_float(double d)
    double lean_unbox_float(lean_object* o)

    # Array construction
    lean_object* lean_mk_empty_array_with_capacity(lean_object* capacity)
    lean_object* lean_array_push(lean_object* a, lean_object* v)

    # Array access (inline, exact signatures from lean.h)
    # lean_array_size: returns size_t directly (NOT a boxed Nat)
    size_t lean_array_size(lean_object* o)
    # lean_array_get_core: takes size_t index, returns BORROWED lean_object*
    lean_object* lean_array_get_core(lean_object* o, size_t i)
    # lean_array_set_core: takes size_t index, CONSUMES v
    void lean_array_set_core(lean_object* o, size_t i, lean_object* v)


# ── Module initialiser + lean_pgd_solve ─────────────────────────────────────

cdef extern from *:
    """
    extern void lean_initialize_runtime_module(void);
    // Module name: optimization-proofs.OptimizationProofs.FFI
    // Hyphen encoded as x2d per Lean's C name mangling
    extern lean_object* initialize_optimization_x2dproofs_OptimizationProofs_FFI(uint8_t builtin);
    extern lean_object* lean_pgd_solve(lean_object* sigmaFlat,
                                       lean_object* muArr,
                                       double lambdaMax,
                                       double leverageCap);
    """
    void lean_initialize_runtime_module()
    lean_object* initialize_optimization_x2dproofs_OptimizationProofs_FFI(uint8_t builtin)
    lean_object* lean_pgd_solve(lean_object* sigmaFlat,
                                lean_object* muArr,
                                double lambdaMax,
                                double leverageCap)

# ── Runtime initialisation ──────────────────────────────────────────────────

cdef bint _lean_initialized = False

def initialize_lean() -> None:
    """Call once before any FFI function. Safe to call multiple times."""
    global _lean_initialized
    if _lean_initialized:
        return
    lean_initialize_runtime_module()
    cdef lean_object* r = initialize_optimization_x2dproofs_OptimizationProofs_FFI(1)
    if lean_io_result_is_error(r):
        raise RuntimeError("Failed to initialize OptimizationProofs.FFI")
    lean_dec(r)
    lean_io_mark_end_initialization()
    _lean_initialized = True

# ── Marshalling helpers ─────────────────────────────────────────────────────

cdef lean_object* np_to_lean_float_array(double* arr, size_t n) except NULL:
    """Pack C double* into a Lean Array Float via lean_array_push."""
    cdef lean_object* a = lean_mk_empty_array_with_capacity(lean_box(n))
    cdef size_t i
    for i in range(n):
        a = lean_array_push(a, lean_box_float(arr[i]))
    return a

cdef void lean_float_array_to_buf(lean_object* a, double* buf, size_t n):
    """Unpack Lean Array Float into a C double* buffer."""
    cdef size_t i
    cdef lean_object* elem
    for i in range(n):
        elem = lean_array_get_core(a, i)   # borrowed — no inc/dec needed
        buf[i] = lean_unbox_float(elem)

# ── Public API ───────────────────────────────────────────────────────────────

def pgd_solve(
    np.ndarray sigma not None,
    np.ndarray mu not None,
    double lambda_max,
    double leverage_cap = 1.5,
) -> np.ndarray:
    """Run the Lean 4 PGD solver via Cython FFI.

    Parameters
    ----------
    sigma : ndarray, shape (N, N), float64
        Shrunk covariance matrix (row-major).
    mu : ndarray, shape (N,), float64
        Mean return vector.
    lambda_max : float
        Maximum eigenvalue of sigma.
    leverage_cap : float, default 1.5
        Gross leverage cap L.

    Returns
    -------
    ndarray, shape (N,), float64
        Optimal portfolio weights.
    """
    if not _lean_initialized:
        raise RuntimeError("Call initialize_lean() before pgd_solve().")

    sigma = np.ascontiguousarray(sigma, dtype=np.float64)
    mu    = np.ascontiguousarray(mu,    dtype=np.float64)

    cdef size_t N = <size_t>mu.shape[0]
    cdef double* sigma_ptr = <double*>sigma.data
    cdef double* mu_ptr    = <double*>mu.data

    # Marshal numpy → Lean arrays (caller gives ownership to lean_pgd_solve)
    cdef lean_object* l_sigma = np_to_lean_float_array(sigma_ptr, N * N)
    cdef lean_object* l_mu    = np_to_lean_float_array(mu_ptr, N)

    # Call Lean solver — acquires l_sigma, l_mu; returns new owned array
    cdef lean_object* l_weights = lean_pgd_solve(l_sigma, l_mu,
                                                  lambda_max, leverage_cap)

    # Marshal result → numpy
    cdef np.ndarray out = np.empty(N, dtype=np.float64)
    lean_float_array_to_buf(l_weights, <double*>out.data, N)
    lean_dec(l_weights)

    return out
