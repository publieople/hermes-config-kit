# LLM 工具签名与 docstring Schema 规则

来源:源码 `astrbot/core/star/register/star_handler.py:580 register_llm_tool` docstring。

## 装饰器

```python
from astrbot.api.event.filter import llm_tool

@llm_tool(name="my_tool")  # name 可省,默认用函数名
async def my_tool(self, event: AstrMessageEvent, param1: str = "", param2: int = 0):
    """LLM 看到的工具描述。

    长描述写在这里,LLM 决定要不要调用、传什么参数。

    Args:
        param1(string): 第一个参数,字符串类型
        param2(number): 第二个参数,数字
    """
    yield event.plain_result("doing...")
    return "result"  # 或 None
```

## docstring 解析规则

`register_llm_tool` 解析 docstring 提取:
1. **第一段(直到 `Args:` 前)**:工具的 `description`
2. **`Args:` 段**:每个参数一行 `name(type): desc`,转成 JSON Schema `parameters.properties`

**没写 `Args:`** → 参数列表为空,LLM 看到 `{}` 不会传参,工具基本没用。

## 支持的参数类型

| Python type | docstring tag | JSON Schema type |
|-------------|---------------|------------------|
| `str` | `string` | `"string"` |
| `int`, `float` | `number` | `"number"` |
| `bool` | `boolean` | `"boolean"` |
| `list` | `array` | `"array"` |
| `dict` | `object` | `"object"` |

## 函数签名约束

- **第一个参数** 必须是 `event: AstrMessageEvent`(或类似事件对象,具体看装饰器)
- 后续参数必须有**类型注解** —— 没注解会被当成 string 但 schema 解析会失败
- **默认值** 强烈建议给,LLM 偶尔漏传参数不报错

```python
# ✅ 正确
@llm_tool(name="x")
async def x(self, event, a: str, b: int = 0, c: bool = False): pass

# ❌ 错误
@llm_tool(name="x")
async def x(self, event, a, b): pass  # 没类型注解
```

## 返回值

- `return "text"` → 文本进入下次 LLM prompt,LLM 据此继续生成
- `return None` → 不进 prompt,工具调用"哑火"
- `return` 不写 → 等同 None

**`yield` 和 `return` 同时存在**:`yield` 的消息直接发给用户,`return` 进 prompt 让 LLM 总结。这是大多数工具的标准模式:

```python
@llm_tool(name="do_thing")
async def do_thing(self, event, x: str = ""):
    """做某事并发送结果。

    Args:
        x(string): 输入
    """
    result = do_something(x)
    yield event.plain_result(f"已处理: {result}")
    return result  # 进 LLM prompt
```

## 多工具组合 + 工具发现

LLM 一次能看多个工具。**每个工具独立可调用**,组合由 LLM 决定(可能一次调多个,或链式调用)。

工具名要清晰:LLM 看到 `send_random_pic` 知道是"发图",看到 `x` 完全不知道。

## 触发调试

1. WebUI → 插件配置 → 确认插件已加载
2. 跟 bot 说话,要求它做某件工具能做的事(如"给我发张图")
3. 看日志:`journalctl -u astrbot --since '1m' | grep -iE 'llm tool:|tool call'`
4. 看到 `Added llm tool: <name>` 说明注册成功

## 常见坑

1. **docstring 缩进错**:`Args:` 必须顶格或符合 PEP 257,AstrBot 用 docstring parser 解析
2. **中文参数名**:JSON Schema key 不能含中文,函数参数名用英文(`category` 而非 `分类`)
3. **类型注解跟 docstring 不一致**:Python 注解 `int` 但 docstring 写 `string` → schema 错乱,以注解为准
4. **参数太多**:5+ 个参数 LLM 容易选错,3 个以内最稳
5. **description 写太短**:LLM 不会判断边界情况,描述里要写明"什么时候用 / 不用"

## 完整例子

```python
@llm_tool(name="search_memory")
async def llm_search_memory(self, event: AstrMessageEvent, query: str, limit: int = 5):
    """在用户的长期记忆里搜索相关内容。

    当用户问"我之前说过什么"或"你记得吗"时调用。返回相关的记忆片段。

    Args:
        query(string): 搜索关键词,使用用户问题原话
        limit(number): 返回条数,默认 5
    """
    results = self.memory.search(query, top_k=limit)
    if not results:
        return "没找到相关记忆"
    formatted = "\n".join(f"- {r.content}" for r in results)
    return f"找到 {len(results)} 条:\n{formatted}"
```
