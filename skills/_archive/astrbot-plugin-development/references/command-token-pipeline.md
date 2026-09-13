# AstrBot `@filter.command` 命令处理管道 — token 切分、位置分配、GreedyStr

**适用场景**: 调试命令"参数没生效""被静默截断""第 3 个 token 没了" 类 bug；写带空格的命令（中文番剧名 + 多段参数）；评估"加新参数 vs 在一个字段里塞多格式"的设计取舍。

## 完整处理路径（基于 AstrBot v4.26.5，源码 `astrbot/core/star/filter/command.py`）

### 1. `@filter.command("X")` 注册（class body scan）
- `CommandFilter.__init__` 扫描函数签名，把参数名→类型/默认值存到 `self.handler_params: dict`
- decorator 在 **class load time**（import 时）执行，不在运行时
- 因此**不能**在循环里注册命令、不能动态加新参数

### 2. 消息匹配 (`filter()` 方法)
```python
message_str = re.sub(r"\s+", " ", event.get_message_str().strip())  # 多空格压成单空格
ok = False
for full_cmd in self.get_complete_command_names():
    if message_str.startswith(f"{full_cmd} ") or message_str == full_cmd:
        ok = True
        message_str = message_str[len(full_cmd):].strip()
if not ok: return False
```

### 3. **位置切分（关键 — 全文最坑的地方）**
```python
ls = message_str.split(" ")              # ← 按空格切, 不是按 key 名
ls = [param for param in ls if param]    # 去空
params = self.validate_and_convert_params(ls, self.handler_params)
```

### 4. 按位置分配 (`validate_and_convert_params`)
遍历 `handler_params` 项，`i` 是参数索引，`params[i]` 是第 i 个 token：

| 参数 index | handler 形参 | 拿到的值 |
|---|---|---|
| 0 | `name: str` | `tokens[0]` |
| 1 | `time: str` | `tokens[1]` |
| 2 | （无） | **丢弃** |

**如果 token 数 > 形参数**，超出部分**静默丢弃，无报错无警告**。  
**如果 token 数 < 形参数**，缺的位置用默认值（带 `= ""` 的）；无默认值则 `ValueError("必要参数缺失")`。

### 5. GreedyStr 特殊路径
```python
is_greedy = param_type_or_default_val is GreedyStr
if is_greedy:
    if i != len(param_items) - 1:
        raise ValueError(f"参数 '{param_name}' (GreedyStr) 必须是最后一个参数。")
    remaining_params = params[i:]   # ← 把当前位置+之后所有 token 全 join
    result[param_name] = " ".join(remaining_params)
    break
```
`GreedyStr` 把**当前索引及之后**的所有 token 合并成一个字符串给你，**之前的 token 仍按位置分配**。所以：

```python
# 错误用法 (有其他参数在 GreedyStr 之前)
async def cmd(self, event, name: str = "", args: GreedyStr = GreedyStr("")):
    pass

# 正确用法 (GreedyStr 必须最后)
async def cmd(self, event, args: GreedyStr):
    tokens = str(args).split()  # 拿全部 token 自己处理
```

#### ⚠️ GreedyStr 默认值陷阱：`is GreedyStr` 用 class 比较，不是 instance

`CommandFilter.init_handler_md` (L76-79) 拿形参时：
```python
if v.default == inspect.Parameter.empty:
    self.handler_params[k] = v.annotation   # class
else:
    self.handler_params[k] = v.default      # ← 默认值的 INSTANCE
```
然后 `validate_and_convert_params` 判断 `is_greedy = param_type_or_default_val is GreedyStr`（class 比较）。
**后果**：
- `args: GreedyStr = GreedyStr("")` → `handler_params["args"] = GreedyStr("")`（实例）→ `instance is GreedyStr` 永远 False → GreedyStr 路径不进 → 当普通字符串 → 按位置取第 i 个 token（**不是全部**）
- `args: GreedyStr` 无默认值 → `handler_params["args"] = GreedyStr`（class）→ `is GreedyStr` True → 全 join
- 缺 token 无默认值会 raise `ValueError("必要参数缺失")`

**验证方法**：在 handler 第一行 `logger.info(f"DEBUG args={args!r}")` 看实际拿到什么。

