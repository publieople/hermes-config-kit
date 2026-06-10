# A2A Bridge 部署记录

## 环境

**Lab Server:**
- Ubuntu 24.04, 4×A10 GPU, Python 3.12
- Fish shell (不支持 heredoc)
- Hermes Agent: `~/.hermes/hermes-agent/`
- systemd 255, user linger=yes
- FRP SSH: `po@3722d01e5a6f.ofalias.com -p35043`

**WSL:**
- systemd 260, user linger=yes

## 部署步骤

### 1. Lab 端安装依赖

```bash
# a2a-adapter
pip3 install --break-system-packages a2a-adapter

# Hermes 需要的 openai 模块（DeepSeek 用 openai SDK）
pip3 install --break-system-packages openai
```

### 2. 部署 server.py

```bash
# 放到永久位置
cp server.py ~/.local/bin/a2a-server.py

# 关键: PYTHONPATH 必须指向 hermes-agent 源码
PYTHONPATH=$HOME/.hermes/hermes-agent python3 ~/.local/bin/a2a-server.py
```

### 3. 安装 systemd 服务

```bash
mkdir -p ~/.local/var/log/

# 复制服务文件
cp a2a-priestess.service ~/.config/systemd/user/

# 启用
systemctl --user daemon-reload
systemctl --user enable --now a2a-priestess.service
```

### 4. WSL 端隧道

```bash
cp a2a-tunnel.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now a2a-tunnel.service
```

## 踩坑记录

### FRP 限流
FRP 隧道有连接频率限制。同一 SSH 连接可复用，但短时间内新建多个连接会被断开。现象：`Connection closed by 103.6.221.134 port 35043`。
解决：systemd RestartSec=30s，手动操作间隔 5-10s。

### Fish shell 无 heredoc
Lab 用 fish，不支持 `cat > file << 'EOF'`。
解决：用 base64 编码传输文件内容。

### fastfetch 破坏 SCP
每次 SSH 登录 fish 运行 fastfetch，输出干扰 SCP 协议。
解决：用 `echo $B64 | base64 -d > file` 代替 scp。

### a2a-sdk 流式模式不通
SSE streaming 在 FRP/SSH 隧道下不可靠，响应为空。
解决：用 `message/send` + `blocking: true` 模式。

### Agent Card URL 问题
Agent Card 的 `supportedInterfaces.url` 是 `http://localhost:9010/`，客户端拿到后直接连这个地址——WSL 的 localhost:9010 不是 Lab 的。
解决：客户端需 override Agent Card 的 URL 为隧道地址。

### Python openai 未安装
HermesAdapter 内部用 openai SDK 调 DeepSeek API。Lab 默认没装。
解决：`pip3 install --break-system-packages openai`

### 服务脚本中的 PYTHONPATH
server.py 自身有 sys.path 插入逻辑，但 systemd 的 ExecStart 环境独立。需要用 `Environment=PYTHONPATH=...` 在 service 文件中显式设置。
