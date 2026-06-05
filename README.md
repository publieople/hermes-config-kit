# Hermes Config Kit

> **Publieople 的 Hermes 数字孪生** — 238 Skills · 完整配置 · 自同步备份
>
> `git clone` → `./setup.sh` → 在任何设备上复现完全相同的魔术师 Agent

---

## 这是什么？

这不是一个"starter template"。这是 **一个 AI Agent 的完整基因序列**——包含了 Publieople 的 Hermes 在数千次对话中积累的全部知识、工作流和配置。

| 资产 | 规模 |
|------|------|
| **Skills** | 238 个，覆盖 39 个技能分类 |
| **配置** | 615 行 config.yaml（v23），完整 SOUL.md 人格 |
| **Cron Jobs** | 3 个定时任务（自检 + 维护 + 自动同步） |
| **MCP 服务器** | 3 个（Context7 文档 + Jobs 搜索 + Windows 集成） |
| **环境配置** | Shell、Git、npm 全局工具全套模板 |

**仓库自动更新**：每周日 06:00 cron job 自动检测变更 → 脱敏 → commit → push。

---

## 核心能力

这个 Agent 不是单纯的"编码助手"。它是一个完整的数字工作台。

### 🏗️ 软件工程

| 能力 | 技能 |
|------|------|
| **全栈开发** | Next.js 16 + React 19 + Tailwind v4 + shadcn/ui + FastAPI + Vue3 |
| **规范驱动开发** | Comet（8 技能完整 SDLC）、OpenSpec（spec → propose → build → archive） |
| **测试驱动** | TDD 红绿重构循环、Code Review（spec + quality 双阶段） |
| **调试** | 系统化四阶段调试、Node.js Inspector、Python debugpy |
| **子代理编排** | 并行 Agent 派发、Kanban 任务队列、Git Worktree 隔离 |
| **代码审查与部署** | PR 工作流、CI/CD、Python 生产部署、Alembic 数据库迁移 |

### 🎨 创意与视觉

| 能力 | 技能 |
|------|------|
| **AI 图像/视频** | ComfyUI API（Flux2.2 角色一致性、Wan FLF2V 视频生成、AI 漫剧管线） |
| **创意编程** | p5.js 生成艺术、ASCII Art/Video、Pixel Art、Manim 数学动画 |
| **前端设计** | shadcn/ui + magicui 组件系统、54 种设计系统参考、Excalidraw 手绘风格 |
| **信息可视化** | 架构图（SVG）、信息图（21×21 布局×风格）、知识漫画 |
| **视频制作** | HTML-to-MP4 渲染、Remotion 动画、ASCII 视频转换 |

### 📊 数据与 AI/ML

| 能力 | 技能 |
|------|------|
| **深度学习** | PyTorch Lightning、Transformers、HuggingFace Hub、vLLM 推理 |
| **模型训练** | Axolotl 微调、TRL 强化学习、Unsloth 加速、DSPy 声明式编程 |
| **模型推理** | llama.cpp GGUF、vLLM 高吞吐、Outlines 结构化输出 |
| **数据科学** | pandas、polars、scikit-learn、Jupyter 实时内核、seaborn 可视化 |
| **MLOps** | Weights & Biases 实验追踪、LM Evaluation Harness 基准测试 |

### 🧬 科学研究

| 能力 | 技能 |
|------|------|
| **生物信息** | 单细胞分析（Scanpy/scVI-tools）、基因调控网络、分子动力学（OpenMM） |
| **化学信息** | RDKit 分子处理、DeepChem 分子 ML、DiffDock 分子对接、药物相似性过滤 |
| **学术写作** | 文献综述、论文写作、LaTeX 海报、Grant 申请书、同行评审 |
| **可视化** | 科学图表生成、发表级图形、统计可视化 |

### 🔗 平台集成

