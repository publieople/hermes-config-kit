---
name: clash-proxy
description: WSL 中访问 Windows 侧 Clash 代理 — 端口、探测、设置、各工具代理用法
category: devops
tags: [proxy, clash, wsl, network]
---

# Clash 代理 (WSL ↔ Windows)

Clash for Windows 运行在 Windows 侧，WSL 通过 `localhost` 转发访问。

## 端口

| 协议 | 地址 |
|------|------|
| HTTP | `http://127.0.0.1:7890` |
| SOCKS5 | `socks5://127.0.0.1:7891` |

## 探测代理是否运行

```bash
curl -s --connect-timeout 1 http://127.0.0.1:7890
```

- 返回 `HTTP 400`（空响应体）→ **正常运行**（对裸请求的预期响应）
- `curl: (7) Failed to connect` 或 `curl: (28) Connection timed out` → **未启动**

一行判断：

```bash
curl -s --connect-timeout 1 http://127.0.0.1:7890 > /dev/null && echo "UP" || echo "DOWN"
```

## 设置代理环境变量

### fish shell（当前默认 shell）

```fish
set -x HTTP_PROXY http://127.0.0.1:7890
set -x HTTPS_PROXY http://127.0.0.1:7890
set -x ALL_PROXY http://127.0.0.1:7890
set -x NO_PROXY localhost,127.0.0.1,::1,.local
```

### bash/zsh

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,::1,.local
```

## 各工具的代理方式

### curl / wget

自动读取 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量，设置后即可。

### git

```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 取消
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### uv (Python 包管理)

```bash
# 方式1：环境变量（推荐，已设置全局 env 后自动生效）
uv pip install <package>

# 方式2：命令行指定
HTTPS_PROXY=http://127.0.0.1:7890 uv pip install <package>
HTTPS_PROXY=http://127.0.0.1:7890 uv python install 3.10
```

### pip

```bash
pip install --proxy http://127.0.0.1:7890 <package>
# 或设置环境变量后自动生效
```

### npm / npx

```bash
npm config set proxy http://127.0.0.1:7890
npm config set https-proxy http://127.0.0.1:7890

# 取消
npm config delete proxy
npm config delete https-proxy
```

### Docker

Docker 拉镜像走代理需要配置 daemon（不是环境变量），见 Docker Desktop 设置或 `/etc/docker/daemon.json`。

但 WSL 中 `docker pull` 实际走的是 Docker Desktop（Windows 侧），已在 Windows 侧配置代理时无需额外设置。

### huggingface-cli / hf download

```bash
# hf-mirror 替代（不需代理，但有时不稳）
export HF_ENDPOINT=https://hf-mirror.com

# 走代理直连 HuggingFace
HTTPS_PROXY=http://127.0.0.1:7890 huggingface-cli download <org>/<repo>
```

### modelscope

Modelscope 是国内 CDN，**不需要代理**，直连即可。

## Hermes 终端命令中的代理

在 `terminal()` 中使用需要代理的命令时，必须在命令前设置环境变量（同一行），因为 Hermes 的 shell 环境变量会跨调用持久化：

```bash
# 如果之前已 set -x，直接运行
curl -L https://github.com/...

# 如果未设置，命令前指定
HTTPS_PROXY=http://127.0.0.1:7890 curl -L https://github.com/...
```

## 常见陷阱

1. **WSL 重启后 localhost 转发可能变化** — 如果 `127.0.0.1:7890` 不通，检查 Windows 侧 Clash 是否在运行，以及 WSL 是否能访问 Windows 的 localhost（通常可以）
2. **SOCKS5 和 HTTP 代理端口不同** — 大部分工具用 HTTP 代理（7890），SOCKS5（7891）用于需要 TCP 级别代理的场景
3. **NO_PROXY 别忘了设** — 否则访问本地服务也会走代理
4. **git clone 走 HTTPS 才走代理** — SSH 协议 (`git@github.com:...`) 不走 HTTP 代理，需要用 `ssh -o ProxyCommand` 或改用 HTTPS 地址
