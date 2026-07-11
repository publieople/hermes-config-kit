---
name: astrbot-plugin-dev
description: AstrBot 插件开发 — 骨架、装饰器、配置 schema、LLM 工具、注册/发布、热重载验证。Fork 优先于从零写,文档先于代码。
---

# AstrBot 插件开发

AstrBot 4.x 插件开发规范与踩坑。覆盖:**写新插件 / Fork 改造现有插件 / 加 LLM 工具 / 调配置 schema / 验证加载**。

---

## 触发场景

- 用户要求"做个 AstrBot 插件" / "把 X 做成插件"
- 需要在 AstrBot 里加一个命令、事件钩子、LLM 工具
- Fork 上游 AstrBot 插件后做定制化
- 排查"插件加载失败 / 命令不响应 / 工具没注册"

---

## ⚠️ 铁律(从对话中复盘)

1. **先看官方文档再写**:`https://docs.astrbot.app/dev/star/plugin-new.html` 是入口。文档站部分链接 404,改路径试试(`/dev/star/guides/...`、`/dev/star/llm-tool.html` 实际路径可能不同)。**不要凭印象猜 API**——这次对话中我曾在没确认 `@filter.llm_tool` 是否存在时就敢写代码,被用户打断。
2. **先调研再开工**:写之前先 `web_search "astrbot 插件 <关键词>"` 找现成的。已经有 90% 相似插件就别造轮子——Fork + 改 3 行,胜过从零写 200 行。
3. **Ponytail 视角**:每次起步时问 "需要从零写吗?现有方案能复用吗?"。`astrbot_plugin_Pic` 已经支持栗次元,Fork 改造就是正确路径,不是从零写 `astrbot_plugin_alcy_pic`。
4. **写代码前先报方案**:列改动点 + 选型 + 风险 → 等用户确认 → 才动文件。禁止 "我先写完你看看"。
5. **改 memory 必查 plugins 目录**:`ls ~/astrbot/data/plugins/` 确认插件**真的装了**,不能凭 memory 说"X 插件已装"。

---

## 最小骨架(4 个文件)

```
astrbot_plugin_xxx/
├── main.py            # 入口,@register 类 + 装饰器方法
├── metadata.yaml      # 插件元数据
├── _conf_schema.json  # 配置 schema(可空 {})
└── requirements.txt   # 依赖(可空,但 aiohttp/httpx 建议列)
```

完整模板见 `templates/helloworld/`(可作为 scaffold 复制)。

### metadata.yaml

```yaml
name: astrbot_plugin_xxx              # 必须 astrbot_plugin_ 前缀,全小写,无空格
display_name: 展示名(可中文)            # WebUI 显示名
desc: 一句话描述
version: v1.0.0                        # v 前缀必须
author: YourName                       # Fork 时标注 ImNotBird / YourName
repo: https://github.com/you/repo
# 可选:
# short_desc: 卡片短描述
# support_platforms: [aiocqhttp, telegram, ...]   # ADAPTER_NAME_2_TYPE key
# astrbot_version: ">=4.16,<5"        # PEP 440 格式
```

### _conf_schema.json(空配置:写 `{}` 即可,文件不能缺)

可配置项类型:`string | text | int | float | bool | object | list | dict | file | template_list`。字段含义:

- `type`(必填)、`description`、`hint`、`default`、`options`(下拉)、`editor_mode`(代码编辑器)
- `_special`: `select_provider` / `select_persona` / `select_knowledgebase` 等(v4.0+)

详见 `references/conf-schema.md`。

### main.py 最小骨架

```python
import os
from typing import AsyncGenerator, Optional
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import (
    llm_tool, command, event_message_type, EventMessageType,
)
from astrbot.api import logger

@register("astrbot_plugin_xxx", "YourName", "描述", "v1.0.0",
          "https://github.com/you/repo")
class XxxPlugin(Star):
    def __init__(self, context: Context, config: Optional[dict] = None):
        super().__init__(context)
        self.config = config or {}

    @command("hi")
    async def cmd_hi(self, event: AstrMessageEvent):
        """hi - 打招呼命令"""
        yield event.plain_result(f"hi {event.get_sender_name()}")

    @llm_tool(name="send_x")
    async def llm_send_x(self, event: AstrMessageEvent, param: str = ""):
        """描述给 LLM 看。

        Args:
            param(string): 参数说明
        """
        # 可以 yield event.xxx_result(...),也可以 return str 给 LLM 总结
        yield event.plain_result("done")
        return "ok"

    async def terminate(self):
        """清理(可选)"""
```

---

## 装饰器一览

| 装饰器 | 模块 | 作用 | 关键参数 |
|--------|------|------|---------|
| `@register(name, author, desc, version, repo)` | `astrbot.api.star` | 类装饰器,声明插件 | 全部必填 |
| `@command("name")` | `astrbot.api.event.filter` | 注册命令(`/name`) | 命令名 |
| `@llm_tool(name="...")` | `astrbot.api.event.filter` | 注册 LLM 工具 | name(默认函数名) |
| `@event_message_type(EventMessageType.ALL)` | `同上` | 监听所有消息 | 事件类型 |
| `@regex("pattern")` | `同上` | 正则匹配 | 模式 |
| `@on_using_llm_tool` | `同上` | 当 AI 调工具时 | 工具名 |
| `@on_llm_tool_respond` | `同上` | 工具响应时 | 工具名 |

**LLM 工具函数签名**:docstring 必须写 `Args:\n    xxx(type): desc`,AstrBot 自动解析为 JSON Schema。支持类型:`string | number | object | array | boolean`。

详见 `references/decorators.md`。

