# WSL2 sshd 实战笔记（Arch WSL，2026-08-26 实测）

场景：在 WSL2 (Arch) 里起 sshd，用 UU远程把它的 SSH 映射出来访问。目标把之前 FRP 转发的 ComfyUI 服务器 SSH 换成 UU 隧道。

## 拓扑（最终落定）

```
本机 → UU隧道(本地2222) → Windows 127.0.0.1:2222 → WSL2 localhost转发 → WSL sshd:2222
```

`~/.ssh/config` 成品两段：

```
Host lab-wsl
    HostName 127.0.0.1
    Port 2222
    User po
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes

Host school
    HostName 127.0.0.1
    Port 2223          # UU 第二条映射：目标 10.1.201.228:22 → 本地 2223
    User po
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
```

## Windows 占 22 的迷惑现场

- `sudo systemctl enable --now sshd` → `start-limit-hit` / control process 失败
- `sudo /usr/sbin/sshd -D -d` → `Bind to port 22 on 0.0.0.0 failed: Address already in use`
- 但 `sudo ss -tlnp | grep ':22'` 和 `ps aux | grep sshd` **都为空** —— 因为占 22 的是 Windows 的 OpenSSH Server，WSL2 网络栈里看不见
- 此时在 WSL 内 `ssh localhost` 连到的是 **Windows sshd**（host key 指纹不是刚 `ssh-keygen -A` 生成的那套，密码也不对）—— 靠指纹差异识破

**根因处置**：不折腾 systemd、不关 Windows OpenSSH——直接把 WSL sshd 换到 2222。WSL2 localhost 转发自动把 Windows 的 127.0.0.1:2222 透进 WSL。

## 涉及的命令

```bash
sudo pacman -S --needed openssh
sudo ssh-keygen -A          # 生成 host key（缺 key 会起不来）
sudo mkdir -p /run/sshd     # 缺 privilege separation 目录
echo 'Port 2222' | sudo tee -a /etc/ssh/sshd_config
sudo systemctl reset-failed sshd   # 清熔断
sudo systemctl restart sshd
sudo ss -tlnp | grep 2222   # 确认在听
ssh -p 2222 localhost       # 指纹应是刚生成的那套
```

## 密钥注入（忘了密码时）

本机 `cat ~/.ssh/id_ed25519.pub`，经 UU远程桌面在 WSL 里：
```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

网关类坑：`ss -tlnp | grep ':22'` 里 `grep` 与引号字符之间要空格，否则无输出。