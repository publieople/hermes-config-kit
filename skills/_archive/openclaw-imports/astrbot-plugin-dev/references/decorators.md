# AstrBot 装饰器与事件 API

基于 AstrBot 4.x core/star/filter 与 core/star/register。**版本变化时核对源码**:`/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/star/filter/__init__.py`。

## 入口导入

```python
from astrbot.api.star import Context, Star, register
from astrbot.api.event.filter import (
    llm_tool, command, command_group,
    event_message_type, EventMessageType,
    regex,
    platform_adapter_type,
    on_using_llm_tool, on_llm_tool_respond,
    permission,
)
```

## @register(name, author, desc, version, repo)

**唯一**的类装饰器,声明插件存在。**必须**在 `Star` 子类上。参数全部必填。

```python
@register("astrbot_plugin_xxx", "Author", "desc", "v1.0.0", "https://github.com/...")
class XxxPlugin(Star):
    ...
```

## @command("name")

注册命令。用户输入 `/name` 触发(中文命令名也可,如 `/看图分类`)。

```python
@command("hi")
async def cmd_hi(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
    yield event.plain_result("hello")
```

命令名**不带** `/`,命令里用空格分隔参数。函数 docstring 写"`name - desc`"格式会被解析为命令帮助。

**带参数**:`@command("hentai")` 后面接收 `def hentai(self, event, arg1: str = "", arg2: str = "")`,AstrBot 自动把命令后的内容按空格拆分传参。

## @command_group

命令组(子命令树),如 `/tool list` / `/tool add xxx`。具体用法查文档。

## @llm_tool(name="...")

注册 LLM 工具。**函数签名必须** `event: AstrMessageEvent` + 类型化参数;**docstring 必须**有 `Args: <name>(<type>): <desc>`,否则 LLM 看到空 schema 不会调。

```python
@llm_tool(name="send_pic")
async def llm_send_pic(self, event: AstrMessageEvent, category: str = ""):
    """向用户发送一张随机图片。

    Args:
        category(string): 可选分类 key(留空随机)
    """
    # 1) yield 消息直接发
    yield event.plain_result("处理中")
    # 2) return 字符串进入下次 LLM prompt,让 LLM 总结工具结果
    return "已发送图片"
```

支持的类型(string/number/object/array/boolean)在 `register/star_handler.py:register_llm_tool` docstring。

**返回值语义**:
- `str` → 进入下次 LLM prompt 让 LLM 总结
- `None` → 不进入 prompt
- `yield` 中间任意时刻可发消息给用户

## @event_message_type(EventMessageType.X)

监听事件类型。常用:

```python
EventMessageType.ALL        # 所有消息
EventMessageType.GROUP_MESSAGE
EventMessageType.PRIVATE_MESSAGE
EventMessageType.OTHER_MESSAGE  # 系统事件
```

```python
@event_message_type(EventMessageType.ALL)
async def on_message(self, event: AstrMessageEvent) -> Optional[MessageEventResult]:
    text = event.message_str.lower()
    if "触发词" in text:
        return event.plain_result("回复")
    return None  # 返回 None 不回复
```

**坑**:`filter.on_message()` 这个名字**不存在**,用 `event_message_type(EventMessageType.ALL)` 代替。

## @regex("pattern")

正则匹配消息文本。`@regex(r"^!echo (.+)$")` 然后 `def on_echo(self, event, match: re.Match)`,AstrBot 把 match 对象传进来。

## @platform_adapter_type

限制监听特定平台适配器(`ADAPTER_NAME_2_TYPE` key,如 `aiocqhttp` / `telegram` / `discord`)。

## @on_using_llm_tool / @on_llm_tool_respond

钩子:当任意 LLM 工具被调用 / 响应时触发,用于日志、统计、限流。

```python
@on_using_llm_tool("send_pic")  # 仅特定工具
async def on_tool_used(self, event, tool_call): pass
```

## @permission

权限控制(管理员/群主/普通用户)。`from astrbot.core.star.filter.permission import ...`。

---

## event 常用方法

| 方法 | 说明 |
|------|------|
| `event.message_str` | 纯文本消息字符串 |
| `event.get_sender_name()` | 发送者昵称 |
| `event.get_sender_id()` | 发送者 QQ 号 |
| `event.get_messages()` | 消息链(list) |
| `event.plain_result(text)` | 纯文本 MessageEventResult |
| `event.image_result(url_or_path)` | 图片 MessageEventResult |
| `event.chain_result([comp, ...])` | 链式组合 |
| `event.make_result().file_image(path)` | 本地文件图片 |
| `event.send(msg)` | **主动**发消息,不等 LLM |
| `event.stop_event()` | 终止事件传播 |
| `event.is_admin` (callable) | 是否管理员 |

`AstrMessageEvent` 完整 API 在 `astrbot/core/platform/astr_message_event.py`,`image_result` 在第 400 行,`chain_result` 第 409 行。
