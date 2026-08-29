---
name: uu-remote-tunnel
description: 用网易UU远程端口映射做私有隧道访问内网服务器，替换FRP。触发"换掉FRP/省公网流量/UU跳板SSH到内网"。
---

# 网易UU远程 端口映射隧道（FRP 替代）

网易UU远程(硬件/被控端在线)提供 TCP 隧道穿透：把被控设备（或其所在局域网内任意主机）的 TCP 服务映射到本机端口。纯私有，省 FRP 公网流量。**仅支持 TCP**（SSH/MySQL/HTTPS 可用，UDP 不行）。

## 核心配置

| 字段 | 说明 |
|---|---|
| 目标服务地址 | 被控机可达的 IP。填 `127.0.0.1` 表示被控机自身服务；填局域网 IP（如 `10.1.201.228`）则经被控机转发到那台机器 |
| 目标服务端口 | 远端服务端口 |
| 本地访问端口 | 映射到本机，访问 `127.0.0.1:该端口` |

映射依赖被控端活跃连接，**关闭面板/断连即失效**（官方 FAQ 明说）。

## 关键坑（都实测遇到过）

1. **本地访问端口和 UU 面板状态**：新建/改规则可能不即时生效——`Connection refused` 时先关掉端口映射面板再重开，状态变「映射成功」即可用。
2. **known_hosts 端口残留**：同一 `[host]:port` 换了 sshd 指纹会卡 `REMOTE HOST IDENTIFICATION HAS CHANGED`。修：`ssh-keygen -R '[127.0.0.1]:2222'`。
3. **跳板连通性测试**：DO NOT rely on ping (常被禁)。用 `timeout 6 bash -c 'echo > /dev/tcp/IP/22' && echo REACHABLE || echo UNREACHABLE`。

## WSL2 作为被控机（sshd 跑在 WSL）

**最大的坑：Windows 的 OpenSSH Server 占着 host 22 端口**，且 WSL2 的 localhost 转发会把 `ssh localhost`（在 WSL 内）也导向 **Windows 的 sshd**——它**不会显示在 WSL 里的 `ss -tlnp`**（`ss`/`ps` 都查不到，但 bind 时报 address already in use）。诊断靠 host key 指纹变化。

处置：
- 把 WSL 的 sshd 放到非 22 端口，如 `echo 'Port 2222' | sudo tee -a /etc/ssh/sshd_config`
- UU 映射目标填 `127.0.0.1:2222`——WSL2 localhost 转发把 Windows 的 127.0.0.1:2222 透进 WSL，地址稳定不变，不用改规则
- Arch WSL：`sudo systemctl enable --now sshd`，失败先 `sudo ssh-keygen -A` 补 host key、`sudo mkdir -p /run/sshd`；若 `sshd -D -d` 报 address in use 就是 Windows 占 22，换端口而非折腾 systemd

见 `references/wsl2-sshd-setup.md`。

## 替换 FRP 的流程

1. 现有 FRP SSH 登上服务器查内网 IP：`ssh school "ip addr show | grep 'inet '"`
2. 跳板机测 `REACHABLE`（见上）确认能直连
3. UU 加映射：目标 = 服务器内网 IP:22，本地映射端口
4. 改 `~/.ssh/config` 对应 Host → `HostName 127.0.0.1 / Port <本地端口>`
5. `ssh school` 通了再停 FRP（确认无他人共用该 FRP 入口）

## 安全

- 密钥登录优先：忘了密码时不能远程绕密码，先用 UU 远程桌面开终端把本机公钥追加到 `~/.ssh/authorized_keys`
- 验证免密后可选 `PasswordAuthentication no` 关密码登录
- UU 是私有隧道：别用于对外发布；他人也要连时保留 FRP