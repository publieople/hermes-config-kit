# 女祭司全栈灾难恢复

当 hermes-agent 源码、skills、a2a-server.py、systemd 服务文件、.env 全部丢失时（如 `/home` bind mount 迁移误删），执行以下完整重建流程。

## 前提

- A2A 隧道仍通（女祭司在内存中运行，或 SSH 仍可访问）
- 损失范围：`/data/home/po/.hermes/hermes-agent/`、`/data/home/po/.hermes/skills/`、`/data/home/po/.local/bin/a2a-server.py`、systemd service 文件、`.ssh/authorized_keys` 等

## 恢复步骤（按顺序）

### 1. 恢复 SSH 访问（如果 SSH 断了）

如果 A2A 通但 SSH 断，先通过 A2A 恢复 SSH（见 `emergency-ssh-recovery.md`）。

### 2. 安装 hermes-agent 源码

```bash
cd /data/home/po/.hermes
git clone https://github.com/nousresearch/hermes-agent.git
pip3 install --break-system-packages -e /data/home/po/.hermes/hermes-agent
pip3 install --break-system-packages a2a-adapter openai
```

### 3. 恢复 Skills（从 config-kit）

```bash
git clone https://github.com/publieople/hermes-config-kit /tmp/hermes-config-kit
cp -r /tmp/hermes-config-kit/skills/* /data/home/po/.hermes/skills/
cp /tmp/hermes-config-kit/SOUL.md /data/home/po/.hermes/SOUL.md
cp /tmp/hermes-config-kit/config.yaml /data/home/po/.hermes/config.yaml
cp /tmp/hermes-config-kit/scripts/* /data/home/po/.hermes/scripts/
# 修改 SOUL.md 中的名字：魔术师 → 女祭司
```

### 4. 重建 a2a-server.py

从 `templates/server.py` 复制内容到 `/data/home/po/.local/bin/a2a-server.py`：

```python
#!/usr/bin/env python3
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
    skills=[...],
)

if __name__ == "__main__":
    serve_agent(adapter, host=HOST, port=PORT)
```

### 5. 创建 systemd 服务文件

`/data/home/po/.config/systemd/user/a2a-priestess.service`：

```ini
[Unit]
Description=女祭司 A2A Server (Hermes Agent)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/po/.local/bin/a2a-server.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/po/.hermes/hermes-agent
Environment=HOME=/home/po
Environment=HERMES_HOME=/home/po/.hermes
EnvironmentFile=/home/po/.hermes/.env

[Install]
WantedBy=default.target
```

### 6. 创建 .env 文件

从 WSL 的 `~/.hermes/.env` 中提取 `DEEPSEEK_API_KEY`，通过 base64 编码传输：

```bash
# WSL 端
bash -c 'set -a; source ~/.hermes/.env; echo -n "$DEEPSEEK_API_KEY" | base64' \
  | ssh po@server 'base64 -d > /tmp/ds_key'

# 服务器端
cat > /data/home/po/.hermes/.env << EOF
DEEPSEEK_API_KEY=$(cat /tmp/ds_key)
...hmod 600 /data/home/po/.hermes/.env
```

### 7. 重启服务

```bash
systemctl --user daemon-reload
systemctl --user enable --now a2a-priestess
```

### 8. 验证

```bash
PRIESTESS_URL=http://localhost:19010 python3 ~/projects/hermes-a2a/client.py "你是谁？"
```

## 常见坑

- **config-kit 的 config.yaml 含占位符 `api_key: YOUR_API_KEY`**：不影响运行——API key 通过 `auth.json` credential pool + `.env` 文件注入
- **新的 .hermes/skills/ 目录是空的**：config-kit 的 skills 复制前，原目录只有 `.curator_state`
- **systemd 服务文件可能在根分区**：如果 `/home/po/.config/` 通过 softlink 指向根分区，文件会随 `/home.old` 一起丢失。重建服务文件后 `systemctl --user daemon-reload` 再启动
- **旧进程内存中的文件无法全部恢复**：Python 源码模块加载后不在 `/proc/PID/fd/` 中，只有二进制和数据文件可恢复
