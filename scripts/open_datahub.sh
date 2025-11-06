#!/usr/bin/env bash
# List Obsidian vaults and open DataHub UI
# Usage: ./open_datahub.sh
#   No arguments required - opens DataHub UI and prints vault info

# Exit on any error
set -e

# DataHub endpoints
: "${DATAHUB_UI:=http://localhost:9002}"

# Check if DataHub UI is accessible
echo "Checking DataHub UI at $DATAHUB_UI..."
if ! curl -s -o /dev/null -w "%{http_code}" "$DATAHUB_UI" | grep -q "200"; then
    echo "Error: DataHub UI not accessible at $DATAHUB_UI"
    echo "Please ensure DataHub quickstart is running."
    exit 1
fi

# Open DataHub UI in default browser
echo "Opening DataHub UI..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$DATAHUB_UI"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux with xdg-open
    xdg-open "$DATAHUB_UI"
else
    echo "Please open $DATAHUB_UI in your browser"
fi

# Print ingested vault info
echo -e "\nListing ingested Obsidian vaults..."
VENV_PYTHON="$(dirname "$(dirname "$0")")/.venv/bin/python"
if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$(dirname "$(dirname "$0")")/datahub/obsidian_datahub_ingestion.py" --list-only
else
    echo "Note: Python venv not found. Run setup.sh first to see vault info."
fi