---
name: astrbot-knowledge-base
description: Manage AstrBot knowledge bases — create, upload, retrieve, delete via WebUI or REST API. Use when adding documents to an AstrBot bot's RAG knowledge base, troubleshooting embedding issues, or automating KB updates.
category: devops
---

# AstrBot Knowledge Base

Manage AstrBot's native RAG knowledge base (v4.5.0+) via REST API or WebUI.

## Prerequisites

- AstrBot >= 4.5.0 (KB is built-in, not a plugin)
- Configured embedding provider (e.g., SiliconFlow `BAAI/bge-m3`)
- WebUI credentials (default `astrbot`/`astrbot` is deprecated — check `cmd_config.json` for actual username, password is hashed)

## Architecture

- KB metadata: `data/knowledge_base/kb.db` (SQLite)
- Per-KB vector store: `data/knowledge_base/{kb_id}/index.faiss` + `doc.db`
- Documents stored as files in `data/knowledge_base/{kb_id}/files/`
- REST API at `http://localhost:6185/api/kb/*`

## API Workflow

### 1. Login

```bash
curl -s -X POST http://localhost:6185/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"USER","password":"PASS"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['token'])" > /tmp/astrbot_token.txt
```

Save token to file — needed for all subsequent calls. Tokens contain JWT with dots; avoid inline `$TOKEN` in shell (redaction can mangle it).

### 2. List knowledge bases

```bash
TOKEN=$(cat /tmp/astrbot_token.txt)
curl -s "http://localhost:6185/api/kb/list" -H "Authorization: Bearer $TOKEN"
```

### 3. Create KB

```bash
curl -s -X POST http://localhost:6185/api/kb/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_name": "MyKB",
    "description": "desc",
    "emoji": "📚",
    "embedding_provider_id": "openai_embedding",
    "chunk_size": 512,
    "chunk_overlap": 50
  }'
```

Requires `embedding_provider_id` — use the provider ID from AstrBot config.

### 4. Upload document

**multipart/form-data only** (not JSON base64):

```bash
curl -s -X POST http://localhost:6185/api/kb/document/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "kb_id=K" -F "file=@/path/to/doc.md"
```

Returns `task_id` — uploads are async. Poll progress:

```bash
curl -s "http://localhost:6185/api/kb/document/upload/progress?task_id=T" \
  -H "Authorization: Bearer $TOKEN"
```

Supported formats: `.txt`, `.md`, `.markdown`, `.pdf`, `.docx`, `.xlsx`, `.epub`, `.rst`, `.adoc`

### 5. Retrieve

```bash
curl -s -X POST http://localhost:6185/api/kb/retrieve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"kb_names":["KB_NAME"], "query":"query text", "top_k":3}'
```

**Key**: `kb_names` is a **list of KB names** (not IDs). Returns chunks with scores.

### 6. Delete document / KB

```bash
# Delete document
curl -s -X POST http://localhost:6185/api/kb/document/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"D", "kb_id":"K"}'

# Delete entire KB
curl -s -X POST http://localhost:6185/api/kb/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"kb_id":"K"}'
```

## Pitfalls

### embedding_dimensions breaks bge-m3 on SiliconFlow

Setting `embedding_dimensions: 1024` causes a warning flood (not a hard error) because SiliconFlow doesn't accept the `dimensions` parameter for non-Qwen models. Set to `0` (or omit). The model natively outputs 1024-dim vectors.

### xlsx upload fails with openpyxl

AstrBot uses openpyxl internally to parse xlsx. If the file has a `Fill()` compatibility issue (common with Excel-generated files on Python 3.12+), upload fails with "文档解析失败". Workaround: convert xlsx to Markdown first. See `references/xlsx-to-markdown-workaround.md`.

### Token redaction in shell

JWT tokens contain dots (`.`) and sometimes braces, which trigger Hermes secret redaction when used inline in `curl -H "Authorization: Bearer $TOKEN"`. Always save token to file and read via `$(cat /tmp/token.txt)` or use Python `urllib` directly.

## Update Workflow

To refresh KB content (e.g., updated spreadsheet data):

1. Delete old document: `POST /api/kb/document/delete`
2. Upload new document: `POST /api/kb/document/upload`
3. Verify: `POST /api/kb/retrieve` with a known query

This can be automated via the `sync-box-weapon-to-astrbot-kb` skill.

## KB vs AstrBot Skill 选型

**KB（知识库）的先天性局限**：
- `kb_agentic_mode: false` 时，AstrBot 用**消息文本内容**做 embedding 检索，而非发送者的 QQ 号
- 问"锐评下福师大"时，query 是"福师大"，不是 QQ 号，检索不到对应的人
- `kb_agentic_mode: true` 可以让 LLM 主动调 KB tool，但 LLM 可能不主动查

**AstrBot Skill 的优势**：
- 放在 `/data/skills/<name>/SKILL.md`，YAML frontmatter + Markdown
- 按任务匹配加载全文，LLM 可以直接搜索 QQ 号
- 适合静态参考数据（如群成员身份表）

**结论**：身份识别用 Skill，主题知识用 KB。

## LLM 收到的消息格式（sender 信息）

```
<system_reminder>
User ID: 2631792752, Nickname: 人民公仆
Current datetime: 2026-06-25 01:32 CST
</system_reminder>
```

源码 `astrbot/core/astr_main_agent.py:861-863`。LLM 能看到 QQ 号，只是天然倾向用 Nickname 而非数字。

## 系统信息

AstrBot 是 systemd 服务：`sudo systemctl restart astrbot`。重启后日志可能在 journal 而非数据目录的 log 文件：`sudo journalctl -u astrbot -f`。

`kb_names` 配置可能在 systemd 重启后被覆盖，关停/启动后需验证 `cmd_config.json` 中的 `kb_names` 是否仍为 `["盒武器"]`。
