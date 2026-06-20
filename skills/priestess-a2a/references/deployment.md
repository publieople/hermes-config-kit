# A2A Bridge 部署记录

## 环境

**Lab Server:**
- Ubuntu 24.04, 4×A10 GPU, Python 3.12
- Fish shell (不支持 heredoc)，tmux 3.6b
- SSH 只监听 127.0.0.1:22（FRP 本地转发，PasswordAuthentication=no）
- Hermes Agent: `/data/home/po/.hermes/hermes-agent/`（via `/home` → `/data/home` 软链接）
- Skills 来源：`https://github.com/publieople/hermes-config-kit`（253 skills）
- systemd 255, user linger=yes
- FRP SSH: `po@3722d01e5a6f.ofalias.com -p35043`
- 磁盘：根分区 98G（18G used），/data 7.3TB（via /dev/sdb XFS）
- `/data/home/po` 通过 fstab bind mount 到 `/home/po`
- 关键服务：clash-meta（mihomo at `/home/po/proxy/`），mcdr（MC server at `/data/mcdr/`）

**WSL:**
- systemd 260, user linger=yes
- A2A 隧道: systemd user service `a2a-tunnel`，SSH -L 19010:localhost:9010

## 通过 config-kit 部署

除了手动部署外，也可用 config-kit 快速恢复配置：

```bash
git clone https://github.com/publieople/hermes-config-kit
cp -r hermes-config-kit/skills/* ~/.hermes/skills/
cp hermes-config-kit/SOUL.md ~/.hermes/SOUL.md
cp hermes-config-kit/config.yaml ~/.hermes/config.yaml
cp hermes-config-kit/scripts/* ~/.hermes/scripts/
# SOUL.md 需将"魔术师"改为"女祭司"
```

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
