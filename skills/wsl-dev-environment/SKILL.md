---
name: wsl-dev-environment
description: WSL 开发环境配置 — NTFS venv 权限、Clash 代理访问、DeepSeek ReAct 模式
category: devops
tags: [wsl, venv, proxy, deepseek, react-agent]
---

# WSL 开发环境

WSL (Windows Subsystem for Linux) 上的开发环境配置与常见陷阱。

## 触发条件

- 在 WSL 中创建 Python venv 失败（NTFS 权限错误）
- 在 WSL 中需要访问 Windows 侧的代理（Clash）
- NTFS 挂载盘上的文件权限/解压问题
- DeepSeek ReAct Agent 在 WSL 环境下的运行

## NTFS 挂载盘上的 venv 权限问题

### 症状

在 `/mnt/c/`、`/mnt/e/` 等 Windows 盘上使用 `uv sync` 或 `pip install` 时报错：

```
Operation not permitted (os error 1)
```

### 原因

Windows NTFS 文件系统不支持 Linux 的文件权限模型，导致 `.venv/` 内的文件复制操作失败。

### 解决方案

将 venv 创建在 Linux 原生文件系统（ext4）上，然后软链接到项目目录：

```bash
# 1. 删除项目下的 .venv
rm -rf .venv

# 2. 在 Linux 侧创建 venv
uv venv --python 3.13 /home/po/.venvs/<project-name>

# 3. 建立软链接
ln -sf /home/po/.venvs/<project-name> .venv

# 4. 正常安装依赖
uv sync
```

注意：pyproject.toml 和项目代码仍可放在 NTFS 盘上，只有 `.venv/` 需要移到 Linux 侧。

## WSL 访问 Windows Clash 代理

Clash for Windows 的 HTTP 代理默认监听 `127.0.0.1:7890`，WSL 可直接访问。

### 探测代理

```bash
curl -s --connect-timeout 1 http://127.0.0.1:7890
# 返回 HTTP 400 = 代理正常运行（对裸请求的预期响应）
# 返回 000 / 无响应 = 代理未启动
```

### 设置代理

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

常见 Clash for Windows 端口：HTTP 7890 | SOCKS5 7891

## DeepSeek ReAct Agent 模式

参见 `references/deepseek-react-patterns.md`。核心陷阱：

1. **必须设置 `stop=["PAUSE"]`** — DeepSeek 不会自然停在 PAUSE，会一次生成完整多轮对话（含幻觉 Observation）
2. **正则匹配需兼容中英文冒号** — DeepSeek 输出可能混用 `:` 和 `：`

## Python 版本冲突与依赖管理

### `uv add` vs `uv pip install`

在 NTFS 挂载盘上的项目，**不要用 `uv add`**（它会尝试重建 NTFS 上的 .venv）。用 `uv pip install` 直接装到 Linux venv：

```bash
uv pip install <package> --python /home/po/.venvs/<project-name>/bin/python
```

### Python 3.14 兼容问题

系统 Python 3.14 可能缺少某些包的 wheel（如 `openai-whisper` 缺少 `pkg_resources`）。用 uv 安装旧版 Python：

```bash
uv python install 3.12
uv venv --python 3.12 /home/po/.venvs/<name>
```

## Vite/Node 开发服务器：Windows 浏览器访问

WSL 中启动的 Vite dev server 在 Windows 浏览器可能无法访问。

### 必须加 `--host`

```bash
npx vite --host 0.0.0.0
# 不加 --host 时 Vite 只监听 localhost，Windows 端可能无法转发
```

不加 `--host` 时 `ss -tlnp | grep 5173` 显示端口未监听（虽然 Vite 打印了 ready 消息）。

### 浏览器地址优先级

| 优先级 | 地址 | 适用场景 |
|---|---|---|
| 1 | `http://localhost:5173/` | WSL2 localhost 转发正常时 |
| 2 | `http://<WSL_IP>:5173/` | localhost 转发失败时（用 `ip addr show eth0` 获取 IP） |

### terminal(background=true) 静默退出

`terminal(background=true)` 启动 `npx vite` 可能静默退出（exit code 0，output 只有 bash ioctl 警告）。替代方案：在用户自己的 WSL 终端中手动运行 `npx vite --host 0.0.0.0`。

## WSL 后台进程调试

后台进程在 WSL 中静默退出是常见问题。排查流程：

1. 先在前台跑一次看报错：`python3 server.py 2>&1`
2. 确认无语法错误后再后台启动：`terminal(background=true)`
3. 检查端口：`ss -tlnp | grep <port>`

## ModelScope 下载

ModelScope（`modelscope.cn`）下载模型不需代理，且比 HuggingFace 更稳定（国内 CDN）。

## 参考文件

- `references/deepseek-react-patterns.md` — DeepSeek ReAct Agent 在 WSL 下的具体坑
- `references/deepseek-api-patterns.md` — DeepSeek API 的 ReAct/Function Calling 坑和写法（从 wsl-python-development 合并）
- `references/mcp-fastmcp-api.md` — MCP FastMCP 三种传输协议的现行 API（从 wsl-python-development 合并）
