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
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    StatusClass,
    OwnershipClass,
    OwnerClass,
    SchemaMetadataClass,
    SchemaFieldClass,
)
from datahub.metadata.schema_classes import AuditStampClass
from datahub.metadata.schema_classes import BrowsePathsClass
from datahub.metadata.schema_classes import (
    SchemaFieldDataTypeClass,
    StringTypeClass,
    SchemalessClass,
    OwnershipSourceClass,
    OwnershipSourceTypeClass,
    OwnershipTypeClass,
)
from datahub.metadata.schema_classes import (
    NumberTypeClass,
    DateTypeClass,
    BooleanTypeClass,
    BytesTypeClass,
    ArrayTypeClass,
    MapTypeClass,
    NullTypeClass,
    TimeTypeClass,
    EnumTypeClass,
    RecordTypeClass,
)

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
    """Create a MetadataChangeProposalWrapper for a single note as a dataset (properties aspect)."""
    # dataset name should be safe for urn; replace spaces with underscores
    safe_vault = vault.name.replace(" ", "_")
    safe_note = note.name.replace(" ", "_")
    dataset_name = f"obsidian.{safe_vault}.{safe_note}"
    dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"

    # DatasetProperties - used by DataHub UI for display
    props = DatasetPropertiesClass(
        name=dataset_name,
        description=f"Obsidian note from vault: {vault.name}\nPath: {note.relative_path}",
        customProperties={
            "vault_name": vault.name,
            "vault_path": str(vault.path),
            "note_path": str(note.relative_path),
            "size_bytes": str(note.size),
            "last_modified": note.modified_time.isoformat(),
            # qualifiedName is important for many integrations/search UIs
            "qualifiedName": f"{dataset_name}@{os.getenv('USER', 'local')}"
            ,"owners": os.getenv('DATAHUB_OWNER_URN', f"urn:li:corpuser:{os.getenv('USER', 'local')}")
        },
    )

    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="datasetProperties",
        aspect=props,
    )


def create_status_mcp(dataset_urn: str) -> MetadataChangeProposalWrapper:
    """Create a simple status aspect to mark the dataset as not removed (visible)."""
    status_aspect = StatusClass(removed=False)
    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="status",
        aspect=status_aspect,
    )


def create_ownership_mcp(dataset_urn: str) -> MetadataChangeProposalWrapper:
    """Create a minimal ownership aspect pointing to the current user as DATAOWNER."""
    user = os.getenv("DATAHUB_OWNER_URN", f"urn:li:corpuser:{os.getenv('USER', 'local')}")
    # Use SDK-provided ownership enums/structs so the emitted object matches writer schema
    owner = OwnerClass(
        owner=user,
        type=OwnershipTypeClass.DATAOWNER,
        source=OwnershipSourceClass(type=OwnershipSourceTypeClass.MANUAL),
    )
    # Provide a proper lastModified AuditStamp (time in milliseconds) to satisfy schema
    now_ms = int(time.time() * 1000)
    actor = user
    last_modified = AuditStampClass(time=now_ms, actor=actor)
    # Some DataHub SDK versions expect ownerTypes to be nullable; use None instead of an empty map
    ownership_aspect = OwnershipClass(owners=[owner], ownerTypes=None, lastModified=last_modified)
    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="ownership",
        aspect=ownership_aspect,
    )


