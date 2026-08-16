# Hermes 记忆提供商：中国用户配置指南

## 概览

Hermes Agent 内置 8 种外部记忆 provider，外加始终可用的内置记忆（MEMORY.md / USER.md）。
同一时间**只能激活一个外部 provider**，内置记忆始终并行运行。

## 选择指南（中国用户视角）

| Provider | 网络要求 | API Key | 自托管 | 国内延迟 | 适合场景 |
|----------|----------|---------|--------|---------|---------|
| **Mem0** | 需外网 | ✅ Cloud | ✅ Docker | 0.5-1.5s | 自动记忆，无脑配置 |
| **Hindsight** | 本地免费 | 可本地 | ✅ 本地 | 零 | 知识图谱，实体关系 |
| **Holographic** | 本地 | 不需要 | ✅ 本地 | 零 | 轻量记忆 |
| **Honcho** | 需外网/自托管 | ✅ Cloud | ❌ 文档有限 | 不定 | 多 Agent 上下文共享 |
| **OpenViking** | 需 embedding 服务 | 需火山/Ollama | ✅ 本地 | 零 | 文件系统式上下文管理 |
| **ByteRover** | 需外网 | ✅ Cloud | ❌ | 不定 | 知识树 Markdown |
| **RetainDB** | 需外网 | ✅ Cloud | 待确认 | 不定 | 专用记忆数据库 |
| **Supermemory** | 需外网 | ✅ Cloud | ❌ | 不定 | 图 API 记忆 |
| **内置记忆** | 无 | 不需要 | ✅ 本地 | 零 | 静态事实（项目路径、偏好） |

## 配置命令

```bash
hermes memory setup        # 交互式向导（选择 provider 并配置）
hermes memory status       # 查看当前状态
hermes memory off          # 停用外部 provider（内置记忆不受影响）
```

或手动配置：

```bash
hermes config set memory.provider <name>
# 在 .env 中设置对应 API Key（如需）
```

## 国内网络注意事项

### pip install 超时

所有 provider 的 Python 包都可用清华镜像：

```bash
pip install mem0ai -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install openviking -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### GitHub API 访问

自托管 provider（Hindsight、OpenViking 等）需要从 GitHub 下载模型或依赖。如遇超时，可考虑：
- 代理：`git -c http.proxy=http://127.0.0.1:7890 clone ...`
- GitHub tarball 回退：`curl -L https://api.github.com/repos/owner/repo/tarball | tar xz`

### Cloud API 延迟

Mem0 / Honcho / Hindsight Cloud 的 API 端点在国外，约 0.5-1.5s 延迟。
Hermes 的**后台预取 + 缓存**机制会屏蔽大部分感知延迟——搜索在会话间隙完成，不阻塞对话。

## 安装后的通用排错

### npm 全局包命令找不到

```bash
# 检查安装位置
ls ~/.npm-global/bin/<cmd>
ls /usr/lib/node_modules/.bin/<cmd>

# 加 PATH（bashrc）
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
```

**fish shell（通过 .bashrc 启动 fish）：** fish 继承 bash 的 PATH。验证用：

```fish
type <cmd>
# → <cmd> is /home/po/.npm-global/bin/<cmd>
```

如果找不到，在 `~/.config/fish/config.fish` 添加：

```fish
fish_add_path ~/.npm-global/bin
```

### npm 报 EACCES

永久解决：将 npm prefix 设为用户目录。

```bash
npm config set prefix ~/.npm-global
# 之后所有 npm install -g 都无需 sudo
# 不要改回 /usr——这是一次性设置，以后所有全局包都受益
```

### fish shell 没有 `which` 命令

fish 没有 `which`。用内置 `type` 代替：

```fish
type mem0
# → mem0 is /home/po/.npm-global/bin/mem0
```

## 各 Provider 配置详情

每个 provider 的完整配置步骤见各自的 Hermes 文档：
https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers
