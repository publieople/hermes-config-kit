---
name: yubai-dramaflow
description: YubAI-DramaFlow 参考 — AI漫剧制作工作流的方法论+模板，已 clone 到本地
---

# YubAI-DramaFlow 参考

> 项目作者：鱼摆摆（B站 @鱼摆摆喂）
> 本地路径：`~/.hermes/references/YubAI-DramaFlow/`

## 什么时候用这个 skill

- 需要设计 storyboard 模板、分镜格式、提示词模板时
- 需要参考角色一致性控制方案（风格锚定）时
- 需要完善管线的质量评估/可行性检查时
- 用户提到 YubAI 或 DramaFlow 或鱼摆摆时

## 项目结构

```
YubAI-DramaFlow/
├── docs/                    # 入门文档
│   ├── 快速开始.md
│   ├── 工具选择指南.md
│   ├── 新手避坑指南.md
│   ├── 常见问题.md
│   └── 更新日志.md
├── templates/               # 9个实用模板（核心资产）
│   ├── 风格定义模板.md        👈 风格锚定 — 生图一致性的基石
│   ├── 故事大纲模板.md
│   ├── 剧本格式模板.md
│   ├── 网文改写模板.md
│   ├── 故事大纲扩写模板.md
│   ├── AI可行性评估模板.md
│   ├── 人物设计模板.md
│   ├── 场景设计模板.md
│   └── 分镜表模板.md          👈 分镜表，含提示词模板
├── references/              # 10篇参考文档（核心方法论）
│   ├── 一致性控制方案.md      👈 风格锚定+人物一致性+参考图
│   ├── 提示词编写规范.md
│   ├── 视频提示词指南.md
│   ├── AI生成难度评估体系.md
│   ├── 五阶段自检制度.md
│   ├── 剧本AI适配原则.md
│   ├── 分镜设计指南.md
│   ├── 网文改写指南.md
│   ├── 常见问题解决方案.md
│   └── 质量评估标准.md
├── examples/                # 案例
│   └── 获得异能的那一天.../
└── assets/                  # 图片资源
```

## 与我们管线的对应关系

| YubAI 五阶段 | 我们的管线组件 | 可借鉴点 |
|---|---|---|
| ① 故事层 | storyboard JSON（LLM生成） | 网文改写模板、剧本格式 |
| ② 风格层 | ❌ 缺失 | **风格定义模板 + 风格锚定提示词** |
| ③ 设计层 | ❌ 缺失 | 人物设计模板、场景设计模板、资产库管理 |
| ④ 分镜层 | storyboard JSON | 分镜表模板（景别/运镜/转场） |
| ⑤ 视频层 | orchestrator + ComfyUI | 视频提示词指南 |

## 核心概念速览

### 风格锚定（最重要）
每次生图都追加**完全相同**的风格前缀字符串，否则 AI 每次都在"重新定义"视觉风格。

```
正确: [风格锚定] + [人物特征] + [场景/动作]
错误: 每次重新写风格描述 → 风格漂移
```

### 人物一致性（3种方案）
1. **风格锚定 + 参考图**（推荐）— 选一张满意的人物图为参考
2. **三视图设计** — front/side/back view
3. **多服装设计** — 校服/便装/正装版

### 分镜表关键字段
镜号 | 景别 | 运镜 | 画面描述 | 时长 | 台词/旁白 | 中文提示词 | 英文提示词 | 视频提示词 | 音效

## 快速打开关键文件

```bash
# 风格定义模板（开始前的第一步）
cat ~/.hermes/references/YubAI-DramaFlow/templates/风格定义模板.md

# 一致性控制方案（角色/场景一致性）
cat ~/.hermes/references/YubAI-DramaFlow/references/一致性控制方案.md

# 分镜表模板
cat ~/.hermes/references/YubAI-DramaFlow/templates/分镜表模板.md

# 人物设计模板
cat ~/.hermes/references/YubAI-DramaFlow/templates/人物设计模板.md

# AI可行性评估
cat ~/.hermes/references/YubAI-DramaFlow/references/AI生成难度评估体系.md
```
