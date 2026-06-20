# SSH 断连应急恢复（通过 A2A 后门）

当服务器 SSH 断连但 A2A 隧道仍通时，通过女祭司诊断并修复 SSH。

## 诊断步骤

通过 A2A 让女祭司并行执行：

```
1. systemctl status sshd
2. ls -la /data/home/po/.ssh/authorized_keys
3. grep ListenAddress /etc/ssh/sshd_config
4. grep PasswordAuthentication /etc/ssh/sshd_config
5. grep PubkeyAuthentication /etc/ssh/sshd_config
```

## 常见根因及修复

### 根因 1：authorized_keys 丢失

**症状**：`~/.ssh/authorized_keys` 不存在，`PasswordAuthentication no`

**场景**：`/home` 迁移后 `.ssh/` 目录未随数据迁移

**修复**：从 WSL 获取公钥，通过 A2A 让女祭司写入：

```bash
mkdir -p /data/home/po/.ssh
echo "ssh-ed25519 AAAAC3..." > /data/home/po/.ssh/authorized_keys
chmod 700 /data/home/po/.ssh
chmod 600 /data/home/po/.ssh/authorized_keys
```

### 根因 2：ListenAddress 限制

**症状**：`ListenAddress 127.0.0.1`

**分析**：如果通过 FRP 本地转发（`127.0.0.1:22`），**不需要改**。更安全。

**只有局域网直连场景才需改成 `0.0.0.0`**。

### 根因 3：sshd 未运行

**修复**：`sudo systemctl start sshd`

## 验证

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 po@3722d01e5a6f.ofalias.com -p35043 "echo OK"
```

## 注意

- A2A 是独立于 SSH 的通道，SSH 断连不影响 A2A
- 修复后需检查其他服务（clash-meta、mcdr）是否也受影响
