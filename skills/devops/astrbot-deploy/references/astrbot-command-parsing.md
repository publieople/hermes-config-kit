# AstrBot `@filter.command` 参数解析 — 实战笔记

## 底层行为 (v4.26.5 源码确认)

`astrbot/core/star/filter/command.py` 关键流程:

```python
# L199-211
message_str = re.sub(r"\s+", " ", event.get_message_str().strip())
ok = False
for full_cmd in self.get_complete_command_names():
    if message_str.startswith(f"{full_cmd} ") or message_str == full_cmd:
        ok = True
        message_str = message_str[len(full_cmd) :].strip()
ls = message_str.split(" ")
ls = [param for param in ls if param]  # 过滤空 token
params = self.validate_and_convert_params(ls, self.handler_params)
```

`handler_params` 来自函数签名(忽略 `self`/`event`)。L76-79:

```python
if v.default == inspect.Parameter.empty:
    self.handler_params[k] = v.annotation   # 类型本身
else:
    self.handler_params[k] = v.default       # 默认值实例
```

`validate_and_convert_params` L101-114 判 GreedyStr:

```python
is_greedy = param_type_or_default_val is GreedyStr  # class 比较
```

## 三大坑的实际表现

### 坑 1: 多 token 截断

| 用户输入 | 函数签名 | 实际收到 |
|---------|---------|---------|
| `/追番 无职转生` | `name: str` | `name="无职转生"` OK |
| `/追番 无职转生 第三季` | `name: str` | `name="无职转生"` (季丢) |
| `/追番 无职转生 第三季` | `name: str, sub: str = ""` | `name="无职转生", sub="第三季"` OK |
| `/放送时间 无职转生 周日 23:00` | `name: str, time: str = ""` | `name="无职转生", time="周日"` (23:00 丢) |

**根因**: `ls[:N]` (N=参数个数),剩余丢弃。

### 坑 2: `GreedyStr` 默认值失效

```python
# BAD  默认值写法 — args 退化成普通字符串,取第 1 个 token
async def show(self, event, args: GreedyStr = GreedyStr("")):
    tokens = str(args).split()
    # 此时 args 实际是命令后的第一个 token

# GOOD  正确写法 — 不给默认值
async def show(self, event, args: GreedyStr):
    raw = event.get_message_str().strip()
    for prefix in ("/放送时间", "放送时间"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):].lstrip()
            break
    tokens = raw.split()
```

`GreedyStr` 默认值失效的根因:

- `handler_params[k] = v.default` (默认值实例 `GreedyStr("")`)
- `is_greedy = GreedyStr("") is GreedyStr` → **False** (instance vs class)
- 走普通字符串路径,按位置取 token

**bilibili 插件的写法验证**: `astrbot_plugin_bilibili/main.py` 的 `dynamic_sub(self, event, uid: str, input: GreedyStr)` 无默认值 — 它需要 `uid` 和 `input` 都是必填,无默认值时缺参会 `raise ValueError("必要参数缺失")`,由 AstrBot 吞掉当未匹配。

### 坑 3: `@filter.regex` 不走命令路由

`@filter.regex(r"^/放送时间(?:\s+(.*))?$")` 看上去是更"直接"的方案,但:

- 路由路径完全不同 — AstrBot 的 wake_prefix / AT_OR_WAKE_COMMAND 检测在 CommandFilter 里,regex 跳过这些
- **容易被 LLM 自然语言回复抢答**: 用户发 `怎么设置放送时间`,regex 不匹配,但 AngelHeart/AstrNa 等前置插件可能把消息转发给 LLM,LLM 调用 bangumi 插件的工具而不是命令
- 命令名字(`/xx`)如果不在 AstrBot 的命令表里,WebUI 的 help 也不会显示

**验证**: 重载后 `journalctl` 看 `Loading plugin ...` 后**没**新行,但命令还是被 regex filter 触发 — 这一点难以用日志确认,只能观察行为(发命令后 AstrBot 是否只回了 regex handler 的输出,没走 LLM)。

### 坑 4: `event.message_str` / `get_message_str()` 末尾带 `[MSG_ID:xxx]`

**仅 aiocqhttp adapter 受影响**。`event.message_str` 不只是用户输入,末尾还带 QQ 消息 ID:

```
[23:51:25] user_message=放送时间 无职转生 周日 23:00 [MSG_ID:1744020215]
```

