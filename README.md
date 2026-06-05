# Hermes Config Kit — README

> Publieople 的 Hermes 数字孪生。完整的 Agent 配置、238 个 Skills、自同步备份。
> **clone → setup.sh → 得到完全相同的魔术师。**

## 这是什么？

这不是一个普通的"starter kit"。这是**一个 AI Agent 的完整数字孪生**——Publieople 的 Hermes 随时随地可以复现的全部配置。

包含：
- **config.yaml** — 完整 615 行配置（API key 占位符化）
- **SOUL.md** — 魔术师人格 + 工作方式定义
- **238 skills** — 覆盖开发、创意、飞书、ComfyUI、生物信息等 39 个分类
- **Cron jobs** — 每日自检、Skills 维护、配置自同步
- **MCP 服务器** — Context7 文档、Jobs、Windows 集成
- **一键安装** — `setup.sh` 交互式配置，5 分钟搞定

## 快速开始

```bash
# 1. Clone
git clone https://github.com/publieople/hermes-config-kit.git
cd hermes-config-kit

# 2. 安装（确保 Hermes CLI 已安装）
chmod +x setup.sh
./setup.sh

# 3. 启动
hermes
```

## 目录结构

```
hermes-config-kit/
├── config.yaml              # Hermes 完整配置（API key 已脱敏）
├── SOUL.md                  # 魔术师人格
├── .env.example             # 环境变量模板
├── setup.sh                 # 一键安装脚本
├── skills/                  # 238 skills（39 分类）
├── scripts/
│   ├── sync-back.sh         # 自同步脚本
│   └── skills-memory-maintenance.py
├── cron/jobs.yaml           # Cron 作业定义
├── mcp/servers.yaml         # MCP 服务器配置
├── shell/                   # Shell 配置模板
│   ├── bashrc
│   ├── config.fish
│   └── gitconfig
├── npm/global-packages.txt  # npm 全局包列表
└── .github/workflows/       # CI 敏感信息检查
```

## 技能分类

| 分类 | 数量 | 典型技能 |
|------|------|----------|
| creative | 20+ | comfyui, p5js, ascii-art, manim, pixel-art |
| devops | 15+ | hermes-bootstrap, kanban, mem0-setup, webhook |
| software-dev | 15+ | plan, tdd, code-review, debugging, subagent |
| comet | 8 | comet-open/design/build/verify/archive |
| mlops | 10+ | minimax-vision, huggingface, vllm, llama-cpp |
| openclaw-imports | 20+ | lark-doc/contact/task/wiki, docx, pdf |
| productivity | 15+ | notion, airtable, google-workspace, linear, maps |
| research | 5+ | arxiv, llm-wiki, polymarket, blogwatcher |
| github | 5+ | auth, code-review, issues, pr-workflow, repo |
| superpowers | 8+ | brainstorming, git-worktrees, executing-plans |

## 自同步

Repo 内包含自同步机制——`scripts/sync-back.sh`：
- 每周日自动检测 `~/.hermes/` 变更
- 自动脱敏后 commit + push
- 无变化时静默退出

配合 cron job 实现完全自动化。

## 安全

- 所有 API key 已替换为占位符（`YOUR_API_KEY`）
- CI 自动检查是否有敏感信息泄露
- 不对仓库外共享 `.env` 或 `auth.json`

## 维护

这个仓库由 `hermes-config-sync` cron job 每周自动更新。
如需手动同步：

```bash
cd ~/projects/hermes-config-kit
bash scripts/sync-back.sh
```

## License

MIT — 随意使用、修改、分发。
