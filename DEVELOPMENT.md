# Obsidian-DataHub Integration Guide

This guide documents how to integrate Obsidian vaults with DataHub for metadata catalog and discovery. It covers setup, development, troubleshooting, and common patterns.

## Quick Start

```bash
# Clone and set up environment
git clone <your-repo>
cd <your-repo>
./scripts/setup.sh

# Run ingestion
./scripts/run_ingestion.sh

# Open DataHub UI
./scripts/open_datahub.sh
```

## Prerequisites

- Python 3.x
- DataHub running locally (quickstart or custom deployment)
- One or more Obsidian vaults

## Environment Variables

```bash
# DataHub endpoints
export DATAHUB_GMS=http://localhost:8080  # DataHub GMS endpoint
export DATAHUB_UI=http://localhost:9002   # DataHub UI endpoint

# Obsidian configuration
export OBSIDIAN_VAULT_PATH=~/path/to/vault  # Optional: specific vault to scan
export DATAHUB_TOKEN=your_token             # Optional: auth token for GMS
export DATAHUB_OWNER_URN=urn:li:corpuser:your_username  # Optional: override owner URN
```

## Project Structure

```
.
├── datahub/
│   └── obsidian_datahub_ingestion.py  # Main ingestion script
├── scripts/
│   ├── run_ingestion.sh      # Run ingestion script
│   ├── check_entity.sh       # Check DataHub entity
│   ├── open_datahub.sh       # Open UI and list vaults
│   └── setup.sh             # Set up Python environment
└── requirements.txt         # Python dependencies
```

## DataHub Integration Details

### Dataset URN Format

DataHub dataset URNs are constructed as:
```
urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.<vault>.<note>,PROD)
```

Example:
```
urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.Kha.Python,PROD)
```

### Metadata Aspects

The integration emits these DataHub aspects:

1. **datasetProperties**
   ```python
   DatasetPropertiesClass(
       name="obsidian.vault.note",
       description="Obsidian note from vault: vault_name\nPath: note_path",
       customProperties={
           "vault_name": str,
           "vault_path": str,
           "note_path": str,
           "size_bytes": str,
           "last_modified": ISO8601,
           "qualifiedName": str,
           "owners": str
       }
   )
   ```

2. **status**
   ```python
   StatusClass(removed=False)
   ```

3. **ownership**
   ```python
   OwnershipClass(
       owners=[
           OwnerClass(
               owner="urn:li:corpuser:username",
               type=OwnershipTypeClass.DATAOWNER,
               source=OwnershipSourceClass(
                   type=OwnershipSourceTypeClass.MANUAL
               )
           )
       ],
       lastModified=AuditStampClass(
           time=int(time.time() * 1000),
           actor="urn:li:corpuser:username"
       )
   )
   ```

4. **schemaMetadata**
   ```python
   SchemaMetadataClass(
       schemaName=dataset_name,
       platform="urn:li:dataPlatform:obsidian",
       version=0,
       hash="",
       platformSchema=SchemalessClass(),
       fields=[
           SchemaFieldClass(
               fieldPath=str,
               type=SchemaFieldDataTypeClass(
                   type=StringTypeClass()  # or other types
               ),
               nativeDataType=str,
               description=str,
               nullable=bool
           )
       ]
   )
   ```

5. **browsePaths**
   ```python
   BrowsePathsClass(
       paths=[f"obsidian/{vault_name}/{note_path}"]
   )
   ```

### Schema Field Types

The integration maps native data types to DataHub types:

| Native Type Pattern | DataHub Type Class |
|-------------------|-------------------|
| bool, boolean | BooleanTypeClass |
| timestamp, datetime, date | DateTypeClass |
| time | TimeTypeClass |
| int, integer, long, float | NumberTypeClass |
| byte, blob | BytesTypeClass |
| array, list | ArrayTypeClass |
| map, json, object | MapTypeClass |
| null, nullable, optional | NullTypeClass |
| (other) | StringTypeClass |

## Development Tips

### Debugging DataHub Integration

1. Check entity in DataHub UI:
   ```bash
   # Open UI and find entity
   ./scripts/open_datahub.sh
   
   # Or check specific entity
   ./scripts/check_entity.sh obsidian.Kha.Python
   ```

2. Inspect emitted aspects:
   ```bash
   # Get raw JSON from GMS
   URN="urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.Kha.Python,PROD)"
   curl -s -H "Accept: application/json" \
     "http://localhost:8080/entities?urn=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$URN'))")"
   ```

3. Common SDK patterns:
   ```python
   # Always wrap DataHub types properly
   from datahub.metadata.schema_classes import (
       SchemaFieldDataTypeClass,
       StringTypeClass
   )
   
   # Create a typed field
   field_type = SchemaFieldDataTypeClass(
       type=StringTypeClass()
   )
   ```

### Adding New Features

1. **New Metadata Fields**
   - Add to `create_dataset_mcp()` customProperties
   - Consider creating new aspects for structured data

2. **Schema Improvements**
   - Extend `map_native_to_type()` for new types
   - Add field metadata (tags, glossary terms)
   - Parse note content for schema fields

3. **Ownership/Permissions**
   - Use environment variables for configuration
   - Support multiple owner types
   - Add source/attribution metadata

## Troubleshooting

### Common Issues

1. **Missing Aspects in UI**
   - Check GMS logs for emission errors
   - Verify aspect construction matches SDK
   - Use try/except to catch specific failures

2. **Schema Type Errors**
   - Ensure proper type wrapping (SchemaFieldDataTypeClass)
   - Check nativeDataType mapping
   - Verify nullable flag when needed

3. **Ownership Issues**
   - Confirm OwnershipTypeClass enum values
   - Include proper AuditStamp with time
   - Check owner URN format

### Debugging Commands

```bash
# Check DataHub service status
curl -s -o /dev/null -w "%{http_code}" http://localhost:9002

# List installed packages
./scripts/setup.sh && source .venv/bin/activate && pip list

# Run with debug logging
OBSIDIAN_DATAHUB_LOG_LEVEL=DEBUG ./scripts/run_ingestion.sh
```

## Best Practices

1. **Error Handling**
   - Wrap aspect emissions in try/except
   - Log warnings for non-fatal errors
   - Continue ingestion on partial failures

2. **Configuration**
   - Use environment variables for endpoints
   - Support vault path overrides
   - Make owner mapping configurable

3. **Testing**
   - Add dry-run mode for validation
   - Unit test aspect construction
   - Integration test with sample vault

## References

- [DataHub Documentation](https://datahubproject.io/docs/)
- [DataHub Python SDK](https://datahubproject.io/docs/sdk/python/overview/)
- [Metadata Ingestion Framework](https://datahubproject.io/docs/metadata-ingestion/)