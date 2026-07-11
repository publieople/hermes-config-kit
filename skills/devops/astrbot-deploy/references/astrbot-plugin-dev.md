# AstrBot 插件开发 — 实测参考手册

本参考基于 AstrBot v4.26+ (Python 3.12) 实际编写、加载、调试过程中验证的 API。文档站可能写得含糊或路径变 404，下面的内容是源码确认过的真值。

## 1. 文档站资源（写插件前必读）

| 用途 | URL | 备注 |
|------|-----|------|
| 插件骨架 | https://docs.astrbot.app/dev/star/plugin-new.html | 装饰器基本语法 |
| 配置 schema | https://docs.astrbot.app/dev/star/guides/plugin-config.html | `_conf_schema.json` 字段类型 |
| LLM 工具 | https://docs.astrbot.app/dev/star/guides/llm-tool.html | `@llm_tool` 注册 |
| Web 页面 | https://docs.astrbot.app/dev/star/guides/plugin-pages.html | `pages/` 目录内嵌 |
| 国际化 | https://docs.astrbot.app/dev/star/guides/plugin-i18n.html | `metadata.yaml` 多语言 |
| 官方模板 | https://github.com/Soulter/helloworld | `main.py` 最小骨架 |

**重要**：文档站偶有 404。比如 `llm-tool.html` 路径在某些版本是 `/dev/star/guides/llm-tool.html`，不是 `/dev/star/llm-tool.html`。如果某页打不开，去 `/docs.astrbot.app/dev/star/` 一层层点。

## 2. 装饰器 import 路径

所有装饰器都从 `astrbot.api.event.filter` 出：

```python
from astrbot.api.event.filter import (
    command,                  # @command("name")
    llm_tool,                 # @llm_tool(name="...")
    event_message_type,       # @event_message_type(EventMessageType.XXX)
    EventMessageType,         # 枚举: ALL/GROUP_MESSAGE/PRIVATE_MESSAGE/...
    on_llm_tool_respond,      # @on_llm_tool_respond()
    on_using_llm_tool,        # @on_using_llm_tool()
    regex,                    # @regex(r"...")
)
```

LLM 工具注册也支持直接调用 context：

```python
from astrbot.api.star import register  # @register("name", "author", "desc", "version", "repo?")
```

`register` 装饰器是 `Star` 子类的类级装饰，**不是方法装饰**。第一个 arg 是插件 id（不是目录名）。

## 3. 装饰器签名（实测）

### `@command(name)`
```python
@command("看图")  # 群里发 /看图 触发
async def cmd_pic(self, event: AstrMessageEvent, category: str = ""):
    # /看图 风景 → category="风景"
    # /看图          → category=""
    yield event.plain_result("...")  # 可 yield 多个 result
```

**注意**：参数按空格分隔。如果用 `/来点 风景 二次元`，函数签名是 `category: str = "", sub: str = ""` 才能接住两个。

### `@llm_tool(name, ...)`
```python
@llm_tool(name="send_pic")  # 名字暴露给 LLM
async def tool_send_pic(self, event: AstrMessageEvent, category: str = ""):
    """向用户发送一张随机图片。
    
    Args:
        category(string): 可选分类 key, 留空则随机。可用值: pc, moe, fj, ys, tx...
    """
    # 可以 yield 消息给用户看
    yield event.plain_result("好的,正在准备图片...")
    # 也可以 return 字符串给 LLM 汇总
    return "已发送一张图片"
```

**关键**：函数 docstring 写 `Args: xxx(type): desc`,AstrBot 解析成 JSON Schema 喂给 LLM。`type` 可选: `string` / `number` / `object` / `array` / `boolean`。

### `@event_message_type(EventMessageType.XXX)`
```python
@event_message_type(EventMessageType.ALL)
async def on_all(self, event: AstrMessageEvent):
    # 所有消息都会进这里
    if "我要看图" in event.message_str:
        await event.send(event.plain_result("好的"))
```

