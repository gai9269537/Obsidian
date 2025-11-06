#!/usr/bin/env python3
"""
Print the path to the Markdown file currently open in Obsidian and read its content.
Uses standard Python packages to get window information.
"""

import os
import psutil
import re

def get_obsidian_window_title():
    """Get the title of the frontmost Obsidian window using psutil."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == 'Obsidian':
                # Import AppKit here to avoid global import on non-macOS systems
                from AppKit import NSWorkspace, NSApplicationActivationPolicyRegular
                workspace = NSWorkspace.sharedWorkspace()
                active_apps = workspace.runningApplications()
                for app in active_apps:
                    if app.activationPolicy() == NSApplicationActivationPolicyRegular and 'Obsidian' in app.localizedName():
                        return app.localizedName()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def get_file_paths_under(root=".", *, suffix=""):
    if not os.path.isdir(root):
        raise ValueError(f"Cannot find files under non-existent directory: {root!r}")
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            p = os.path.join(dirpath, f)
            if os.path.isfile(p) and f.lower().endswith(suffix):
                yield p

if __name__ == "__main__":
    # Get Obsidian window title using psutil and AppKit
    window_title = get_obsidian_window_title()

    if not window_title:
        raise RuntimeError("Could not find Obsidian window")

    # Use a more reliable method to find the vault
    vault_root = os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Kha")
    
    if not os.path.exists(vault_root):
        raise ValueError(f"Could not find Obsidian vault at {vault_root}")
    
    # Find the most recently modified markdown file in the vault
    note_path = None
    latest_mtime = 0
    
    for path in get_file_paths_under(vault_root, suffix=".md"):
        mtime = os.path.getmtime(path)
        if mtime > latest_mtime:
            latest_mtime = mtime
            note_path = path

    if not note_path:
        raise RuntimeError("Could not find any markdown files in the vault")

    # Read and print the note content
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Path: {note_path}\nContent:\n{content[:1000]}")  # Print first 1000 chars


