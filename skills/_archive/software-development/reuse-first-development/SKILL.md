---
name: reuse-first-development
description: 功能选型流程：先搜现成方案→评估对比→集成，不自己写。适用于任何需要引入新能力的功能选型。
triggers: [选方案, 调研, 找库, npm选型, 不重复造轮子, 用什么库, 功能调研]
category: software-development
---

# Reuse-First Development

## 核心原则

> **每个需求先找现成最优开源方案，评估后集成。绝不自己实现核心功能。**

这是用户（冯周杰 / Publieople）在多个项目中反复强化的核心方法论。违反此原则就是返工。

## 决策流程

```
功能需求出现
    │
    ├── 1. 搜索 ──→ web_search × 3 (不同关键词)
    │         ──→ npm search / GitHub search
    │         ──→ 看 npmtrends.com 对比下载量
    │
    ├── 2. 评估 ──→ web_extract 拉 README + npm 页面
    │         按以下维度打分：
    │         ├── 浏览器兼容？(不能是 Node-only)
    │         ├── Bundle 大小？(PWA 优先 <50KB gzip)
    │         ├── 维护状态？(最近一年有更新, 下载量趋势)
    │         ├── API 简洁？(一行能搞定的不要十行)
    │         └── 生态验证？(dependents 数量 > 100)
    │
    ├── 3. 对比 ──→ 2-3 个候选，输出对比表
    │         ──→ 标注推荐 + 理由
    │
    └── 4. 集成 ──→ npm install → 验证 build → 写 handler/组件
              ──→ 更新 SPEC.md 记录选型决策
```

## 评估维度

| 维度 | 权重 | 问题 |
|------|------|------|
| 浏览器兼容 | 🔴 否决项 | 能在浏览器跑吗？有没有 `global`/`process`/`fs` 引用？ |
| Bundle 大小 | 🟡 高 | gzip 后多大？有没有 CDN 选项避免打包？ |
| 维护状态 | 🟡 高 | 最近 commit？issues 响应速度？ |
| API 简洁 | 🟢 中 | 集成需要多少行？有无 React 封装？ |
| 生态验证 | 🟢 中 | npm 周下载量？dependents 数量？ |

## 已形成的选型结论（可直接复用）

| 需求 | 方案 | 理由 |
|------|------|------|
| 编码检测 | `chardet` | 22KB, Pure TS, 25 encodings, 1477 dependents |
| TOML 解析 | `smol-toml` | 1.6KB, 浏览器兼容, 替换了 `@iarna/toml` |
| 快捷键 | `react-hotkeys-hook` | <3KB, 2.5M 周下载 |
| i18n | `react-i18next` | ~5KB gzip, React 最主流 |
| PDF 查看 | `react-pdf` + CDN worker | React 封装, worker 1MB 走 CDN 不打包 |
| 压缩包 | `fflate` | 30KB, 最快纯 JS, ZIP 支持仅 +3KB |
| CSV 表格 | TanStack Table + PapaParse | 业内标准 |
| 图片编辑 | TUI Image Editor | 功能最完整 |
| 代码编辑 | CodeMirror 6 | 浏览器最成熟 |
| JSON 编辑 | vanilla-jsoneditor | 树形+代码双模式 |

## 反模式

| ❌ 不要 | ✅ 要 |
|---------|------|
| 自己写编码检测逻辑 | 用 `chardet` |
| 手写 UTF-8→GBK 回退 | 交给专业库 |
| 自己实现 CSV 解析 | 用 `papaparse` |
| 自己写 PDF 渲染 | 用 `react-pdf` / `pdfjs-dist` |
| 自己写 ZIP 解压 | 用 `fflate` |
| 引入 Node-only 包碰运气 | 先验证浏览器兼容 |

## 选型记录规范

每次选型后，在 SPEC.md 或 commit message 中记录：

```
feat: add PDF handler using react-pdf
- Selected react-pdf over pdfjs-dist raw: React wrapper, ~50KB
- Worker loaded via CDN to avoid 1MB bundle
- Alternatives considered: native <iframe> (too limited), Nutrient (paid)
```

## 参考

- `references/phase3-research.md` — open-any Phase 3 调研实例（PDF/压缩包/音视频/主题/i18n/快捷键/CI）
