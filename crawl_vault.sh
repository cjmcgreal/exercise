#!/bin/bash
# Crawl Obsidian vault and generate CSV + reference tree
# Usage: ./crawl_vault.sh [vault_path]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_PATH="${1:-$SCRIPT_DIR}"

python "$SCRIPT_DIR/vault_crawler.py" "$VAULT_PATH"
