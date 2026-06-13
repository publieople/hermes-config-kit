---
name: astrbot-deploy
description: 在 WSL/Linux 上通过 uv 部署 AstrBot QQ 机器人，对接已有 NapCatQQ
version: 1.1.0
author: Hermes Agent
tags: [astrbot, qq, napcat, onebot, deploy, uv]
prerequisites:
  commands: [uv, python3]
---

# AstrBot 部署（uv 方式）

在 WSL/Linux 上用 uv 一键部署 AstrBot，对接 Windows 上已运行的 NapCatQQ。

## 架构

```
QQ 群聊 ←→ NapCatQQ (Windows, 寄生 NTQQ)
                │
    WebSocket Client → ws://127.0.0.1:6199/ws
                │
                ↓
         AstrBot (WSL, uv 安装)
         WebUI: :6185, WS: :6199
```

NapCat 是 WS 客户端，AstrBot 是 WS 服务端。

## 1. 安装

```bash
# Python 3.12+ 必需
uv tool install astrbot --python 3.12

# 初始化（在目标目录）
mkdir -p ~/astrbot && cd ~/astrbot
yes Y | astrbot init
```

## 2. 启动

```bash
cd ~/astrbot
astrbot run
```

首次启动会自动下载 WebUI（~10MB）。成功时显示：
```
AstrBot vX.XX WebUI is ready
➜  Local: http://localhost:6185
➜  Initial username: astrbot
➜  Initial password: xxxxxxxxxx
```

## 3. 后台持久化

WSL 无 systemd user bus 时用 Python subprocess：

```python
import subprocess, os
proc = subprocess.Popen(
    ["/home/po/.local/bin/astrbot", "run"],
    cwd="/home/po/astrbot",
    env={**os.environ, "HOME": "/home/po"},
    start_new_session=True,
)
```

或写 systemd 服务单元到 `~/.config/systemd/user/astrbot.service`。

## 4. 密码管理

```bash
cd ~/astrbot
printf 'NewPass123!\nNewPass123!\n' | /home/po/.local/bin/astrbot password
```

⚠️ **密码修改后必须重启 AstrBot**（杀进程 → 重新启动）。密码要求至少一个大写字母。

## 5. 对接 NapCatQQ

### AstrBot 端（WebUI: :6185）
左边栏 → **机器人** → **+ 创建机器人** → **OneBot v11**：
- ID: 随意（如 `QQ`）
- 启用 ✅
- 反向 WS 主机地址: `0.0.0.0`
- 反向 WS 端口: `6199`
- Token: 留空

### NapCat 端（WebUI: :6099）
「网络配置」→ 修改/新建 WebSocket 客户端：
```
ws://127.0.0.1:6199/ws
```
⚠️ **必须带 `/ws` 后缀**。消息格式 Array，不需要 token。

验证：AstrBot WebUI → 控制台，看到蓝色 `aiocqhttp(OneBot v11) 适配器已连接` 即成功。

## 6. 配置 LLM

左边栏 → 配置 → 服务提供商 → 添加 → **OpenAI 兼容接口**：
- Base URL: `https://api.deepseek.com/v1`
- API Key: DeepSeek key
- 默认模型: `deepseek-chat`

## 7. 人格配置（Persona）

WebUI：左边栏 → 配置 → **人格情境** → 新建/切换。社区最佳实践见 `references/persona-magician.md`。

### QQ 内切换人格（最快）

在群聊/私聊发指令即可切换，无需开 WebUI：

```
/persona list              → 列出所有可用人格
/persona <人格名>          → 切换到指定人格
/persona unset             → 取消人格（恢复默认）
/persona view <人格名>     → 查看某个人格的详细信息
/reset                     → 切人格后清空上下文（建议切完就发）
```

### 人格模板来源

- **jiupamiao.asia**（玖帕喵）：提示词模板市场，有成熟的"拟人模板"（如第二版拟人模板 `market?id=509`），可直接参考结构（社会关系、社交距离、对话安全等模块）
- AstrBot 插件市场搜 `portrayal`、`Private Companion` 等辅助人格连续性

### 核心要点

- **身份用"你"**："你是损友"比"角色是损友"有效
- **预设对话是关键**：给出 5-8 组"用户说→你回"的理想示例，比长篇描述更有效
- **开启识别群员**：配置 → 大语言模型 → 勾选「识别群员」
- **开启日期时间提示**：让 bot 有时间感

## 与 Hermes NapCat 的对比

WebUI → 插件市场，搜以下关键字安装：

| 插件 | 作用 |
|------|------|
| `Self-Learning` | 自动学习群聊风格、黑话、社交关系（越聊越像人） |
| `Private Companion` | 人格连续性、关系识别、长期记忆 |
| `Multimodal Router` | 图片自动路由到有视觉能力的模型（DeepSeek 不支持图片） |
| `Meme Manager` | 表情包管理 |

## 与 Hermes NapCat 的对比

| | Hermes NapCat | AstrBot |
|---|---|---|
| WS 方向 | Hermes 是服务端 | AstrBot 是服务端 |
| 端口 | 8646 | 6185(UI) + 6199(WS) |
| 部署方式 | 代码级 hack | `uv tool install` |
| 更新风险 | 每次 update 需修复 | 无 |
| Web 面板 | 无 | ✅ |

## 踩坑

- **`uv tool install` 输出被抑制**：Hermes 后台 bash 不显示 uv 进度条。用 `HOME=/home/po /home/po/.local/bin/uv ...` 绝对路径 + 前台运行。
- **Docker 国内拉镜像超时**：直接用 uv，不走 Docker。DaoCloud 等镜像代理也可能超时。
- **Docker 国内拉镜像超时**：直接用 uv，不走 Docker。
- **密码修改后不生效**：必须重启 AstrBot 进程才能加载新密码。密码要求至少一个大写字母。
- **NapCat WS URL 必须带 `/ws`**：`ws://127.0.0.1:6199/ws`，少写后缀就 400。
- **端口默认 6199 不是 6186**：AstrBot 官方文档默认的 aiocqhttp 端口是 6199。
- **UI 路径变更**：新版本中「消息平台」在「机器人」菜单下，选「OneBot v11」而非单独 aiocqhttp。

### 配置文件相关（高频陷阱）
- **Hermes `read_file`+`write_file` 会破坏 JSON**：`read_file` 返回带行号前缀（`123|content`）的文本，`write_file` 会原样写入。**绝对不要**用于编辑 JSON 配置文件——读用 `execute_code` 中的 `open`，写用 `execute_code` 中的 `json.dump`。此链导致 `cmd_config.json` 被写入行号前缀，AstrBot 启动崩溃。详见 `hermes-file-pitfalls` skill。
- **AstrBot 会静默重建损坏的 config**：如果 `cmd_config.json` 无法解析，AstrBot 启动时**不会报错而是直接生成默认配置**，导致你手动写的所有设置丢失。写完配置后务必用 `python3 -c "import json; json.load(open('data/cmd_config.json','rb'))"` 验证合法性。
- **JSON 文件的 BOM 头**：AstrBot 的 `cmd_config.json` 自带 UTF-8 BOM。`execute_code` 沙箱可能因 Python 版本差异报 BOM 错误——这不代表文件损坏，AstrBot 自己能正常读取。

### 插件渲染相关

- **Pillow 渲染插件需要 CJK 字体**：如 `astrbot_plugin_bangumi_enhance` 等生成图片的插件，依赖 NotoSansCJK 字体。插件初始化时会后台下载，但国内网络直连 GitHub 必失败 → 字体目录为空 → Pillow 降级到 `load_default()` → 渲染白板。解决：手动装字体或软链系统已有中文字体到插件 fonts 目录。详见 `references/bangumi-plugin-rendering.md`。

### 数据库相关
- **`begin_dialogs` / `tools` / `skills` 必须是合法 JSON**：`personas` 表中这三个 JSON 列**不能是空字符串 `""`**，必须是 `"[]"` 或 `"{}"`。空字符串会导致 AstrBot 启动时 `json.loads("")` 抛出 `JSONDecodeError` 崩溃。插入数据时务必用 `json.dumps()` 而非硬编码。
- **`begin_dialogs` 格式兼容问题**：某些 AstrBot 版本对预设对话格式敏感——存入 `[{role, content}]` JSON 后 LLM 调用时可能报 `validation error for Message`。报此错时**直接清空字段**（`UPDATE personas SET begin_dialogs='[]'`），让用户通过 WebUI 手动填预设对话。不要再反复尝试不同格式。
- **MiniMax M3**（2026-06-01 发布）是原生多模态模型，可作为 AstrBot 的聊天+看图统一方案，避免多模态路由插件。详见 `references/minimax-multimodal.md`。
- **写数据库后必须重启**：直接 SQLite 写入不会热加载，需要 kill 进程重启 AstrBot。
- **FutureTask 的 note 要自包含**：Agent 被唤醒时只有 note 文本，没有原会话上下文。note 必须包含完整的检查步骤和数据路径，不能依赖"之前的对话中提过"。
- **bangumi 订阅用内置服务**：不需要 Hermes 的 cronjob/send_message 工具。AstrBot 自己就是 QQ bot——Agent 输出文本即自动推送到群。番剧更新检查用 `curl` + `python3 -c` 行内脚本即可。

### 用户偏好
- **用户说"我来手动配置"时立即停手**：当用户明确表示要自己通过 WebUI 操作时，不要再碰数据库/配置文件。只确保服务在运行就行。
- **`begin_dialogs` 的预设对话格式报错时停止深入**：AstrBot 对不同版本对 `begin_dialogs` 格式要求不一致（某些版本期望纯文本而非 JSON），一旦报 `validation error` 直接清空该字段让用户手动配，不要反复尝试修复。

## 直接配置人格（写数据库，绕过 WebUI）

WebUI 的「人格情境」最终存储在 SQLite 数据库 `/home/po/astrbot/data/data_v4.db` 的 `personas` 表中。可直接写入：

```python
import sqlite3, json, datetime

conn = sqlite3.connect("/home/po/astrbot/data/data_v4.db")
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

system_prompt = "完整的系统提示词..."
begin_dialogs = [
    {"role": "user", "content": "用户说的示例"},
    {"role": "assistant", "content": "bot 应该回的示例"},
]

conn.execute("""
    INSERT INTO personas (created_at, updated_at, persona_id, system_prompt,
                          begin_dialogs, tools, skills, custom_error_message,
                          folder_id, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (now, now, "persona-id", system_prompt,
      json.dumps(begin_dialogs, ensure_ascii=False),
      json.dumps({}), json.dumps({}), "", None, 0))
conn.commit()
conn.close()
```

然后修改 `cmd_config.json` 中的 `provider_settings.default_personality` 为对应的 `persona_id`，重启 AstrBot。

## AstrBot Skills 管理

AstrBot v4.13+ 支持 Anthropic Skills 格式。Skills 存放在 `~/astrbot/data/skills/`，两种路径格式均支持：

```
~/astrbot/data/skills/
├── <skill名>-<version>/        ← 市场安装（带版本号 + _meta.json）
│   ├── SKILL.md
│   ├── _meta.json
│   └── skill-card.md
├── <skill名>/                   ← 本地手动安装（不带版本号）
│   ├── SKILL.md
│   ├── scripts/                 ← 可选：可执行脚本
│   ├── .venv/                   ← 可选：Python 虚拟环境
│   └── references/              ← 可选
└── skills.json                  ← 注册表：{"skills":{"<name>":{"active":bool}}}
```

### ⚠️ `npx skills add` 不适用于 AstrBot

`npx skills add <repo>` 命令输出会宣称 "symlinked: AstrBot"，但**实际上不会更新 `skills.json`**，skill 在 AstrBot 中不可用。该 CLI 主要面向 OpenClaw、Claude Code 等 agent。

**正确做法**：手动复制 SKILL.md + 更新 skills.json，见下方"直接安装"。

### Python 依赖：始终用 venv

PEP 668 阻止系统级 pip install。AstrBot skill 需要 Python 库时，在 skill 目录下创建 venv：

```bash
SKILL_DIR="$HOME/astrbot/data/skills/<skill名>"
python3 -m venv "$SKILL_DIR/.venv"
"$SKILL_DIR/.venv/bin/pip" install <包名>
```

