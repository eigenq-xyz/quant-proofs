#!/usr/bin/env bash
# Copy rendered PDF + figure-PDF asset bundles from Quarto's output-dir to a
# committed stable path in reports/. GitHub Pages CI (.github/workflows/pages.yml)
# copies these committed artifacts directly to the Pages site — CI does NOT
# re-render the paper because it would require Lean + Cython FFI + research deps.
#
# Always run `make paper` (which invokes `quarto render`) before committing
# changes that should appear on the published site. This script keeps the
# committed artifacts in sync with the QMD source automatically.
#
# This project distributes the paper as PDF only; no HTML output is generated.
set -euo pipefail

OUTPUT_DIR="${QUARTO_OUTPUT_DIR:-_output}"

# Copy PDFs (one per .qmd in reports/)
find "${OUTPUT_DIR}" -maxdepth 1 -name "*.pdf" | while IFS= read -r pdf; do
    dest="$(basename "${pdf}")"
    cp "${pdf}" "${dest}"
    echo "post-render: copied ${pdf} → ${dest}"
done

# Copy *_files/ asset bundles (figure-pdf PDFs only; HTML asset subdirs pruned)
find "${OUTPUT_DIR}" -maxdepth 1 -type d -name "*_files" | while IFS= read -r files_dir; do
    dest="$(basename "${files_dir}")"
    rm -rf "${dest}"
    cp -r "${files_dir}" "${dest}"
    # Prune HTML-specific subdirectories if Quarto happens to emit them
    rm -rf "${dest}/figure-html" "${dest}/libs"
    echo "post-render: copied ${files_dir}/ → ${dest}/ (PDF assets only)"
done
