#!/usr/bin/env bash
# Version backup for publieople-perspective skill
# Usage: bash backup.sh [comment]
set -e

SKILL_DIR="$HOME/.hermes/skills/publieople-perspective"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMMENT="${1:-no-comment}"
BACKUP_DIR="$SKILL_DIR/.versions/${TIMESTAMP}_${COMMENT}"

mkdir -p "$BACKUP_DIR"

# Backup all tracked files
cp "$SKILL_DIR/SKILL.md" "$BACKUP_DIR/SKILL.md"
cp "$SKILL_DIR/work.md" "$BACKUP_DIR/work.md" 2>/dev/null || true
cp "$SKILL_DIR/persona.md" "$BACKUP_DIR/persona.md" 2>/dev/null || true
cp "$SKILL_DIR/meta.json" "$BACKUP_DIR/meta.json" 2>/dev/null || true
cp -r "$SKILL_DIR/references" "$BACKUP_DIR/" 2>/dev/null || true

# Keep only last 20 versions
ls -dt "$SKILL_DIR"/.versions/*/ 2>/dev/null | tail -n +21 | xargs rm -rf 2>/dev/null || true

echo "Backup: $BACKUP_DIR"
echo "Files: $(find "$BACKUP_DIR" -type f | wc -l)"
