# AstrBot Skill 格式 & LLM 上下文速查

## AstrBot Skill 文件格式

位置：`/home/po/astrbot/data/skills/<skill-name>/SKILL.md`

格式：
```markdown
---
name: skill-name
description: 简短描述，决定触发条件。关键词要覆盖任务场景。
---

# Skill Title

内容...
```

- Skill 按 `description` 做语义匹配，匹配时加载全文到 LLM 上下文
- 热加载：文件保存后自动生效，无需重启
- 适合：静态参考数据、查表任务、身份识别

## LLM 收到的消息格式

每条群消息，LLM 在 `<system_reminder>` 中收到 sender 信息：

```
<system_reminder>
User ID: 2631792752, Nickname: 人民公仆
Current datetime: 2026-06-25 01:32 CST
</system_reminder>
```

源码：`astrbot/core/astr_main_agent.py:861-863`
```python
user_id = event.message_obj.sender.user_id
user_nickname = event.message_obj.sender.nickname
system_parts.append(f"User ID: {user_id}, Nickname: {user_nickname}")
```

其中 `User ID` 就是 QQ 号。

## KB vs Skill 选型

| | 知识库 (KB) | Skill |
|---|---|---|
| 触发 | 消息文本 embedding 检索 | 任务描述匹配 → 加载全文 |
| QQ号匹配 | ❌ 消息里没有QQ号 | ✅ LLM 直接查表 |
| 更新 | API 删旧传新 | 编辑文件即生效 |
| 适合 | 主题知识、FAQ | 身份查表、静态参考 |

身份识别场景：**Skill 优于 KB**。

## AstrBot 系统信息

- systemd 服务：`sudo systemctl restart astrbot`
- 实时日志：`sudo journalctl -u astrbot -f`
- WebUI：`http://localhost:6185`，用户名 `Publieople`
- 插件热加载：放到 `data/plugins/` 自动检测，不 kill 进程
- 失败插件重载：`POST /api/plugin/reload-failed` + `{"dir_name": "目录名"}`
- Token 在 Hermes shell 中被红action，API 操作优先用 `execute_code` + `urllib`
