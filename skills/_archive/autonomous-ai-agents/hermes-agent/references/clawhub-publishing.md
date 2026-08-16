# ClawHub Skill Publishing — Agent 工作流

## 概述

ClawHub (clawhub.ai) 是 OpenClaw 生态的公开技能注册中心。Hermes Agent 的 `hermes skills publish` 命令目前对 ClawHub 的支持标注为 "not yet supported"。正确的发布方式是使用 ClawHub 官方的 `clawhub` CLI。

**发布路径:** `clawhub skill publish <skill-dir> --version x.y.z`

## 前置条件

```bash
npm install -g clawhub
```

如果报 EACCES（`prefix=/usr` 但无 sudo）：

```bash
npm config set prefix ~/.npm-global
npm install -g clawhub
# 为所有 npm 全局包永久解决 EACCES 问题
```

## 登录

### 方法 A：API Token（推荐，无额外依赖）

用户在 ClawHub web UI（clawhub.ai）中生成 token，直接复制给 Agent：

```bash
clawhub login --token clh_xxxxxxxxxxxxxxx
# → ✔ OK. Logged in as @username
```

用户拿到 token 后，Agent 可以直接完成 publish。

### 方法 B：Device Code 流

CLI 打印授权码，用户访问 clawhub.ai/cli/device 输入：

```bash
clawhub login --device
# → Device code received. Enter code: XXXX-YYYY at https://clawhub.ai/cli/device
# → Waiting for authorization...
```

**注意:** device code 流需要 CLI 进程保持运行等待回掉。使用 `execute_code`（Python subprocess）或 `terminal(background=true)` 的 process 会在工具调用结束后被清理，导致授权失败。推荐用 `execute_code` 工具运行子进程，用户授权期间保持等待。

## 发布 Skill

```bash
clawhub skill publish <skill-dir> --version 1.0.0
# → ✔ OK. Published <name>@1.0.0 (<ref>)
```

**说明:**
- `--version` 是 semver，必填
- `--owner <handle>` — 指定组织/用户发布（默认个人）
- `--clawscan-note` — 为 ClawScan 审核添加上下文说明（如 "Uses network access only to call the configured API"）
- 默认许可 MIT-0（自由使用、修改、重分发，无需署名）

## 验证

```bash
clawhub search <skill-name>
# → <name>  @<owner>  <Display Name>  (<relevance>)

clawhub inspect <skill-name>
# → 显示完整元数据、版本、审核状态
```

期望输出：
```
Moderation: CLEAN
Moderation Summary: No suspicious patterns detected.
```

## 更新已发布的 Skill

```bash
# 更新本地文件后
clawhub skill publish <skill-dir> --version 1.0.1
```

或者用同步命令批量处理：

```bash
clawhub sync --all              # 扫描本地 skill 目录并发布新增/变更
clawhub sync --all --dry-run    # 预览变更不实际发布
```

## 从 GitHub 安装

```bash
hermes skills tap add <owner>/<repo>
```

ClawHub 发布的 skill 也可以通过 GitHub Tap 方式安装（如果同时推了 GitHub）。两者不冲突。

## 完整发布流程示例

```bash
# 1. 安装 CLI
npm install -g clawhub
# 2. 登录（用 API Token）
clawhub login --token clh_xxxxxxxxxxxx
# 3. 发布
clawhub skill publish ~/.hermes/skills/devops/mem0-memory-setup --version 1.0.0
# 4. 验证
clawhub inspect mem0-memory-setup
```

## 已知问题

### 1. Device Code 流在非交互环境

device code 流要求 CLI 进程保持运行直到用户输入授权码。以下场景会失败：
- `terminal(background=true)` + 短期超时后被杀
- `terminal()` 前台命令 + `&` 后台（会被检测到阻止）

**解法：** 用 `execute_code` 的 Python subprocess 模式，或直接用 API Token 登录。

### 2. Moderation 延迟

新发布的 skill 审核状态初始为 `pending.scan`，ClawScan 后台自动处理。通常几秒内变为 `CLEAN`，不影响搜索和安装。

### 3. Hermes skills publish 的 ClawHub 路径

`hermes skills publish --to clawhub` 会提示 "not yet supported"。`--to github` 支持但需要 `--repo owner/repo`（会 fork 并创建 PR）。目前不能直接用 Hermes CLI 完成 ClawHub 发布——必须用 `clawhub` CLI。
