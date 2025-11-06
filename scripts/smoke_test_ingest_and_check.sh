#!/usr/bin/env bash
# Smoke test: run ingestion (dry-run by default) and verify domain assignment via GraphQL helper.
# Usage: ./smoke_test_ingest_and_check.sh [--run] [--dataset <dataset_name>]

set -euo pipefail

: "${DATAHUB_GMS:=http://localhost:8080}"
CLI_SCRIPT="./datahub/obsidian_datahub_cli.py"
CHECK_SCRIPT="$(dirname "$0")/check_domain.py"

RUN=false
DATASET_NAME="obsidian.Kha.Python"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run)
      RUN=true; shift;;
    --dataset)
      DATASET_NAME="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

URN="urn:li:dataset:(urn:li:dataPlatform:obsidian,$DATASET_NAME,PROD)"

echo "Smoke test: dataset=$DATASET_NAME, GMS=$DATAHUB_GMS"

if [ "$RUN" = true ]; then
  echo "Running real ingestion..."
  python3 "$CLI_SCRIPT" --create-domain --debug || { echo "Ingestion failed"; exit 2; }
else
  echo "Dry-run: skipping ingestion. To run, re-run with --run"
fi

echo "Checking dataset domain via GraphQL..."
python3 "$CHECK_SCRIPT" "$URN" "$DATAHUB_GMS" --json || { echo "Domain check failed"; exit 3; }

echo "Smoke test complete."