## 4. `event` 助手表

| 表达式 | 用途 | 返回类型 |
|--------|------|----------|
| `event.plain_result("text")` | 纯文本回复 | `MessageEventResult` |
| `event.image_result(url_or_path)` | 发一张图（URL/本地路径） | `MessageEventResult` |
| `event.chain_result([Image.fromURL(url)])` | 多 component 链 | `MessageEventResult` |
| `event.make_result().file_image(path)` | 本地图片消息 | `MessageChain` |
| `event.send(result)` | 主动推送（不等生成器） | awaitable |
| `event.message_str` | 纯文本消息 | `str` |
| `event.get_sender_name()` | 发送者昵称 | `str` |
| `event.get_sender_id()` | 发送者 ID | `str` |
| `event.unified_msg_origin` | 会话 ID | `str` |
| `event.is_admin` (callable) | 是否管理员 | `bool` |
| `event.stop_event()` | 终止事件传播 | None |

## 5. `Image` / `Record` / 其他 message component

`from astrbot.api.message_components import *` 拿到 `Image`/`Record`/`Video`/`File`/`At`/`Plain`/`Reply` 等。

构造方式：
- `Image.fromURL(url)` — 网络图片
- `Image.fromFileSystem(path)` — 本地文件
- `Image.fromBase64(b64_string)` — base64
- `Image.fromBytes(raw_bytes)` — 字节流

发图最常见两种写法：

```python
# 写法 1: 直接 URL
yield event.image_result("https://example.com/x.png")

# 写法 2: 本地文件
yield event.image_result("/tmp/x.png")

# 写法 3: chain 多 component
yield event.chain_result([
    Plain(text="分类 [风景横图]"),
    Image.fromURL(url)
])
```

## 6. `_conf_schema.json` 字段速查

v4.x 实测可用的字段类型：

```json
{
  "string_field":  {"type": "string", "default": "hello", "hint": "..."},
  "text_field":    {"type": "text", "default": "", "hint": "大文本框"},
  "int_field":     {"type": "int", "default": 0, "slider": {"min": 0, "max": 100}},
  "float_field":   {"type": "float", "default": 1.0},
  "bool_field":    {"type": "bool", "default": false},
  "object_field":  {"type": "object", "items": {"subkey": {"type": "string"}}},
  "list_field":    {"type": "list", "items": {"type": "string"}, "default": []},
  "select_string": {
    "type": "string",
    "options": ["a", "b", "c"],
    "labels": ["选项 A", "选项 B", "选项 C"]
  },
  "select_multichoice": {
    "type": "list",
    "items": {
      "type": "string",
      "options": ["k1", "k2", "k3"],
      "labels": ["K1 标签", "K2 标签", "K3 标签"]
    },
    "default": []
  },
  "select_provider": {
    "type": "string",
    "_special": "select_provider",
    "default": ""
  }
}
```

`_special` 字段（v4.0+）支持的值：
- `select_provider` — 选择 LLM provider
- `select_provider_tts` — TTS provider
- `select_provider_stt` — STT provider
- `select_persona` — 人格
- `select_knowledgebase` — 知识库（多选，type=list）

`options` + `labels` 配对使用：`options` 是值，`labels` 是 WebUI 显示名（等长数组）。

## 7. 在插件中读 config

`Star.__init__` 第二个参数是 `config: AstrBotConfig`：

```python
@register("my_plugin", "me", "desc", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: Optional[AstrBotConfig] = None):
        super().__init__(context)
        self.config = config or {}
        # 直接字典访问
        max_retries = int(self.config.get("max_retries", 2))
        # list 默认空列表处理
        enabled = self.config.get("enabled_categories") or list(DEFAULT_CATEGORIES)
```

## 8. 加载失败的诊断

**加载成功标志**（journal 看到这些行）：

