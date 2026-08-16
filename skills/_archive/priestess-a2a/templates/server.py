#!/usr/bin/env python3
"""女祭司 A2A Server — systemd 部署用

Usage:
    PYTHONPATH=~/.hermes/hermes-agent python3 server.py

EnvironmentFile (~/.hermes/.env):
    DEEPSEEK_API_KEY=sk-...
"""

import os, sys

HERMES_AGENT_PATH = os.environ.get("HERMES_AGENT_PATH", os.path.expanduser("~/.hermes/hermes-agent"))
if HERMES_AGENT_PATH not in sys.path:
    sys.path.insert(0, HERMES_AGENT_PATH)

MODEL = os.environ.get("HERMES_MODEL", "deepseek/deepseek-v4-flash")
ENABLED_TOOLSETS = ["terminal", "file", "web", "search", "skills", "memory"]
HOST = os.environ.get("A2A_HOST", "0.0.0.0")
PORT = int(os.environ.get("A2A_PORT", "9010"))

from a2a_adapter import HermesAdapter, serve_agent

adapter = HermesAdapter(
    model=MODEL,
    enabled_toolsets=ENABLED_TOOLSETS,
    name="女祭司",
    description="实验室守护神 — 4xA10 GPU, ComfyUI, OpenList管理员。通过A2A协议接受任务委托。",
    skills=[
        {"id":"comfyui","name":"ComfyUI 图像生成","description":"使用ComfyUI生成图像、视频","tags":["image","video","comfyui"]},
        {"id":"system-admin","name":"系统管理","description":"管理Docker、GPU监控、服务部署","tags":["docker","gpu","devops"]},
    ],
)

if __name__ == "__main__":
    print(f"🔮 女祭司 A2A Server {HOST}:{PORT}")
    serve_agent(adapter, host=HOST, port=PORT)
