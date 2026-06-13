# QQ 群身份管理：成员属性与 Bot 名片

## 成员属性的三层结构

`get_group_member_list` 返回每个成员有三个不同的身份字段，**不要混淆它们**：

| 字段 | 含义 | 示例 | 可被谁改 |
|------|------|------|---------|
| `nickname` | QQ 账号昵称 | `"亓玖"` | 用户自己 |
| `card` | 群名片（显示在群里的名字） | `"我发现尬黑小翁会很舒服"` | 群管理/本人 |
| `title` | 群头衔（群主/管理设置的称号） | `"人出"` / `"阮派"` / `"余出"` | 群主/管理 |
| `role` | 身份级别 | `"owner"` / `"admin"` / `"member"` | 群主 |

### 常见陷阱

- **"人出" 是群头衔 (title)，不是群名片 (card)，也不是 QQ 昵称 (nickname)**。`title` 字段在列表最后，容易被忽略。
- 群成员发送消息时，群里显示的是 **card**（群名片），但 `napcat_call get_group_member_list` 才暴露 `title`。
- 同一个人的 `nickname`、`card`、`title` 可能完全不同。不要看到一条就断定身份。

## 设置/修改 Bot 群名片

```bash
napcat_call action="set_group_card" params={"card":"新名字","group_id":群号,"user_id":你的botQQ号}
```

- `user_id` 不可省略。省略或用 `0` 会报 `retcode=1200`（成员不存在）。
- 修改立即生效，群里可见。

### 确定 Bot 的 QQ 号

```bash
napcat_call action="get_login_info"
# 或从 gateway 日志 grep: "NapCat connected (self_id=2628392161"
```

## 群成员身份发现流程

当用户问"某人是/某称号是谁"时，正确的排查顺序：

1. `napcat_call action="get_group_member_list" params={"group_id": 群号}`
2. 遍历结果，检查三个字段：
   - `card` 匹配 → 这是群名片
   - `nickname` 匹配 → 这是 QQ 昵称
   - `title` 匹配 → 这是群头衔，**不是一个人名**
   - `role == "owner"` → 群主
3. 注意：`card` 字段可能包含 `@`（群名片里写了 at 别人）

### "人出" 类头衔命名模式

群里常见 `X出` 格式的群头衔（如 `人出`、`阮派` → 实际上是 `阮出`? 不，`阮派` 是 title，`人出` 也是 title）。这类头衔是群主/管理设置的，不是 QQ 昵称，也不是群名片。当用户问"XXX是谁"时，先查是不是 title。

## 群成员角色速查

| role 值 | 含义 | 权限 |
|---------|------|------|
| `owner` | 群主 | 最高权限，可设头衔 |
| `admin` | 管理员 | 可改群名片、踢人 |
| `member` | 普通成员 | 有限 |

## 常见错误

- ❌ `set_group_card` 的 `user_id` 传 `0` → `retcode=1200 "群成员0不存在"`
- ❌ 把 `title`（群头衔）当成 `card`（群名片）回答"XXX是谁" → 答错，用户会"？"
- ❌ 记忆里写死身份映射（"1213070170=人出"）→ 过时。身份映射应从群成员列表实时读取，而不是依赖记忆缓存。