```
[Core] Loading plugin astrbot_plugin_xxx ...
[Plug] Created images folder  ← 你的 logger.info 输出
[Core] Added llm tool: my_tool_name   ← LLM 工具注册成功
[Core] Plugin astrbot_plugin_xxx (v1.0.0) by author: desc
```

**没有 `Added llm tool:` 行 = 工具没注册**：可能是装饰器名错（`@llm_tool` vs `@llm_function`）、函数签名错（少 `event: AstrMessageEvent` 第一参）、docstring 缺 `Args:`。

**`ModuleNotFoundError` 在加载阶段**：
- `import aiohttp` / `import aiofiles` 等写 `requirements.txt` — AstrBot 不会自动装,首次重启会装
- WSGI 错误 → 重新 `sudo systemctl restart astrbot`

**热重载不生效**：
- 改 main.py 后,WebUI 点"重载插件"无效 → 必须 `sudo systemctl restart astrbot`（AstrBot 缓存了装饰器扫描结果）

## 9. fork 工作流

```bash
# 1. GitHub 端 fork
gh repo fork <upstream>/<name> --clone=false

# 2. 拉到自己
cd ~/astrbot/data/plugins
gh repo clone <your-username>/<name>  # 名字跟 GitHub 一致

# 3. 添加 upstream（gh fork 不一定自动加）
cd <name>
git remote add upstream https://github.com/<upstream>/<name>.git
git fetch upstream

# 4. 改代码 + commit + push
git add -A
git -c user.email=you@example.com -c user.name=you commit -m "..."
git push origin main

# 5. 让 AstrBot 重新加载
sudo systemctl restart astrbot
```

## 10. 不踩的坑

- **不要** 在插件目录外（`~/astrbot/data/config/...`）建 `metadata.yaml` 引用插件。
- **不要** `pip install` 第三方包到系统 Python。AstrBot 用 uv tool 部署，装到系统 Python 它读不到。要么写在 `requirements.txt` 让 AstrBot 装，要么装到 `/home/po/.local/share/uv/tools/astrbot/bin/` 对应的 venv。
- **不要** `gh repo fork --clone=true` 之后又 `git remote add upstream` 加错名字（容易和 origin 重复）。用 `--clone=false` 在 GitHub 端先 fork，再单独 clone。
- **不要** 在主分支直接改代码再 push — 提 PR 的话应该开 feature branch；自用就直接 push main，简单。
- **不要** 忘记 `__pycache__/` 排除（`rm -rf __pycache__/` 后再 commit，否则 push 进去污染仓库）。

## 11. 实战 ad-hoc 验证脚本模板

```python
"""ad-hoc: verify my_plugin vX.Y.Z changes."""
import ast, json, re, sys
from pathlib import Path

p = Path("/path/to/plugin/main.py")
src = p.read_text()
ok = True
def chk(label, cond, detail=""):
    global ok
    mark = "OK  " if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f" -- {detail}" if detail else ""))
    ok &= cond

tree = ast.parse(src)

# 1. 找 @llm_tool
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "llm_tool":
        for kw in n.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                chk(f"@llm_tool name={kw.value.value}", True)

# 2. 找 @command
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "command":
        if n.args and isinstance(n.args[0], ast.Constant):
            chk(f"@command name={n.args[0].value}", True)

# 3. 找 @register
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "register":
        if n.args and isinstance(n.args[0], ast.Constant):
            chk(f"@register name={n.args[0].value}", True)

# 4. _conf_schema.json 合法
sch = json.load(open("/path/to/plugin/_conf_schema.json"))
chk("schema JSON valid", True)

# 5. options + labels 长度匹配
for k, v in sch.items():
    if isinstance(v, dict) and "options" in v and "labels" in v:
        chk(f"{k} options/labels aligned", len(v["options"]) == len(v["labels"]))

print(f"\nresult: {'ALL OK' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
```

跑一次、删脚本。这是 spec-first 实践的延伸——把"我心里想这样对"翻译成"代码说它是这样"。
