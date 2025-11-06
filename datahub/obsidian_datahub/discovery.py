"""
Obsidian vault and note discovery.
"""
from __future__ import annotations

import os
import datetime
from pathlib import Path
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger("obsidian-datahub.discovery")

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