#!/bin/bash

# Ensure DataHub is running
if ! docker ps | grep -q 'datahub-frontend'; then
    echo "DataHub doesn't appear to be running. Please start it first."
    exit 1
fi

# Run the ingestion script
python3 obsidian_datahub_ingestion.py