**修法四选一**（按场景）：

| 场景 | 推荐 |
|---|---|
| 命令必带参数（如 bilibili 的 `bili_global_sub`） | `args: GreedyStr`（无默认值），缺 token 时 raise 失败 |
| 命令可空（无参走"列全部"分支，有参走 N 段参数） | **官方标准模式：保留 `command(name, x)` 单参数 + handler 内 `event.message_str` 自拆**（见下方 qzone 范式） |
| 想完全脱离 AstrBot 命令路由自己定义语法 | `@filter.regex(r"^/X(?:\s+(.*))?$")` + `event.get_message_str()` 自解析 |
| 想兼容"无参 + 多参"且不想用 regex | ASTRBOT 不支持"GreedyStr 可选"——只能加空检测或新命令 |

#### 官方标准模式：`@filter.command` + `event.message_str` 自拆（qzone 范式）

AstrBot 官方插件 `astrbot_plugin_qzone` 处理 `<序号>`/`<@群友>`/范围参数的方式，是装饰器签名 0~1 个 token，内部 `event.message_str` 拿全文自解析。**这是 AstrBot 自己团队的标准写法**，比 GreedyStr 和 `@filter.regex` 都更稳——命令仍然走 `/` 前缀路由，不影响 `/help` 自动补全。

```python
# 来源: astrbot_plugin_qzone/main.py "评说说" 命令
@filter.command("评说说", alias={"评论说说", "读说说"})
async def comment_feed(self, event: AiocqhttpMessageEvent):  # 0 token 参数
    """评说说 <序号/范围>"""                                # docstring 只是说明
    posts = await self._get_posts(event, no_commented=True, no_self=True)
    # ...

# _get_posts 内部用 event.message_str (注意是属性不是 get_message_str 方法):
def parse_range(event: AstrMessageEvent) -> tuple[int, int]:
    """用户输入: n / s~e / 无 — 拿到 (offset, limit)"""
    parts = event.message_str.strip().split()  # 完整 args 都在这里
    if not parts:
        return 0, 1
    end = parts[-1]
    if "~" in end:
        s, e = end.split("~", 1)
        # ...
```

**应用到你自己的命令**（比如 `放送时间 无职转生 周日 23:00`）：

```python
@filter.command("放送时间")
async def show_broadcast_time(self, event: AstrMessageEvent, name_or_id: str = ""):
    # command 装饰器只接 1 个 token (name_or_id), 多 token 的部分自己拿 message_str 拆
    raw = event.message_str.strip()
    for prefix in ("/放送时间", "放送时间"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):].lstrip()
            break
    tokens = raw.split()  # 全部 args (包括被 command 装饰器丢掉的第 3+ token)
    # tokens[0] == name_or_id, 剩下的自己从 tokens[-2:] 反解析 HH:MM / 周X HH:MM
    ...
```

#### ⚠️ aiocqhttp `event.message_str` 末尾带 `[MSG_ID:xxx]` —— 反向扫描才是对的

qzone 范式默认假设 `event.message_str` 等于"用户原始文本"。**aiocqhttp adapter 不成立**——它在 message_str 末尾追加 `[MSG_ID:<id>]`，日志里看 `user_message=<user input> [MSG_ID:1744020215]`。`tokens[-1]` / `tokens[-2]` 会拿到 `[MSG_ID:...]` 这种 token，HH:MM 匹配不上但**不会报错**，让你以为"格式错误"其实只是尾部索引错了。

**症状**：`tokens[-2:]` 拿到的尾两段对不上 `HH:MM` / `周X` 模式，但中间 token 里能找到完整 `HH:MM`；`logger.warning(f"DEBUG full_tokens={full_tokens}")` 能看到末尾的 `[MSG_ID:xxx]` 段。

**修法（反向扫描找第一个合法 token）**：

```python
for i in range(len(full_tokens) - 1, 0, -1):
    if time_pat.match(full_tokens[i]):           # 找第一个 HH:MM (从尾往头)
        time_str = full_tokens[i]
        if i >= 2 and (
            full_tokens[i - 1] in weekday_map
            or (full_tokens[i - 1].isdigit() and 1 <= int(full_tokens[i - 1]) <= 7)
        ):
            weekday = weekday_map.get(full_tokens[i - 1]) or int(full_tokens[i - 1])
        break
# 其它位置取 weekday / 清空标记的代码也类似: 从后往前扫
```

