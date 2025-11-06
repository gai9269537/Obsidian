# Obsidian DataHub Integration

A Python package for integrating Obsidian vaults with DataHub metadata catalog.

## Installation

```bash
# In repository root
python -m pip install -r requirements.txt
```

## Usage

The package provides a CLI tool for vault discovery and DataHub ingestion:

```bash
# List available vaults
./obsidian_datahub_cli.py --list-only

# Dry run to validate
./obsidian_datahub_cli.py --dry-run

# Full ingestion with debug logging
./obsidian_datahub_cli.py --debug

# Select specific aspects
./obsidian_datahub_cli.py --aspects ownership,schema

# Specify vault path
./obsidian_datahub_cli.py --vault-path ~/Documents/MyVault
```

## Package Structure

The package is organized into several modules:

- `obsidian_datahub/discovery.py`: Vault and note discovery
- `obsidian_datahub/aspects.py`: DataHub aspect creation
- `obsidian_datahub/cli.py`: Command-line interface
- `obsidian_datahub_cli.py`: CLI wrapper script

## Configuration

Environment variables:
- `DATAHUB_GMS`: DataHub GMS endpoint (default: http://localhost:8080)
- `DATAHUB_UI`: DataHub UI endpoint (default: http://localhost:9002)
- `DATAHUB_TOKEN`: Optional auth token for GMS
- `DATAHUB_OWNER_URN`: Optional owner URN override
- `OBSIDIAN_VAULT_PATH`: Optional specific vault path
- `OBSIDIAN_DATAHUB_LOG_LEVEL`: Logging level (default: INFO)
## Features

- Multi-vault discovery and scanning
- DataHub aspect generation:
  - Dataset properties
  - Ownership
  - Schema metadata
  - Browse paths
  - Status
- Selective aspect emission
- Dry-run validation
- Debug logging
- Configurable paths and owners

## Development

See [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed development guide.

### Quick Development Setup

```bash
# Clone repo and install dependencies
git clone <repo>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Development run with debug logging
OBSIDIAN_DATAHUB_LOG_LEVEL=DEBUG ./obsidian_datahub_cli.py --dry-run
```


```

```
I've made several changes to avoid using AppleScript:

1. Removed the AppleScript dependency and replaced it with `psutil` and `AppKit` (which comes with Python on macOS) to get information about running applications.

2. Instead of relying on the window title to find the specific note, the script now looks for the most recently modified markdown file in your Obsidian vault directory. This is actually more reliable since it will work regardless of whether the window title is visible or formatted in a specific way.

3. The code now uses standard Python libraries and macOS-specific Python packages that are properly supported and maintained.

4. Simplified the error handling and made the messages more clear.

The new approach:
- Uses `psutil` to find the Obsidian process
- Uses `AppKit` to verify Obsidian is running (this is a standard macOS framework accessible through Python)
- Finds the most recently modified markdown file in your vault, which is likely the one you're currently editing
- Still maintains the ability to read and display the file content

This solution is more robust because:
1. It doesn't rely on AppleScript which can be fragile and version-dependent
2. It uses standard Python packages that are well-maintained
3. It's more reliable in finding the current file (using modification time instead of window title parsing)

To use this updated script, you just need to make sure you have the required packages installed (which we did using pip). The script will now work more reliably and with better error handling.

Made changes.

gai9269537: great. change this file to list all notes in the current vault

GitHub Copilot: I'll modify the code to list all notes in the Obsidian vault, including their paths and some basic metadata. Here's the updated version:

````python
#!/usr/bin/env python3
"""
List all Markdown notes in the Obsidian vault with their metadata.
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict

class ObsidianNote:
    def __init__(self, path: Path):
        self.path = path
        self._stat = path.stat()
        
    @property
    def name(self) -> str:
        return self.path.stem
    
    @property
    def modified_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._stat.st_mtime)
    
    @property
    def size(self) -> int:
        return self._stat.st_size
    
    @property
    def relative_path(self) -> str:
        return str(self.path.relative_to(self.path.parent.parent))

def get_all_notes(vault_path: str) -> List[ObsidianNote]:
    """Get all markdown notes from the vault."""
    vault_path = os.path.expanduser(vault_path)
    if not os.path.exists(vault_path):
        raise ValueError(f"Could not find Obsidian vault at {vault_path}")
    
    notes = []
    for path in Path(vault_path).rglob("*.md"):
        notes.append(ObsidianNote(path))
    
    return sorted(notes, key=lambda x: x.modified_time, reverse=True)

def format_note_info(note: ObsidianNote) -> str:
    """Format note information for display."""
    return (f"📄 {note.name}\n"
            f"   📂 Path: {note.relative_path}\n"
            f"   🕒 Modified: {note.modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"   📊 Size: {note.size:,} bytes\n")

if __name__ == "__main__":
    # Use the same vault path as before
    VAULT_PATH = "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Kha"
    
    try:
        notes = get_all_notes(VAULT_PATH)
        print(f"Found {len(notes)} notes in the vault:\n")
        
        for note in notes:
            print(format_note_info(note))
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")
````

This updated version:

1. Creates an `ObsidianNote` class to organize note metadata
2. Uses `pathlib.Path` for better file path handling
3. Lists all `.md` files recursively in the vault
4. Shows for each note:
   - File name
   - Relative path
   - Last modified time
   - File size
5. Sorts notes by modification time (most recent first)
6. Includes emoji icons for better visual organization
7. Handles errors gracefully

Run this script and it will show all notes in your vault with their metadata. The output will look something like:

```
Found 42 notes in the vault:

📄 Example Note
   📂 Path: folder/Example Note.md
   🕒 Modified: 2025-11-06 14:30:22
   📊 Size: 1,234 bytes
--------------------------------------------------
```

You can modify the `format_note_info()` function to display different metadata or change the formatting to suit your needs.

gai9269537: update this to list all vaults and notes in each vault

GitHub Copilot: I'll update the code to scan for all Obsidian vaults and list their notes. The updated version will first look for Obsidian vaults in common locations and then list all notes within each vault.

````python
#!/usr/bin/env python3
"""
List all Obsidian vaults and their notes with metadata.
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict, Generator
from dataclasses import dataclass

@dataclass
class ObsidianVault:
    path: Path
    name: str
    notes: List['ObsidianNote']

class ObsidianNote:
    def __init__(self, path: Path, vault: Path):
        self.path = path
        self.vault = vault
        self._stat = path.stat()
        
    @property
    def name(self) -> str:
        return self.path.stem
    
    @property
    def modified_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._stat.st_mtime)
    
    @property
    def size(self) -> int:
        return self._stat.st_size
    
    @property
    def relative_path(self) -> str:
        return str(self.path.relative_to(self.vault))

def find_vaults() -> List[Path]:
    """Find all Obsidian vaults on the system."""
    potential_locations = [
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/",  # iCloud
        "~/Documents/",  # Local documents
        "~/Obsidian/",  # Custom Obsidian folder
    ]
    
    vaults = []
    for location in potential_locations:
        location_path = Path(os.path.expanduser(location))
        if not location_path.exists():
            continue
            
        # Look for .obsidian folder which indicates an Obsidian vault
        for path in location_path.glob("*/.obsidian"):
            vaults.append(path.parent)
            
    return vaults

def get_vault_notes(vault_path: Path) -> List[ObsidianNote]:
    """Get all markdown notes from a vault."""
    notes = []
    for path in vault_path.rglob("*.md"):
        # Skip files in .obsidian folder
        if ".obsidian" not in str(path):
            notes.append(ObsidianNote(path, vault_path))
    
    return sorted(notes, key=lambda x: x.modified_time, reverse=True)

def format_vault_info(vault: ObsidianVault) -> str:
    """Format vault information for display."""
    return (f"📚 Vault: {vault.name}\n"
            f"   📂 Location: {vault.path}\n"
            f"   📝 Notes: {len(vault.notes)}\n")

def format_note_info(note: ObsidianNote, indent: str = "    ") -> str:
    """Format note information for display."""
    return (f"{indent}📄 {note.name}\n"
            f"{indent}   📂 Path: {note.relative_path}\n"
            f"{indent}   🕒 Modified: {note.modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{indent}   📊 Size: {note.size:,} bytes\n")

if __name__ == "__main__":
    try:
        # Find all vaults
        vault_paths = find_vaults()
        if not vault_paths:
            print("No Obsidian vaults found.")
            exit(0)
            
        print(f"Found {len(vault_paths)} Obsidian vault(s):\n")
        
        # Process each vault
        for vault_path in vault_paths:
            notes = get_vault_notes(vault_path)
            vault = ObsidianVault(
                path=vault_path,
                name=vault_path.name,
                notes=notes
            )
            
            # Print vault info
            print(format_vault_info(vault))
            
            # Print notes in vault
            if notes:
                print("    Notes:")
                for note in notes:
                    print(format_note_info(note))
                    print("    " + "-" * 46)
            else:
                print("    No notes found in this vault.\n")
            
            print("-" * 50 + "\n")
            
    except Exception as e:
        print(f"Error: {e}")
````

Key changes made:

1. Added `ObsidianVault` class to represent vault metadata
2. Added `find_vaults()` function to discover Obsidian vaults in common locations
3. Modified `ObsidianNote` to track which vault it belongs to
4. Updated relative path calculation to be relative to the vault root
5. Added nested formatting for better visual hierarchy
6. Added vault summary information

The script will now:

1. Search for Obsidian vaults in common locations (iCloud, Documents, etc.)
2. For each vault found:
   - Show vault name and location
   - Count total notes
   - List all notes with their metadata
3. Skip `.obsidian` configuration files
4. Maintain hierarchical display with proper indentation

The output will look like:

```
Found 2 Obsidian vaults:

📚 Vault: Personal Notes
   📂 Location: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Personal
   📝 Notes: 42
    Notes:
    📄 Example Note
       📂 Path: folder/Example Note.md
       🕒 Modified: 2025-11-06 14:30:22
       📊 Size: 1,234 bytes
    --------------------------------------------------
...
```

gai9269537: great. I want to use datahub data catalog to track all vaults and notes .  create a simple solution for me to try on my local datahub starter kit in docker on macos

GitHub Copilot: I'll help you create a solution that integrates your Obsidian vault scanner with DataHub. This will create a data catalog of your Obsidian vaults and notes as datasets. Here's a step-by-step solution:

1. First, install the DataHub Python SDK:

```bash
pip install acryl-datahub 'acryl-datahub[datahub-rest]'
```

2. Here's the modified code that integrates with DataHub:

````python
#!/usr/bin/env python3
"""
Ingest Obsidian vaults and notes metadata into DataHub
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    DatasetSnapshotClass,
    DatasetProperties,
)
from datahub.metadata.com.linkedin.pegasus2avro.metadata.snapshot import DatasetSnapshot
from datahub.metadata.com.linkedin.pegasus2avro.common import Status

# ... existing ObsidianVault and ObsidianNote classes ...

def create_datahub_emitter() -> DatahubRestEmitter:
    """Create DataHub REST emitter."""
    return DatahubRestEmitter(
        gms_server="http://localhost:8080",  # Default DataHub REST endpoint
        token=os.getenv("DATAHUB_TOKEN", ""),  # Optional: Add your token here
    )

def create_dataset_mcp(note: ObsidianNote, vault: ObsidianVault) -> MetadataChangeProposalWrapper:
    """Create DataHub MCP for an Obsidian note."""
    dataset_name = f"obsidian.{vault.name}.{note.name}"
    dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"
    
    custom_properties = {
        "vault_name": vault.name,
        "vault_path": str(vault.path),
        "note_path": str(note.relative_path),
        "size_bytes": str(note.size),
        "last_modified": note.modified_time.isoformat(),
    }
    
    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="datasetProperties",
        aspect=DatasetPropertiesClass(
            name=dataset_name,
            description=f"Obsidian note from vault: {vault.name}",
            customProperties=custom_properties,
        ),
        changeType="UPSERT",
    )

def ingest_to_datahub(vaults: List[ObsidianVault]) -> None:
    """Ingest Obsidian metadata into DataHub."""
    emitter = create_datahub_emitter()
    
    for vault in vaults:
        for note in vault.notes:
            mcp = create_dataset_mcp(note, vault)
            emitter.emit(mcp)
    
    emitter.close()

if __name__ == "__main__":
    try:
        # Find all vaults
        vault_paths = find_vaults()
        if not vault_paths:
            print("No Obsidian vaults found.")
            exit(0)
            
        print(f"Found {len(vault_paths)} Obsidian vault(s):\n")
        
        # Process each vault
        all_vaults = []
        for vault_path in vault_paths:
            notes = get_vault_notes(vault_path)
            vault = ObsidianVault(
                path=vault_path,
                name=vault_path.name,
                notes=notes
            )
            all_vaults.append(vault)
            
            # Print vault info (existing code)
            print(format_vault_info(vault))
            
        # Ingest to DataHub
        print("\nIngesting metadata to DataHub...")
        ingest_to_datahub(all_vaults)
        print("Ingestion complete!")
            
    except Exception as e:
        print(f"Error: {e}")
````

3. To run this with the DataHub quickstart:

```bash
# Start DataHub using quickstart
curl -L https://datahubproject.io/quickstart.sh | bash

# Wait for all services to start (usually takes a few minutes)
docker ps
```

4. Create a shell script to run the ingestion:

````bash
#!/bin/bash

# Ensure DataHub is running
if ! docker ps | grep -q 'datahub-frontend'; then
    echo "DataHub doesn't appear to be running. Please start it first."
    exit 1
fi

# Run the ingestion script
python3 obsidian_datahub_ingestion.py
````

5. Make the script executable:

```bash
chmod +x run_obsidian_ingestion.sh
```

This solution will:

1. Create a dataset in DataHub for each Obsidian note
2. Include metadata like:
   - Vault name and path
   - Note path and name
   - Last modified time
   - File size
   - Custom properties for Obsidian-specific metadata

To use this:

1. Start DataHub using the quickstart script
2. Wait for all services to be healthy (check with `docker ps`)
3. Run the ingestion script
4. Visit `http://localhost:9002` in your browser to access DataHub
5. Search for "obsidian" to see your notes catalog

The notes will be organized as:
- Platform: `obsidian`
- Dataset name format: `obsidian.{vault_name}.{note_name}`

You can then use DataHub's features to:
- Search across all your notes
- Add tags and descriptions
- Track lineage (if you add links between notes)
- Monitor changes over time
- Add ownership information

To enhance this further, you could:
1. Add support for note content indexing
2. Include note relationships (links between notes)
3. Add glossary terms for better organization
4. Set up regular ingestion using DataHub's scheduler

Let me know if you need help with any of these enhancements!