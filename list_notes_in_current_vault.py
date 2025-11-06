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


