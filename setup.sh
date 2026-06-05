#!/bin/bash
# Hermes Config Kit — One-Click Setup
# Clone this repo, run setup.sh, get a fully configured Hermes agent.
# Safe for re-run: backs up existing skills before overwriting.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "  Hermes Config Kit — Setup"
echo "  Publieople's Digital Twin"
echo ""

# ── 1. Prerequisites ──────────────────────────────────────
info "Checking prerequisites..."
if ! command -v hermes &>/dev/null; then
    err "Hermes CLI not found. Install: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
    exit 1
fi
ok "Hermes CLI found"
if ! command -v git &>/dev/null; then
    err "git not found."
    exit 1
fi
ok "git found"

# ── 2. API Keys (interactive) ─────────────────────────────
echo ""
info "API Key configuration"
echo "  Press Enter to skip optional keys."
echo ""
read -rp "  DeepSeek API Key [required]: " KEY
if [ -n "$KEY" ]; then
    hermes config set model.api_key "$KEY" 2>/dev/null || true
    ok "DeepSeek API key set"
else
    warn "No DeepSeek key — agent won't work without it"
fi

read -rp "  MiniMax API Key [TTS+Vision]: " KEY
[ -n "$KEY" ] && ok "MiniMax key received" || warn "Skipped"

read -rp "  Mem0 API Key [memory]: " KEY
[ -n "$KEY" ] && ok "Mem0 key received" || warn "Skipped"

# ── 3. Copy config ────────────────────────────────────────
echo ""
info "Copying config..."
mkdir -p "$HERMES_HOME"
cp "$SCRIPT_DIR/config.yaml" "$HERMES_HOME/config.yaml"
ok "config.yaml"
cp "$SCRIPT_DIR/SOUL.md" "$HERMES_HOME/SOUL.md"
ok "SOUL.md"

# ── 4. Skills ─────────────────────────────────────────────
info "Installing skills..."
if [ -d "$HERMES_HOME/skills" ] && [ "$(ls -A "$HERMES_HOME/skills" 2>/dev/null)" ]; then
    BKDIR="$HERMES_HOME/skills.backup.$(date +%Y%m%d_%H%M%S)"
    mv "$HERMES_HOME/skills" "$BKDIR"
    warn "Existing skills backed up to $BKDIR"
fi
mkdir -p "$HERMES_HOME/skills"
cp -r "$SCRIPT_DIR/skills"/* "$HERMES_HOME/skills/"
COUNT=$(find "$HERMES_HOME/skills" -name "SKILL.md" | wc -l)
ok "$COUNT skills installed"

# ── 5. Scripts ────────────────────────────────────────────
info "Installing scripts..."
mkdir -p "$HERMES_HOME/scripts"
cp "$SCRIPT_DIR/scripts"/* "$HERMES_HOME/scripts/" 2>/dev/null || true
chmod +x "$HERMES_HOME/scripts"/*.sh 2>/dev/null || true
ok "Scripts installed"

# ── 6. npm tools ──────────────────────────────────────────
if [ -f "$SCRIPT_DIR/npm/global-packages.txt" ]; then
    echo ""
    info "Installing npm global tools..."
    while IFS= read -r pkg; do
        [ -z "$pkg" ] && continue
        [[ "$pkg" =~ ^# ]] && continue
        npm install -g "$pkg" 2>/dev/null && ok "$pkg" || warn "$pkg (skipped)"
    done < "$SCRIPT_DIR/npm/global-packages.txt"
fi

# ── 7. Shell hints ────────────────────────────────────────
echo ""
info "Add to your shell rc file:"
echo '  export HERMES_TUI=1'
echo '  export MINIMAX_API_KEY=<your-key>'
echo '  export MINIMAX_CN_API_KEY=<your-key>'
echo '  export DEEPSEEK_API_KEY=<your-key>'
echo ""
echo "  export MINIMAX_CN_API_KEY=<your-key>"
echo "  export DEEPSEEK_API_KEY=<your-key>"
echo ""

# ── 8. Verify ─────────────────────────────────────────────
info "Verifying..."
CFG="✗"; SOUL="✗"; SK="✗"
[ -f "$HERMES_HOME/config.yaml" ] && CFG="✓"
[ -f "$HERMES_HOME/SOUL.md" ]   && SOUL="✓"
[ "$COUNT" -gt 100 ]             && SK="✓"
echo "  config.yaml : $CFG"
echo "  SOUL.md     : $SOUL"
echo "  skills      : $SK ($COUNT skills)"

# ── 9. Done ───────────────────────────────────────────────
echo ""
echo "  Setup complete. Start Hermes:"
echo "    hermes"
echo ""
