#!/usr/bin/env bash
# Run Obsidian note ingestion into DataHub
# Usage: ./run_ingestion.sh [vault_path]
#   vault_path: Optional path to a specific vault to ingest

# Exit on any error
set -e

# Set environment variables if provided
if [ ! -z "$1" ]; then
    export OBSIDIAN_VAULT_PATH="$1"
fi

# Optional override for DataHub GMS endpoint (default: http://localhost:8080)
: "${DATAHUB_GMS:=http://localhost:8080}"
export DATAHUB_GMS

# Run ingestion script using project's venv Python
VENV_PYTHON="$(dirname "$(dirname "$0")")/.venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "Error: Python venv not found at $VENV_PYTHON"
    echo "Please run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Run the ingestion
echo "Using DataHub GMS at $DATAHUB_GMS"
"$VENV_PYTHON" "$(dirname "$(dirname "$0")")/datahub/obsidian_datahub_ingestion.py"