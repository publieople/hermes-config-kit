# AstrBot 启动崩溃诊断

## 快速诊断命令

```bash
cd ~/astrbot && astrbot run 2>&1 | head -50
```

关键日志：看到 `CRIT` 或 `CRITICAL` 行就是崩溃原因。

## 常见崩溃模式

### 1. `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
→ 数据库 `personas` 表中有 JSON 列是空字符串 `""`。
→ 修复：
```bash
cd ~/astrbot && python3 -c "
import sqlite3
conn = sqlite3.connect('data/data_v4.db')
conn.execute(\"UPDATE personas SET begin_dialogs = '[]' WHERE begin_dialogs = ''\")
conn.execute(\"UPDATE personas SET tools = '{}' WHERE tools = ''\")
conn.execute(\"UPDATE personas SET skills = '{}' WHERE skills = ''\")
conn.commit(); conn.close()
print('done')
"
```

### 2. `JSONDecodeError: Extra data`
→ `cmd_config.json` 被写入了行号前缀（如 `1|{`）。
→ 检查：`head -c 5 ~/astrbot/data/cmd_config.json | xxd`
→ 修复：删除文件让 AstrBot 重建，或从备份恢复。

### 3. `Validation errors for Message`
→ Persona 的 `begin_dialogs` 格式不对（通常是 JSON 结构和 AstrBot 版本不匹配）。
→ 修复：清空 `begin_dialogs` 字段：
```bash
cd ~/astrbot && python3 -c "
import sqlite3
conn = sqlite3.connect('data/data_v4.db')
conn.execute(\"UPDATE personas SET begin_dialogs = '[]'\")
conn.commit(); conn.close()
print('done')
"
```

## 配置被清空后恢复

如果 `cmd_config.json` 被 AstrBot 静默重建为默认值：
1. 删除当前配置文件：`rm ~/astrbot/data/cmd_config.json`
2. 重启 AstrBot 让它生成全新的
3. 通过 WebUI 重新配置
