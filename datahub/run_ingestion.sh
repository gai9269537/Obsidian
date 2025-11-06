#!/bin/bash
set -e

# Ensure DataHub is running
if ! docker ps | grep -q 'datahub-frontend'; then
    echo "DataHub doesn't appear to be running. Please start it first."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Set default DataHub endpoints if not set
: ${DATAHUB_GMS:=http://localhost:8080}
: ${DATAHUB_UI:=http://localhost:9002}

# Default to info logging if not specified
: ${OBSIDIAN_DATAHUB_LOG_LEVEL:=INFO}

# Run the ingestion script with all passed arguments
exec ./obsidian_datahub_cli.py "$@"