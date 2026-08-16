---
name: lab-server-home-migration-recovery
description: Lab 服务器 /home 迁移到 /data 后的恢复流程 — SSH 断连、配置丢失、bind mount 陷阱
---

# Lab 服务器 /home 迁移恢复

当服务器执行 `/home` → `/data/home` 迁移后出现 SSH 断连、服务崩溃时的恢复流程。

## 背景架构

```
/dev/sdb (7.3T XFS) ──┬── /data           ← 主挂载
                      └── /home.old/po     ← bind mount 残留

fstab: /data/home/po → /home/po (bind mount)
```

**关键陷阱**：bind mount 会"遮盖"底层目录。用户在 `/home/po` 下创建的文件在 bind mount 层，不在底层 `/data/home/po/` 中。卸载 bind mount 后这些文件会消失。

## 恢复流程

### 1. 通过 A2A 联系女祭司（SSH 断连时）

```bash
# WSL 端检查隧道
systemctl --user status a2a-tunnel

# 调用女祭司
PRIESTESS_URL=http://localhost:19010 python3 ~/projects/hermes-a2a/client.py "<消息>"
```

### 2. 直接 SSH（修复后）

```bash
ssh po@3722d01e5a6f.ofalias.com -p35043
```

注意：服务器默认 shell 是 fish，远程执行复杂 bash 脚本用：
```bash
ssh ... /bin/bash << 'SSHEOF'
...
SSHEOF
```

### 3. 从内存进程抢救文件

进程的文件即使被删除，仍可通过 `/proc/PID/` 恢复：

```bash
# 恢复二进制
cp /proc/<PID>/exe /data/home/po/<target_path>/

# 恢复打开的文件
# 检查 /proc/<PID>/fd/ 中的文件描述符
ls -la /proc/<PID>/fd/ | grep -v 'socket\|pipe\|anon'
```

### 4. 关键服务

| 服务 | systemd 路径 | 二进制 | 配置 |
|------|------------|--------|------|
| clash-meta | `/etc/systemd/system/clash-meta.service` | `/data/home/po/clashctl/bin/mihomo` | `/data/home/po/clashctl/resources/runtime.yaml` |
| mcdr | `/etc/systemd/system/mcdr.service` | uv run mcdreforged | `/data/mcdr/` |
| sshd | 系统服务 | 监听 127.0.0.1:22 | `PasswordAuthentication no` |

### 5. 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 pip3 install --user uv
```

### 6. 删除 /home.old

```bash
# 先 lazy umount（进程还在用时）
sudo umount -l /home.old/po

# 再删除
sudo rm -rf /home.old
```

## 已踩的坑

- bind mount 在 mv 时会跟随迁移，导致底层文件被"遮盖"
- 迁移前必须先 umount bind mount，不能直接 mv
- `lsof +D /home.old` 为空不代表没进程占用（bind mount 的进程 cwd 也会指向旧路径）
- Fish shell 远程执行 bash 脚本会解析失败，必须用 `/bin/bash` 包裹
