#!/usr/bin/env python3
"""Benchmark Laya agent.system_one: correctness + real latency (no official numbers)."""
import json, statistics, sys, time

MODEL_DIR = sys.argv[1]
DEVICE = sys.argv[2] if len(sys.argv) > 2 else "cuda"
SUBFOLDER = sys.argv[3] if len(sys.argv) > 3 else None
N = int(sys.argv[4]) if len(sys.argv) > 4 else 20

import laya  # noqa: E402

STATE = "客户:我的信用卡被扣了两次,要求今天之内退款。"
QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which team?",
        "criteria": {"billing": "charges, refunds", "technical": "bugs"},
    },
    "need_human": {"type": "noul", "instructions": "Needs a human agent?"},
}

t0 = time.time()
kwargs = {"device": DEVICE}
if SUBFOLDER:
    kwargs["subfolder"] = SUBFOLDER
agent = laya.load(MODEL_DIR, **kwargs)
load_s = time.time() - t0
print(f"[load] {load_s:.1f}s device={DEVICE} subfolder={SUBFOLDER} model_id={getattr(agent,'model_id',None)}", flush=True)

for _ in range(3):
    agent.system_one(STATE, QUESTIONS)

times = []
for _ in range(N):
    t = time.perf_counter()
    res = agent.system_one(STATE, QUESTIONS)
    times.append((time.perf_counter() - t) * 1000)

xs = sorted(times)
out = {
    "answers": res.get("answers"),
    "usage": res.get("usage"),
    "model_id": getattr(agent, "model_id", None),
    "e2e_ms": {
        "mean": round(statistics.mean(xs), 2),
        "median": round(statistics.median(xs), 2),
        "min": round(xs[0], 2),
        "max": round(xs[-1], 2),
        "p95": round(xs[min(len(xs) - 1, int(0.95 * len(xs)))], 2),
    },
    "load_s": round(load_s, 1),
}
if DEVICE.startswith("cuda"):
    import torch
    out["peak_vram_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    out["gpu"] = torch.cuda.get_device_name(0)
print(json.dumps(out, ensure_ascii=False, indent=2))
print("BENCH_OK")
