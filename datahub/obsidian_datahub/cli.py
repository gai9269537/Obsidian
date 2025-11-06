"""
Main CLI entry point for Obsidian-DataHub integration.
"""
from __future__ import annotations

import os
import time
import logging
import argparse
from typing import List, Optional

from .discovery import (
    find_vaults,
    get_vault_notes,
    ObsidianVault,
    format_vault_info,
    format_note_info,
)
from .aspects import create_datahub_emitter, emit_note_metadata, ensure_domain_exists

logger = logging.getLogger("obsidian-datahub")


def discover_vaults(vault_path: Optional[str] = None) -> List[ObsidianVault]:
    """Find Obsidian vaults and their notes."""
    if vault_path:
        os.environ["OBSIDIAN_VAULT_PATH"] = vault_path

    vault_paths = find_vaults()
    if not vault_paths:
        logger.error("No Obsidian vaults found. Set OBSIDIAN_VAULT_PATH to test a specific vault.")
        return []

    all_vaults: List[ObsidianVault] = []
    for vp in vault_paths:
        notes = get_vault_notes(vp)
        vault = ObsidianVault(path=vp, name=vp.name, notes=notes)
        all_vaults.append(vault)

    return all_vaults


def print_vaults(vaults: List[ObsidianVault]) -> None:
    """Print discovered vaults and notes."""
    print(f"Found {len(vaults)} Obsidian vault(s):\n")
    for vault in vaults:
        print(format_vault_info(vault))
        if vault.notes:
            print("    Notes:")
            for n in vault.notes:
                print(format_note_info(n, indent="    "))
                print("    " + "-" * 46)
        else:
            print("    No notes found in this vault.\n")
        print("-" * 50 + "\n")


def ingest_vaults(
    vaults: List[ObsidianVault],
    aspects: Optional[List[str]] = None,
    dry_run: bool = False,
    sleep_ms: int = 100,
) -> None:
    """Ingest vault metadata into DataHub."""
    if not vaults:
        logger.error("No vaults to ingest")
        return

    if dry_run:
        logger.info("Dry run - would emit metadata for:")
        for vault in vaults:
            logger.info("  Vault: %s", vault.name)
            for note in vault.notes:
                logger.info("    Note: %s", note.relative_path)
        return

    emitter = create_datahub_emitter()
    try:
        for vault in vaults:
            for note in vault.notes:
                emit_note_metadata(emitter, note, vault, aspects)
                # small sleep to avoid overwhelming the server
                time.sleep(sleep_ms / 1000.0)

        # allow backend a moment to index items
        time.sleep(1)
    finally:
        emitter.close()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Obsidian metadata ingestion for DataHub")
    parser.add_argument(
        "--vault-path",
        help="Path to a specific Obsidian vault (overrides OBSIDIAN_VAULT_PATH)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="List discovered vaults and notes without ingesting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be ingested without emitting",
    )
    parser.add_argument(
        "--aspects",
        nargs="+",
        choices=["properties", "status", "ownership", "schema", "browse", "domain"],
        help="Only emit specific aspects",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--create-domain",
        action="store_true",
        help="Create the domain specified in DATAHUB_DOMAIN_URN if it doesn't exist",
    )
    args = parser.parse_args()

    # configure logging
    level = "DEBUG" if args.debug else os.getenv("OBSIDIAN_DATAHUB_LOG_LEVEL", "INFO")
    logging.basicConfig(level=level)

    # discover vaults
    vaults = discover_vaults(args.vault_path)

    if args.list_only:
        print_vaults(vaults)
        return

    # create domain if requested
    if args.create_domain:
        emitter = create_datahub_emitter()
        try:
            ensure_domain_exists(emitter)
        finally:
            emitter.close()
        return

    # ingest metadata
    print("\nIngesting metadata to DataHub...")
    ingest_vaults(vaults, aspects=args.aspects, dry_run=args.dry_run)
    print("Ingestion complete!")


if __name__ == "__main__":
    main()