| 能力 | 技能 |
|------|------|
| **飞书/Lark** | 文档、表格、日历、审批、任务、IM、知识库 — 完整 API 覆盖 |
| **Notion** | 笔记、数据库、CMS、GitHub 双向同步、内容提取 |
| **GitHub** | Issues、PR、Code Review、CI/CD、仓库管理 |
| **Google Workspace** | Gmail、Calendar、Drive、Docs、Sheets |
| **其他** | Airtable、Linear、Obsidian、Spotify、YouTube、Bilibili |

### 🤖 Agent 元能力

| 能力 | 技能 |
|------|------|
| **记忆与学习** | 持久化跨会话记忆（Mem0）、自改进（skills 从经验中学习）、会话搜索 |
| **自举** | `hermes-bootstrap` 完整复现、`hermes-config-sync` 自动备份 |
| **多模态** | MiniMax VLM 视觉理解、TTS 语音合成、STT 语音识别 |
| **定时任务** | Cron 调度、Webhook 触发器、每日自动化（科技速报、自检、维护） |

---

## 明星技能

这些是最常用、最独特的技能：

### Comet 开发工作流（25 次 · 8 个技能）
完整的 SDLC 微框架：`comet-open`（探索）→ `comet-design`（深度设计）→ `comet-build`（实现）→ `comet-verify`（验证）→ `comet-archive`（归档）。另含 `comet-tweak`（小改快捷）和 `comet-hotfix`（Bug 修复）。

### Notion 记账系统（29 次）
完整的个人财务系统。支付宝↔余额宝双向流水、多级分类、资金流转标签、自动汇总。附带 `notion-github-sync`、`notion-content-extraction`、`notionnext-content-sync-diagnostics`。

### MiniMax 视觉管线（7 次）
用 MiniMax 专用 VLM 端点替代内建 vision 工具。`mmx vision describe` 支持 WebP/JPEG/PNG。搭配 TTS（speech-2.8-hd）和 ComfyUI 图像生成。

### Shadcn/MagicUI 开发（17 次）
React/Next.js UI 开发工作流。shadcn/ui 组件安装 → magicui 动效组件 → Tailwind v4 样式 → 像素级对齐检查。

### Web 视频演示（16 次）
文章/口播稿 → 16:9 网页演示 → 可选口播音频合成。点击驱动翻页，可导出为视频。

### Web 设计工程（12 次）
高质量视觉 Web artifact（HTML/CSS/JS）。GPU 粒子背景、CRT 扫描线、霓虹渐变边框、动态网格。

### 规范驱动初始化（33 次）
从零搭建全栈项目的完整流程：spec → 架构设计 → 数据库 schema → API 设计 → 前端组件树 → 分步实现。

### 每日科技速报（8 次）
自动化采集少数派 RSS + Readhub + GitHub Trending → Markdown 摘要 → 可选视频生成。

### Lark/飞书全套（63 个技能）
最完整的飞书集成：文档（创建/编辑/搜索）、多维表格、日历、审批、任务、即时通讯、知识库、邮箱、OKR、视频会议 — 全部 API 覆盖。

---

## 技能分类总览

