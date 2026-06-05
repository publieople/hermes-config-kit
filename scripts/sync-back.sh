#!/bin/bash
# Hermes Config Kit — Self-Sync Script
# Run weekly to detect changes in ~/.hermes/ and push to the repo.
# Safe for cron: no_agent mode, stdout is the message delivered.

set -euo pipefail

REPO_DIR="$HOME/projects/hermes-config-kit"
HERMES_DIR="$HOME/.hermes"

cd "$REPO_DIR" || { echo "ERROR: Repo $REPO_DIR not found"; exit 1; }

# ── 1. Sync config.yaml (redact API keys) ──────────────────
if [ -f "$HERMES_DIR/config.yaml" ]; then
    # Copy and redact
    sed -E \
        -e "s/(api_key:\s*['\"])[^'\"]*(['\"])/\1YOUR_API_KEY\2/g" \
        -e "s/(api_key:\s*)[^[:space:]].*/\1YOUR_API_KEY/g" \
        -e "s/(Authorization: Bearer\s+)\S+/\1YOUR_BEARER_TOKEN/g" \
        -e "s/([0-9]{1,3}\.){3}[0-9]{1,3}/YOUR_IP_REPLACED/g" \
        -e "s/oc_[a-f0-9]{28}/YOUR_FEISHU_CHANNEL/g" \
        "$HERMES_DIR/config.yaml" > config.yaml.tmp
    mv config.yaml.tmp config.yaml
fi

# ── 2. Sync skills/ ────────────────────────────────────────
if [ -d "$HERMES_DIR/skills" ]; then
    # Remove old skills, copy new (preserve repo's .git)
    find skills/ -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
    cp -r "$HERMES_DIR/skills"/* skills/ 2>/dev/null || true
    # Clean metadata
    rm -rf skills/.hub skills/.bundled_manifest skills/.usage.json skills/.curator_state 2>/dev/null || true
fi

# ── 3. Sync SOUL.md ────────────────────────────────────────
if [ -f "$HERMES_DIR/SOUL.md" ]; then
    cp "$HERMES_DIR/SOUL.md" SOUL.md
fi

# ── 4. Sync scripts/ ───────────────────────────────────────
if [ -d "$HERMES_DIR/scripts" ]; then
    cp "$HERMES_DIR/scripts"/* scripts/ 2>/dev/null || true
fi

# ── 5. Check for changes ───────────────────────────────────
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    exit 0  # No changes, silent exit
fi

# ── 6. Commit and push ─────────────────────────────────────
git add -A
git commit -m "sync: $(date -Iseconds)" || exit 0
git push 2>&1 || echo "WARNING: git push failed"

echo "Synced hermes-config-kit: $(date -I)"
