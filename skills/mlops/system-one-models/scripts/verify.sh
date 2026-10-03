#!/usr/bin/env bash
# One-shot verification: dependency self-check + 20-run latency for whichever tier is installed.
# Usage: verify.sh <work_root> [device]
set -uo pipefail
ROOT="${1:-$HOME/s1}"
DEV="${2:-cuda}"
PY="$ROOT/venv/bin/python"
SELF="$(cd "$(dirname "$0")" && pwd)"

[ -x "$PY" ] || { echo "no venv at $PY"; exit 1; }

"$PY" - <<'EOF'
import torch, transformers
print("torch", torch.__version__, "cuda_avail", torch.cuda.is_available(),
      "cxx11abi", torch._C._GLIBCXX_USE_CXX11_ABI)
print("transformers", transformers.__version__, "(must be 5.14.1)")
for m in ("fla", "causal_conv1d", "laya"):
    try:
        mod = __import__(m); print(m, "OK", getattr(mod, "__version__", ""))
    except Exception as e:
        print(m, "MISSING", repr(e)[:100])
EOF

for d in "$ROOT"/Intern-Decision-*B; do
  [ -d "$d" ] || continue
  echo "=== $d (device=$DEV) ==="
  "$PY" "$SELF/bench_id.py" "$d" "$DEV" bfloat16 20
done

if [ -d "$ROOT/laya" ]; then
  echo "=== laya english (device=$DEV) ==="
  "$PY" "$SELF/bench_laya.py" "$ROOT/laya" "$DEV" "" 20
  echo "=== laya multilingual (device=$DEV) ==="
  "$PY" "$SELF/bench_laya.py" "$ROOT/laya" "$DEV" multilingual 20
fi
echo "VERIFY_DONE"
