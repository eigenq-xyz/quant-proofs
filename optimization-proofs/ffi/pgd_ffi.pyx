# cython: language_level=3
"""
Cython FFI bindings to the Lean 4 PGD solver (OptimizationProofs).

Two variants timed side-by-side:
  pgd_solve      — Array Float (boxed): 110 lean_box_float calls per solve
  pgd_solve_flat — FloatArray (unboxed): N lean_float_array_push + 1 memcpy

Reference-counting rules (Lean deterministic RC):
  Objects created here start at rc=1 (caller owns).
  Passing to an FFI function transfers ownership — do NOT lean_dec after.
  Return values from FFI are owned by caller — lean_dec when done.
"""

import numpy as np
cimport numpy as np
from libc.stdint cimport uint8_t
from libc.stddef cimport size_t
from libc.string cimport memcpy

np.import_array()

# ── lean.h declarations ──────────────────────────────────────────────────────

cdef extern from "lean/lean.h":
    ctypedef void* lean_object

    void lean_io_mark_end_initialization()
    bint lean_io_result_is_error(lean_object* r)
    void lean_inc(lean_object* o)
    void lean_dec(lean_object* o)

    lean_object* lean_box(size_t n)
    size_t lean_unbox(lean_object* o)

    # ── Slow path: boxed Array Float ─────────────────────────────────────────
    lean_object* lean_box_float(double d)
    double lean_unbox_float(lean_object* o)
    lean_object* lean_mk_empty_array_with_capacity(lean_object* capacity)
    lean_object* lean_array_push(lean_object* a, lean_object* v)
    size_t lean_array_size(lean_object* o)
    lean_object* lean_array_get_core(lean_object* o, size_t i)

    # ── Fast path: unboxed FloatArray ────────────────────────────────────────
    # lean_float_array_push: writes double directly to backing buffer (no malloc)
    lean_object* lean_float_array_push(lean_object* a, double d)
    # lean_float_array_uget: direct double read (no unboxing, no malloc)
    double lean_float_array_uget(lean_object* a, size_t i)
    # lean_float_array_cptr: raw double* pointer to backing buffer
    double* lean_float_array_cptr(lean_object* a)


# ── Lean module exports ──────────────────────────────────────────────────────

cdef extern from *:
    """
    extern void lean_initialize_runtime_module(void);
    extern lean_object* initialize_optimization_x2dproofs_OptimizationProofs_FFI(uint8_t builtin);

    // Slow path: Array Float (boxed doubles)
    extern lean_object* lean_pgd_solve(lean_object* sigma, lean_object* mu,
                                       double lam, double lev);
    // Fast path: FloatArray (unboxed doubles)
    extern lean_object* lean_pgd_solve_flat(lean_object* sigma, lean_object* mu,
                                            double lam, double lev);
    // The canonical empty FloatArray global (initialised during module init)
    extern lean_object* l_FloatArray_empty;
    """
    void lean_initialize_runtime_module()
    lean_object* initialize_optimization_x2dproofs_OptimizationProofs_FFI(uint8_t builtin)
    lean_object* lean_pgd_solve(lean_object* sigma, lean_object* mu,
                                double lam, double lev)
    lean_object* lean_pgd_solve_flat(lean_object* sigma, lean_object* mu,
                                     double lam, double lev)
    # l_FloatArray_empty is a global variable (NOT a function)
    lean_object* l_FloatArray_empty


# ── Runtime initialisation ───────────────────────────────────────────────────

cdef bint _lean_initialized = False

def initialize_lean() -> None:
    """Call once before any FFI function."""
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


# ── Marshalling: slow path (Array Float, boxed) ──────────────────────────────

cdef lean_object* _np_to_array_float(double* ptr, size_t n) except NULL:
    """Pack C doubles into Lean Array Float via lean_box_float (one malloc per element)."""
    cdef lean_object* a = lean_mk_empty_array_with_capacity(lean_box(n))
    cdef size_t i
    for i in range(n):
        a = lean_array_push(a, lean_box_float(ptr[i]))
    return a

