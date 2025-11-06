"""
Obsidian metadata ingestion for DataHub.
"""
from .discovery import ObsidianNote, ObsidianVault, find_vaults, get_vault_notes
from .aspects import (
    create_datahub_emitter,
    emit_note_metadata,
    create_dataset_urn,
    create_dataset_mcp,
    create_status_mcp,
    create_ownership_mcp,
    create_schema_mcp,
    create_browse_paths_mcp,
)
from .cli import main

__all__ = [
    "ObsidianNote",
    "ObsidianVault",
    "find_vaults",
    "get_vault_notes",
    "create_datahub_emitter",
    "emit_note_metadata",
    "create_dataset_urn",
    "create_dataset_mcp",
    "create_status_mcp",
    "create_ownership_mcp",
    "create_schema_mcp",
    "create_browse_paths_mcp",
    "main",
]