---
name: wsl-clash-proxy
description: WSL 内部进程通过本地 clash (端口 7890) 访问外网。一键给当前 shell 注入 HTTP_PROXY/HTTPS_PROXY，让 curl/git/pip/npm/wget/npx 等能出网。出现 "Could not resolve host"、"Connection timed out"、gh CLI 无法登录、npm install 卡住、git clone 失败时使用。
---

# WSL Clash Proxy Injector

WSL 默认不走 Windows 侧代理。当工具看到网络错误但浏览器/Windows 正常时，启这个 skill。

## 适用场景（trigger）

- `curl https://github.com` 返回 Connection timed out
- `git clone https://...` 失败
- `npm install` / `pip install` / `uv add` / `cargo build` 因网络挂掉
- `gh auth login` 进不去
- `npx <tool>` 拿不到包
- `apt` 装新源失败但内网正常（少用）

## 不适用

- 浏览器/Windows 应用层问题 —— 这不在 WSL 范围
- DNS 层问题（先看 `/etc/resolv.conf`，可能是 WSL2 自身的问题，不是代理）

## 用法（一个 shell 内用一次，export 后该 session 全部命令都生效）

```bash
# 1. 验证代理活着
curl -sS -x http://127.0.0.1:7890 -o /dev/null -w "%{http_code}\n" --max-time 5 https://github.com
# 期望: 200

# 2. 给当前 shell 注入（最常用）
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="socks5://127.0.0.1:7890"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export ALL_PROXY="$all_proxy"
# ponytail: 不动 no_proxy —— clash 已是 transparent proxy, 局域网流量走原本路径更快

# 3. 跑你本来跑不动的命令
curl https://api.github.com -I
git clone https://github.com/...
npm install
```

## 一次性命令形式（不需要持久 export）

```bash
curl -x http://127.0.0.1:7890 -L -o file.tar.gz https://...
https_proxy=http://127.0.0.1:7890 git clone https://github.com/...
HTTPS_PROXY=http://127.0.0.1:7890 pip install xxx
```

## 排查（代理不通时）

```bash
# clash 端口是否在监听
ss -tlnp | grep 7890   # 或: netstat -tlnp | grep 7890

# clash 进程在不在
pgrep -af clash | head -5   # 或: pgrep -af "Clash for Windows"

# 用 telnet 测端口可达
bash -c '(echo > /dev/tcp/127.0.0.1/7890) && echo OK || echo FAIL'

# Windows 侧 clash 是否开着
# 去 Windows 任务栏看 "Clash for Windows" 图标 —— 关了就开
```

## 副作用 & 注意

- 注入后所有流量走代理，包括 apt/系统包管理。**平时不要 export**，要时再 export。
- GitHub SSH 不走 HTTP，clone 还是用 git@... 时这条不生效（用 HTTPS URL）。
- 有些工具绕开环境变量（K8s in-cluster、Docker daemon、systemd）——这不在 skill 范围内
- 不要写到 `/etc/environment`，会让所有进程包括不需要的都走代理

## 关联

- WSL 跟 Windows 共享网络栈，但代理是 per-app 的。Browser 在 Windows 里配置代理 ≠ WSL 里能用。
- 这是 Windows 侧 "Clash for Windows" / Clash Verge / mihomo 的端口默认 7890；如果用 clash-meta 改了端口，跟着改。
