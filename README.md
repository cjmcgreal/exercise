# Obsidian Vault Crawler

Generates a CSV of all notes and a `reference_tree_python.md` from the `parent` field in frontmatter.

## Usage

```bash
./crawl_vault.sh
```

## Output

- `vault_notes.csv` - All notes with frontmatter fields
- `reference_tree_python.md` - Hierarchical tree based on `parent` links