用 self-parse 时如果直接 `tokens[-1]` / `tokens[-2]` 取末尾两个 token,会拿到 `23:00` + `[MSG_ID:1744020215]`,时间解析失败。

**修法**: 不要固定取尾部,从尾反向扫描第一个匹配的 `HH:MM`:

```python
time_pat = re.compile(r"^([01]\d|2[0-9]):([0-5]\d)$")
for i in range(len(tokens) - 1, 0, -1):
    if time_pat.match(tokens[i]):
        time_str = tokens[i]
        # weekday 在它前一位
        if i >= 2 and (tokens[i-1] in weekday_map or
                       (tokens[i-1].isdigit() and 1 <= int(tokens[i-1]) <= 7)):
            weekday = weekday_map.get(tokens[i-1]) or int(tokens[i-1])
        break
```

**复用 framework 切分时不受影响** (切的是前 N 个 token,不会切到末尾的 `[MSG_ID:]`),所以走坑 1 的解法天然规避。只有用 `event.message_str` 自拆时才踩。

**诊断**: 加 logger 打印 `full_tokens` 列表,看到末尾带 `[MSG_ID:...]` 就确认了。

## 推荐的统一解法 (跨命令复用)

```python
from astrbot.core.star.filter.command import GreedyStr

@filter.command("xxx")  # 仍走命令路由,helper 文案/help 都生效
async def handler(self, event: AstrMessageEvent, args: GreedyStr):
    """接收完整 args 自己解析。"""
    raw = event.get_message_str().strip()
    # 剥前缀(兼容 /前缀 / 无斜杠两种触发方式)
    for prefix in (f"/{CMD_NAME}", CMD_NAME):
        if raw.startswith(prefix):
            raw = raw[len(prefix):].lstrip()
            break
    if not raw:  # 用户没传参
        # 走 "无参" 分支
        ...
    tokens = raw.split()
    # 自己处理多 token
```

**要求无参也能触发命令**时这种解法没问题;**GreedyStr 无默认值 + 用户无参调用 → ValueError → AstrBot 当未匹配吞掉**,行为上跟命令不存在一样,但不会崩。

## 已踩过的 Bangumi 插件实例 (publieople fork)

`/放送时间` 历史上走过:

1. BAD  `name: str = "", time: str = ""` — 三段以上 token 被截
2. BAD  `args: GreedyStr = GreedyStr("")` — 默认值让 GreedyStr 失效,args 退化成首 token
3. BAD  `@filter.regex(r"^/放送时间(?:\\s+(.*))?$")` — 路由绕过,被 LLM 抢答
4. GOOD  `@filter.command("放送时间") + args: GreedyStr + 自己 split` — 正确

第 4 种写法是当前 fork 推荐模式。其他类似命令(`/追番`、`/弃坑`、`/bgm番剧`)番剧名都含空格,**用同样的解法重写**是顺手的事。

## 诊断命令 (5 秒内定位问题)

```bash
# 1. 看命令是否被 AstrBot 注册
journalctl -u astrbot --since '5 min ago' | grep -E "show_broadcast_time|加载插件|Loading"

# 2. 看命令触发时 AstrBot 看到的消息原文
journalctl -u astrbot --since '5 min ago' | grep -E "user_message=|message_str"

# 3. 看前置插件是否改写了消息 (ForwardReader / AstrNa / AngelHeart)
journalctl -u astrbot --since '5 min ago' | grep -E "ForwardReader|forward_reader|natural_intent"
```

如果 `user_message=放送时间 无职转生 周日 23:00` 跟用户发的完全一致,但 AstrBot 没调用 handler,**多半是被前置插件的 LLM 抢了**——看 `analysis_type natural_intent=True` 之类的日志确认。

## 经验教训 (本轮调试复盘)

1. **改完代码没要求用户验证就报"修好了"** — 用户两次"再看看日志"才暴露问题。下次: 改完代码必明确说"重启后告诉我结果/贴日志",不主动宣告修好。
2. **连续 3 次尝试同一种思路** (都试图用 command 参数捕获多 token),失败时没立刻换思路 — 应该第一次失败就考虑改用 `event.get_message_str()`。
3. **没看 AstrBot 官方文档** — 用户提醒"先查相关文档",意识到应该看源码 + bilibili 插件用法,而不是凭印象猜。

下一步: **有 git 改动前先单测 + 至少跑一次模拟消息**。fork 上加了 `tests/` 但没强制让新代码触发测试。