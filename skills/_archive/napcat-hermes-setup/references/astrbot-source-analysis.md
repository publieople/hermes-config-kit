# AstrBot 源码调研：系统提示词构建机制

## 方法

克隆 `AstrBotDevs/AstrBot` master 分支，分析核心提示词构建流程。

## 关键发现

### 1. 用户身份注入（astr_main_agent.py:862-872）

```python
def _append_system_reminders(event, req, cfg, timezone):
    system_parts = []
    if cfg.get("identifier"):
        user_id = event.message_obj.sender.user_id
        user_nickname = event.message_obj.sender.nickname
        system_parts.append(f"User ID: {user_id}, Nickname: {user_nickname}")
    ...
    if system_parts:
        system_content = "## System Reminders\n\n"
        req.system_prompt += system_content + "\n".join(system_parts)
```

**结论**：AstrBot 把每条消息的发送者 QQ 号直接注入系统提示词。
Bot 每一轮都知道"现在跟我说话的人 QQ 号是 2631792752，叫人民公仆"。

### 2. 群组信息采集（aiocqhttp_message_event.py:228-261）

```python
async def _get_group_info(self, group_id):
    info = await self.bot.call_action("get_group_info", group_id=group_id)
    members = await self.bot.call_action("get_group_member_list", group_id=group_id)
    
    owner_id = None
    admin_ids = []
    for member in members:
        if member["role"] == "owner": owner_id = member["user_id"]
        if member["role"] == "admin": admin_ids.append(member["user_id"])
    
    group = Group(
        group_id=str(group_id),
        group_name=info.get("group_name"),
        group_owner=str(owner_id),
        group_admins=admin_ids,
        members=[MessageMember(user_id=m["user_id"], nickname=m.get("card") or m.get("nickname")) for m in members],
    )
    return group
```

**结论**：AstrBot 调用 OneBot `get_group_member_list` API 获取完整群成员列表，
包括群主(owner)和管理员(admins)。这样 Bot 知道群里的权力结构。

### 3. 预设对话注入（astr_main_agent.py:483-488）

```python
async def _ensure_persona_and_skills(...):
    persona_id, persona, ... = await plugin_context.persona_manager.resolve_selected_persona(...)
    
    if persona:
        if prompt := persona["prompt"]:
            req.system_prompt += f"\n# Persona Instructions\n\n{prompt}\n"
        if begin_dialogs := copy.deepcopy(persona.get("_begin_dialogs_processed")):
            req.contexts[:0] = begin_dialogs  # 前置到对话开头
```

**结论**：`begin_dialogs` 是用户预设的示例对话，被前置（prepend）到 LLM 对话历史中。
这是人格设置最强大的功能——LLM 通过模仿示例学习如何回应，比规则描述有效得多。

### 4. 人格数据结构

```json
{
    "persona_id": "my-persona",
    "system_prompt": "你是...",
    "begin_dialogs": ["用户：...", "助手：...", "用户：...", "助手：..."],
    "tools": [...],
    "skills": [...],
    "custom_error_message": "抱歉，出错了"
}
```

### 5. 群组信息格式（astrbot_message.py:37-47）

```python
class Group:
    def __str__(self):
        return (
            f"Group ID: {self.group_id}\n"
            f"Name: {self.group_name}\n"
            f"Owner ID: {self.group_owner}\n"
            f"Admin IDs: {self.group_admins}\n"
            f"Members Len: {len(self.members)}\n"
            f"First Member: {self.members[0]}\n"
        )
```

## Hermes 对照差距

| 功能 | AstrBot | Hermes NapCat |
|------|---------|---------------|
| 用户 QQ 号注入系统提示词 | ✅ 每条消息 | ❌ 只有 user_name（群名片） |
| 群主/管理员识别 | ✅ get_group_member_list | ❌ 未实现 |
| 预设对话(begin_dialogs) | ✅ 系统级支持 | ⚠️ 用 SKILL.md 文本模拟 |
| 人格管理 | ✅ WebUI CRUD | ❌ 只靠文件编辑 |

## 对 Hermes 的改进建议

1. **最重要**：修改 napcat 适配器，在消息前拼接 `[QQ:2631792752|人民公仆]` 标识
2. 在 napcat 适配器中加入群组信息采集（群主、管理员列表）
3. 考虑在 SKILL.md 中加入更多预设对话案例覆盖常见攻击模式
