# Bangumi 插件数据库诊断

## 插件数据库位置

`~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/data.db`

## 表结构

### bangumi_subjects

| 列 | 类型 | 说明 |
|----|------|------|
| subject_id | VARCHAR | Bangumi 条目 ID |
| name | VARCHAR | 番剧名 |
| air_date | VARCHAR | 开播日期 |
| total_episodes | INTEGER | 总话数（0 = 未知） |
| current_episode | INTEGER | 已通知到第几话 |
| broadcast_time | VARCHAR | 播出时间 HH:MM（CST），如 "22:00" |
| updated_at | DATETIME | 最后更新时间 |

### subscriptions

| 列 | 类型 | 说明 |
|----|------|------|
| group_id | VARCHAR | QQ 群号 |
| subject_id | VARCHAR | Bangumi 条目 ID |
| created_at | DATETIME | 订阅时间 |

## ⚠️ 双重追番系统冲突

Hermes 的 `bangumi-subscription` skill 和 AstrBot 插件 **各自维护独立的订阅和通知系统**，会导致重复推送。**追番通知统一由 AstrBot 插件处理**，不要在 Hermes 侧另建 cron job。

如果发现 Hermes 侧还有 bgm 相关 cron job，立即删除：
```bash
# Hermes 侧清理
cronjob action=remove job_id=<job-id>  # 逐个删
rm -f ~/.hermes/bangumi_subscriptions.json ~/.hermes/scripts/bangumi.py
skill_manage action=delete name=bangumi-subscription absorbed_into=""
```

## AstrBot Agent 工作区

Agent 在 QQ 群里被要求改代码时，改动的 git 仓库在：
```
~/astrbot/data/workspaces/{platform}_{chat_type}_{chat_id}/{repo}/
# 例：~/astrbot/data/workspaces/default_GroupMessage_707942526/astrbot_plugin_bangumi/
```

Agent 可能在 feature branch 上有未提交的改动——`git status`、`git diff`。

## 读取 Agent 会话记录

Agent 对话历史在 `data_v4.db` 的 `conversations` 表（JSON content 字段）：

```python
import sqlite3, json
conn = sqlite3.connect('/home/po/astrbot/data/data_v4.db')
rows = conn.execute('''
    SELECT conversation_id, user_id, updated_at, content
    FROM conversations ORDER BY updated_at DESC LIMIT 10
''').fetchall()
for r in rows:
    msgs = json.loads(r[3])  # [{role, content}, ...]
```

`platform_message_history` 表**只存 webchat 消息**，QQ 群聊全在 conversations 里。