---
name: hermes-dev-workflow
description: 将 bili-fe-workflow 方法论移植到 Hermes 的标准化开发工作流。用 AGENTS.md + Memory + Skills 三件套替代 .workflow 知识库，实现从需求到提测的 AI 全链路自动化。
version: 1.0.0
author: Hermes Agent (adapted from bilibili/bili-fe-workflow)
license: MIT
metadata:
  hermes:
    tags: [workflow, dev-workflow, ai-workflow, bili-fe, standardization]
    related_skills: [writing-plans, spec-kit-greenfield-init, plan, subagent-driven-development]
---

# Hermes Dev Workflow

## 概述

将 B 站 bili-fe-workflow 的核心理念移植到 Hermes 原生生态：

```
B站方案: .workflow 知识库 + MCP 命令链 → 标准化 AI 产出
Hermes版: AGENTS.md + Memory + Skills → 标准化 AI 产出
```

**核心逻辑不变**：先铺上下文 → 再走标准化节点 → 最后自动化产出。

## When to Use

**触发条件：**
- 用户说"新需求" / "开始做这个功能" / "实现这个 PRD"
- 用户给了一个需求文档或链接，需要落地开发
- 需要标准化 AI 输出的质量
- 项目信息散乱，AI 产出经常偏离规范

**Do NOT use when：**
- 只是修个小 bug（直接调 debug 流程）
- 用户明确说"直接写代码，别走流程"

## 核心架构：Hermes 三件套

### 1. AGENTS.md — 项目知识库（≈ .workflow/knowledge/）

在每个项目根目录放一个 `AGENTS.md`，相当于 `.workflow/knowledge/` 的合并版：

```markdown
# Project AGENTS.md

## 技术栈
- 前端: Vue3 + TypeScript + Vite
- 后端: FastAPI + SQLAlchemy async + PostgreSQL
- 样式: TailwindCSS
- 包管理: uv (Python) / npm (前端)

## 目录结构
```
project/
├── src/                # 后端源码
│   ├── api/            # FastAPI 路由
│   ├── services/       # 业务逻辑
│   └── models/         # 数据模型
├── frontend/           # 前端源码
├── tests/              # 测试
└── docs/               # 文档
```

## 编码规范
- 组件命名: PascalCase
- API 路径: /api/v1/*
- 错误响应: `{code: int, message: string, data: any}`
- 所有 public 函数写 docstring
- 异步优先: async/await

## 关键约定
- 数据库迁移用 Alembic
- 环境变量在 .env 里管理
- 测试用 pytest + pytest-asyncio
- Commit 规范: feat/fix/docs/refactor 前缀
```

**初始化命令：**
```bash
# 在项目根目录创建 AGENTS.md
```

### 2. Hermes Memory — 持久化项目记忆（≈ .workflow/knowledge/ 增量更新）

把项目级的"活的"信息存进 Memory：

```markdown
# 每次项目重要的发现或变更，存进 memory
ProjectX:
  - 前端用了 Pinia 做状态管理（非 Vuex）
  - 用户偏好: 优先写单元测试再写功能
  - API 基础路径已从 v1 改为 v2
  - 团队成员: 张三(前端), 李四(后端)
```

### 3. Hermes Skills — 标准化工作流节点（≈ MCP 命令链）

每个 Skill 对应 bili-fe-workflow 的一个节点，Skill 之间通过约定文件（如 `PLAN.md`）衔接。

---

## 工作流节点

### 节点 1：PRD 预处理（≈ prd-preprocess）

**目标：** 把原始需求文档拆解成 AI 可执行的标准化开发文档。

**输入：** 需求描述 / PRD 链接 / 口头需求
**输出：** 结构化开发计划（`PLAN.md`）

**流程：**

#### Step 1：资源获取
问用户要：需求文档、设计稿链接、技术方案（如果有）。

#### Step 2：需求分析
按四个维度分析需求：
- **界面改动** — UI 要改什么
- **功能改动** — 新增/修改/删除什么功能
- **交互改动** — 用户操作流程变化
- **数据改动** — API/数据结构变更

#### Step 3：代码影响分析
扫描现有代码，分析涉及模块：
```python
# 用 search_files 定位要改的文件
search_files("*.py", target="files", path="src/")
search_files("*.vue", target="files", path="frontend/")
```

#### Step 4：需求澄清
从三个角度提问：
- **完整性**：有没有遗漏的边界情况？
- **一致性**：和现有功能是否冲突？
- **明确性**：有没有歧义或模糊描述？

#### Step 5：拆解输出
生成 `PLAN.md`，按依赖关系拆成子任务。

---

### 节点 2：开发工作流（≈ Dev Workflow）

**目标：** 按 PLAN.md 分步实现功能。

**流程：**

#### Step 1：读上下文
```markdown
> 加载 AGENTS.md → 加载 Memory → 加载 PLAN.md
```

#### Step 2：动态计划
判断需求类型，选择执行策略：
- **新页面/新模块** → 走完整流程（schema → model → API → UI → 测试）
- **修改现有功能** → 只走受影响的部分
- **纯 UI 改动** → 前端优先

