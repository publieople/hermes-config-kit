#!/usr/bin/env bash
# System One stack bootstrap (Laya + 书生·明决 Intern-Decision).
# Usage: bootstrap.sh <work_root> [tier] [cuda_tag]
#   tier: 2b | 0.8b | 4b | none   (none = Laya only, the CPU-only choice)
#   cuda_tag: cu128 (default) | cu130 | cpu
# Probes hardware itself when tier is omitted. Never touches the system Python.
set -uo pipefail

ROOT="${1:-$HOME/s1}"
TIER="${2:-}"
CUDA="${3:-}"
VENV="$ROOT/venv"
PY="$VENV/bin/python"
LOGD="$ROOT/logs"
mkdir -p "$ROOT" "$LOGD"
LOG="$LOGD/bootstrap.log"
SELF="$(cd "$(dirname "$0")" && pwd)"
say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

# ---------- 0. hardware probe ----------
if [ -z "$CUDA" ]; then
  if /usr/lib/wsl/lib/nvidia-smi >/dev/null 2>&1 || nvidia-smi >/dev/null 2>&1; then CUDA=cu128; else CUDA=cpu; fi
fi
if [ -z "$TIER" ]; then
  if [ "$CUDA" = cpu ]; then TIER=none
  else
    TOT=$(/usr/lib/wsl/lib/nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null || nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
    if   [ "$TOT" -ge 10240 ]; then TIER=4b
    elif [ "$TOT" -ge 6144 ];  then TIER=2b
    else TIER=0.8b; fi
  fi
fi
say "ROOT=$ROOT TIER=$TIER CUDA=$CUDA"

# ---------- 1. venv (uv-managed python, system python untouched) ----------
[ -x "$PY" ] || uv venv "$VENV" --python 3.12.12 >>"$LOG" 2>&1

# ---------- 2. torch ----------
if [ "$CUDA" = cpu ]; then
  uv pip install --python "$PY" torch==2.9.1 torchvision==0.24.1 >>"$LOG" 2>&1
else
  uv pip install --python "$PY" torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/$CUDA >>"$LOG" 2>&1
fi
say "torch rc=$?"

# ---------- 3. core deps ----------
uv pip install --python "$PY" transformers==5.14.1 Pillow einops packaging numpy safetensors huggingface_hub laya >>"$LOG" 2>&1
say "core+laya rc=$?"

# ---------- 4. GPU-only accelerators ----------
if [ "$CUDA" != cpu ]; then
  # flash-linear-attention MUST come from git: the PyPI wheel is a broken package
  # (no __init__ / missing modules) -> ModuleNotFoundError or a silent slow fallback.
  uv pip install --python "$PY" --no-deps "flash-linear-attention @ git+https://github.com/fla-org/flash-linear-attention@v0.4.2" >>"$LOG" 2>&1
  say "fla rc=$?"
  # causal-conv1d: PyPI ships sdist only and building needs nvcc (absent on a driver-only
  # WSL2 host). Use the prebuilt GitHub-release wheel matching torch/cuda/ABI/py exactly.
  "$PY" "$SELF/pick_causal_conv1d.py" >>"$LOG" 2>&1
  say "causal-conv1d rc=$?"
fi

# ---------- 5. models (local_dir real dirs; NEVER HF_ENDPOINT mirror here) ----------
dl() { # dl <repo> <dest>
  env -u HF_ENDPOINT HF_HUB_DISABLE_XET=1 uv run --no-project --python 3.12.12 \
    --with huggingface_hub python "$SELF/dl_model.py" "$1" "$2" >>"$LOG" 2>&1
  say "download $1 rc=$?"
}
case "$TIER" in
  2b)   dl internlm/Intern-Decision-2B   "$ROOT/Intern-Decision-2B" ;;
  0.8b) dl internlm/Intern-Decision-0.8B "$ROOT/Intern-Decision-0.8B" ;;
  4b)   dl internlm/Intern-Decision-4B   "$ROOT/Intern-Decision-4B" ;;
esac
dl convaiinnovations/laya "$ROOT/laya"

say "DONE TIER=$TIER CUDA=$CUDA"
