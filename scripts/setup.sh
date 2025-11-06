#!/usr/bin/env bash
# Set up Python virtual environment and install dependencies
# Usage: ./setup.sh
#   No arguments required - creates venv and installs packages

# Exit on any error
set -e

# Create Python virtual environment if it doesn't exist
if [ ! -d "$(dirname "$(dirname "$0")")/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$(dirname "$(dirname "$0")")/.venv"
fi

# Activate venv and install dependencies
echo "Installing Python dependencies..."
source "$(dirname "$(dirname "$0")")/.venv/bin/activate"
pip install -r "$(dirname "$(dirname "$0")")"/requirements.txt

# Make scripts executable
chmod +x "$(dirname "$0")"/*.sh

echo "Setup complete! You can now use:"
echo "  ./scripts/run_ingestion.sh      - Ingest Obsidian notes to DataHub"
echo "  ./scripts/check_entity.sh       - Check a DataHub dataset entity"
echo "  ./scripts/open_datahub.sh       - Open DataHub UI and list vaults"