#### Step 3：逐任务实现
用 `subagent-driven-development` Skill，每个任务独立子代理执行：
1. 读 PLAN.md 当前任务
2. 实现（TDD 循环）
3. 验证
4. commit

#### Step 4：集成验证
所有任务完成后：
```bash
# 后端测试
cd project && uv run pytest

# 前端构建
cd frontend && npx vite build
```

---

### 节点 3：自动化测试工作流（≈ Test Workflow）

**目标：** 系统化地为功能编写测试。

**流程：**

#### Step 1：生成测试计划
分析功能变更 → 确定测试范围：
- 单元测试：新增/修改的函数
- 集成测试：涉及 API 端点的
- 边界情况：空值、异常、超时

#### Step 2：人工 Review 测试计划
输出测试计划给用户确认，避免浪费 Token。

#### Step 3：AI 执行测试
按计划逐条实现：
1. 写测试 → 2. 跑失败 → 3. 实现 → 4. 跑过

#### Step 4：生成测试报告
```bash
uv run pytest tests/ -v --tb=short > test-report.txt
```

---

### 节点 4：需求到提测的完整流水线

> 这是上述节点的整合，适合"接到一个完整需求"的场景。

**完整流程（7 步）：**

```
Step 1: PRD 预处理 → 输出 PLAN.md
Step 2: 用户 Review PLAN.md（确认方向）
Step 3: 按 Plan 逐 Task 开发（subagent-driven-development）
Step 4: Task 间自动测试验证
Step 5: 全部 Task 完成后全量回归测试
Step 6: 生成测试报告
Step 7: 输出变更摘要（供提测/PR 用）
```

---

## 实操指南

### 首次接入项目

**第一步：创建 AGENTS.md**

```bash
# 在项目根目录
touch AGENTS.md
```

然后填充项目信息（技术栈、目录结构、编码规范、关键约定）。

**第二步：初始化 Memory**

通知 Hermes：`"记住这个项目的关键事实"` — 比如目录结构、用户偏好、团队人员。

**第三步：首次需求**

```markdown
用户: "新需求，实现用户登录功能"
→ 用 hermes-dev-workflow 走完整流程
   - 先 PRD 预处理 → 输出 PLAN.md
   - 用户确认 → 逐 Task 开发
   - 测试验证 → 输出变更摘要
```

### 日常使用

**场景 A：接到新需求**
```
用户: "加个功能：[描述]"
→ 自动：读 AGENTS.md → 读 Memory → PRD 预处理 → 输出 PLAN.md → 等用户确认
```

**场景 B：修 Bug**
```
用户: "[Bug 描述]"
→ 快速路径：定位代码 → 分析原因 → 修 → 加测试 → 验证
```

**场景 C：代码 Review**
```
用户: "Review 这些改动"
→ 读 AGENTS.md 规范 → 逐文件 Review → 输出 Review 摘要
```

---

## AGENTS.md 模板

直接复制这个到项目根目录，按实际修改：

```markdown
# [项目名称] AGENTS.md

## 技术栈
- 前端: 
- 后端: 
- 数据库: 
- 包管理: 
- 其他关键依赖: 

## 目录结构
```
.
├── 
```

## 编码规范
- 命名: 
- 文件结构: 
- 错误处理: 
- 测试: 

## 关键约定
- Git: 
- 部署: 
- 环境变量: 
- API 设计: 

## 团队信息
- 技术负责人: 
- 团队成员: 

## 项目状态
- 当前阶段: 
- 待办项: 
```

---

## 输出文件规范

### PLAN.md 格式

每个需求生成一份 `PLAN.md`：

```markdown
# [功能名称] 实现计划

> 生成日期: YYYY-MM-DD | 来源: PRD 预处理

## 需求摘要
一句话描述。

## 涉及模块
- src/api/xxx.py — 新增接口
- src/models/xxx.py — 新增模型
- ...

## 任务列表

### Task 1: [第一步做什么]
- [ ] 子步骤 1
- [ ] 子步骤 2
- 验证方式: ...

### Task 2: [第二步做什么]
...
```

### 变更摘要格式（提测/PR 用）

```markdown
## 变更摘要

### 新增文件
- `src/api/user.py` — 用户登录接口

### 修改文件
- `src/models/user.py` — 新增 password_hash 字段

### 测试
- `tests/test_user.py` — 8 条用例，全部通过

### 涉及配置
- 环境变量新增: JWT_SECRET
- 数据库迁移: 新增 users 表
```

---

## Pitfalls

### ⚠️ 不要跳过上下文
每次开工前先读 AGENTS.md + Memory + 相关 Skills。跳过的后果：AI 产出偏离规范。

### ⚠️ PLAN.md 需要用户确认
不要直接按 PLAN.md 开干。先给用户看计划 → 等确认 → 再执行。

### ⚠️ 三件套不是一次性建好的
AGENTS.md 需要迭代更新。Memory 需要持续积累。Skills 需要根据项目特点调整。

### ⚠️ 不要过度自动化
小改动（一行代码、改个文案）直接修，不用走完整流水线。判断标准：改动涉及 3+ 文件或跨模块 → 走流程；否则直接修。

### ⚠️ 区分"需求"和"任务"
一个需求可能包含多个任务。PLAN.md 按需求拆分，不是按文件拆分。