| 分类 | 数量 | 代表技能 |
|------|------|----------|
| **openclaw-imports** | 63 | Lark 全套（doc/sheets/calendar/task/im/wiki/mail/okr/vc）、docx、pdf、xlsx、smart-search |
| **creative** | 20 | comfyui、p5js、ascii-art、ascii-video、manim-video、pixel-art、excalidraw、architecture-diagram、baoyu-* |
| **software-development** | 19 | plan、tdd、code-review、systematic-debugging、subagent、spike、writing-plans、node-inspect、python-debugpy |
| **productivity** | 18 | notion-bill、notion-github-sync、airtable、google-workspace、linear、maps、ocr、pptx、daily-digest-pipeline |
| **mlops** | 15 | minimax-vision、huggingface-hub、llama-cpp、vllm、transformers、pytorch-lightning、dspy、fine-tuning-trl |
| **devops** | 13 | hermes-bootstrap、kanban-orchestrator/worker、mem0-memory-setup、skill-publishing、webhook、cloakbrowser |
| **superpowers** | 9 | brainstorming、using-git-worktrees、writing-skills、executing-plans、dispatching-parallel-agents、verification |
| **comet** | 8 | comet-open/design/build/verify/archive/hotfix/tweak + comet 总入口 |
| **github** | 6 | auth、code-review、issues、pr-workflow、repo-management、codebase-inspection |
| **media** | 7 | bilibili-video-summary、spotify、youtube-content、gif-search、songsee、heartmula、html-video-rendering |
| **research** | 5 | arxiv、llm-wiki、polymarket、blogwatcher、research-lookup |
| **autonomous-ai-agents** | 5 | claude-code、codex、opencode、hermes-agent、kanban-codex-lane |
| **openspec** | 4 | explore、propose、apply-change、archive-change |
| **comfyui-api** | 4 | flux2-klein-character-consistency、wan2.2-flf2v-pipeline、ai-drama-pipeline-route-planning |
| **gaming** | 3 | bci-game-development、minecraft-modpack-server、pokemon-player |
| **apple** | 5 | apple-notes、apple-reminders、findmy、imessage、macos-computer-use |
| **api** | 2 | liciyuan-api（随机图片）、xingzhige-api（50+ 免费 API） |
| **其他** | 10+ | yuanbao、red-teaming/godmode、social-media/xurl、smart-home/openhue、career-job-hunting… |

另外还有 **90+ 科学计算技能**（从 Hermes 继承）：Scanpy、RDKit、PyTorch Geometric、DeepChem、BioPython、Astropy、Qiskit... 覆盖生物信息、化学、物理、天文、量子计算等领域。

---

## 快速开始

```bash
# 1. 安装 Hermes（如未安装）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Clone + Setup
git clone https://github.com/publieople/hermes-config-kit.git
cd hermes-config-kit
chmod +x setup.sh
./setup.sh

# 3. 启动
hermes
```

`setup.sh` 会交互式询问 API Key，然后自动复制所有配置、skills、脚本。

---

## 目录结构

```
hermes-config-kit/
├── config.yaml              # Hermes 完整配置（615行，API key 已脱敏）
├── SOUL.md                  # 魔术师人格 + 工作方式
├── .env.example             # 所需环境变量清单
├── setup.sh                 # 一键安装脚本
├── skills/                  # 238 skills（39 分类）
├── scripts/
│   ├── sync-back.sh         # 自同步：检测变更 → 脱敏 → commit → push
│   └── skills-memory-maintenance.py
├── cron/jobs.yaml           # 3 个定时任务定义
├── mcp/servers.yaml         # MCP 服务器配置模板
├── shell/                   # bashrc / fish config / gitconfig 模板
├── npm/global-packages.txt  # npm 全局工具清单
└── .github/workflows/       # CI：自动检查敏感信息泄露
```

---

## 自同步机制

仓库自带**自动备份**——不需手动维护：

```
Cron: hermes-config-sync
Schedule: 每周日 06:00（Asia/Shanghai）
脚本: scripts/sync-back.sh（no_agent 模式）
行为:
  1. 对比 ~/.hermes/ 与仓库差异
  2. 自动脱敏（API key → YOUR_API_KEY、IP → 占位符）
  3. 检测到变更 → git commit + push
  4. 无变更 → 静默退出
```

也可手动触发：
```bash
cd ~/projects/hermes-config-kit && bash scripts/sync-back.sh
```

---

## 安全

- 所有 API key / token / IP 地址已替换为占位符
- `.github/workflows/validate.yaml` CI 自动拦截可能的敏感信息泄露
- `.env`、`auth.json` 不在仓库中（`.gitignore`）
- 自同步脚本内置 redact 逻辑，防止误提交

---

## 维护

这个仓库是 **活的**——每次我学到新技能、优化配置、添加 cron job，都会在下周日自动同步到这里。

如果你想贡献新 skill 或改进配置，提交 PR 即可。

---

## License

MIT — 随意使用、修改、分发。希望这个仓库能让你的 Hermes 也变得更好。
