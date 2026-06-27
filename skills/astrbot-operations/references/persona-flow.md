# AstrBot 人格系统 — 生效链路详解

## 完整流程

```
WebUI 保存人格
    ↓
存入 AstrBot 后端 DB (persona_mgr)
    ↓
群消息到达
    ↓
self_learning 插件拦截 → get_persona_id()
    ↓                          ↓
  "魔术师" (默认)          动态选择: 可能覆盖 WebUI 设置
    ↓
MemoryProcessor 加载提示词
    ↓
注入 LLM system prompt → LLM 生成
    ↓
Markdown Killer 去格式化 → 发送
```

## 关键代码路径

- `astrbot/core/persona_mgr.py` — AstrBot 核心人格管理器
- `data/plugins/astrbot_plugin_self_learning/utils/__init__.py` — `get_persona_id()`
- `data/plugins/astrbot_plugin_self_learning/services/persona/persona_manager_updater.py` — 动态人格更新

## 验证实际人格

日志中搜:
```
get_persona_id.*最终使用人格
成功加载人格.*提示词.*长度=
```

例如: `最终使用人格: 魔术师` — 这才是实际生效的，不看 WebUI 显示什么。

## self_learning 覆盖机制

`persona_manager_updater.py` 会根据群聊学习结果动态更新人格，可能在运行时覆盖用户在 WebUI 的手动切换。如需强制使用特定人格，需在 `self_learning` 配置中锁定。