脚本中通过 `SKILL_DIR/../.venv/bin/<command>` 引用 venv 内的工具。**不要尝试 `uv pip install --system` 或 `pip install` 到全局**，都会失败。

### 直接安装 Skill（无需 WebUI）

```bash
VERSION="1.0.0"
SKILL_NAME="<skill名>"
SKILL_DIR="$HOME/astrbot/data/skills/${SKILL_NAME}-${VERSION}"

mkdir -p "$SKILL_DIR"

# 下载 SKILL.md（从 GitHub raw、skills.sh、SkillHub 等市场）
curl -sL "https://raw.githubusercontent.com/<作者>/<仓库>/main/SKILL.md" \
  -o "$SKILL_DIR/SKILL.md"

# 写 _meta.json
cat > "$SKILL_DIR/_meta.json" << EOF
{"ownerId":"local","slug":"${SKILL_NAME}","version":"${VERSION}","publishedAt":$(date +%s)000}
EOF

# 注册
python3 -c "
import json
with open('$HOME/astrbot/data/skills.json') as f:
    c = json.load(f)
c['skills']['${SKILL_NAME}-${VERSION}'] = {'active': True}
with open('$HOME/astrbot/data/skills.json', 'w') as f:
    json.dump(c, f, indent=4, ensure_ascii=False)
"
```

### 重启 AstrBot（安全方法）

⚠️ **AstrBot 不能直接 `pkill astrbot` 重启自己**——agent 进程跑在 AstrBot 内部，直接 kill 会把自己也杀了。用延时脚本分离进程：

```bash
cat > /tmp/astrbot_restart.sh << 'SCRIPT'
#!/bin/bash
sleep 2
pkill -f 'astrbot run' 2>/dev/null
sleep 3
cd ~/astrbot && nohup astrbot run > data/astrbot.log 2>&1 &
SCRIPT
chmod +x /tmp/astrbot_restart.sh
nohup /tmp/astrbot_restart.sh > /dev/null 2>&1 &
```

### 从 OpenClaw/Claude Code 适配 Skill 到 AstrBot

外部 skill（来自 ClawHub、skills.sh、GitHub 等）通常面向 OpenClaw 或 Claude Code 环境，需要以下适配：

**路径映射：**

| 原始路径 | AstrBot 路径 |
|----------|-------------|
| `~/workspace/` | `~/astrbot/data/` |
| `~/.openclaw/workspace/` | `~/astrbot/data/` |
| `$HOME/workspace/knowledge/` | `~/astrbot/data/transcripts/` 或自定义 |
| `scripts/`（skill 内） | `$(dirname "$0")/..` 推导 SKILL_DIR |

**功能替换：**

| OpenClaw 功能 | AstrBot 替代 |
|---------------|-------------|
| `openclaw cron add` | AstrBot FutureTask（自然语言创建） |
| Discord 发文件 | QQ 群发消息（无文件附件时发摘要） |
| `knowledge-rag` 索引 | 手动 `cat` 读取 + Agent 总结 |
| `clawhub install` | 手动复制 + skills.json 注册 |

**SKILL.md 重写要点：**
- 触发条件改为 QQ 群场景（"发送 B站链接"而非 Discord 命令）
- 输出格式适配 QQ（纯文本，避免复杂表格和超长内容）
- 去掉对 OpenClaw 专用工具（`openclaw cron`、Discord webhook、`knowledge-rag`）的引用
- 脚本中的输出目录改为 `~/astrbot/data/` 子目录

**示例：** 从 ClawHub 获取 `bilibili-auto-transcript`，适配为 AstrBot skill：
```bash
# 1. 获取源 skill
clawhub install bilibili-auto-transcript  # → ~/.openclaw/workspace/skills/...

# 2. 复制核心脚本
cp -r scripts/ ~/astrbot/data/skills/bilibili-transcript/scripts/

# 3. 修改脚本中的路径 (OUTPUT_DIR, SKILL_DIR)
# 4. 写 AstrBot 版 SKILL.md（QQ 群触发 + 简洁回复格式）
# 5. 创建 venv 装依赖
python3 -m venv ~/astrbot/data/skills/bilibili-transcript/.venv
# 6. 注册并重启
```

### Skill 市场来源

