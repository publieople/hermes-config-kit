# UU 远程端口映射 → WSL sshd（FRP 替代方案）

适用：从外部网络 SSH 到一台无公网 IP 的 Windows 主机上的 WSL，替代 FRP。前提：该 Windows 主机装了网易 UU 远程并保持在线。

## 架构

```
本机 → UU 隧道(本地端口) → Windows 127.0.0.1:2222 → WSL2 localhost 转发 → WSL sshd:2222
```

UU 远程的端口映射只支持 TCP，SSH 正好是 TCP。跳板 = 装 UU 的 Windows 主机；WSL sshd 是真正目标。

## 步骤

### 1. WSL 里配 sshd（Arch 为例）

```bash
sudo pacman -S --needed openssh
sudo ssh-keygen -A
echo 'Port 2222' | sudo tee -a /etc/ssh/sshd_config   # 避开 Windows 占的 22，见 SKILL.md「幽灵占用」
sudo systemctl enable --now sshd                       # wsl.conf 需 [boot] systemd=true
```

加公钥：

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

可选加固：sshd_config 加 `PasswordAuthentication no` 后 `sudo systemctl restart sshd`。

### 2. UU 远程建映射规则（设备详情 → 更多 → 端口映射 → 新建）

| 字段 | 填 |
|---|---|
| 目标服务地址 | `127.0.0.1` |
| 目标服务端口 | `2222` |
| 本地访问端口 | 任意，如 `2222` |

**为什么填 127.0.0.1 而不是 WSL 的 eth0 IP**：WSL2 localhost 转发会把 Windows 的 127.0.0.1:2222 透到 WSL，地址稳定；eth0 的 172.x.x.x 重启 WSL 会变，规则要跟着改。

### 3. 本机 ssh config

```
Host lab-wsl
    HostName 127.0.0.1
    Port 2222
    User po
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

再跳内网其他服务器：`ProxyJump lab-wsl`。

## 注意事项

- **映射依赖 UU 面板保持连接**：关闭面板或断连即失效，需重新打开端口映射面板
- **仅 TCP**：UDP/HTTP 不支持
- **本地端口不能重复**：每条规则的本地访问端口必须唯一
- **sshd 已 enable**：WSL 重启自动拉起（前提是 systemd=true）
- 映射失败先查：WSL 里 `sudo ss -tlnp | grep 2222` 确认 sshd 在听；再查 UU 规则的目标地址/端口

## 从 FRP 迁移时

UU 方案是**私有隧道**——只在你自己装了 UU 的设备上能用。以下情况保留 FRP：
- 其他设备/人也要连同一台服务器
- FRP 上还跑着对外发布的 HTTP 服务

纯个人 SSH 用途可以直接换：UU 加规则 → 改本机 ssh config → 验证连通 → 停 FRP 客户端。

### 关键坑：本机"FRP 服务"常常不是 frpc，而是 ssh -L 隧道

被 FRP 转发的服务在本机那一端，往往不是 frpc 进程自己，而是**一条 `ssh -p <frp端口> -N -L <本地端口>:127.0.0.1:<远程端口> po@<frp地址>` 的 SSH 隧道**。从 FRP 换 UU 时，占着本地端口（如 8188）的是这条旧 `-L` 隧道，不是 frpc。

**必须先杀掉旧 `-L` 隧道再建新的**，否则新 `ssh -L 8188` 会 `bind: Address already in use`。

辨认谁占着本地端口（WSL 侧 `ss` 就能看到，Windows 侧要看 `netstat.exe -ano`）：

```bash
sudo ss -tlnp | grep 8188        # 若 users:((\"ssh\",pid=...)) → 是隧道不是 frpc
ps -p <pid> -o pid,cmd           # 看到 ssh -p 35043 ... -N -L 8188 ... = 走 FRP 的旧隧道
```

批量收掉所有走 FRP 公网地址的旧隧道（比逐个 kill PID 稳，PID 会变）：

```bash
pkill -f 'ssh.*-p 35043.*ofalias'   # 匹配所有走 FRP 端口的 -L 隧道
```

然后建新 UU 隧道：

```bash
ssh -fN -L 8188:127.0.0.1:8188 school   # school 已指向 UU 的 127.0.0.1:2223
```

### 服务器侧的 frpc：只停被替换的那一条

FRP 客户端在服务器上常以多个 systemd 服务存在，每个 service 转一个本地服务：

```bash
ssh school "pgrep -af frpc"     # 显示 N 个 frpc -c /etc/frp/frpc-<名>.toml
ssh school "head -40 /etc/frp/frpc-<名>.toml | grep -Ei 'serverName|name|localPort|remotePort'"
```

`head` 一行看 `localPort` + `name`，对照你要替换的那个服务（本会话案例：`frpc-ssh` 转发 `22→35043` 的就是要停的；`frpc`/`frpc-fp` 是 Minecraft 25565/25566，别动）。只停对应一条：

```bash
sudo systemctl disable --now frpc-ssh
```

> ⚠️ 远程登录 shell 是 fish 时，inline `for f in a b c; do ...; done` 会报 `Missing end to balance this for loop`。用分号串行命令替代，或 `ssh user@host bash -c 'for ...'` 强制 bash。

### 换端口的持久心智模型

`~/.ssh/config` 里给目标加 `ControlMaster auto` + `ControlPersist 10m`，之后 `ssh` 会复用同一条连接，`-L` 隧道不重复建；机器重启或 UU 面板重开后连接会掉，需重跑一次 `ssh -fN -L ...`。
