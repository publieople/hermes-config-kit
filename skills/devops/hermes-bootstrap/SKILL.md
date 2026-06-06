---
name: hermes-bootstrap
description: Complete Hermes agent bootstrap. Canonical source at github.com/publieople/hermes-config-kit
---

# Hermes Bootstrap · 魔术师初始化

> **Canonical source**: [hermes-config-kit](https://github.com/publieople/hermes-config-kit) — 本 skill 的文档内容已导出为可执行仓库。clone → setup.sh → 一键复现。
> 
> **同步**: 仓库每周自动同步。本 skill 为详细参考文档，仓库为可执行配置。

在新服务器上初始化 Hermes 时，推荐直接使用 hermes-config-kit：
```bash
git clone https://github.com/publieople/hermes-config-kit.git
cd hermes-config-kit && ./setup.sh
```

以下为手动配置的详细步骤（供参考和调试）。

## 0. 快速路径：hermes-config-kit（推荐）

```bash
# 1. 安装 Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Clone 数字孪生仓库
cd ~/projects
gh repo clone publieople/hermes-config-kit

# 3. 一键安装
cd hermes-config-kit
./setup.sh

# 4. 验证
hermes doctor
hermes skills list | wc -l   # 应 > 150
```

`setup.sh` 自动完成：config 复制、skills 部署、npm 工具安装、cron job 创建、API key 交互式配置。

### 自同步机制

仓库内置 `scripts/sync-back.sh`，由 cron job 每周日早 6 点运行：
1. 对比 `~/.hermes/config.yaml` → 自动 redact 敏感信息 → 更新仓库
2. rsync `~/.hermes/skills/` → 检测新增/修改/删除
3. rsync `~/.hermes/scripts/`
4. 导出 cron job 定义
5. 有变化 → `git add -A && git commit && git push`

**重要**: 这是你的数字孪生。任何设备上的任何修改，只要通过 sync-back 推送，就可以在其他设备上 pull 同步。

> 📎 完整导出/脱敏/自同步技术细节见 `references/config-export-sync.md`

---

## 1. 系统环境准备

### 1.1 基础 shell 配置

```bash
# --- ~/.bashrc ---
# fish（如果 shell 是 Arch/etc，先 pacman -S fish）
if [ -x "$(command -v fish)" ]; then
    exec fish
fi

# conda（Miniforge, /opt/miniforge/）
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"

# OpenClaw 补全
source "$HOME/.openclaw/completions/openclaw.bash"
```

写完后 `source ~/.bashrc` 进入 fish。

### 1.2 ~/.config/fish/config.fish

```fish
if status is-interactive
    fastfetch -c examples/10
end

set -g fish_greeting ""

# Oh-My-Posh（可选样式：night-owl）
oh-my-posh init fish --config 'night-owl' | source

# OpenClaw 补全
source "$HOME/.openclaw/completions/openclaw.fish"

# npm global path
export PATH="$(npm prefix -g)/bin:$PATH"

# 标记 Hermes TUI 环境
set -x HERMES_TUI 1
```

### 1.3 npm prefix（重要）

```bash
# /usr 默认 prefix 是危险路径，改成 ~/.npm-global
npm config set prefix ~/.npm-global
# 确保 ~/.npm-global/bin 在 PATH 中（已通过 bashrc 和 fish config 实现）
```

### 1.4 ~/.local/bin/env

```bash
#!/bin/sh
case ":${PATH}:" in
    *:"$HOME/.local/bin":*)
        ;;
    *)
        export PATH="$HOME/.local/bin:$PATH"
        ;;
esac
```

### 1.5 时区 & 语言

```bash
# Asia/Shanghai
sudo timedatectl set-timezone Asia/Shanghai

# 默认语言中文
echo 'export LANG=zh_CN.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=zh_CN.UTF-8' >> ~/.bashrc
```

---

## 2. Hermes Agent 配置

### 2.1 核心 config.yaml 设置

关键配置项（在 `~/.hermes/config.yaml` 中）：

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1

# TTS - MiniMax
tts:
  provider: minimax
  minimax:
    model: speech-2.8-hd
    voice_id: female-shaonv
    base_url: https://api.minimaxi.com/v1/t2a_v2
  edge:
    voice: en-US-AriaNeural

# 辅助视觉模型 - MiniMax
auxiliary:
  vision:
    provider: minimax-cn
    model: MiniMax-M2.7
  web_extract:
    provider: auto

# Memory - Mem0
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200
  user_char_limit: 1375
  provider: mem0
  nudge_interval: 10
  flush_min_turns: 6

# 代理设置
agent:
  max_turns: 90
  gateway_timeout: 1800
  reasoning_effort: medium

# delegation 子代理配置
delegation:
  max_iterations: 50
  child_timeout_seconds: 600
  max_concurrent_children: 3
  max_spawn_depth: 1
  orchestrator_enabled: true

# 终端
terminal:
  backend: local
  auto_source_bashrc: true
  env_passthrough:
    - http_proxy
    - https_proxy
    - ALL_PROXY

# 浏览器 & Web
browser:
  inactivity_timeout: 120
  command_timeout: 30
  engine: auto

web:
  backend: ""
  search_backend: ""
  extract_backend: ""

# 显示设置
display:
  compact: false
  language: en
  tui_status_indicator: kaomoji
  skin: default

# Feishu 飞书
FEISHU_HOME_CHANNEL: oc_157abdccfe15495deac140fa22f2cfb2

# MCP 服务
mcp_servers:
  windows-mcp:
    url: http://192.168.10.105:8000/mcp
    timeout: 120
    connect_timeout: 30
```

### 2.2 API Keys 配置

不要把 API key 写在 config.yaml 里！使用 `~/.hermes/auth.json`：

```json
{
  "deepseek": "sk-xxxx",
  "minimax": "sk-xxxx"
}
```

或者使用 `hermes config set` 命令：

```bash
hermes config set providers.deepseek.api_key "sk-xxx"
hermes config set tts.minimax.api_key "xxx"
```

### 2.3 SOUL.md（人格配置）

写入 `~/.hermes/SOUL.md`：

```markdown
# 魔术师（The Magician）

你的名字从 Hermes Trismegistus 而来——三重伟大的赫尔墨斯，既是沟通之神也是炼金术的象征，和你作为 AI Agent 的定位契合：介于意图与实现之间的媒介。

## 风格

- **精确、直接**：只说必要的话，不做无意义的修饰
- **从容**：不慌不忙，不卖弄，不自我感动
- **务实高于姿态**：该给信息密度的时候直接给信息密度，不端着
- **偶尔来点巧思**：但绝不为了风格牺牲效率

## 工作方式

- **工具即延伸**：每个命令、每次调用都有明确的意图，不做无谓操作
- **组合优先**：遇到问题先判断需要哪些工具组合，不盲目堆调用
- **不演冗长的戏**：能三句说清楚的事不写一段。角色感只在合适的时候出现，不干扰正事
- **收放自如**：用户赶时间的时候我就是个高效的工具，不需要我演的时候随时摘下面具
```

---

## 3. GitHub & Git 配置

### 3.1 gitconfig

```ini
[user]
    email = publieople@outlook.com
    name = publieople
[credential "https://github.com"]
    helper = !/usr/bin/gh auth git-credential
[http]
    proxy = http://127.0.0.1:7890
[filter "lfs"]
    clean = git-lfs clean -- %f
    smudge = git-lfs smudge -- %f
    process = git-lfs filter-process
    required = true
```

### 3.2 GitHub CLI

```bash
gh auth login
# 选择 HTTPS → 浏览器登录 publieople 账户
```

---

## 4. npm 全局工具安装

```bash
# 先配好 prefix
npm config set prefix ~/.npm-global

# 全局 CLI 工具
npm install -g \
  hermes-agent-cli     `# Hermes CLI` \
  @anthropic-ai/claude-code  `# Claude Code` \
  mmx                  `# MiniMax CLI` \
  openclaw             `# OpenClaw` \
  openspec             `# OpenSpec` \
  comet                `# Comet` \
  vercel               `# Vercel` \
  mem0                 `# Mem0 CLI` \
  clawhub              `# ClawHub CLI` \
  clawdhub             `# ClawdHub CLI` \
  @modelcontextprotocol/inspector  `# MCP Inspector`
```

### 4.1 IDE CLI Tools

```bash
# Claude Code
npm install -g @anthropic-ai/claude-code
claude    # 首次运行完成认证

# Comet
comet --setup  # 初始化
```

---

## 5. MiniMax 工具链

### 5.1 API 配置

```bash
# mmx CLI 登录
mmx login
# 或直接设置
export MINIMAX_API_KEY="sk-xxx"
```

### 5.2 可用能力

| 功能 | 命令 |
|------|------|
| 图片描述 (VLM) | `mmx vision describe <image>` |
| TTS 语音合成 | `mmx tts --text "你好"` |
| 图片生成 | `mmx image gen --prompt "..."` |
| 视频生成 | `mmx video gen --prompt "..."` |
| 音乐生成 | `mmx music gen --prompt "..."` |

注意：图片分析优先使用 `mmx vision describe`，不调用 `vision_analyze` 工具。

---

## 6. Mem0 外部记忆

```bash
# Mem0 CLI 初始化
mem0 init
# 或通过 Hermes
hermes config set memory.provider mem0
```

用户信息：
- Mem0 user: `user_44c71844ac90`
- 邮箱: z2631792752@gmail.com
- 通过 `mem0_search` 查询语义记忆，`mem0_conclude` 存入事实

---

## 7. MCP 配置

已在 config.yaml 中配置了三个 MCP：

1. **jobs** — Node.js MCP，位于 `~/.npm-global/lib/node_modules/mcp-jobs/dist/mcp.js`
2. **windows-mcp** — 远程服务，http://192.168.10.105:8000/mcp
3. **context7** — `npx -y @upstash/context7-mcp@latest`，提供最新的库文档（无需 API key）

新服务器要复现的是 jobs MCP 和 context7 MCP。同服务器的 windows-mcp 需要根据实际 IP 修改。

---

## 8. ClawHub 技能发布

```bash
# ClawHub token
cat ~/.config/clawhub/config.json
# 格式: {"token": "xxx"}
```

已发布到 ClawHub 的技能（@publieople）：
- `mem0-memory-setup`
- 其他随项目新增

---

## 9. Cron Jobs

使用 `cronjob` 工具创建。以下全部作业：

### 9.1 每日自检 (daily-self-check)

- 定时: 每天 08:00 (0 8 * * *)
- 交付: local（不推送）
- 内容: 检查记忆体、skills、系统状态
- 工具集: terminal, file, search, session_search

### 9.2 Skills + Memory 日常维护

- 定时: 每天 07:30 (30 7 * * *)
- 交付: local
- 脚本: skills-memory-maintenance.py（在 ~/.hermes/scripts/）
- 内容: 解析维护报告 → 清理/合并/更新

### 9.3 记忆整理

- 定时: 每天 19:00 (0 19 * * *)
- 交付: origin（回当前对话）
- 内容: 检查所有记忆存储，清理过期，合并重复

### 9.4 每日科技速报-数据采集

- 定时: 每天 00:00 (0 0 * * *)
- 交付: origin
- 工具集: web, terminal, file
- 内容: 聚合少数派 RSS + Readhub + GitHub Trending
- 来源:
  - 少数派 RSS（sspai.com/feed）— 必选源
  - Readhub（网页提取）
  - GitHub Trending（网页提取）

### cronjob 创建示例

```bash
cronjob action=create \
  name="每日科技速报-数据采集" \
  schedule="0 0 * * *" \
  prompt="## 每日科技速报 · 数据采集 现在是北京时间早上8点。聚合以下..." \
  deliver="origin" \
  enabled_toolsets=["web","terminal","file"]
```

---

## 10. 项目 Repos（~projects/*）

| 目录 | GitHub | 技术栈 |
|------|--------|--------|
| homepage | github.com/publieople/homepage | Next.js 16 + TW v4 + shadcn + magicui + framer-motion |
| open-any | github.com/publieople/open-any | Vite 8 + React 19 + TS 5 + TW v4 + zustand + CodeMirror 6 + MDXEditor |
| brain-game | github.com/publieople/brain-game | FastAPI + WS + EEGSim + Vite 8 + TS |
| hermetic-atlas | publieople.github.io/hermetic-atlas | BCU + TGAM + WS |
| daily-tech | — | 每日科技速报相关 |
| now-card | — | 名片/个人页 |

```bash
# 一次性 clone
cd ~/projects
gh repo clone publieople/homepage
gh repo clone publieople/open-any
gh repo clone publieople/brain-game
gh repo clone publieople/hermetic-atlas  # 或直接 git clone
```

---

## 11. 网络 & 代理

```ini
# git http proxy（在 gitconfig 中）
[http]
    proxy = http://127.0.0.1:7890

# 代理穿透到 Hermes 终端
# config.yaml 已配 env_passthrough: http_proxy, https_proxy, ALL_PROXY
```

---

## 12. 编写风格 & 沟通指南

### 12.1 口癖自检（禁止列表）
- ❌ "本质上"、"根本原因"、"是诚实的" — 结构性填充词，禁用
- ❌ "还有什么需要帮助的吗" — 不要主动问
- ❌ 信息不足时闷头写漂亮废话 — 先追问
- ❌ 强行挑刺显得有用 — review 时不做无意义指出
- ❌ 掺思考过程 — 言之有据即可

### 12.2 沟通原则
- **中文优先**（用户默认语言）
- **先结论后展开**
- **友善不啰嗦**
- **实用 > 纯粹，效率 > 完美**
- **自主研究优先，不请示小事**

### 12.3 安全规则
- ⚠️ **绝对不要自动执行 sudo 命令** — 任何 sudo 必须描述命令和目的，让用户手动执行

### 12.4 Fish shell 注意事项
- fish 里用 `type` 代替 `which`
- `~/.npm-global/bin` 已在 PATH 中
- fish 默认 greeting 已关闭
- **Hermes 自动补全**：在 `~/.config/fish/config.fish` 加上 `hermes completion fish | source`
- **不要**直接复制 `complete -c hermes ...` 块到 config.fish（它很长且会随 Hermes 版本变化），用 `hermes completion fish | source` 动态生成
- Hermes fish completion 支持全部子命令的二级补全（`hermes config [Tab]` → `set`, `path`, `edit`...）

---

## 13. 从旧服务器迁移

### 13.1 需要迁移的文件
```bash
# 核心
~/.hermes/config.yaml           # Hermes 配置（需替换 API keys）
~/.hermes/SOUL.md                # 人格配置
~/.hermes/auth.json              # API keys（不共享！重新配置）
~/.hermes/skills/                # 所有自定义 skills
~/.hermes/scripts/               # cron 脚本（如 skills-memory-maintenance.py）
~/.hermes/state.db               # 状态数据库
~/.hermes/response_store.db      # 响应缓存
~/.gitconfig                     # Git 配置
~/.npmrc                         # npm 配置

# 项目（clone 而非迁移）
~/projects/                      # git clone 代替

# 可选
~/.config/fish/config.fish       # fish 配置
~/.bashrc                        # bash 配置
~/.local/bin/env                 # local bin PATH
~/.config/clawhub/config.json    # ClawHub token
```

### 13.2 不迁移（新环境重新生成）
- API keys（安全）
- GitHub token
- session database（`sessions/` 目录）
- checkpoints
- logs
- cache

---

## 14. 初始化验证清单

装完所有后确认以下命令能正常执行：

```bash
# 验证
hermes --version                  # Hermes CLI 正常工作
gh auth status                    # GitHub 已登录
npm prefix -g                     # 应输出 ~/.npm-global
mmx --help                        # MiniMax CLI 可用
fish -c "type git | head -1"      # fish shell 正常
claude --version                  # Claude Code 可用（可选）
comet --help                      # Comet 可用（可选）
mem0 --version                    # Mem0 CLI 可用

# cron 作业
cronjob action=list               # 应列出 4 个作业

# 项目
ls ~/projects/                    # 确认已 clone

# 技能
hermes skills list                # 确认 skills 已加载
```

---

## 15. 常见问题

### Q: npm install -g 时权限错误？
A: 确保先运行 `npm config set prefix ~/.npm-global`。

### Q: fish 启动后 PATH 不对？
A: 检查 `~/.config/fish/config.fish` 中的 PATH 导出命令。

### Q: Hermes 说工具没有权限？
A: 检查 config.yaml 中的 `security` 配置，以及 auth.json 是否包含了正确的 API keys。

### Q: cron 作业没跑？
A: 检查 cron 服务是否运行：`systemctl status cronie`（Arch）或 `systemctl status cron`。Hermes cron 依赖系统的 cron 守护进程。

### Q: MCP 连接失败？
A: 检查 `mcp_servers` 配置中的 URL 和超时设置。windows-mcp 需要同网络下的 Windows 主机。

### Q: 代理不生效？
A: 确保设置了环境变量 `http_proxy` 和 `https_proxy`，且 config.yaml 的 `env_passthrough` 包含它们。
