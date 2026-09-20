# Personas 表 JSON 列诊断与修复

AstrBot 启动崩溃且堆栈指向 `get_personas() → json.loads → JSONDecodeError` 时使用。

## 症状

```
[CRIT] [core.initial_loader:32]: Traceback (most recent call last):
  ...
  File ".../persona_mgr.py", line 174, in get_all_personas
    return await self.db.get_personas()
  ...
  File ".../json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
😭 初始化 AstrBot 失败
```

备选症状（修复过头时）：
```
ValueError: Invalid isoformat string: '"2026-06-10 17:25:13.380503"'
```

## 诊断脚本

```python
import sqlite3, json

conn = sqlite3.connect("/home/po/astrbot/data/data_v4.db")
c = conn.cursor()

# personas 表完整列列表
cols = [r[1] for r in c.execute("PRAGMA table_info(personas)").fetchall()]

# JSON 列（ORM 期望 JSON 类型）
JSON_COLS = {"system_prompt", "begin_dialogs", "tools", "skills", "custom_error_message"}

# 非 JSON 列（纯文本/datetime/integer）
NON_JSON_COLS = {"created_at", "updated_at", "persona_id", "folder_id", "sort_order"}

rows = c.execute("SELECT * FROM personas").fetchall()

issues = []
for row in rows:
    pid = row[3]  # persona_id 列索引
    for i, col in enumerate(cols):
        val = row[i]
        if val is None or val == "":
            if col in JSON_COLS and val == "" and col not in ("custom_error_message",):
                issues.append((pid, col, "空字符串 — JSON 列不能为空"))
            continue
        if col in JSON_COLS:
            try:
                json.loads(val)
            except (json.JSONDecodeError, TypeError):
                issues.append((pid, col, f"不是合法 JSON: {repr(str(val)[:60])}"))
        elif col in NON_JSON_COLS:
            # 非 JSON 列不应有 JSON 引号
            if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                issues.append((pid, col, f"被错误 JSON 包裹: {val[:50]}"))

if issues:
    print(f"发现 {len(issues)} 个问题:")
    for pid, col, desc in issues:
        print(f"  ❌ [{pid}] {col}: {desc}")
else:
    print("✅ 所有列格式正确")

conn.close()
```

## 修复

### JSON 列缺 JSON 包裹

```python
import sqlite3, json

conn = sqlite3.connect("/home/po/astrbot/data/data_v4.db")
c = conn.cursor()

JSON_COLS = {"system_prompt", "begin_dialogs", "tools", "skills", "custom_error_message"}

rows = c.execute("SELECT persona_id, " + ", ".join(JSON_COLS) + " FROM personas").fetchall()
for row in rows:
    pid = row[0]
    for i, col in enumerate(JSON_COLS):
        val = row[i+1]
        if val is None:
            continue
        if val == "" and col != "custom_error_message":
            # tools/skills 空串 → "{}"，begin_dialogs 空串 → "[]"
            new_val = '"[]"' if col == "begin_dialogs" else '"{}"'
        else:
            try:
                json.loads(val)
                continue  # 已是合法 JSON，跳过
            except:
                new_val = json.dumps(val, ensure_ascii=False)
        c.execute(f"UPDATE personas SET {col} = ? WHERE persona_id = ?", (new_val, pid))
        print(f"[{pid}] {col} 已修复")

conn.commit()
conn.close()
```

### 非 JSON 列被错误 JSON 包裹

```python
import sqlite3, json

conn = sqlite3.connect("/home/po/astrbot/data/data_v4.db")
c = conn.cursor()

NON_JSON_COLS = {"created_at", "updated_at", "persona_id"}

rows = c.execute("SELECT persona_id, " + ", ".join(NON_JSON_COLS) + " FROM personas").fetchall()
for row in rows:
    pid = row[0]
    for i, col in enumerate(NON_JSON_COLS):
        val = row[i+1]
        if val is None:
            continue
        if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
            original = json.loads(val)  # 去掉 JSON 引号
            c.execute(f"UPDATE personas SET {col} = ? WHERE persona_id = ?", (original, pid))
            print(f"[{pid}] {col}: {val[:30]} → {repr(original)}")

conn.commit()
conn.close()
```

## 根因

AstrBot v4.25.x 的 SQLAlchemy ORM 将 `personas` 表的多数字段定义为 `JSON` 类型（包括 `system_prompt`），但 WebUI 写入时对一些字段使用纯文本格式。当通过外部 SQL（非 ORM）修改数据库时，必须手动保证 JSON 类型字段的格式正确。

**两个方向的错误都不能犯**：
1. JSON 列存裸文本 → `JSONDecodeError`
2. 非 JSON 列存 JSON 包裹值 → `ValueError: Invalid isoformat string`
