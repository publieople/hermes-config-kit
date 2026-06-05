# 中国用户 Hermes Memory Provider 配置指南

## 概述

Hermes Agent 的 8 个外部 memory provider 中，**Mem0** 是中国用户的最佳实践起点（无邮箱注册，npm CLI 一键注册），**Hindsight 本地模式** 是第二候选（无需额外 API Key），**OpenViking** 配置门槛较高（需 embedding 模型），其余 provider 大多需要外网 API Key。

本文基于实际安装配置经验整理。

---

## Mem0（推荐 ★★★★★）

| 项目 | 内容 |
|------|------|
| 模式 | Cloud（Mem0 Platform API） |
| 费用 | 免费额度（未认领 ≤ 5 次/IP/天） |
| 网络 | 需外网访问 api.mem0.ai |
| 配置步骤 | 2 安装 + 2 配置共 4 步 |

### 安装配置步骤

**Step 1 — 安装 Python 库**（Hermes 插件所需）

```bash
pip3 install mem0ai
# 国内镜像加速：
pip3 install mem0ai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Step 2 — 安装 CLI 并注册 Agent 模式**（无邮箱，自动生成 API Key）

```bash
# 如果 ~/.npm-global/bin/ 不在 PATH，先设 npm prefix
npm config set prefix ~/.npm-global    # 仅首次
# 安装 CLI
npm install -g @mem0/cli
# Agent 模式注册（--agent-caller 替换为你的 agent 名）
export PATH="$HOME/.npm-global/bin:$PATH"
mem0 init --agent --agent-caller hermes
```

注册成功后，API Key 自动写入 `~/.mem0/config.json`：
```json
{
  "platform": {
    "api_key": "m0-xxxxxxxxxxxx",
    "agent_mode": true
  }
}
```

**Step 3 — 将 API Key 注入 Hermes 配置**

```bash
# 从 ~/.mem0/config.json 读取 key 并写入 .env
MEM0_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.mem0/config.json'))['platform']['api_key'])")
echo "export MEM0_API_KEY=$MEM0_KEY" >> ~/.hermes/.env

# 设置 provider
hermes config set memory.provider mem0
```

**Step 4 — 验证**

```bash
hermes memory status
# 期望输出：Plugin: installed ✓  Status: available ✓
```

### 测试写入与检索

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
mem0 add "测试记忆：用户喜欢简洁的回答"
mem0 search "用户偏好"
```

### Agent 账号认领

Mem0 Agent Mode 注册的账号是未认领的。建议用户尽快认领：

```bash
mem0 init --email your@email.com
```

认领后 API Key 不变，记忆不丢，可访问 Web 面板（app.mem0.ai）。

---

## Hindsight（替代方案 ★★★★）

| 项目 | 内容 |
|------|------|
| 模式 | 本地模式（local daemon） |
| 网络 | 无需外网（LLM 用已有 API Key） |
| 适用 | 有任意 LLM API Key（DeepSeek、OpenAI 等） |
| 特性 | 知识图谱 + 实体解析 + `hindsight_reflect` 跨记忆综合 |

```bash
pip3 install hindsight
hermes memory setup    # 选 hindsight
# 本地模式无需设置 HINDSIGHT_API_KEY
# LLM 用已有的 DEEPSEEK_API_KEY 等
hermes config set memory.provider hindsight
```

---

## OpenViking（不推荐 ★★）

| 项目 | 内容 |
|------|------|
| 问题 | **需要 embedding 模型**启动 Server |
| 选项 | VolcEngine（需注册）、Ollama 本地（需安装）、OpenAI（需 Key） |
| 国内 | VolcEngine 可用但需要额外注册获取 API Key |

### 为什么不适合快速上手

1. `openviking-server` 必须运行才能使用，默认端口 1933
2. `openviking-server init` 交互式配置，需要选择 embedding provider
3. 支持的 embedding provider：volcengine / byteplus / openai / ollama / llama.cpp
4. 没有 embedding 模型服务端不会正确工作（health check 不通）

### 如需使用

```bash
pip3 install openviking
# 准备 ov.conf（参考 GitHub README）
openviking-server doctor
openviking-server              # 启动在 :1933
hermes config set memory.provider openviking
```

---

## 其他 Provider 速览

| Provider | 部署方式 | 中国用户 |
|----------|----------|----------|
| Honcho | Cloud / 自托管 | 需外网或自搭 |
| ByteRover | Cloud | 需外网 |
| RetainDB | Cloud / 本地 | 看情况 |
| Supermemory | Cloud | 需外网 |
| Holographic | 本地 | ✅ 国内友好 |

---

## Troubleshooting

### `hermes memory status` 显示 provider 但 Status: not available

```
Missing:
  ✗ OPENVIKING_ENDPOINT
  ✗ OPENVIKING_API_KEY
  ...
```

Hermes 检查 `env vars` 是否存在。如果 provider 不需要某些 env（如本地模式），需要在代码中标记为非必需。通常这意味着：
- 没有正确安装 provider 的 Python 包（`pip3 install mem0ai` 等）
- 需要写环境变量到 `.env`（`echo "export XXX_KEY=..." >> ~/.hermes/.env`）
- server 没有启动（OpenViking 必须 `openviking-server` 运行中）

### `memory setup` 交互式无法使用

`hermes memory setup` 是交互式 Picker，在非 TTY 环境中无法完成选择。解决方案：
1. 直接 `hermes config set memory.provider <name>`
2. 手动写环境变量到 `.env`
3. 重启会话（`/reset` 或重开 Hermes）

### npm 全局安装 EACCES

```bash
npm config get prefix   # 如果返回 /usr → 需要 sudo 或改 prefix
npm config set prefix ~/.npm-global
# 然后重新安装
npm install -g <pkg>
# 并将 ~/.npm-global/bin 加入 PATH
export PATH="$HOME/.npm-global/bin:$PATH"
```

---

## Mem0 关键 API 参考

| 端点 | 用途 | 文档 |
|------|------|------|
| POST `/v1/memories/` | 写入记忆 | [Memory operations](https://docs.mem0.ai/core-concepts/memory-operations) |
| POST `/v1/memories/search/` | 语义搜索 | 同上 |
| POST `/v1/users/` | 创建用户 | [Platform API](https://docs.mem0.ai/api-reference) |

Mem0 的 Hermes 插件默认 `user_id: hermes-user`、`agent_id: hermes`，可通过 `~/.hermes/mem0.json` 覆盖。