**trigger signal**：self-parse 报 "时间格式错误" / weekday=None，但用户消息里其实有正确 `HH:MM`；debug log 末尾有 `[MSG_ID:` 段。**通用化**：任何 aiocqhttp 插件用 `event.message_str` 自拆前，都应该在 handler 第一行 `logger.warning(f"DEBUG raw={event.message_str!r}")` 看实际内容，确认 adapter 后缀是否干扰解析。

**为什么这是首选**：
- `@filter.command` 路由命中 + `/help` 自动补全都保留（regex filter 不进 command_management）
- 不会撞 GreedyStr 默认值陷阱
- 不会撞 `@filter.regex` 不走命令路由导致"命令没被插件收到，只触发 LLM"的问题
- 装饰器签名最小化（1 个可选参数），token 切分只是兜底路由，主战场在 `event.message_str`

**何时仍用 GreedyStr / regex**：如果想强调"args 必须存在"（bilibili 的全局订阅场景），用 GreedyStr 让缺 token 直接 raise；如果命令语法完全不规则（必须自定义引号、嵌套等），用 regex 完全自控。

## 常见 bug 与决策表

### Bug 1: "时间格式错误" 但用户明明写了正确 HH:MM
**根因**: `split(" ")` 把 token 数切多于形参数, 第 3+ 个 token 被吞。
**验证**:
```python
# 在你的 handler 第一行加 print, 确认 args 数量
@filter.command("my_cmd")
async def cmd(self, event, a: str = "", b: str = ""):
    logger.info(f"DEBUG: a={a!r}, b={b!r}")  # 用户报"格式错误"时看这里
```

### Bug 2: 中文番剧名带空格被截断
**症状**: `/追番 "无职转生 第三季"` 只匹配到 `无职转生`，后续被当成新参数。
**真相**: tokenizer **不解析引号**。`validate_and_convert_params` 直接按 `split(" ")` 切。
**修法**: 用 GreedyStr 收全部 args，自己 join。或者用官方 qzone 范式（`event.message_str` 自拆）。

### Bug 3: 加第 3 个参数编译期 OK 运行时无效
**症状**: `async def cmd(self, event, a, b, c)` 三个形参，但用户发 `/cmd 1 2 3 4` 第 4 个丢了。
**修法**: 同上，GreedyStr 或 qzone 范式。

### Bug 4: aiocqhttp `[MSG_ID:xxx]` 后缀导致 `tokens[-1]/[-2]` 解析失败
**症状**: self-parse 走完日志报 "时间格式错误" 或 weekday=None，但消息里有合法 `HH:MM`。
**根因**: `event.message_str` 末尾被 aiocqhttp adapter 追加 `[MSG_ID:<id>]`，`tokens[-1]` 拿到的是后缀段。
**修法**: 反向扫描找第一个合法 `HH:MM` token，详见"aiocqhttp `event.message_str` 末尾带 `[MSG_ID:xxx]`" 节。
**预防**: handler 第一行 `logger.warning(f"DEBUG raw={event.message_str!r}")` 一行确认 adapter 后缀。

## 决策树：新加参数怎么办

```
需要从用户消息里取第 3 段 / 段数不定？
├─ 段数固定且 < 3 → 加形参 OK（但要测试边界）
├─ 段数固定但 ≥ 3 → 必须 GreedyStr 或 qzone 范式
├─ 段数不定（"周X HH:MM" 等可选前缀） → qzone 范式 + 自己解析（首选）
│                                       └─ 也可 GreedyStr（需无默认值）
└─ 用户期望"按 key 名"匹配 → 不支持，AstrBot 不解析引号不解析 =
```

## 测试用例（不入库, dev 时复制)

