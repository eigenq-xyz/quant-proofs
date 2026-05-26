"""Strip Quarto GFM HTML wrappers so Sphinx/Jupyter Book can parse the files.

Quarto GFM output wraps figures and tables in <div id="..."> blocks and
emits long-dash horizontal-rule separators before footnotes.  Both cause
Sphinx "adjacent transitions" errors.  This script:

  1. Removes bare <div ...> and </div> wrapper lines (keeps content inside).
  2. Removes the Quarto footnote separator (--------...).
  3. Optionally collapses the Quarto auto-TOC bullet list at the top
     (Jupyter Book generates its own navigation; the in-file list is redundant).

Usage (from repo root):
    python3 docs/strip_quarto_html.py docs/portfolio/*.md
"""

from __future__ import annotations

import re
import sys


def clean(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        # Drop bare <div ...> and </div> wrapper lines
        stripped = line.strip()
        if re.match(r'^</?div(\s[^>]*)?>$', stripped):
            continue
        # Drop Quarto footnote separator (4+ consecutive dashes, nothing else)
        if re.match(r'^-{4,}\s*$', stripped):
            continue
        out.append(line)
    return "".join(out)


def main() -> None:
    paths = sys.argv[1:]
    if not paths:
        print("Usage: strip_quarto_html.py <file.md> [file.md ...]")
        sys.exit(1)
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                original = fh.read()
            cleaned = clean(original)
            if cleaned != original:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(cleaned)
                print(f"  cleaned: {path}")
            else:
                print(f"  ok:      {path}")
        except OSError as exc:
            print(f"  error:   {path}: {exc}")


if __name__ == "__main__":
    main()
