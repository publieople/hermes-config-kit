# Persona Skill 限定到指定群 — 源码细节

## 关键源码路径

```python
# Persona 数据模型
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/db/po.py
  - Persona class (line 132): tools, skills fields
  - Personality TypedDict (line 555): tools, skills fields

# Persona 管理器 — 人格选择和生效逻辑
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/persona_mgr.py
  - resolve_selected_persona() (line 75): 读取 session_service_config.persona_id
  - create_persona() (line 315): 创建时传 tools/skills
  - update_persona() (line 137): 更新时传 tools/skills

# 会话规则管理
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/umop_config_router.py
  - UMO 到配置文件 ID 的匹配规则，支持 fnmatch 通配符

# Session Rules API
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/dashboard/services/session_management_service.py
  - update_session_rule() (line 245): 更新 session_service_config.persona_id
```

## Persona 字段语义（po.py 132-166）

```python
class Persona(TimestampMixin, SQLModel, table=True):
    persona_id: str          # 唯一标识
    system_prompt: str       # 系统提示词
    tools: list | None       # None=全开, []=全关, ["a","b"]=白名单
    skills: list | None      # 同上，针对 Anthropic Skills
    custom_error_message: str | None  # Agent 失败时的自定义回复
```

## 会话规则绑定链路

1. WebUI → 会话管理 → 选 UMO → 设 `session_service_config` → 存 `SharedPreferences`（`sp`），scope=`umo`, scope_id=`umo字符串`

2. `persona_mgr.resolve_selected_persona()`:
   - 读取 `sp.get_async(scope="umo", scope_id=umo, key="session_service_config")`
   - 取 `force_applied_persona_id = session_service_config.get("persona_id")`
   - 如果非空，强制使用该 Persona

3. 绑定后，LLM 请求时只加载该 Persona 的 `tools`/`skills` 白名单列表

## UMO 格式

`平台ID:消息类型:会话ID`

QQ 群示例: `aiocqhttp:GroupMessage:547540978`
QQ 私聊示例: `aiocqhttp:PrivateMessage:123456789`

## 注意

- 会话规则存在 `Preference` 表（scope=umo），不是 cmd_config.json
- 重启后保留
- `/persona <name>` 指令可以临时切换，但会被 `session_service_config.persona_id` 覆盖
- `self_learning` 插件也有自己的人格选择逻辑，可能覆盖 WebUI 的会话规则—查看日志确认实际生效人格
