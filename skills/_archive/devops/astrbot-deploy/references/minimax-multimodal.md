# MiniMax M3 多模态配置

> 2026-06-01 发布

## 能力

- 原生多模态：文本 + 图片 + 视频理解，Step 0 起混合训练
- 1M Token 上下文（DeepSeek V4 的 10 倍），MSA 稀疏注意力架构
- Coding & Agentic SOTA，BrowseComp 83.5 超 Opus 4.7
- OpenAI 兼容：`https://api.minimaxi.com/v1`（中国站）

## AstrBot 配置

### 方案 A：M3 替代 DeepSeek（推荐）

一个模型同时聊天 + 看图。WebUI → 服务提供商 → 添加 OpenAI 兼容：
- Base URL: `https://api.minimaxi.com/v1`
- API Key: MiniMax Key
- 模型: `MiniMax-M3`

### 方案 B：分离式

DeepSeek 聊天 + M3 看图，装 `astrbot_plugin_multimodal_router`。

## 价格

Token Plan: Plus ¥49/月(6亿token), Max ¥119/月, Ultra ¥469/月