```python
import re
from astrbot.core.star.filter.command import GreedyStr

def parse_args(args_str: str):
    """replicate AstrBot tokenization in your handler"""
    s = re.sub(r"\s+", " ", args_str.strip())
    tokens = s.split(" ") if s else []
    return [t for t in tokens if t]

cases = [
    ("无职转生 周日 23:00",          ["无职转生", "周日", "23:00"]),
    ("无职转生 第三季 周日 23:00",    ["无职转生", "第三季", "周日", "23:00"]),
    # aiocqhttp adapter 在 message_str 末尾追加 [MSG_ID:xxx], 自拆逻辑必须容忍
    ("无职转生 周日 23:00 [MSG_ID:1744020215]", ["无职转生", "周日", "23:00", "[MSG_ID:1744020215]"]),
    ("",                             []),
    ("  ",                           []),
]
for inp, expected in cases:
    got = parse_args(inp)
    assert got == expected, f"FAIL {inp!r}: got {got}, want {expected}"
print("AstrBot tokenizer parity: OK")

# 反向扫描找 HH:MM 的回归测试
def find_time_and_weekday(tokens, time_pat, weekday_map):
    weekday = None
    time_str = ""
    for i in range(len(tokens) - 1, 0, -1):
        if time_pat.match(tokens[i]):
            time_str = tokens[i]
            if i >= 2 and (
                tokens[i - 1] in weekday_map
                or (tokens[i - 1].isdigit() and 1 <= int(tokens[i - 1]) <= 7)
            ):
                weekday = weekday_map.get(tokens[i - 1]) or int(tokens[i - 1])
            break
    return weekday, time_str

time_pat = re.compile(r"^([01]\d|2[0-9]):([0-5]\d)$")
weekday_map = {"周一":1,"周二":2,"周三":3,"周四":4,"周五":5,"周六":6,"周日":7}
reverse_cases = [
    (["无职转生","周日","23:00"],                                    7, "23:00"),
    (["无职转生","周日","23:00","[MSG_ID:1744020215]"],               7, "23:00"),
    (["无职转生","7","24:28"],                                       7, "24:28"),
    (["无职转生","22:00"],                                          None, "22:00"),
    (["无职转生","周日","23:00","foo","bar"],                        7, "23:00"),
    (["无职转生","清空"],                                           None, ""),
]
for tokens, exp_wd, exp_t in reverse_cases:
    wd, t = find_time_and_weekday(tokens, time_pat, weekday_map)
    assert (wd, t) == (exp_wd, exp_t), f"FAIL {tokens}: got {(wd, t)}, want {(exp_wd, exp_t)}"
print("Reverse-scan parser: OK")
```

## 跨版本注意
- AstrBot v3 vs v4 的命令处理路径**不同**——v3 是 `click` 风格，支持 type hints 转 int/bool/...；v4 是当前这套位置分配。
- 老插件从 v3 升 v4 时如果依赖了 click 的 type conversion（比如 `count: int = 0`），会在 v4 下报错或拿不到值——必须改成 `count: str = "0"` 自己 `int()`。
- GreedyStr 在 v3 没有，v4.20+ 才加的。

## 文件位置
- `astrbot/core/star/filter/command.py:191-220` — `CommandFilter.filter`
- `astrbot/core/star/filter/command.py:93-179` — `validate_and_convert_params`
- `astrbot/core/star/filter/command.py:15` — `class GreedyStr(str)`
- 官方范式参考：`astrbot_plugin_qzone/main.py`（所有 `@filter.command` 都是 0~1 个 token，参数走 `event.message_str`）

## 完整决策流程（新增/修改命令前必读）

1. **先 trace 一次完整调用链**：用户消息 → AstrBot 接收 → `event.message_str` 是什么 → `CommandFilter.filter()` 怎么切 token → handler 拿到什么 → 自己下游代码怎么解析。这一步**在写任何 patch 之前做**。
2. **本地确认 `event.message_str` 拿到的是原始用户文本**：QQ adapter 可能 strip 前缀也可能不 strip，看源码确认；qzone 写法用 `event.message_str.strip().split()` 是因为 `message_str` 拿到的是 strip 后的明文。
3. **评估段数**：固定 ≤2 段直接形参；固定 ≥3 段或段数不定用 qzone 范式（首选）或 GreedyStr。
4. **改完后 `ast.parse()` 校验 + `logger.info(f"DEBUG: tokens={tokens}")` 看实际拿到**——别靠脑补。
5. **用户报"还是有问题"** 时，**回 step 1 重新 trace**。不要继续 patch 表面逻辑。