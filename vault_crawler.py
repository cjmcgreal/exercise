"""
Obsidian Vault Crawler

Crawls through an Obsidian vault and:
1. Generates a CSV with details of all notes (frontmatter fields)
2. Generates a reference_tree_python.md showing parent-child hierarchy

Usage:
    python vault_crawler.py [vault_path]

    If vault_path is not provided, uses current directory.
"""

import os
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Extract YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Dictionary of frontmatter fields, empty dict if no frontmatter
    """
    frontmatter = {}

    # Check if file starts with frontmatter delimiter
    if not content.startswith('---'):
        return frontmatter

    # Find the closing delimiter
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return frontmatter

    # Extract frontmatter block (skip opening ---)
    fm_content = content[4:end_match.start() + 3]

    # Parse simple YAML key-value pairs
    for line in fm_content.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Remove surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            frontmatter[key] = value

    return frontmatter


def extract_parent_name(parent_field: str) -> Optional[str]:
    """
    Extract the note name from a parent field like "[[note_name]]".

    Args:
        parent_field: The parent field value (e.g., "[[agility]]")

    Returns:
        The note name without brackets, or None if not found
    """
    match = re.search(r'\[\[([^\]]+)\]\]', parent_field)
    if match:
        return match.group(1)
    return None


def crawl_vault(vault_path: str) -> List[Dict[str, Any]]:
    """
    Crawl through all markdown files in the vault and extract metadata.

    Args:
        vault_path: Path to the Obsidian vault root

    Returns:
        List of dictionaries containing note metadata
    """
    notes = []
    vault_path = Path(vault_path)

    for md_file in vault_path.rglob('*.md'):
        # Skip hidden folders (like .obsidian)
        if any(part.startswith('.') for part in md_file.parts):
            continue

        # Read file content
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
            continue

        # Parse frontmatter
        frontmatter = parse_frontmatter(content)

        # Get note name (filename without .md extension)
        note_name = md_file.stem

        # Extract parent name if present
        parent_name = None
        if 'parent' in frontmatter:
            parent_name = extract_parent_name(frontmatter['parent'])

        # Build note record
        note_record = {
            'name': note_name,
            'file_path': str(md_file.relative_to(vault_path)),
            'parent': parent_name,
            'status': frontmatter.get('status', ''),
            'category': frontmatter.get('category', ''),
        }

        # Add any additional frontmatter fields
        for key, value in frontmatter.items():
            if key not in ['parent', 'status', 'category']:
                note_record[key] = value

        notes.append(note_record)

    return notes


def generate_csv(notes: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a CSV file with all note details.

    Args:
        notes: List of note metadata dictionaries
        output_path: Path to write the CSV file
    """
    if not notes:
        print("No notes found to write to CSV")
        return

    # Collect all unique keys across all notes
    all_keys = set()
    for note in notes:
        all_keys.update(note.keys())

    # Define preferred column order, then add remaining columns
    preferred_order = ['name', 'file_path', 'parent', 'status', 'category']
    fieldnames = [k for k in preferred_order if k in all_keys]
    fieldnames += sorted([k for k in all_keys if k not in preferred_order])

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort notes by name for consistent output
        sorted_notes = sorted(notes, key=lambda x: x['name'].lower())
        writer.writerows(sorted_notes)

    print(f"CSV generated: {output_path} ({len(notes)} notes)")


def build_tree(notes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build a parent-to-children mapping from notes.

    Args:
        notes: List of note metadata dictionaries

    Returns:
        Dictionary mapping parent names to lists of child names
    """
    # Create mapping of parent -> children
    children_map: Dict[str, List[str]] = {}
    note_names = {note['name'] for note in notes}

    for note in notes:
        parent = note['parent']
        name = note['name']

        if parent:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(name)

    # Sort children alphabetically for consistent output
    for parent in children_map:
        children_map[parent].sort(key=str.lower)

    return children_map


def find_roots(notes: List[Dict[str, Any]]) -> List[str]:
    """
    Find root notes (notes with no parent or whose parent doesn't exist).

    Args:
        notes: List of note metadata dictionaries

    Returns:
        List of root note names
    """
    note_names = {note['name'] for note in notes}
    roots = []

    for note in notes:
        parent = note['parent']
        # A note is a root if it has no parent, or parent doesn't exist in vault
        if not parent or parent not in note_names:
            roots.append(note['name'])

    return sorted(roots, key=str.lower)


def generate_tree_md(
    name: str,
    children_map: Dict[str, List[str]],
    indent: int = 0,
    visited: Optional[set] = None
) -> str:
    """
    Recursively generate markdown tree for a note and its children.

    Args:
        name: Note name to generate tree for
        children_map: Mapping of parent -> children
        indent: Current indentation level
        visited: Set of already visited notes (to prevent cycles)

    Returns:
        Markdown string representing the tree
    """
    if visited is None:
        visited = set()

    # Prevent infinite loops from circular references
    if name in visited:
        return ""
    visited.add(name)

    # Build the line for this note
    if indent == 0:
        line = f"[[{name}]]\n"
    else:
        # Use tabs for indentation (matching original reference_tree.md style)
        tabs = "\t" * (indent - 1)
        line = f"{tabs}- [[{name}]]\n"

    # Recursively add children
    children = children_map.get(name, [])
    for child in children:
        line += generate_tree_md(child, children_map, indent + 1, visited.copy())

    return line


def generate_reference_tree(notes: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate the reference_tree_python.md file showing parent-child hierarchy.

    Args:
        notes: List of note metadata dictionaries
        output_path: Path to write the markdown file
    """
    children_map = build_tree(notes)
    roots = find_roots(notes)

    # Generate tree starting from each root
    tree_content = ""
    for root in roots:
        tree_content += generate_tree_md(root, children_map)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tree_content)

    print(f"Reference tree generated: {output_path}")


def main(vault_path: str = ".") -> None:
    """
    Main function to crawl vault and generate outputs.

    Args:
        vault_path: Path to the Obsidian vault (defaults to current directory)
    """
    vault_path = Path(vault_path).resolve()
    print(f"Crawling vault: {vault_path}")

    # Crawl the vault
    notes = crawl_vault(vault_path)
    print(f"Found {len(notes)} notes")

    # Generate outputs
    csv_path = vault_path / "vault_notes.csv"
    tree_path = vault_path / "reference_tree_python.md"

    generate_csv(notes, str(csv_path))
    generate_reference_tree(notes, str(tree_path))


if __name__ == "__main__":
    import sys

    # Get vault path from command line argument, or use current directory
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."

    print("=" * 50)
    print("Obsidian Vault Crawler")
    print("=" * 50)

    main(vault_path)

    print("\nDone!")
