# OneBot v11 消息事件字段参考

来源: https://github.com/botuniverse/onebot-11/blob/master/event/message.md

## 群消息事件

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| `time` | number (int64) | 事件发生时间戳 |
| `self_id` | number (int64) | 机器人 QQ 号 |
| `post_type` | string | `message` |
| `message_type` | string | `group` |
| `sub_type` | string | `normal` / `anonymous` / `notice` |
| `message_id` | number (int32) | 消息 ID |
| `group_id` | number (int64) | 群号 |
| `user_id` | number (int64) | 发送者 QQ 号 |
| `anonymous` | object | 匿名信息，非匿名则为 null |
| `message` | message | **消息内容**（array 或 string，取决于 messagePostFormat） |
| `raw_message` | string | 原始 CQ 码消息内容 |
| `font` | number (int32) | 字体 |
| `sender` | object | 发送人信息 |

## sender 字段 (群消息)

| 字段名 | 说明 |
|--------|------|
| `user_id` | QQ 号 |
| `nickname` | 昵称 |
| `card` | 群名片 |
| `role` | `owner` / `admin` / `member` |

## message 字段格式

**array 格式** (OneBot 消息段数组):
```json
[
  {"type": "at", "data": {"qq": "2628392161"}},
  {"type": "text", "data": {"text": " 你好"}}
]
```

**string 格式** (CQ 码):
```
[CQ:at,qq=2628392161] 你好
```

## at 消息段

来源: https://github.com/botuniverse/onebot-11/blob/master/message/segment.md

| 参数 | 收 | 发 | 说明 |
|------|-----|-----|------|
| `qq` | ✓ | ✓ | @的 QQ 号，或 `all`（全体成员） |

---

## Hermes NapCat 适配器的 _strip_self_mention 逻辑

```python
# 检查每个 segment 是否为 type="at" 且 data.qq == self._self_id
if seg_type == "at":
    qq = str(data.get("qq") or "").strip()
    if qq == self._self_id:   # self_id 来自 X-Self-ID header
        mentioned = True
        continue  # 移除这个 at 段，不加入 text
```

关键点：
- `self._self_id` 是**字符串** `"2628392161"`
- `data.get("qq")` 可能是 int 或 string，`str()` 统一转换
- 如果 `message` 是 string（CQ 码），at 段被 `_normalize_segments` 正则洗掉，不会进入此检查

## _normalize_segments 的三种处理路径

```python
if isinstance(raw_message, list):    # array 格式 → 直接返回
    return [seg for seg in raw_message if isinstance(seg, dict)]
if isinstance(raw_message, dict):    # 单个 segment → 包成列表
    return [raw_message]
if isinstance(raw_message, str):     # CQ 码 string → ❗at 段被洗掉
    stripped = re.sub(r"\[CQ:[^\]]*\]", "", raw_message)
    if stripped.strip():
        return [{"type": "text", "data": {"text": stripped}}]
return []  # → _strip_self_mention 返回 (False, "")
```
