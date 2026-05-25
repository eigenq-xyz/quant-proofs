#!/usr/bin/env python3
"""
Pre-commit hook: verify that Lean 4 import statements appear before any
non-comment, non-whitespace content in each file.

In Lean 4, `import` commands must come at the very beginning of a file.
Whitespace and comments (line `--` and block `/-  -/`) are allowed before
imports, but any Lean declaration (namespace, def, theorem, open, section,
variable, etc.) makes subsequent import statements a hard error.

Usage (by pre-commit): python3 lean_import_order.py file1.lean file2.lean ...
"""

import sys

# Lean keywords that signal the import section has ended.
# An `import` after any of these is invalid.
DECLARATION_KEYWORDS = (
    "namespace",
    "end",
    "open",
    "section",
    "variable",
    "def",
    "theorem",
    "lemma",
    "noncomputable",
    "instance",
    "class",
    "structure",
    "abbrev",
    "notation",
    "macro",
    "syntax",
    "attribute",
    "#check",
    "#eval",
    "#print",
)


def check_file(path: str) -> list[str]:
    errors: list[str] = []
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    in_block_comment = False
    past_imports = False  # True once we've seen a declaration keyword

    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()

        # Track block comments (/-  -/)
        # A line can both open and close a block comment (e.g. /- foo -/)
        opens = raw.count("/-")
        closes = raw.count("-/")
        if not in_block_comment and opens > closes:
            in_block_comment = True
            continue
        if in_block_comment:
            if closes > opens:
                in_block_comment = False
            continue

        # Skip blank lines and line comments
        if not line or line.startswith("--"):
            continue

        if line.startswith("import "):
            if past_imports:
                errors.append(
                    f"{path}:{lineno}: 'import' after non-import content — "
                    "move all imports to the top of the file"
                )
        elif any(line.startswith(kw) for kw in DECLARATION_KEYWORDS):
            past_imports = True

    return errors


def main() -> None:
    files = sys.argv[1:]
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(check_file(path))

    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
