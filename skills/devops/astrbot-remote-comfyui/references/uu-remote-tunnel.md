# UU 远程替代 FRP：WSL sshd + 端口映射 + 隧道迁移

迁移场景：ComfyUI SSH 隧道原来走 FRP（`3722d01e5a6f.ofalias.com:35043` → 服务器 22），改用网易 UU 远程端口映射经跳板机进实验室内网，省 FRP 流量。整套是「跳板机直连 + UU 端口映射 + 本机 ssh 隧道」三层。

## 架构（迁移后）

```
本机 127.0.0.1:8188
  → ssh -L 8188:127.0.0.1:8188 server   (config host)
    → 127.0.0.1:2223                    (UU 端口映射本地端)
      → UU 隧道 → 跳板机
        → 跳板机内网 → 服务器 10.1.201.228:22 (服务器 SSH)
          → 服务器 127.0.0.1:8188        (ComfyUI)
```

UU 远程端口映射面板字段：`目标服务地址`(跳板机可达的 IP/127.0.0.1)、`目标服务端口`、`本地访问端口`。**只支持 TCP**（SSH/HTTP 都行）。

## ~/.ssh/config host 命名约定

本机两个 host：
```
Host PubliPC    # 本机 WSL sshd (UU 映射 127.0.0.1:2222)
    HostName 127.0.0.1
    Port 2222
Host server     # 实验室 ComfyUI 服务器 (UU 映射 127.0.0.1:2223)
    HostName 127.0.0.1
    Port 2223
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
```

## 坑

### 1. WSL2 localhost 转发 + Windows OpenSSH 占 22 —— 必须换 WSL sshd 端口
- WSL 里 `ssh localhost` 连到的是 **Windows 宿主的 OpenSSH Server**（走 WSL2 localhost 转发），不是 WSL 自己的 sshd。host key 指纹对不上 → "REMOTE HOST IDENTIFICATION HAS CHANGED"，且宿主密码不认。
- WSL sshd 想 bind 22 会报 `Address already in use`（被宿主占），但 `ss`/`ps` 里**看不到**宿主进程——这是 WSL 特性，不是 bug。
- 解决：WSL sshd 换端口。Arch: `echo 'Port 2222' | sudo tee -a /etc/ssh/sshd_config`，`sudo systemctl enable --now sshd`。UU 映射目标填 `127.0.0.1:2222`。
- Arch WSL sshd 依赖 systemd：`sudo systemctl restart sshd` 前确保 `/etc/wsl.conf` 有 `[boot] systemd=true`。

### 2. UU 映射掉线：`Connection reset by 127.0.0.1 port <port>` + `kex_exchange_identification: read: Connection reset by peer`
- 即使 `timeout bash '/dev/tcp'` 测 2223 TCP 通，SSH 握手仍可能被 reset——UU 层闪断。
- **修法：关掉 UU 端口映射窗口再重开**，之后隧道 10s 内自动恢复。这是反复出现的坑，不是配置错误。

### 3. 旧 FRP 隧道是 root/system 级 systemd 服务（PartOf=astrbot）
- 查：`systemctl cat comfyui-tunnel`（root 级文件 `/etc/systemd/system/comfyui-tunnel.service`，`PartOf=astrbot.service`，`ExecStart=ssh -p 35043 -L 8188...`，`Restart=on-failure`）。
- 它随 AstrBot 启停，`Restart=on-failure` 会让残留 ssh 被 systemd 自动复活——光 kill 进程会被拉回。
- 弃用：`sudo systemctl disable --now comfyui-tunnel; sudo pkill -f "ssh.*<host>.*8188"`。

### 4. systemd user 服务 vs 手动 mux 打架
- 隧道改 systemd user 服务（`~/.config/systemd/user/comfyui-tunnel.service`，`Restart=on-failure` + `RestartSec`）vs 手动 `ssh -fN -L`（ControlMaster auto 建 mux）。
- **两者路径不同但目标/端口相同 → 互抢**：手动 mux 占住 8188，systemd 服务 bind 失败退到 inactive/inactive。别混用，选一边。
- 用户最终偏好**手动连接端口转发**，放弃 systemd 托管。手动命令：`ssh -fN -L 8188:127.0.0.1:8188 server`，停止 `pkill -f 'ssh.*-L.*8188.*server'`。

### 5. pkill 自杀坑
- `pkill -f 'ssh.*-L.*8188.*server'` 会匹配到**自己所在 bash 的命令串**（命令文本含该关键字）把整个 shell 杀掉。
- 规避：模式写得和自身命令无关（如 `pkill -f 'ssh -NT.*8188'`），或先 `pgrep` 确认 PID 再 `kill`。

## 服务器端 frpc 情况（未改动）
- 服务器跑多个 frpc：`frpc-ssh`(22→35043, SSH, 共享多人用)、`frpc`(25565 EHC)、`frpc-fp`(25566 FPS)。
- **多用户共享的 frpc-ssh 不能停**——只有你一个人走 UU，别人还靠 35043 进服务器。迁移只影响本机 client 连接，服务器端服务保留。

## 排查顺序（隧道起不来时）
1. `timeout bash /dev/tcp/127.0.0.1/<端口>` 测 TCP
2. TCP 通但 ssh 握手 reset → UU 面板重开
3. 报 host key 变化 → `ssh-keygen -R '[127.0.0.1]:<端口>'`
4. 端口被占 → `ss -tlnp | grep <端口>` 看是不是手动 mux / 另一个 comfyui-tunnel，决定清哪个