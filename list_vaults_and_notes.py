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