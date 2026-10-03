#!/usr/bin/env python3
"""Same as bench_id.py but forces the pure-torch linear-attention fallback (FLA disabled),
to MEASURE the real fla speedup on this machine instead of trusting the 3.4x figure."""
import json, statistics, sys, time

MODEL_DIR = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 10

# Patch BEFORE transformers imports modeling_qwen3_5 (which binds the name at import time).
import transformers.utils.import_utils as iu
iu.is_flash_linear_attention_available = lambda: False
import transformers.utils.import_utils as _check
print("[ab] fla detection forced to:", _check.is_flash_linear_attention_available(), flush=True)

sys.path.insert(0, MODEL_DIR)
from inference import DecisionEngine  # noqa: E402

REQ = {
    "state": "客户:我的信用卡被扣了两次,要求今天之内退款。",
    "questions": {
        "department": {"type": "choice", "instructions": "Which team?",
                       "criteria": {"billing": "charges, refunds", "technical": "bugs"}},
        "need_human": {"type": "noul", "instructions": "Needs a human agent?"},
    },
}
t0 = time.time()
eng = DecisionEngine(checkpoint=MODEL_DIR, device="cuda", dtype="bfloat16")
print(f"[load] {time.time()-t0:.1f}s (FLA DISABLED)", flush=True)
for _ in range(3):
    eng.predict(REQ)
xs = []
for _ in range(N):
    t = time.perf_counter(); r = eng.predict(REQ); xs.append((time.perf_counter()-t)*1000)
xs.sort()
import torch
print(json.dumps({"mode": "fla_disabled", "n": N,
                  "median_ms": round(statistics.median(xs), 2),
                  "min_ms": round(xs[0], 2), "max_ms": round(xs[-1], 2),
                  "peak_vram_gb": round(torch.cuda.max_memory_allocated()/1e9, 2)}, indent=2))
print("AB_OK")
