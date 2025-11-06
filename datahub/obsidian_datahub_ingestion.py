#!/usr/bin/env python3
"""
Ingest Obsidian vaults and notes metadata into DataHub.

Usage:
    python3 obsidian_datahub_ingestion.py
"""
from __future__ import annotations

import os
import datetime
import logging
import time
from pathlib import Path
from typing import List
from dataclasses import dataclass

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import DatasetPropertiesClass

# configure logging so we can see what's happening
logging.basicConfig(level=os.getenv("OBSIDIAN_DATAHUB_LOG_LEVEL", "INFO"))
logger = logging.getLogger("obsidian-datahub")

# --- Obsidian model and scanning utilities ---------------------------------

@dataclass
class ObsidianNote:
    path: Path
    vault: Path

    def __post_init__(self):
        self._stat = self.path.stat()

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


@dataclass
class ObsidianVault:
    path: Path
    name: str
    notes: List[ObsidianNote]


def find_vaults() -> List[Path]:
    """Discover Obsidian vault folders by looking for a `.obsidian` subfolder
    under common locations."""
    potential_locations = [
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents",  # iCloud-synced vaults
        "~/Documents",  # local documents
        "~/Obsidian",  # common custom location
    ]

    vaults: List[Path] = []
    for loc in potential_locations:
        base = Path(os.path.expanduser(loc))
        if not base.exists():
            continue
        for candidate in base.iterdir():
            # ensure candidate is a directory and contains a .obsidian folder
            if candidate.is_dir() and (candidate / ".obsidian").is_dir():
                vaults.append(candidate.resolve())

    # Also allow a VAULT_PATH env var to point at a single vault for testing
    env_vault = os.getenv("OBSIDIAN_VAULT_PATH")
    if env_vault:
        p = Path(os.path.expanduser(env_vault)).resolve()
        if p.exists() and (p / ".obsidian").is_dir() and p not in vaults:
            vaults.append(p)

    return vaults


def get_vault_notes(vault_path: Path) -> List[ObsidianNote]:
    """Recursively list .md notes in the vault, excluding the .obsidian config folder."""
    notes: List[ObsidianNote] = []
    for p in vault_path.rglob("*.md"):
        # skip files that are inside a .obsidian folder
        if ".obsidian" in p.parts:
            continue
        try:
            notes.append(ObsidianNote(path=p.resolve(), vault=vault_path.resolve()))
        except FileNotFoundError:
            # file may have been removed between discovery and stat; skip
            continue
    # sort most recently modified first
    notes.sort(key=lambda n: n.modified_time, reverse=True)
    return notes


def format_vault_info(vault: ObsidianVault) -> str:
    return f"📚 Vault: {vault.name}\n   📂 Location: {vault.path}\n   📝 Notes: {len(vault.notes)}\n"


def format_note_info(note: ObsidianNote, indent: str = "    ") -> str:
    return (
        f"{indent}📄 {note.name}\n"
        f"{indent}   📂 Path: {note.relative_path}\n"
        f"{indent}   🕒 Modified: {note.modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{indent}   📊 Size: {note.size:,} bytes\n"
    )


# --- DataHub ingestion ------------------------------------------------------

def create_datahub_emitter() -> DatahubRestEmitter:
    """Create a DataHub REST emitter pointed at local quickstart by default."""
    gms = os.getenv("DATAHUB_GMS", "http://localhost:8080")
    logger.info("Using DataHub GMS at %s", gms)
    return DatahubRestEmitter(gms_server=gms, token=os.getenv("DATAHUB_TOKEN", ""))


def create_dataset_mcp(note: ObsidianNote, vault: ObsidianVault) -> MetadataChangeProposalWrapper:
    """Create a MetadataChangeProposalWrapper for a single note as a dataset."""
    # dataset name should be safe for urn; replace spaces with underscores
    safe_vault = vault.name.replace(" ", "_")
    safe_note = note.name.replace(" ", "_")
    dataset_name = f"obsidian.{safe_vault}.{safe_note}"
    dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"

    custom_properties = {
        "vault_name": vault.name,
        "vault_path": str(vault.path),
        "note_path": str(note.relative_path),
        "size_bytes": str(note.size),
        "last_modified": note.modified_time.isoformat(),
    }

    aspect = DatasetPropertiesClass(
        name=dataset_name,
        description=f"Obsidian note from vault: {vault.name}",
        customProperties=custom_properties,
    )

    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="datasetProperties",
        aspect=aspect,
    )


def ingest_to_datahub(vaults: List[ObsidianVault]) -> None:
    emitter = create_datahub_emitter()
    try:
        for vault in vaults:
            for note in vault.notes:
                mcp = create_dataset_mcp(note, vault)
                logger.info("Emitting MCP for %s", mcp.entityUrn)
                try:
                    emitter.emit(mcp)
                    logger.info("Emit OK: %s", mcp.entityUrn)
                except Exception as e:
                    logger.error("Emit failed for %s: %s", mcp.entityUrn, e)
        # allow the backend a moment to index items
        time.sleep(1)
    finally:
        emitter.close()


# --- CLI --------------------------------------------------------------------

if __name__ == "__main__":
    try:
        vault_paths = find_vaults()
        if not vault_paths:
            print("No Obsidian vaults found. Set OBSIDIAN_VAULT_PATH to test a single vault.")
            raise SystemExit(0)

        all_vaults: List[ObsidianVault] = []
        print(f"Found {len(vault_paths)} Obsidian vault(s):\n")
        for vp in vault_paths:
            notes = get_vault_notes(vp)
            vault = ObsidianVault(path=vp, name=vp.name, notes=notes)
            all_vaults.append(vault)
            print(format_vault_info(vault))
            if notes:
                print("    Notes:")
                for n in notes:
                    print(format_note_info(n, indent="    "))
                    print("    " + "-" * 46)
            else:
                print("    No notes found in this vault.\n")
            print("-" * 50 + "\n")

        print("\nIngesting metadata to DataHub...")
        ingest_to_datahub(all_vaults)
        print("Ingestion complete!")

    except Exception as e:
        logger.exception("Unhandled error in ingestion: %s", e)
        print(f"Error: {e}")