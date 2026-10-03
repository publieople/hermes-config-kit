#!/usr/bin/env python3
"""Benchmark Intern-Decision DecisionEngine: correctness + real latency (no official numbers)."""
import json, statistics, sys, time

MODEL_DIR = sys.argv[1]
DEVICE = sys.argv[2] if len(sys.argv) > 2 else "cuda"
DTYPE = sys.argv[3] if len(sys.argv) > 3 else "bfloat16"
N = int(sys.argv[4]) if len(sys.argv) > 4 else 20

sys.path.insert(0, MODEL_DIR)
from inference import DecisionEngine  # noqa: E402

REQ = {
    "state": "客户:我的信用卡被扣了两次,要求今天之内退款。",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Which team?",
            "criteria": {"billing": "charges, refunds", "technical": "bugs"},
        },
        "need_human": {"type": "noul", "instructions": "Needs a human agent?"},
    },
}

t0 = time.time()
eng = DecisionEngine(checkpoint=MODEL_DIR, device=DEVICE, dtype=DTYPE)
load_s = time.time() - t0
print(f"[load] {load_s:.1f}s device={DEVICE} dtype={DTYPE}", flush=True)

# warmup
for _ in range(3):
    eng.predict(REQ)

times, infer_ms = [], []
for _ in range(N):
    t = time.perf_counter()
    res = eng.predict(REQ)
    times.append((time.perf_counter() - t) * 1000)
    infer_ms.append(res["timing"]["inference_ms"])

def stat(xs):
    xs = sorted(xs)
    return {
        "mean": round(statistics.mean(xs), 2),
        "median": round(statistics.median(xs), 2),
        "min": round(xs[0], 2),
        "max": round(xs[-1], 2),
        "p95": round(xs[min(len(xs) - 1, int(0.95 * len(xs)))], 2),
    }

out = {
    "answers": res["answers"],
    "usage": res["usage"],
    "model": res["model"],
    "backend": res["backend"],
    "calibration": res.get("calibration"),
    "e2e_ms": stat(times),
    "engine_inference_ms": stat(infer_ms),
    "load_s": round(load_s, 1),
}
if DEVICE.startswith("cuda"):
    import torch
    out["peak_vram_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    out["gpu"] = torch.cuda.get_device_name(0)
print(json.dumps(out, ensure_ascii=False, indent=2))
print("BENCH_OK")
