#!/usr/bin/env python3
"""Verify that Lean theorem names cited in Python docstrings exist in Lean sources.

Scans Python docstrings for patterns of the form::

    guaranteed by theorem ``name``
    proven by theorem ``name``
    by theorem ``name``

and checks that ``name`` appears as a theorem, lemma, or def in the Lean
source tree.  References that are marked as planned (surrounded by words
like "planned", "roadmap", "not yet", "targeted") are reported as warnings
rather than errors.

Exit codes
----------
0 — all cited theorems resolved (or explicitly marked as planned/roadmap).
1 — one or more theorem names cited as hard guarantees but absent in Lean.

Usage
-----
::

    # Check specific files (from the monorepo root):
    python3 .github/scripts/check_theorem_refs.py portfolio-proofs/lean_pgd.py

    # Check all Python sources (excluding scenarios and tests):
    python3 .github/scripts/check_theorem_refs.py $(find portfolio-proofs \
        -name "*.py" -not -path "*/scenarios/*" -not -path "*/tests/*")
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches: "guaranteed by theorem `name`" or "proven by ``name``"
# Captures the theorem name.
_HARD_CLAIM = re.compile(
    r"\b(?:guaranteed|proven|proved|certified|verified)\s+by\s+"
    r"(?:theorem|lemma)\s+[`]{1,2}(\w+)[`]{1,2}",
    re.IGNORECASE,
)

# Matches any theorem/lemma backtick-reference after "see theorem", "by theorem", etc.
_SOFT_CLAIM = re.compile(
    r"\btheorem\s+[`]{1,2}(\w+)[`]{1,2}",
    re.IGNORECASE,
)

# Markers that indicate the reference is planned/unproven.
_PLANNED_MARKERS = re.compile(
    r"\b(planned|roadmap|not\s+yet\s+proven|not\s+yet\s+proved|"
    r"targeted\s+for|proof\s+obligation|theorem\s+roadmap)\b",
    re.IGNORECASE,
)

# Lean definition patterns: theorem/lemma/def/abbrev at the start of a line.
_LEAN_DEF = re.compile(
    r"^\s*(?:theorem|lemma|def|noncomputable\s+def|abbrev|private\s+def)\s+"
    r"(\w+)",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Lean source scanning
# ---------------------------------------------------------------------------

# Monorepo root is two levels above this script.
_REPO_ROOT = Path(__file__).parent.parent.parent


def _collect_lean_names() -> set[str]:
    """Return all theorem/lemma/def names from every .lean file in the repo."""
    names: set[str] = set()
    for lean_file in _REPO_ROOT.rglob("*.lean"):
        # Skip build artifacts and archived work.
        parts = lean_file.parts
        if ".lake" in parts or "archive" in parts:
            continue
        text = lean_file.read_text(encoding="utf-8", errors="ignore")
        for m in _LEAN_DEF.finditer(text):
            names.add(m.group(1))
    return names


# ---------------------------------------------------------------------------
# Python docstring scanning
# ---------------------------------------------------------------------------


def _extract_docstrings(py_file: Path) -> list[tuple[int, str]]:
    """Return (lineno, docstring) for every docstring in *py_file*."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            continue
        docstring = ast.get_docstring(node)
        if docstring:
            # lineno of the def/class; module docstring is line 1.
            lineno = getattr(node, "lineno", 1)
            results.append((lineno, docstring))
    return results


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_file(
    py_file: Path,
    lean_names: set[str],
) -> list[str]:
    """Return a list of error/warning strings for *py_file*.

    Returns an empty list if the file is clean.
    """
    messages: list[str] = []
    rel = py_file.relative_to(_REPO_ROOT) if py_file.is_absolute() else py_file

    for lineno, docstring in _extract_docstrings(py_file):
        is_planned = bool(_PLANNED_MARKERS.search(docstring))

        # Hard claims: "guaranteed by theorem `X`"
        for m in _HARD_CLAIM.finditer(docstring):
            name = m.group(1)
            if name not in lean_names:
                if is_planned:
                    messages.append(
                        f"WARNING {rel}:{lineno}: "
                        f"theorem `{name}` cited as guarantee but not found in Lean "
                        f"(docstring contains a 'planned' marker — treat as roadmap item)"
                    )
                else:
                    messages.append(
                        f"ERROR   {rel}:{lineno}: "
                        f"theorem `{name}` cited as guarantee but not found in Lean "
                        f"(add a 'planned' marker if this is aspirational)"
                    )

        # Soft claims: "theorem `X`" anywhere in the docstring
        for m in _SOFT_CLAIM.finditer(docstring):
            name = m.group(1)
            if name not in lean_names and not is_planned:
                messages.append(
                    f"WARNING {rel}:{lineno}: "
                    f"theorem `{name}` referenced but not found in Lean sources"
                )

    return messages


def main(argv: list[str]) -> int:
    """Run the check on the files given as arguments."""
    if not argv:
        print("Usage: check_theorem_refs.py <file.py> [file.py ...]", file=sys.stderr)
        return 1

    lean_names = _collect_lean_names()
    all_messages: list[str] = []

    for arg in argv:
        py_file = Path(arg)
        if not py_file.exists():
            print(f"Skipping missing file: {py_file}", file=sys.stderr)
            continue
        all_messages.extend(check_file(py_file, lean_names))

    if not all_messages:
        print("theorem-refs: all citations resolved.", file=sys.stderr)
        return 0

    # Print warnings first, errors last so they're visible.
    warnings = [m for m in all_messages if m.startswith("WARNING")]
    errors = [m for m in all_messages if m.startswith("ERROR")]

    for msg in warnings:
        print(msg)
    for msg in errors:
        print(msg)

    if errors:
        print(
            f"\ntheorem-refs: {len(errors)} unresolved citation(s). "
            "Add a 'planned' marker or prove the theorem.",
            file=sys.stderr,
        )
        return 1

    print(
        f"\ntheorem-refs: {len(warnings)} planned citation(s) — no hard errors.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