def create_schema_mcp(note: ObsidianNote, vault: ObsidianVault, dataset_name: str, dataset_urn: str) -> MetadataChangeProposalWrapper:
    """Create a lightweight schemaMetadata aspect describing available fields."""
    # Provide a small schema with common fields so DataHub can render a schema panel.
    # field dictionaries follow the DataHub JSON shape for SchemaField (fieldPath, nativeDataType, description)
    fields = [
        {
            "fieldPath": "note_name",
            "nativeDataType": "string",
            "description": "Note base name (without extension)",
        },
        {
            "fieldPath": "note_path",
            "nativeDataType": "string",
            "description": "Path of the note relative to the vault root",
        },
        {
            "fieldPath": "size_bytes",
            "nativeDataType": "long",
            "description": "File size in bytes",
        },
        {
            "fieldPath": "last_modified",
            "nativeDataType": "timestamp",
            "description": "Last modification time (ISO 8601)",
        },
    ]

    # Some generated SchemaFieldClass signatures require a 'type' positional argument.
    # Provide `type=None` to satisfy the constructor while keeping nativeDataType populated.
    # Build typed SchemaFieldDataType for each field by mapping nativeDataType text
    def map_native_to_type(native: str):
        if not native:
            return StringTypeClass()
        n = native.lower()
        # boolean
        if any(tok in n for tok in ("bool", "boolean")):
            return BooleanTypeClass()
        # date / timestamp
        if any(tok in n for tok in ("timestamp", "datetime", "date", "iso8601")):
            return DateTypeClass()
        # time
        if "time" == n:
            return TimeTypeClass()
        # integer / number
        if any(tok in n for tok in ("int", "integer", "long", "bigint", "number", "float", "double")):
            return NumberTypeClass()
        # bytes
        if "byte" in n or "blob" in n:
            return BytesTypeClass()
        # array / list
        if any(tok in n for tok in ("array", "list")):
            return ArrayTypeClass()
        # map / json / object
        if any(tok in n for tok in ("map", "json", "object", "struct")):
            return MapTypeClass()
        # null / unknown
        if any(tok in n for tok in ("null", "none", "nullable", "optional")):
            return NullTypeClass()
        # fallback to string
        return StringTypeClass()

    schema_fields = []
    for f in fields:
        dtype = SchemaFieldDataTypeClass(type=map_native_to_type(f.get("nativeDataType")))
        nullable = any(tok in (f.get("nativeDataType") or "").lower() for tok in ("null", "nullable", "optional"))
        sf = SchemaFieldClass(
            fieldPath=f["fieldPath"],
            type=dtype,
            nativeDataType=f["nativeDataType"],
            nullable=nullable,
            description=f.get("description", ""),
        )
        schema_fields.append(sf)

    # SchemaMetadataClass expects: schemaName, platform, version, hash, platformSchema, fields
    schema_aspect = SchemaMetadataClass(
        schemaName=dataset_name,
        platform="urn:li:dataPlatform:obsidian",
        version=0,
        hash="",
        platformSchema=SchemalessClass(),
        fields=schema_fields,
    )

    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="schemaMetadata",
        aspect=schema_aspect,
    )


def ingest_to_datahub(vaults: List[ObsidianVault]) -> None:
    emitter = create_datahub_emitter()
    try:
        for vault in vaults:
            for note in vault.notes:
                # build identifiers
                safe_vault = vault.name.replace(" ", "_")
                safe_note = note.name.replace(" ", "_")
                dataset_name = f"obsidian.{safe_vault}.{safe_note}"
                dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"

                # emit dataset properties (display)
                mcp_props = create_dataset_mcp(note, vault)
                logger.info("Emitting datasetProperties for %s", dataset_urn)
                emitter.emit(mcp_props)

                # emit status (makes it visible in UI)
                mcp_status = create_status_mcp(dataset_urn)
                logger.info("Emitting status for %s", dataset_urn)
                emitter.emit(mcp_status)

                # emit ownership (so dataset shows owners panel)
                mcp_own = create_ownership_mcp(dataset_urn)
                logger.info("Emitting ownership for %s", dataset_urn)
                try:
                    emitter.emit(mcp_own)
                except Exception as e:
                    logger.warning("Emitting ownership failed for %s: %s -- continuing without ownership aspect", dataset_urn, e)

                # emit schema metadata (so dataset shows schema panel). Wrap in try/except
                try:
                    mcp_schema = create_schema_mcp(note, vault, dataset_name, dataset_urn)
                    logger.info("Emitting schemaMetadata for %s", dataset_urn)
                    emitter.emit(mcp_schema)
                except Exception as e:
                    logger.warning("Emitting schemaMetadata failed for %s: %s -- continuing without schema", dataset_urn, e)

                # emit browsePaths so dataset appears in browse UI under obsidian/<vault>
                try:
                    browse_path = f"obsidian/{vault.name}/{note.relative_path}"
                    bp = BrowsePathsClass(paths=[browse_path])
                    mcp_bp = MetadataChangeProposalWrapper(
                        entityType="dataset",
                        entityUrn=dataset_urn,
                        aspectName="browsePaths",
                        aspect=bp,
                    )
                    logger.info("Emitting browsePaths for %s -> %s", dataset_urn, browse_path)
                    emitter.emit(mcp_bp)
                except Exception:
                    # non-fatal
                    logger.debug("browsePaths emission failed for %s", dataset_urn, exc_info=True)

                logger.info("Emit OK: %s", dataset_urn)

        # allow backend a moment to index items
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