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