`find-skills` skill 内置了 6 个搜索来源，按速度和质量排序：

| 来源 | 规模 | 特点 |
|------|------|------|
| skills.sh | 350K+ | 全球最大，`npx skills` CLI，Vercel 背书 |
| ClaudeSkills.info | 658+ | 人工精选，质量高 |
| SkillHub (`skillhub.cn`) | — | 国内加速（腾讯云广州 COS），`skillhub search/install` CLI |
| vercel-labs/anthropics/obra | — | 官方 Awesome 合集，免搜索直接翻目录 |
| ClawHub | 13.7K+ | VirusTotal + Socket 安全审计 |
| GitHub 代码搜索 | 全网 | 兜底方案 |

### 现有参考 Skill

| Skill | 用途 |
|-------|------|
| `find-skills` | 自动搜索 6 个 skill 市场并安装到 AstrBot |
| `skill-vetter` | 安装前安全检查 |
| `writing-skills` | 怎么写好 Skill（TDD 方法论） |
| `clash-proxy` | Clash 代理管理（`http://127.0.0.1:7890`） |
| `bangumi-subscription` | 番剧订阅 + FutureTask 定时推送 |
| `hermes-file-pitfalls` | Hermes 文件操作避坑（read_file 行号污染等） |
| `markdown-to-image-plugin` | Markdown 转图片插件（正则问题 + 自定义样式） |
| `astrbot_plugin_bangumi_enhance` | 番剧查询插件（united-pooh），Pillow 渲染需 CJK 字体，详见 `references/bangumi-plugin-rendering.md` |

---

## Whisper (Local) 语音转文字 + GPU 加速

AstrBot 内置 `openai_whisper_selfhost` 提供商会自动加载 openai-whisper 模型。**源码只认 `cpu` 和 `mps`，不认 `cuda`**，需手动 patch。

### 1. 装 CUDA 版 torch + whisper

```bash
ASTRBOT_PY=$(/home/po/.local/bin/uv python find 3.12)
uv pip install --python /home/po/.local/share/uv/tools/astrbot/bin/python \
  --index-url https://download.pytorch.org/whl/cu128 torch
uv pip install --python /home/po/.local/share/uv/tools/astrbot/bin/python \
  -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper
```

### 2. 源码加 CUDA 支持

编辑 `/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/whisper_selfhosted_source.py`，在 `_resolve_device()` 最前面加：

```python
if self.device == \"cuda\":
    import torch
    if getattr(torch.cuda, \"is_available\", None) and torch.cuda.is_available():
        return \"cuda\"
    logger.warning(\"Whisper 已配置为使用 CUDA，但当前环境不可用，将回退到 CPU。\")
    return \"cpu\"
```

### 3. 配置 cmd_config.json

⚠️ **该文件有 UTF-8 BOM**，Python 读时必须用 `encoding='utf-8-sig'`。

```python
import json
with open('data/cmd_config.json', encoding='utf-8-sig') as f:
    conf = json.load(f)

# 改 provider 内嵌列表中的 whisper_selfhost 条目
for p in conf['provider']:
    if p.get('id') == 'whisper_selfhost':
        p['model'] = 'small'           # RTX 4070 8GB → small
        p['whisper_device'] = 'cuda'   # 不是 cpu 不是 mps

# 启用 STT
conf['provider_stt_settings'] = {'enable': True, 'provider_id': 'whisper_selfhost'}

with open('data/cmd_config.json', 'w', encoding='utf-8-sig') as f:
    json.dump(conf, f, indent=2, ensure_ascii=False)
```

### GPU 模型选择

| GPU 显存 | 模型 | 速度 |
|----------|------|------|
| ≥12GB | medium | ~0.45x 实时 |
| 6-12GB | **small** | ~0.21x 实时 |
| <6GB | base | — |

> WSL CUDA 下 medium 反而比 small 慢（开销大），4070 8GB 选 small。

### 验证

```bash
/home/po/.local/share/uv/tools/astrbot/bin/python -c "
import torch; print('CUDA:', torch.cuda.is_available(), torch.cuda.get_device_name(0))
import whisper; print('whisper OK')
"
```

### 注意

