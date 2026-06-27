# AstrBot 群员「盒武器」数据接入方案

## 背景

群 707942526 有一个「盒武器」——腾讯文档表格 `群员信息总览`，记录 37 位群友的详细信息：
姓名、是否在群、性别、昵称、QQ、电话、生日、去向（城市）、位置（学校）、专业、Steam 好友代码、XP、收货地址。

> 腾讯文档链接：https://docs.qq.com/sheet/DR3R2UXZDVG53UHVn?tab=BB08J2
> 导出 xlsx 后共 38 行（1 header + 37 members），14 列。

## 现有基础设施

### qqadmin 插件（v3.3.0）

已有 `group_members` 表结构（`/home/po/astrbot/data/plugin_data/astrbot_plugin_qqadmin/qqadmin_data_v3.db`）：

```sql
group_members(group_id, user_id, nickname, card, role, level, join_time, last_sent_time, last_updated)
```

- 通过 QQ API 获取成员列表（`/群友信息` 命令）
- 同步逻辑在 `core/member_handle.py`
- DB 层在 `data.py`
- **当前状态：0 groups**（无人触发过同步）

### AstrBot 原生知识库（v4.5.0+）

- 数据库已初始化：`/home/po/astrbot/data/knowledge_base/kb.db`
- 需要配置 Embedding 模型（推荐硅基流动 `BAAI/bge-m3`，免费）
- WebUI 上传文件即可，AI 对话时自动检索
- **当前状态：Embedding Provider 未配置**（日志中持续报 `等待 Provider 就绪（未就绪: Embedding Provider）`）

### 其他可参考的插件

| 插件 | 功能 | 相关性 |
|------|------|--------|
| self_learning | 人格/风格/表达学习，群友画像 | 已有 76 条待审人格更新 |
| livingmemory | 长期记忆 | 可存储群友事实 |
| portrayal | LLM 分析群友画像 | 依赖聊天记录 |

## 三种接入方案

### 方案 A：AstrBot 原生知识库（最简单）

把 xlsx 清洗为结构化 Markdown/JSON 文本 → WebUI 上传到知识库。
Bot 对话时自动 embedding 召回相关内容。

**优点**：零代码、原生支持、AI 自动检索
**缺点**：依赖外部 embedding 服务；更新需重新上传；无法精确查询（如"QQ 号以 2 开头的有谁"）

### 方案 B：导入 qqadmin 数据库

把 xlsx 数据映射到 qqadmin 的 `group_members` 表（或新建扩展表）。
需要写导入脚本（xlsx 列 → 表字段映射）。

**优点**：本地 SQLite，零外部依赖；`/群友信息` 命令直接可用
**缺点**：qqadmin 表缺盒武器特有字段（专业、电话、XP 等），需加列或另建表；AI 不能直接查询

### 方案 C：自建「盒武器」专用表 + LLM Function Tool

新建 `box_weapon` 表（完整 14 列）→ 注册 AstrBot LLM Tool 供 AI 调用。
支持模糊搜索、多条件筛选。

**优点**：数据结构完整；AI 通过 function call 精确查询；可扩展
**缺点**：需要写 plugin handler 代码

### 推荐路径

**A → C 渐进**：先用 A 快速上线（5 分钟配 embedding + 上传文本），后续要精确查询再走 C。

## 当前状态（2026-06-25）

✅ **方案 A 已实施**：数据已上传到 AstrBot 原生知识库「盒武器」。

| 项目 | 值 |
|------|-----|
| kb_id | `c0ca81b9-f1f0-4479-9ce8-f6c3017958cf` |
| kb_name | 盒武器 |
| Embedding | SiliconFlow `BAAI/bge-m3` (openai_embedding) |
| dimensions | 已设为 0（bge-m3 不支持该参数） |
| 文档 | `box_weapon_qq.md`（38 chunks）|
| 数据格式 | QQ 号索引版（`## QQ: xxxxx`） |
| kb_agentic_mode | true（LLM 主动用 tool 查 KB） |
| 人格规则 | 已加身份识别规则（提取 QQ 号 → 搜 KB → 确认真实身份） |

### 已知限制

- **KB 检索用消息文本做 query**（非发送者 QQ 号），agentic mode 缓解但非根治
- **群名片 ≠ 真名**：如「边牧」= 马涵君，「反模联战士」= 林浩阳。LLM 需要通过 QQ 号 bridge
- **CLOSE-WAIT 挂死**：DeepSeek API 连接卡住会导致消息处理全线停摆，`sudo systemctl restart astrbot` 修复

### 更新流程

详见 skill `sync-box-weapon-to-astrbot-kb`。

- **群号**：707942526
- **WebUI**：http://localhost:6185（用户名 `Publieople`，密码已改为随机强密码）
- **已退群 4 人**：陈嘉雯、陈孟祺、何司盈、杨芸裳（标记"否"）
- **生日字段**：Excel 序列号格式（如 38728 = 2006-01-11），需转换
- **QQ 字段**：部分人有多个号（如冯周杰 2631792752/3807095822）
- **XP 列**：大面积「男同」😂 — 这是群内 meme，不是真实 XP
