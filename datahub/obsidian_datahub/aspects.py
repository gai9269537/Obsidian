"""
DataHub aspect generation and emission.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, Any, Optional

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    StatusClass,
    OwnershipClass,
    OwnerClass,
    SchemaMetadataClass,
    SchemaFieldClass,
    AuditStampClass,
    BrowsePathsClass,
    SchemaFieldDataTypeClass,
    StringTypeClass,
    SchemalessClass,
    OwnershipSourceClass,
    OwnershipSourceTypeClass,
    OwnershipTypeClass,
    NumberTypeClass,
    DateTypeClass,
    BooleanTypeClass,
    BytesTypeClass,
    ArrayTypeClass,
    MapTypeClass,
    NullTypeClass,
    TimeTypeClass,
    DomainPropertiesClass,
)

from .discovery import ObsidianNote, ObsidianVault

logger = logging.getLogger("obsidian-datahub.aspects")


def create_datahub_emitter() -> DatahubRestEmitter:
    """Create a DataHub REST emitter pointed at local quickstart by default."""
    gms = os.getenv("DATAHUB_GMS", "http://localhost:8080")
    logger.info("Using DataHub GMS at %s", gms)
    return DatahubRestEmitter(gms_server=gms, token=os.getenv("DATAHUB_TOKEN", ""))


def ensure_domain_exists(emitter: DatahubRestEmitter) -> None:
    """Create the domain in DataHub if it doesn't exist."""
    from datahub.metadata.schema_classes import (
        DomainPropertiesClass,
        DomainKeyClass,
    )

    domain_urn = get_domain_urn()
    if not domain_urn:
        return

    domain_name = domain_urn.split(":")[-1]  # Get name from urn:li:domain:name
    logger.info("Ensuring domain exists: %s", domain_name)

    # Create the domain key aspect (required)
    key_aspect = DomainKeyClass(id=domain_name)
    key_mcp = MetadataChangeProposalWrapper(
        entityType="domain",
        entityUrn=domain_urn,
        aspectName="domainKey",
        aspect=key_aspect,
    )

    # Create domain properties using the correct class
    domain_props = DomainPropertiesClass(
        name=domain_name,
        description=f"Domain for Obsidian notes and vaults"
    )
    props_mcp = MetadataChangeProposalWrapper(
        entityType="domain",
        entityUrn=domain_urn,
        aspectName="domainProperties",
        aspect=domain_props,
    )

    # Emit both MCPs (key then properties)
    try:
        emitter.emit(key_mcp)
        emitter.emit(props_mcp)
        logger.info("Domain created/updated successfully: %s", domain_name)
    except Exception as e:
        logger.warning("Failed to create domain %s: %s", domain_name, e)


def get_domain_urn() -> Optional[str]:
    """Get the DataHub domain URN from environment variable."""
    domain_urn = os.getenv("DATAHUB_DOMAIN_URN")
    if domain_urn and not domain_urn.startswith("urn:li:domain:"):
        # If only domain name is provided, construct the full URN
        domain_urn = f"urn:li:domain:{domain_urn}"
    return domain_urn


def create_domain_mcp(dataset_urn: str) -> Optional[MetadataChangeProposalWrapper]:
    """Create a domain aspect for a dataset if DATAHUB_DOMAIN_URN is set."""
    from datahub.metadata.schema_classes import DomainsClass
    
    domain_urn = get_domain_urn()
    if not domain_urn:
        return None

    domains_aspect = DomainsClass(
        domains=[domain_urn]
    )

    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="domains",
        aspect=domains_aspect,
    )


def create_dataset_urn(vault: ObsidianVault, note: ObsidianNote) -> str:
    """Create a DataHub dataset URN for a note."""
    safe_vault = vault.name.replace(" ", "_")
    safe_note = note.name.replace(" ", "_")
    dataset_name = f"obsidian.{safe_vault}.{safe_note}"
    return f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"


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


def map_native_to_type(native: str) -> Any:
    """Map a native data type string to a DataHub SchemaFieldDataType."""
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


def create_browse_paths_mcp(dataset_urn: str, vault: ObsidianVault, note: ObsidianNote) -> MetadataChangeProposalWrapper:
    """Create browsePaths aspect for UI navigation."""
    browse_path = f"obsidian/{vault.name}/{note.relative_path}"
    bp = BrowsePathsClass(paths=[browse_path])
    return MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn=dataset_urn,
        aspectName="browsePaths",
        aspect=bp,
    )


def emit_note_metadata(
    emitter: DatahubRestEmitter,
    note: ObsidianNote,
    vault: ObsidianVault,
    aspects: Optional[list[str]] = None,
) -> None:
    """Emit metadata for a single note."""
    if aspects is None:
        aspects = ["properties", "status", "ownership", "schema", "browse", "domain"]
        
    # Ensure domain exists if we're going to use it
    if "domain" in aspects and get_domain_urn():
        ensure_domain_exists(emitter)

    # build identifiers
    safe_vault = vault.name.replace(" ", "_")
    safe_note = note.name.replace(" ", "_")
    dataset_name = f"obsidian.{safe_vault}.{safe_note}"
    dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:obsidian,{dataset_name},PROD)"

    # emit dataset properties (display)
    if "properties" in aspects:
        mcp_props = create_dataset_mcp(note, vault)
        logger.info("Emitting datasetProperties for %s", dataset_urn)
        emitter.emit(mcp_props)

    # emit status (makes it visible in UI)
    if "status" in aspects:
        mcp_status = create_status_mcp(dataset_urn)
        logger.info("Emitting status for %s", dataset_urn)
        emitter.emit(mcp_status)

    # emit ownership (so dataset shows owners panel)
    if "ownership" in aspects:
        mcp_own = create_ownership_mcp(dataset_urn)
        logger.info("Emitting ownership for %s", dataset_urn)
        try:
            emitter.emit(mcp_own)
        except Exception as e:
            logger.warning("Emitting ownership failed for %s: %s -- continuing without ownership aspect", dataset_urn, e)

    # emit schema metadata (so dataset shows schema panel)
    if "schema" in aspects:
        try:
            mcp_schema = create_schema_mcp(note, vault, dataset_name, dataset_urn)
            logger.info("Emitting schemaMetadata for %s", dataset_urn)
            emitter.emit(mcp_schema)
        except Exception as e:
            logger.warning("Emitting schemaMetadata failed for %s: %s -- continuing without schema", dataset_urn, e)

    # emit browsePaths so dataset appears in browse UI
    if "browse" in aspects:
        try:
            mcp_bp = create_browse_paths_mcp(dataset_urn, vault, note)
            logger.info("Emitting browsePaths for %s -> %s", dataset_urn, f"obsidian/{vault.name}/{note.relative_path}")
            emitter.emit(mcp_bp)
        except Exception:
            # non-fatal
            logger.debug("browsePaths emission failed for %s", dataset_urn, exc_info=True)

    # emit domains (assign dataset to a DataHub domain) if configured
    if "domain" in aspects:
        try:
            mcp_domain = create_domain_mcp(dataset_urn)
            if mcp_domain:
                logger.info("Emitting domains for %s", dataset_urn)
                emitter.emit(mcp_domain)
        except Exception as e:
            logger.warning("Emitting domains failed for %s: %s -- continuing without domains", dataset_urn, e)

    logger.info("Emit OK: %s", dataset_urn)