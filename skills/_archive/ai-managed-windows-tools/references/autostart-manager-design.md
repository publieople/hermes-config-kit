# 自启动管理工具设计决策（grill-me 会话 2026-08-02，BootKeeper 项目）

目标：开源 Windows 自启动管理工具。差异化卖点：现代 GUI + i18n + AI 可调用 + 中文支持。
仓库：`github.com/publieople/BootKeeper`，GPL-3.0，PLAN.md 在仓库根。

## v1 范围（已钉死）

- **注册表 Run 键**（HKCU + HKLM）
- **启动文件夹**（用户级 + 系统级）
- **任务计划程序**

服务 / WMI 订阅 / 组策略 / Winlogon / AppInit_DLLs 等后期。枚举完整清单参考 `p0w3rsh3ll/AutoRuns`（PowerShell 模块）。

## 技术栈（参考 motrix-next，已确认）

- **Tauri 2 (Rust)** + Vue 3 + TypeScript
- **Naive UI** 组件壳 + **@material/material-color-utilities**（MD3 动态取色内核——motrix-next 的 MD3 就是这么实现的）
- Pinia、Vue Router
- i18n：**vue-i18n** + **tauri-plugin-locale-api**，v1 只做中/英
- Vite + Cargo 构建

## 核心依赖（调研定稿）

| 能力 | 方案 | 理由 |
|---|---|---|
| 注册表 | `winreg` v0.56 | 196M 下载，活跃 |
| 任务计划 | `windows` crate `Win32_System_TaskScheduler` (COM) | taskschd crate 已死（2023 停更）；schtasks CLI 输出本地化脆弱 |
| 签名校验 | `windows` crate `Win32_Security_WinTrust` (WinVerifyTrust) | 官方绑定；v1 只验有效性 |

## 架构（三进程）

- **sidecar**（`app --daemon`）：常驻、普通权限、MCP server、HTTP localhost + token 鉴权。开机自启用 Run 键（dogfood）。
- **helper**（`app --exec`）：一次性提权（ShellExecute runas），弹独立确认窗，独立核验事实后执行。
- **GUI**：用户主动打开，可 UAC 重启自己，与 sidecar IPC。

token 存 Windows Credential Manager（DPAPI），首次 GUI 展示给用户复制。

## 安全模型（勿再砍）

- 硬确认 token：写工具默认拒绝，除非 AI 先拿确认 token。
- 弹窗事实由 helper 独立核验（sidecar 只传操作意图 + 条目 ID）。
- 风险定级 = 软件规则（签名校验、路径、发布者），AI 只分析建议，用户拍板。
- 快照：写操作前备份 + 前后快照，保留 7 天，`restore_item` 进 tool surface。
- 禁用语义：**改名**（`Foo` → `Foo.disabled`，Autoruns 思路），恢复 = 改回名字。

## AI 交互：CLI-first

`bootkeeper` CLI + SKILL.md 先行（skill 不是跨 agent 标准，CLI 才是通用底座），MCP 后置为薄适配层包 CLI。
CLI 命令面：list / get / analyze / enable / disable / remove / add / restore / snapshot list。

**SKILL.md 标准已定：skills.sh（Vercel Agent Skills，vercel-labs/skills，27.8k★）。** 不是自造格式：
- 格式 = 标准 SKILL.md（与 Anthropic agentskills.io 同规范），skills.sh 是生态层（CLI + 目录 + 排行榜）
- 安装：`npx skills add publieople/BootKeeper` — 把 SKILL.md 装进项目，任何 agent 都能读
- 覆盖 19+ agent，含 **nous-research（Hermes）**、Claude Code、Cursor、Codex、Gemini 等
- 三层分工：CLI = 执行面（任何 agent 能调）、SKILL.md = 说明书（19+ agent 支持）、MCP = 协议适配（后置）

## 里程碑

- M0：workspace 骨架 + core（枚举三件套 + 规则引擎 + 快照）
- M1：CLI 读链路 + SKILL.md
- M2：helper 提权 + 确认窗 + 写命令
- M3：GUI（Naive UI + MD3 + 中英 i18n）
- M4：AI 全链路 + 快照恢复 + 打包 + MCP 适配层

## 待定项（M1 阶段再定，不阻塞 M0）

- CLI 参数与 JSON 输出格式细节
- token 存储实现（Credential Manager vs 配置文件）
- SKILL.md 编写与 agent 兼容性验证
- MCP 适配层（后置，包 CLI）
