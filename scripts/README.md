# Helper Scripts for Obsidian-DataHub Integration

This directory contains helper scripts for managing Obsidian note ingestion into DataHub.

## Setup

First, run the setup script to create a Python virtual environment and install dependencies:

```bash
# Make scripts executable and set up Python environment
./scripts/setup.sh
```

## Available Scripts

### 1. Run Ingestion

Ingest Obsidian notes into DataHub:

```bash
# Ingest all discovered vaults
./scripts/run_ingestion.sh

# Ingest a specific vault
./scripts/run_ingestion.sh ~/path/to/vault
```

Environment variables:
- `OBSIDIAN_VAULT_PATH`: Override to ingest a specific vault
- `DATAHUB_GMS`: DataHub GMS endpoint (default: http://localhost:8080)
- `DATAHUB_TOKEN`: Optional auth token for DataHub GMS

### 2. Check Entity

Check a specific dataset entity in DataHub:

```bash
# View entity details for a note
./scripts/check_entity.sh obsidian.Kha.Python

# The script will:
# 1. Print the DataHub UI URL
# 2. Print the GMS API URL
# 3. Fetch and display the entity JSON
```

### 3. Open DataHub

Open the DataHub UI and list ingested vaults:

```bash
./scripts/open_datahub.sh
```

This will:
1. Check if DataHub UI is accessible
2. Open http://localhost:9002 in your default browser
3. List discovered Obsidian vaults and notes

## Environment Variables

- `DATAHUB_GMS`: DataHub GMS endpoint (default: http://localhost:8080)
- `DATAHUB_UI`: DataHub UI endpoint (default: http://localhost:9002)
- `OBSIDIAN_VAULT_PATH`: Path to a specific Obsidian vault to ingest
- `DATAHUB_TOKEN`: Optional authentication token for DataHub GMS

## Example Workflow

1. Start DataHub quickstart (if not already running)
2. Run setup: `./scripts/setup.sh`
3. Ingest notes: `./scripts/run_ingestion.sh`
4. Open UI: `./scripts/open_datahub.sh`
5. Check entity: `./scripts/check_entity.sh obsidian.Kha.Python`

## Adding New Scripts

When adding new scripts:
1. Create the script in this directory
2. Make it executable: `chmod +x scripts/your_script.sh`
3. Add usage instructions to this README
4. Update `setup.sh` if needed