- **WebUI 下拉框可能仍只显示 CPU**（前端硬编码），但配置文件写 `cuda` 后端能认。别在 WebUI 里改这个 provider。
- **`uv tool update` 会覆盖源码 patch**，更新后需重新 patch。
- **stt_health_check.wav 缺失**：PyPI wheel 中不包含 `samples/stt_health_check.wav`，测试会报"文件不存在"。用 ffmpeg 生成一个 16kHz 单声道 WAV 放到 `/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/samples/`。
- **systemctl 重启**：`sudo systemctl restart astrbot`（如已配 systemd service）。

### 速度优化

- **清华 PyPI 镜像**：国内网络 pip 下载极慢，加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` 秒装。
- **PyTorch CUDA 索引**：`--index-url https://download.pytorch.org/whl/cu128`，不能和 `-i` 混用。`uv pip install` 报 `cannot be used multiple times` → 分两次调用。
- **Python 3.14 避坑**：Arch 系统 Python 3.14 下很多包（openai-whisper 等）因 `pkg_resources` 移除而无法安装。**始终用 `uv venv --python 3.12`**。
- **Python 3.14 避坑**：Arch 系统 Python 是 3.14，但很多包（openai-whisper、setuptools 等）在 3.14 下因 `pkg_resources` 移除而无法安装。**始终用 `uv venv --python 3.12` 或 `uv tool install --python 3.12`**，别和系统 3.14 死磕。

### B站视频转录（bilibili-transcript）

详见 `references/bilibili-transcript.md`。核心要点：B站 412 反爬 → 加 `Origin` 头；Whisper 不要强设 `--language zh`；必须 Python 3.12 venv。

## FutureTask 定时任务

AstrBot v4.14+ 支持主 Agent 管理定时任务。用户说自然语言即可触发：

> "帮我创建定时任务：每周五 23:00 检查番剧更新"
> "每天早上 8 点提醒我开会"

Agent 会调用内置的 `create_future_task` 等工具。任务到时间后 AstrBot 自动唤醒 Agent，执行 `note` 中的 prompt，结果通过 `send_message_to_user` 推送到原会话。

**支持的推送平台**：OneBot v11（QQ）、Telegram、Slack、飞书、Discord、Misskey、Satori。

**⚠️ 所有 FutureTask 都是 LLM 推理模式**——Agent 收到 note 文本后自主决策。没有"直接发固定消息"的硬执行模式。适合需要智能判断的场景（如检查 API 是否有更新），不适合纯确定性操作。

---

## 从 Hermes 迁出 NapCat（完全清理）

当你决定不再用 Hermes 接 QQ，而是换 AstrBot 时：

```bash
# 1. 禁用 NapCat
sed -i 's/NAPCAT_ENABLED=true/NAPCAT_ENABLED=false/' ~/.hermes/.env
sed -i '/^NAPCAT/d' ~/.hermes/.env  # 或直接清掉所有 NapCat 行

# 2. 停止 gateway
pkill -f 'gateway run'

# 3. 重置到官方 main（如果之前用了 fork）
cd ~/.hermes/hermes-agent
git fetch origin
git reset --hard origin/main
git remote remove upstream 2>/dev/null
git remote remove moeover 2>/dev/null
git remote remove fork 2>/dev/null
git remote set-url origin https://github.com/NousResearch/hermes-agent.git

# 4. 同步个人 fork（如果 fork 存在）
git remote add fork https://github.com/<username>/hermes-agent.git
git push fork main --force
git remote remove fork

# 5. 重启 gateway（systemd 自动重启，或手动）
```

清除后 gateway 会以 2 个平台运行（api_server + feishu），**端口 8646 释放**，NapCat 不再连接。

---

## cmd_config.json 关键字段

| 字段 | 路径 | 说明 |
|------|------|------|
| `default_personality` | `provider_settings` | 设为 persona_id（如 `"magician"`） |
| `identifier` | `provider_settings` | 识别群员，设为 `true` |
| `datetime_system_prompt` | `provider_settings` | 日期时间提示，设为 `true` |
| `reply_with_mention` | `platform_settings` | 只看@才回复，设为 `true` |
| `default_provider_id` | `provider_settings` | 默认模型 ID |
