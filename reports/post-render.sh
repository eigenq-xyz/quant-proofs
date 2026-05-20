#!/usr/bin/env bash
# Copy rendered PDF from Quarto's output-dir to a committed stable path.
# Quarto runs this after every successful render of any .qmd in reports/.
# The committed PDF at reports/<name>.pdf is what CI copies to GitHub Pages.
set -euo pipefail

OUTPUT_DIR="${QUARTO_OUTPUT_DIR:-_output}"

find "${OUTPUT_DIR}" -maxdepth 1 -name "*.pdf" | while IFS= read -r pdf; do
    dest="$(basename "${pdf}")"
    cp "${pdf}" "${dest}"
    echo "post-render: copied ${pdf} → ${dest}"
done
