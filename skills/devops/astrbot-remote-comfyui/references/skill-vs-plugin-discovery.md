# ComfyUI 集成路径识别（plugin / skill / 直调）

用户说"给 AstrBot 接 ComfyUI"或"加 ComfyUI 能力"时，先 30 秒定位它现在用的是哪条路。

## 0. 决策指针

| 用户措辞 | 含义 | 走哪 |
|---|---|---|
| "找一下 skill" / "skill 市场有什么" | **AstrBot `data/skills/`**（或 Hermes `~/.hermes/skills/`）| 路径 B |
| "有没有现成的 AstrBot 插件" | **AstrBot Plugin Marketplace**（`plugins.astrbot.app`）| 路径 A |
| "AstrBot 直接调 ComfyUI，不写插件" | docs-only skill | 路径 B |
| "装个 ComfyUI 插件" / "找插件" | plugin marketplace | 路径 A |

**口误检测**：用户说"skill 市场"，先确认是指 AstrBot skill 还是 Hermes skill，两个目录完全独立（一个在 `/home/po/astrbot/data/skills/`，一个在 `/home/po/.hermes/skills/`）。

## 1. 探测已有路径

```bash
# 当前 AstrBot 工作目录（uv tool 装的话是 /home/po/astrbot/）
ASTRBOT_DIR=$(readlink /proc/$(pgrep -f "astrbot run" | head -1)/cwd 2>/dev/null)
[ -z "$ASTRBOT_DIR" ] && ASTRBOT_DIR="/home/po/astrbot"

# A. 已装的 ComfyUI 插件
ls "$ASTRBOT_DIR/data/plugins/" | grep -i comfy

# A'. 已装的 ComfyUI 插件配置
ls "$ASTRBOT_DIR/data/config/" | grep -i comfy

# B. 已装的 skill
ls "$ASTRBOT_DIR/data/skills/" | grep -i -E "comfy|anima|stable|sd"
```

**如果只有 plugin，没 skill**：用户当前走的是 A 路径，问要不要加 B 路径。

**如果两者都有**：skill 是用户自己加的 LLM-direct 补充，plugin 是历史包袱——可能没在用。

**如果只有 skill**：纯文档路径，最干净。

## 2. 一个 AstrBot skill 多大才算合规

最小公约数：
- `<slug>/SKILL.md` — 有 YAML frontmatter + `## 何时调用` + 具体调用示例
- `<slug>/_meta.json` — `{"ownerId", "slug", "version", "publishedAt"}`

**够了**。AstrBot v4 loader 不要求 `requirements.txt`、不要求 `__init__.py`、不要求 metadata.yaml、**不要求 Python 代码**。

例：`data/skills/comfyui-anima-t2i/`（user 自维护）只有 SKILL.md + _meta.json 两文件，LLM 直接 curl ComfyUI，能跑。

## 3. skills.json vs _meta.json vs metadata.yaml

| 文件 | 谁读 | 作用 | 缺了 |
|---|---|---|---|
| `data/skills.json` | AstrBot 启动 | 全局 skill 注册表 | skill 不会被发现 |
| `<slug>/_meta.json` | AstrBot skill loader | skill 元数据 | 显示在 WebUI 标红或不显示 |
| `<plugin>/metadata.yaml` | AstrBot plugin loader | AstrBot **插件**（不是 skill）的元数据 | 与 skill 无关 |

**三个文件三个 loader，别混**。`data/skills.json` 是用户手动维护或 AstrBot 自动生成；skill 目录下只需要 `_meta.json`。

## 4. 从"插件废"到"skill 起"的最小迁移

用户装过插件（cjxzdzh / easy_comfyui / promax / YuanBao / Lumingya...），后来嫌麻烦想换，纯 skill 路线：

```bash
# 1. 找到现有 skill 模板（user 自维护的）
ls $ASTRBOT_DIR/data/skills/ | grep -i comfy

# 2. 跟用户确认工作流 JSON 文件放哪里
#    一般两种做法：
#    - skill 内的 workflows/ 子目录（skill 自包含）
#    - 用户项目根的 workflows/（共享）

# 3. 在 AstrBot WebUI「技能市场」页面，启用该 skill

# 4. 给 LLM 一条触发测试："画一个抽烟的白毛猫娘"
#    看 journalctl -u astrbot --since "5 minutes ago"
#    期望看到 "LLM 决定调用 SKILL: comfyui-anima-t2i" 之类
```

**如果 LLM 不调**：大概率是 skill 描述的 `description` 字段没把触发词写全（"画"/"生成"/"文生图"/"复刻"等信号词都得在 description 里）。LLM 是按 description 做 trigger 匹配的，不是按 skill 名字。
