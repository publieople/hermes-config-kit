# `_conf_schema.json` 配置 Schema 详解

AstrBot 4.x 插件配置 schema 完整字段参考。来源:官方文档 `https://docs.astrbot.app/dev/star/guides/plugin-config.html`,本地源码 `astrbot/core/star/config.py`。

## 顶层结构

```json
{
  "key_name": { "type": "...", ... },
  "sub_group": {
    "type": "object",
    "items": {
      "nested_key": { "type": "string", ... }
    }
  }
}
```

## 通用字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | 配置项类型 |
| `description` | - | WebUI 显示的一行说明 |
| `hint` | - | tooltip,鼠标悬浮问号时显示 |
| `obvious_hint` | - | hint 是否醒目显示 |
| `default` | - | 默认值(未配时使用) |
| `options` | - | 下拉选项列表 |
| `invisible` | - | 是否在 WebUI 隐藏 |

## 支持的 type

| type | 说明 | 额外字段 |
|------|------|----------|
| `string` | 短文本 | - |
| `text` | 多行文本(可拖拽 textarea) | - |
| `int` | 整数 | `slider: {min, max, step}` |
| `float` | 浮点 | `slider` |
| `bool` | 开关 | - |
| `object` | 嵌套对象 | `items: {...}` 子 schema |
| `list` | 列表 | `items: {...}` 元素 schema |
| `dict` | 键值对 | `items: {...}`, 可选 `template_schema` |
| `file` | 文件上传(≥v4.13.0) | `file_types: ["pdf", "docx"]` |
| `template_list` | 模板列表(≥v4.10.4) | `templates: {...}` 多模板 |

## `_special`(v4.0.0+)

WebUI 特殊选择器,常用:

| 值 | 用途 | 返回类型 |
|----|------|---------|
| `select_provider` | 选模型 provider(chat) | string |
| `select_provider_tts` | 选 TTS provider | string |
| `select_provider_stt` | 选 STT provider | string |
| `select_persona` | 选人格 | string |
| `select_knowledgebase` | 选知识库(可多选) | list |

```json
{
  "chat_model": {
    "type": "string",
    "description": "使用的对话模型",
    "_special": "select_provider",
    "default": ""
  },
  "kb_refs": {
    "type": "list",
    "description": "使用的知识库",
    "_special": "select_knowledgebase",
    "default": []
  }
}
```

## 代码编辑器

`editor_mode: true` 启用 Monaco 编辑器,配合 `editor_language` (json/python/...) 和 `editor_theme` (vs-light/vs-dark)。

## dict 类型的 template_schema

`dict` 类型可选 `template_schema` 字段,让用户可视化编辑键值对(类似 template_list 但只有一种模板)。

```json
{
  "custom_extra_body": {
    "type": "dict",
    "items": {},
    "template_schema": {
      "temperature": {
        "type": "float",
        "default": 0.6,
        "slider": {"min": 0, "max": 2, "step": 0.1}
      }
    }
  }
}
```

## template_list 模板列表(≥v4.10.4)

每个用户可加多个条目,每个条目从 `templates` 里选一种模板:

```json
{
  "feeds": {
    "type": "template_list",
    "templates": {
      "rss": {
        "name": "RSS Feed",
        "items": {
          "url": {"type": "string", "default": ""}
        }
      },
      "json_api": {
        "name": "JSON API",
        "items": {
          "endpoint": {"type": "string", "default": ""}
        }
      }
    }
  }
}
```

保存后 config 是 `[{__template_key: "rss", url: "..."}, ...]`。

## 运行时使用

```python
class MyPlugin(Star):
    def __init__(self, context: Context, config: Optional[AstrBotConfig] = None):
        super().__init__(context)
        self.config = config or {}
        # config 是 AstrBotConfig,继承 dict 的所有方法
        v = self.config.get("my_key", "default")
```

`AstrBotConfig` 自动从 schema 加载,**没有 `_conf_schema.json` 时 config 是 None**。空 schema 写 `"{}"` 即可,不能省略文件。

## Schema 迁移

发布新版本时,AstrBot **递归对比** schema:
- 新增字段:用 default 填充
- 删除字段:从 config 移除
- 已存在字段:保留用户值

**坑**:重命名字段会被当作"删除 + 新增",**用户配置会丢**。破坏性变更要明确告知用户。