cdef void _array_float_to_np(lean_object* a, double* buf, size_t n):
    """Unpack Lean Array Float into C doubles via lean_unbox_float."""
    cdef size_t i
    cdef lean_object* elem
    for i in range(n):
        elem = lean_array_get_core(a, i)   # borrowed reference
        buf[i] = lean_unbox_float(elem)


# ── Marshalling: fast path (FloatArray, unboxed) ─────────────────────────────

cdef lean_object* _np_to_float_array(double* ptr, size_t n) except NULL:
    """Pack C doubles into Lean FloatArray via lean_float_array_push.

    lean_float_array_push writes the double directly into the backing buffer —
    no lean_box_float, no per-element heap allocation.

    l_FloatArray_empty is a Lean global variable (not a function); we must
    lean_inc it before passing to lean_float_array_push since push takes
    ownership of its first argument.
    """
    lean_inc(l_FloatArray_empty)    # push takes ownership; keep global alive
    cdef lean_object* fa = l_FloatArray_empty
    cdef size_t i
    for i in range(n):
        fa = lean_float_array_push(fa, ptr[i])
    return fa

cdef void _float_array_to_np(lean_object* a, double* buf, size_t n):
    """Unpack Lean FloatArray via lean_float_array_uget (direct double read,
    no lean_unbox_float, no per-element heap access).
    """
    cdef size_t i
    for i in range(n):
        buf[i] = lean_float_array_uget(a, i)


# ── Public API ───────────────────────────────────────────────────────────────

def pgd_solve(
    np.ndarray sigma not None,
    np.ndarray mu not None,
    double lambda_max,
    double leverage_cap = 1.5,
) -> np.ndarray:
    """Slow path: Array Float (boxed). Marshalling: N² lean_box_float calls."""
    if not _lean_initialized:
        raise RuntimeError("Call initialize_lean() first.")
    sigma = np.ascontiguousarray(sigma, dtype=np.float64)
    mu    = np.ascontiguousarray(mu,    dtype=np.float64)
    cdef size_t N = <size_t>mu.shape[0]
    cdef lean_object* l_sigma = _np_to_array_float(<double*>sigma.data, N * N)
    cdef lean_object* l_mu    = _np_to_array_float(<double*>mu.data, N)
    cdef lean_object* l_w = lean_pgd_solve(l_sigma, l_mu, lambda_max, leverage_cap)
    cdef np.ndarray out = np.empty(N, dtype=np.float64)
    _array_float_to_np(l_w, <double*>out.data, N)
    lean_dec(l_w)
    return out


def pgd_solve_flat(
    np.ndarray sigma not None,
    np.ndarray mu not None,
    double lambda_max,
    double leverage_cap = 1.5,
) -> np.ndarray:
    """Fast path: FloatArray (unboxed).
    In:  N² + N lean_float_array_push calls (direct double write, no malloc)
    Out: 1 memcpy via lean_float_array_cptr
    """
    if not _lean_initialized:
        raise RuntimeError("Call initialize_lean() first.")
    sigma = np.ascontiguousarray(sigma, dtype=np.float64)
    mu    = np.ascontiguousarray(mu,    dtype=np.float64)
    cdef size_t N = <size_t>mu.shape[0]
    cdef lean_object* l_sigma = _np_to_float_array(<double*>sigma.data, N * N)
    cdef lean_object* l_mu    = _np_to_float_array(<double*>mu.data, N)
    cdef lean_object* l_w = lean_pgd_solve_flat(l_sigma, l_mu, lambda_max, leverage_cap)
    cdef np.ndarray out = np.empty(N, dtype=np.float64)
    _float_array_to_np(l_w, <double*>out.data, N)
    lean_dec(l_w)
    return out
