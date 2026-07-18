#!/usr/bin/env bash
# AstrBot plugin CI-style preflight — run before pushing a PR.
# Mirrors the GitHub Actions CI workflow (.github/workflows/CI.yml):
#   ruff check . + ruff format --check . + mypy src main.py + pytest -q
#
# astrbot 4.26.5 must be installable from PyPI; locally we use a fresh
# /tmp/.venv-astrbot-preflight (clean per run, no cache pollution).
#
# Usage:
#   bash templates/ci-preflight.sh            # in plugin repo root
#   bash templates/ci-preflight.sh --keep-venv # keep venv for debugging

set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

KEEP_VENV=0
[[ "${1:-}" == "--keep-venv" ]] && KEEP_VENV=1

VENV_DIR="${TMPDIR:-/tmp}/.venv-astrbot-preflight-$$"
trap '[[ $KEEP_VENV -eq 0 ]] && rm -rf "$VENV_DIR"' EXIT

echo "==> Creating venv at $VENV_DIR"
uv venv "$VENV_DIR" --python 3.12 --quiet

PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo "==> Installing runtime + test deps (astrbot from PyPI)"
UV_HTTP_TIMEOUT=120 $PIP install --quiet \
  -r requirements.txt \
  ruff mypy pytest pytest-asyncio types-PyYAML 2>&1 | tail -3

echo "==> ruff check ."
$PY -m ruff check . || { echo "ruff check failed"; exit 1; }

echo "==> ruff format --check ."
$PY -m ruff format --check . || { echo "ruff format --check failed (run \`ruff format .\` locally)"; exit 1; }

echo "==> mypy src main.py"
$PY -m mypy src main.py || { echo "mypy failed"; exit 1; }

echo "==> pytest -q"
$PY -m pytest -q || { echo "pytest failed"; exit 1; }

echo ""
echo "✓ All CI checks passed locally."
[[ $KEEP_VENV -eq 1 ]] && echo "(venv kept at $VENV_DIR)"