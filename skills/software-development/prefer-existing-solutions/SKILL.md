---
name: prefer-existing-solutions
description: 每个技术需求先找现成最优开源方案，集成而非自己实现。Use when adding any new capability, dependency, or feature to a project.
tags: [reuse, research, open-source, philosophy]
trigger: 加功能|加依赖|实现新能力|找库|用什么库|怎么实现
category: software-development
---

# 复用优先

## 核心原则

**绝不重复造轮子。** 每个技术需求先找社区已验证的最优解，评估后集成。自己实现是最后手段。

这是项目方法论的核心——不是"省钱"，是"站在巨人肩膀上"。社区维护了几年的方案比你花半小时写的健壮得多。

## 决策流程

```
新需求出现
    │
    ├── 1. 明确需求边界（我需要解决什么问题？）
    │
    ├── 2. 搜索现成方案
    │      ├── npm 搜索关键词
    │      ├── GitHub 搜索同类项目
    │      └── web_search 找推荐/对比文章
    │
    ├── 3. 对比候选（按优先级）
    │      ├── 浏览器兼容性（如果目标是 PWA/前端）
    │      ├── 体积（minified + gzip，对 PWA 尤其重要）
    │      ├── TypeScript 原生支持
    │      ├── 维护活跃度（最近 commit、Star 数）
    │      ├── 生态验证（被多少项目依赖）
    │      └── API 设计是否简洁
    │
    ├── 4. 选最优，npm install
    │
    └── 5. 只在确认"无可用的现成方案"后才自己写
```

## 触发时机

任何以下信号出现时，必须走上述流程：

- "需要一个 XXX 功能" → 先搜，别先写
- "这个库不行，我写一个" → 先搜替代品
- "处理编码 / 解析格式 / 转换数据" → 大概率有现成库
- "加个 XX 检测 / XX 识别" → 先搜，别自己写规则

## 实战案例

### 本次会话：编码检测

```
需求：文本文件可能存在多种编码（UTF-8、GB2312、Shift-JIS…）
     需要自动检测并正确解码

我的第一步（错误）：手写 UTF-8 → GBK 回退逻辑
用户反馈：     "先找现成的，不要自己实现"

正确做法：
  1. npm search / web_search → 找到 jschardet、chardet
  2. 对比：chardet 更小（22KB）、TypeScript 原生、1477 项目在用
  3. npm install chardet → 3 行集成 → 搞定
  4. 覆盖 25 种编码，比手写的 2 种强 10 倍
```

### TOML 解析：@iarna/toml → smol-toml

```
原始选择：@iarna/toml（Node.js 生态的默认 TOML 解析器）
问题：     浏览器报 global is not defined（Node-only 包）
解决：     smol-toml（~3KB，纯 ESM，浏览器兼容，API 相同）
```

## 反模式

| 反模式 | 为什么错 |
|--------|---------|
| "这个简单，我写个正则就行" | 边界情况比你想象的多。编码检测、格式解析、数据验证——社区方案经过数百项目验证 |
| "不想加依赖" | 依赖不是敌人。一个 22KB 的库替代 100 行手写代码 + 未来 N 次 bug 修复，是净收益 |
| "这个库功能太多了" | 看 tree-shaking 支持。现代打包器（Vite/Rolldown）只打包你实际使用的代码 |
| "我先写一版，后面再换" | 现在多花 5 分钟搜索，省掉后续替换的 30 分钟 |

## 搜索策略速查

| 需求类型 | 搜索关键词模板 | 示例 |
|---------|--------------|------|
| AstrBot 插件 | `astrbot <功能> plugin site:github.com` | `astrbot cosyvoice TTS 语音 plugin` |
| 格式解析/编码 | `<format> <language> library browser` | `toml parser javascript browser` |
| 检测/识别 | `<thing> detection <language> npm` | `encoding detection javascript npm` |
| UI 组件 | `<component> react npm lightweight` | `csv table react npm lightweight` |
| 通用工具 | `<problem> <language> library` | `uuid generate javascript library` |

## 边界

- **Always**: 每个新需求先搜索 30 秒，确认没有现成方案再自己动手
- **Ask first**: 如果两个候选方案旗鼓相当，列出对比让用户选
- **Never**: 不搜索直接手写；明知有社区方案却坚持自己实现

## 相关

- `references/chardet-evaluation.md` — 编码检测方案对比（chardet vs jschardet vs 手写）
- `reference-design-contract` — 已建立设计 token 和规范时使用
- `source-driven-development` — 验证实现与官方文档一致性