---

## 发消息(返回值/生成器)

```python
# 纯文本
yield event.plain_result("hello")
# 图片(URL 或本地路径)
yield event.image_result("https://...")  # 或本地路径
# 链式组合(推荐异步生成器)
yield event.chain_result([Plain("hi"), Image.fromURL(url)])
# 文件图片(本地)
yield event.make_result().file_image("/path/to.png")
# 主动发(不等用户): await event.send(msg)
```

完整 `message_components` 列表(Plain/Image/Record/Video/At/Reply/Face/Node/Forward/Share/Music/Poke/...)在 `astrbot.core.message.components`。

---

## Fork 工作流(标准做法)

```bash
# 1. GitHub 上 fork
gh repo fork <upstream> --clone=false
# 例如:gh repo fork ImNotBird/astrbot_plugin_Pic

# 2. 克隆到本地 AstrBot 插件目录
cd ~/astrbot/data/plugins
gh repo clone <your_user>/<repo>

# 3. 改 metadata.yaml 的 name/author/version(同目录同名)
# 4. 改 main.py(加新装饰器、新功能)
# 5. 提交推送
cd ~/astrbot/data/plugins/<repo>
git add -A
git -c user.email=you@x -c user.name=you commit -F /tmp/msg
git push origin main
```

gh fork 自动加 upstream remote → `git fetch upstream && git merge upstream/main` 同步上游。

**commit message 文件**避免中文多行被 shell 吃换行,写到 `/tmp/msg` 再 `git commit -F`。

---

## 验证清单(每次必跑)

1. **Python 语法**:`python3 -c "import ast; ast.parse(open('main.py').read())"`
2. **AST 装饰器检查**:确认 `@command` / `@llm_tool` / `@register` 存在且参数对。`scripts/check_plugin.py` 可直接用。
3. **JSON 合法**:`python3 -c "import json; json.load(open('_conf_schema.json'))"`
4. **metadata 字段存在**:`python3 -c "import yaml; yaml.safe_load(open('metadata.yaml'))"`
5. **真加载验证**:`sudo systemctl restart astrbot` + `sudo journalctl -u astrbot --since '1 min ago' | grep -iE 'plugin <name>|llm tool: <tool>'`

成功标志:
```
[Core] Loading plugin astrbot_plugin_xxx ...
[Core] Added llm tool: <tool_name>
[Core] Plugin astrbot_plugin_xxx (vX.Y.Z) by Author: <desc>
```

**热重载陷阱**:`@filter.command` generator 在 system reload 时可能不重新绑定 → 改代码后必须 `sudo systemctl restart astrbot`,**不能只 WebUI 触发热重载**。

**日志位置**:AstrBot 4.x 单一日志走 systemd journal,**不是** `~/astrbot/logs/`(目录可能空)。用 `sudo journalctl -u astrbot`。

---

## 发布到插件市场(流程要点)

- 仓库命名必须 `astrbot_plugin_<name>`(全小写、`_` 分隔)
- `metadata.yaml` 字段齐全(name/display_name/desc/version/author/repo)
- 至少 1 个 release tag
- 提交 PR 到 `AstrBotDevs/AstrBot_Plugins_Collection`(或自建索引)
- **不需要**先建独立站点;GitHub 仓库就是发行渠道

---

## 常见坑

1. **Persona 在 WebUI 侧边栏,不在插件配置**:人格是 AstrBot 框架层功能,改 `provider_settings.default_personality` 或 WebUI 侧边栏 → 人格。插件里的 personality 字段是**叠加**补充,不替代。
2. **多套记忆/认知插件并存会污染**:livingmemory + self_learning + angel_heart/angel_memory 不能同时开,同条消息被记 N 次。保留一套,关其他。
3. **配置 schema 缺文件 vs 空 dict**:`_conf_schema.json` 缺失 vs `"{}"` 行为不同。空 dict = 显式无配置;缺文件 = 用插件自带默认。**没有它,`_conf_schema.json` 不会被读**。
4. **aiohttp 异步,requests 禁用**:AstrBot 开发原则明确"不要使用 requests 库"。所有外部 HTTP 用 `aiohttp` 或 `httpx`。
5. **持久化数据放 `data/` 下**:插件自身的目录会被更新/重装覆盖。数据存 `~/astrbot/data/<plugin_name>/`。
6. **图片网络重定向**:很多图源 API 返回 302,`httpx` 用 `follow_redirects=True` 自动跟,`aiohttp` 用 `allow_redirects=True`。
7. **LLM 工具返回值**:返回 `str` 进 LLM prompt 让其总结;返回 `None` 不进 prompt。要"发出去 + 总结"两边都要:`yield` 消息 + `return` 字符串。
8. **Fork 后没改 name**:Fork 仓的 `name` 跟上游同名,装到 AstrBot 时会跟上游版本冲突 → 改 name 加后缀。

---

## 与其他 Skill 的关系

- **astrbot-operations**:管部署/进程/人格,**不**管插件开发。两者互补。
- **astrbot-knowledge-base**:知识库管理(数据侧),不涉及插件骨架。
- **lab-server-deploy**:AstrBot 整体部署,跟插件开发正交。

---

## 速查文件

- 完整骨架模板:`templates/helloworld/`
- 装饰器/事件完整列表:`references/decorators.md`
- `_conf_schema.json` 详细字段:`references/conf-schema.md`
- LLM 工具签名/docstring 规则:`references/llm-tool-schema.md`
- AST 装饰器校验脚本:`scripts/check_plugin.py`
- 端到端验证脚本(语法+AST+JSON+YAML):`scripts/verify_plugin.py`
