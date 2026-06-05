---
name: skill-publishing
description: >-
  将 Hermes Agent 技能发布到 GitHub 仓库和 ClawHub 注册表的完整流程。
  涵盖 gh API 直接上传、普通 git push、clawhub CLI device code 授权发布、
  以及发布后的验证和 tap 安装。适用于任何需要共享技能给其他 Hermes/OpenClaw 用户的场景。
---

# 技能发布指南（GitHub + ClawHub）

将本地 Hermes Agent 技能发布到公开注册表，让其他用户安装使用。

## 触发条件

- 用户要求将技能"发布分享"、"推到 GitHub"、"提交到 ClawHub"
- 用户创建了新的 SKILL.md 并想公开
- `hermes skills publish --to <target>` 失败或文档不全

## 准备工作

### 所需工具

```bash
# 两个都需要
npm install -g clawhub               # ClawHub CLI
# gh 通常已随 Hermes 安装，确认：
gh auth status
```

### 核心架构

```
技能目录（本地）:
  ~/.hermes/skills/<category>/<name>/
  ├── SKILL.md                  # 技能定义（必须）
  ├── references/               # 参考文档（可选）
  ├── templates/                # 模板文件（可选）
  └── scripts/                  # 可执行脚本（可选）

GitHub 仓库（源）:
  https://github.com/<owner>/<repo>/tree/main/<category>/<name>/

ClawHub 注册表（索引）:
  https://clawhub.ai/skills/<slug>   ← 用户搜索安装的入口
```

**关键概念：** GitHub 是技能的**存储和版本管理**层，ClawHub 是技能的**发现和安装**层。先推 GitHub，再发 ClawHub。

### skill 目录结构规范（ClawHub 兼容）

ClawHub 要求技能目录直接包含 SKILL.md，发布时会打包整个目录。推荐：

```bash
skill-name/
├── SKILL.md
├── references/          # 可选：补充文档
├── templates/           # 可选：可复用的模板文件
└── scripts/             # 可选：可直接执行的脚本
```

## 发布到 GitHub

### 方式 A：创建独立仓库（推荐新手）

```bash
# 1. 创建公开仓库
gh repo create <owner>/<repo-name> --public --description "描述"

# 2. 将技能推上去
# 方式 A1: 通过 gh API 直接创建文件（推荐，避免 git clone 慢）
SKILL_B64=$(base64 -w0 ~/.hermes/skills/<category>/<name>/SKILL.md)
gh api --method PUT repos/<owner>/<repo-name>/contents/<category>/<name>/SKILL.md \
  -f message="feat: add <skill-name> skill" \
  -f content="$SKILL_B64"

# 方式 A2: git clone + push（国内网络慢时备用）
cd /tmp
git clone https://github.com/<owner>/<repo-name>.git
cp -r ~/.hermes/skills/<category>/<name> <repo-name>/<category>/<name>/
cd <repo-name>
git add -A && git commit -m "feat: add <skill-name> skill"
git push
```

### 方式 B：添加到已有技能合集（推荐维护）

适用于 `owner/hermes-agent-skills` 这类合集仓库：

```bash
SKILL_B64=$(base64 -w0 ~/.hermes/skills/<category>/<name>/SKILL.md)
gh api --method PUT repos/<owner>/<repo-name>/contents/<category>/<name>/SKILL.md \
  -f message="feat: add <skill-name> skill" \
  -f content="$SKILL_B64"
```

**支持文件也逐个上传：**

```bash
for f in ~/.hermes/skills/<category>/<name>/references/*.md; do
  name=$(basename "$f")
  content=$(base64 -w0 "$f")
  gh api --method PUT repos/<owner>/<repo-name>/contents/<category>/<name>/references/$name \
    -f message="add reference: $name" \
    -f content="$content"
done
```

### 方式 C：`hermes skills publish --to github`

Hermes 内置功能。它会 fork 目标仓库、创建分支、提交 PR：

```bash
hermes skills publish ~/.hermes/skills/<category>/<name> \
  --to github --repo <target-owner>/<target-repo>
```

