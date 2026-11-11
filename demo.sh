#!/usr/bin/env bash
# KubeMend demo: scan a vulnerable manifest, preview the patch, apply it,
# rescan clean, and generate an audit report. Works on a temp copy - the
# examples in the repo are never modified.
set -euo pipefail
cd "$(dirname "$0")"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp examples/vulnerable-app.yaml "$WORK/app.yaml"

echo "=== 1. Scan (dry run - nothing on disk changes) ==="
python -m kubemend scan "$WORK/app.yaml" || true

echo
echo "=== 2. Why KM006 matters (--explain, one rule) ==="
python -m kubemend scan "$WORK/app.yaml" --rules KM006 --explain || true

echo
echo "=== 3. Apply the patch with --write, then rescan ==="
python -m kubemend scan "$WORK/app.yaml" --write || true
echo "--- rescan after fixes ---"
python -m kubemend scan "$WORK/app.yaml" || true
echo "(KM005 remains: pinning an image needs the real digest from your"
echo " registry, so KubeMend flags it instead of inventing one.)"

echo
echo "=== 4. Audit report (second app, same engine) ==="
python -m kubemend_report examples/vulnerable-app.yaml --format md --out "$WORK/report.md"
head -20 "$WORK/report.md"

echo
echo "=== 5. A clean manifest scans clean ==="
python -m kubemend scan examples/hardened-app.yaml
echo "exit code $? - no findings"
