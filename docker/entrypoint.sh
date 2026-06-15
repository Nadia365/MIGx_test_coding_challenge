#!/usr/bin/env bash
# Docker entrypoint: run ETL + analytics (+ optional tests).
set -euo pipefail

ZIP_PATH="sample_data/archive.zip.download/archive.zip"
NUM_TRIALS="${MAX_STUDIES:-500}"

echo "=============================================="
echo " Clinical Trial Pipeline (Docker)"
echo "=============================================="
echo "Trials to load: ${NUM_TRIALS} (set MAX_STUDIES to change)"

if [[ "${RUN_TESTS:-0}" == "1" ]]; then
  echo ""
  echo "Running tests..."
  pytest -q
fi

echo ""
if [[ -f "$ZIP_PATH" ]]; then
  echo "Loading up to ${NUM_TRIALS} trials from zip..."
  python -m src.run_pipeline --max-studies "${NUM_TRIALS}" --report
else
  echo "Zip not mounted — running fixture demo (2 sample studies)..."
  echo "Mount zip: ./sample_data/archive.zip.download -> /app/sample_data/archive.zip.download"
  python -m src.run_pipeline --fixtures --report
fi

echo ""
echo "Done."