注意：
- 需要 `GITHUB_TOKEN` 在 `.env` 中或 `gh auth login` 已完成
- 适用于向开源仓库（如 `openai/skills`）提交 PR
- 不适用于自己控制的仓库（用方式 A/B 更直接）

## 发布到 ClawHub

ClawHub 使用独立 CLI `clawhub`，与 Hermes 的 `hermes skills publish --to clawhub` **无关**（后者显示"not yet supported"）。

### Step 1: 安装 clawhub CLI

```bash
npm install -g clawhub
```

### Step 2: 登录（Device Code 流）

ClawHub 支持 AI Agent 通过 device code 流授权，不需要浏览器 cookie：

```bash
# 在后台启动登录等待授权
clawhub login --device
# → 输出:
#   To authenticate, visit: https://clawhub.ai/cli/device?code=***
#   And enter code: ABCD-1234
#   Code expires in 15 minutes.
#   Waiting for authorization...
```

**Agent 操作流程：**
1. 运行 `clawhub login --device`（CLI 打印授权码）
2. 告诉用户打开 `https://clawhub.ai/cli/device` 输入授权码
3. 用户输入后，CLI 自动完成登录
4. 验证：`clawhub whoami`

> **注意：** 必须在 CLI 等待时用户完成输入。`clawhub login --device` 启动后使用 HTTP 轮询等待授权完成。使用 `execute_code`（Python subprocess）运行可以捕获输出并保持进程存活。

### Step 3: 发布技能

```bash
clawhub skill publish ~/.hermes/skills/<category>/<name> \
  --version 1.0.0 \
  --owner <github-handle>
```

说明：
- `--version` 强制要求语义化版本号（如 1.0.0）
- `--owner` 指定发布者 GitHub 用户名或组织名
- 技能在 ClawHub 发布的 slug 由发布者自动分配
- 发布后技能在 ClawHub 上公开可用

### Step 4: 在 ClawHub 验证

```bash
clawhub search <skill-name>
clawhub inspect <skill-slug>
```

## 发布后的验证

### 从 GitHub tap 安装（Hermes 用户）

```bash
hermes skills tap add <owner>/<repo-name>
# 然后可以：hermes skills browse 或 hermes skills search <skill>
```

### 从 ClawHub 安装（OpenClaw 用户）

```bash
clawhub install <skill-slug>
```

## 已知问题与排错

### 1. gh API 上传换行问题

`base64 -w0` 强制单行输出，避免 GitHub API 的 JSON 多行解析问题。

### 2. git clone 慢（国内网络）

优先使用 `gh api --method PUT .../contents/...` 方式逐个文件创建，跳过 git clone。如果必须用 git，设置代理：

```bash
git -c http.proxy=http://127.0.0.1:7890 clone ...
```

### 3. clawhub login 超时

Device code 有效期 15 分钟。如果用户确认已输入但 CLI 仍超时：

- 可能原因：CLI 用 `stdout` 缓冲区未刷新，看不到输出。用 `python3 -c` 启动 subprocess 并逐行读取输出
- 重试：杀进程后重新 `clawhub login --device`

### 4. ClawHub 没有重名 slug 检查

发布同名技能会触发更新而不是报错。如果想更新已发布的技能，重新 `clawhub skill publish` 加新版本号即可。

### 5. `hermes skills publish --to clawhub` 不能用

Hermes 内置的 ClawHub 发布目前返回 "not yet supported"。始终使用独立的 `clawhub` CLI。

## 发布清单

- [ ] SKILL.md 的 frontmatter 包含 name + description
- [ ] description ≤ 1024 chars
- [ ] 技能目录结构完整
- [ ] GitHub 仓库已创建并可见
- [ ] 技能文件已推送到 GitHub
- [ ] `hermes skills tap add owner/repo` 能发现技能
- [ ] clawhub CLI 已登录
- [ ] `clawhub skill publish` 成功
- [ ] `clawhub search <skill>` 能找到
