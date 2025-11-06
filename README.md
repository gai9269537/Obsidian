# Obsidian DataHub Integration

A Python package that integrates Obsidian vaults with DataHub metadata catalog, enabling metadata discovery and organization of your notes.

## Features

- 🔍 Automatic vault discovery and note scanning
- 📊 Rich metadata extraction from Obsidian notes
- 🏷️ DataHub aspect generation (properties, schema, ownership)
- 🗂️ Domain organization support
- 🔄 Incremental updates
- 🚀 Easy-to-use CLI interface
- 📝 Comprehensive logging and error handling

## Quick Start

1. **Clone and Setup**
```bash
git clone <your-repo>
cd <your-repo>
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**

Create a `.env` file (you can copy from `.env.template`):
```bash
# DataHub Connection
DATAHUB_GMS=http://localhost:8080
DATAHUB_UI=http://localhost:9002
DATAHUB_TOKEN=your_token             # Optional: auth token

# DataHub Entity Configuration
DATAHUB_OWNER_URN=urn:li:corpuser:your_username
DATAHUB_DOMAIN_URN=urn:li:domain:your_domain  # Optional: assign to domain

# Obsidian Configuration
OBSIDIAN_VAULT_PATH=~/path/to/vault  # Optional: specific vault
OBSIDIAN_DATAHUB_LOG_LEVEL=INFO
```

3. **Run Ingestion**

```bash
# List available vaults
./datahub/obsidian_datahub_cli.py --list-only

# Run ingestion with all aspects
./datahub/obsidian_datahub_cli.py

# Dry run to validate
./datahub/obsidian_datahub_cli.py --dry-run

# Specific aspects only
./datahub/obsidian_datahub_cli.py --aspects properties schema domain

# Debug mode
./datahub/obsidian_datahub_cli.py --debug
```

## CLI Options

```
--vault-path PATH    Path to specific Obsidian vault
--list-only         List vaults without ingestion
--dry-run           Validate without ingesting
--aspects ASPECTS   Select specific aspects to emit
                    [properties,status,ownership,schema,browse,domain]
--debug             Enable debug logging
```

## Quick domain check

After running ingestion you can verify a dataset was assigned to your configured domain.

Using the helper script (recommended):

```bash
# show domain details (human-readable)
./scripts/check_domain.py "urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.Kha.Python,PROD)"

# machine-friendly JSON output (good for CI)
./scripts/check_domain.py "urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.Kha.Python,PROD)" http://localhost:8080 --json
```

Or use the combined smoke-test (dry-run) which queries GraphQL for the domain:

```bash
./scripts/smoke_test_ingest_and_check.sh

# To run ingestion then verify, add --run
./scripts/smoke_test_ingest_and_check.sh --run
```

The `check_entity.sh` script now falls back to this GraphQL helper when checking `domains`.

## DataHub Integration

### Metadata Organization

- **URN Format**: `urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.<vault>.<note>,PROD)`
- **Browse Path**: `/obsidian/<vault_name>/<note_path>`
- **Domain**: Optional organization using DataHub domains
- **Owner**: Configurable via `DATAHUB_OWNER_URN`

### Emitted Aspects

1. **Properties**
   - Note metadata (path, size, modified time)
   - Vault information
   - Custom properties

2. **Schema**
   - Note content structure
   - YAML frontmatter fields
   - Links and references

3. **Ownership**
   - Configurable owner assignment
   - Source attribution

4. **Domain** (Optional)
   - Organization by domain
   - Hierarchical grouping

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Detailed project structure
- Development setup
- API documentation
- Testing instructions
- Troubleshooting guide

## Project Structure

```
.
├── datahub/
│   ├── obsidian_datahub/        # Main package
│   │   ├── __init__.py         # Package exports
│   │   ├── discovery.py        # Vault/note discovery
│   │   ├── aspects.py          # DataHub aspect creation
│   │   └── cli.py             # CLI interface
│   ├── obsidian_datahub_cli.py # CLI wrapper script
│   └── README.md              # Package documentation
├── scripts/                    # Helper scripts
└── requirements.txt           # Dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests and add new ones
4. Submit a pull request

## License

[Your chosen license]