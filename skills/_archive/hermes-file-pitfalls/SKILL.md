---
name: hermes-file-pitfalls
description: 用 Hermes 的 file 工具读写文件时避免数据损坏——read_file 会注入行号，不要直接拿去 write_file
---

# Hermes 文件操作避坑

## 核心坑：read_file 的行号会污染 write_file

`read_file` 返回的内容带行号前缀：

```
1|{
2|  "key": "value"
3|}
```

如果用这个输出直接喂给 `write_file`，行号会写进去，文件变成：

```
1|{
2|  "key": "value"
3|}
```

→ JSON/YAML 损坏，程序启动崩溃。

## 正确做法

**场景 A：读→改→写非代码文件（JSON/YAML/TOML）**

不要用 `read_file` + `write_file` 组合。用 `terminal`：

```bash
# 读原始内容
cat /path/to/file

# 或用 python3 读写（保持编码正确）
python3 -c "
import json
with open('/path/to/file') as f:
    config = json.load(f)
config['key'] = 'new_value'
with open('/path/to/file', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
```

**场景 B：读→改→写代码文件（Python/JS/Markdown）**

用 `read_file` 读内容到上下文做参考，但修改用 `patch` 工具（只改目标行，不会污染）：

```
patch(path='...', old_string='...', new_string='...')
```

**场景 C：只是读，不改写**

`read_file` 随便用——行号不会造成问题。

**场景 D：必须用 read_file 的输出去写**

执行前用 `execute_code` 把行号 strip 掉：

```python
from hermes_tools import read_file, write_file
content = read_file("/path/to/file")
# 行号格式: "123|actual content"，去掉开头的数字+竖线
clean = "\n".join(
    line.split("|", 1)[1] if "|" in line and line.split("|")[0].strip().isdigit()
    else line
    for line in content["content"].split("\n")
)
write_file("/path/to/file", clean)
```

## 已证明会坏的场景

- JSON 配置文件（AstrBot `cmd_config.json` 被 `read_file` + `write_file` 损坏过两次）
- SQLite 数据库操作——不要用文件工具碰 `.db`，用 `python3 -c "import sqlite3; ..."`
- 任何有 BOM 的文件——`read_file` 可能破坏 BOM，导致 UTF-8-sig 解析失败

### 会话见证

- 2026-06-20 open-any Phase 2 修复：`execute_code` 的 `read_file`+`write_file` 组合损坏 4 个 `.tsx` 文件，靠 `git checkout` 恢复。详见 `references/execute-code-corruption.md`。
- 同日：`patch` 工具的 `\\n` 转义漂移损坏 `json.tsx` 和 `text.tsx`，改回 `terminal` + `sed` 修复。
- 同日：`npm uninstall @iarna/toml` 级联删除 95 个包（包括 `@vitejs/plugin-react`），导致 `vitest` 和 `tsc` 全部丢失。全量 `rm -rf node_modules package-lock.json && npm install` 恢复，但第一次 `npm install` 仍有包缺失（vitest 二进制未安装），需二次 `npm install vitest --save-dev` 才修复。

## 核心坑 2：patch 工具的 `\n` 转义漂移

当 `old_string` / `new_string` 中包含多行内容时，工具调用序列化层可能对反斜杠做双重转义，导致文件中被写入字面量 `\n` 字符串而非真正的换行符：

```diff
-    };
-  }, [file.id, readOnly]);
+    };\n    // eslint-disable-next-line\n  }, [file.id, readOnly]);
```

症状：补丁后文件出现大量 `Expected expression` / `Declaration or statement expected` 等 TS 错误，因为 `\n` 被当成了代码而不是换行。

**触发条件：** `old_string` 中跨越多行且包含 React JSX 或字符串字面量时更容易触发。

**解决方案（按优先级）：**

1. **小改动用 terminal `sed`** — 不经过 patch 工具，直接编辑：
   ```bash
   sed -i '/^  }, \[file\.id, readOnly\]);/i\    // eslint-disable-next-line' file.tsx
   ```

2. **大改动用 `write_file` 重写整个文件** — `write_file` 没有转义问题，但需要先 `read_file` 拿到完整内容（注意：在上下文中读，不要用 execute_code 的 read_file）

3. **用 `execute_code` + regex 替换** — 但注意 execute_code 的 `read_file` 返回行号前缀，需要先 strip（见核心坑 1）

**识别方法：** 如果 patch 返回的 diff 中包含 `\\n` 字面量（而不是真正的换行），说明发生了转义漂移，文件已损坏。立即 `git checkout -- <file>` 恢复并用上述替代方案重做。

## 核心坑 2.5：patch 工具的多行嵌套重复 (multi-line nesting bug)

当 `old_string` 跨多行时（典型场景：被替换的代码本身就是 `func_call(\n  arg1\n)` 这种多行调用），patch 工具的字符串拼接逻辑有时会产出**结构合法的嵌套重复**：

期望：
```python
lines.append(f"item {idx}")
```

实际写出来：
```python
lines.append(
    lines.append(f"item {idx}")
)
```

`old_string` 包含了 `lines.append(\n` 这种换行尾的片段，工具在拼接时把 `new_string` 的开头几行当成新内容保留，旧的结尾几行（包括 `lines.append(`）也保留下来——结果是 `lines.append(\n new\n) ` 套在原始 `lines.append(...)\n)` 上。

**症状：**
- 文件 syntax 合法（不会立刻报错），但 linter/mypy 会抓出奇怪的"argument of type None"或"too many positional arguments"
- 看代码像多套了一层函数包装
- patch 返回的 diff 看起来"对"——但实际文件不对

**触发条件：**
- `old_string` 跨度 ≥ 3 行
- `old_string` 末尾包含半开的括号/方括号（`[`, `(`, `{`），没匹配闭合
- 替换行本身也是多行表达式

**识别方法：** patch 后立刻 read_file 看一下原被替换位置，**不要相信 diff 显示的"匹配了多少行"**。diff 是从 old_string 到 new_string 的字面变化，**它不会告诉你 new_string 跟上下文合起来有没有重复嵌套**。

**解决方案：** patch 后**必须立刻 read_file 检查整段被替换位置的上下文**，确认结构没多套：

```bash
# 用 terminal + sed 看包含被替换段的几行
grep -n -B 2 -A 4 '可疑的标识符' file.py
```

如果发现嵌套，直接 `git checkout -- <file>` 恢复再换写法（`write_file` 整文件重写最稳）。

## 核心坑 3：npm uninstall 的级联删除

`npm uninstall <pkg>` 可能移除该包的传递依赖，导致其他包也被删除。例：`npm uninstall @iarna/toml` 移除了 95 个包，包括 `@vitejs/plugin-react`，导致 vitest 和 vite build 全部崩溃。

**症状：** uninstall 后 `npx vitest run` 报 `ERR_MODULE_NOT_FOUND`，`npm run build` 报 `tsc: 未找到命令`。

**正确做法：**

1. 优先用 `npm install <new-pkg> && npm uninstall <old-pkg>` 两步操作，让 npm 在 install 阶段补回缺失的传递依赖
2. 如果已经级联损坏，用 `npm install`（不删 node_modules）增量修复，而不是 `rm -rf node_modules && npm install`
3. 极端情况：`rm -rf node_modules package-lock.json && npm install` 全量重建

## 浏览器不兼容的 Node 包

部分 npm 包在浏览器环境直接报错，因为引用了 `global`、`process`、`Buffer`、`fs` 等 Node-only API。即使 Vite/Rolldown 做了 CJS→ESM 转换，运行时引用仍会炸。

**常见症状：** `Uncaught ReferenceError: global is not defined`

**已知不兼容 → 兼容替换：**

| 不兼容 | 浏览器替代 | 说明 |
|--------|-----------|------|
| `@iarna/toml` | `smol-toml` | TOML 解析，API 几乎相同 (`.parse()` / `.stringify()`) |
| `fs` / `path` | 避免使用 | 文件系统操作只能用 File System Access API |

**检测方法：** 在 `vite --host 0.0.0.0` 启动后打开浏览器 F12 → Console，查看红色报错。如果报错指向某个 `node_modules` 包，该包就不兼容浏览器。

详见 `references/browser-incompatible-packages.md`。

## 核心坑 4：openpyxl 在 Python 3.14 下无法读取 xlsx

Arch Linux 的 openpyxl 包与 Python 3.14 存在兼容问题（`TypeError: Fill() takes no arguments`），pandas 读取 xlsx 也会因相同原因失败。Python 3.12 venv 中安装的 openpyxl 同样受影响。

**症状：**
```
TypeError: expected <class 'openpyxl.styles.fills.Fill'>
```

**根本原因：** openpyxl 的 stylesheet 解析在遇到某些 xlsx 样式时触发类型检查 bug，与 Python 版本无关（不同 Python 版本都可能遇到）。

**解决方案 — 直接解析 xlsx 原始 XML：**

xlsx 本质是 zip 文件，解析其内部 XML 可完全绕过 openpyxl：

```bash
# 1. 解压
unzip file.xlsx -d /tmp/xl/

# 2. 读 sharedStrings.xml（文本字典）
python3 -c "
import xml.etree.ElementTree as ET
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
tree = ET.parse('/tmp/xl/xl/sharedStrings.xml')
strings = []
for si in tree.getroot():
    texts = [t.text or '' for t in si.iter(f'{{{ns}}}t')]
    strings.append(''.join(texts))
# strings[0] = '姓名', strings[1] = '张三', ...

# 3. 读 sheet1.xml（单元格引用 sharedStrings 索引）
tree = ET.parse('/tmp/xl/xl/worksheets/sheet1.xml')
for row in tree.findall(f'.//{{{ns}}}row'):
    for c in row.findall(f'{{{ns}}}c'):
        ref = c.get('r')        # 'A1'
        t = c.get('t', '')      # 's' = shared string
        v = c.find(f'{{{ns}}}v')
        if v is not None and v.text:
            val = strings[int(v.text)] if t == 's' else v.text
"

# 4. 日期序列号转换（Excel 日期从 1900-01-01 起算）
from datetime import datetime, timedelta
def excel_date(serial):
    return (datetime(1899, 12, 30) + timedelta(days=int(serial))).strftime('%Y-%m-%d')
```

**前置条件：** 文件需先从 NTFS 分区拷贝到 `/tmp`（NTFS 权限问题可能导致读取失败）。

## 安全操作速查

| 操作 | 用这个 | 注意事项 |
|------|--------|---------|
| 读 JSON/YAML 改配置 | `terminal` + `python3 -c` | |
| 读代码参考 | `read_file`（安全） | |
| 改代码 — 单行/小改动 | `terminal` + `sed` | 跨行 JSX 用 sed 比 patch 更可靠 |
| 改代码 — 多行/大改动 | `write_file` 重写整个文件 | 先 `read_file` 拿到内容到上下文 |
| 改代码 — 极简单行 | `patch` | 仅在 old_string 是单行且不含反斜杠时安全 |
| 写入新文件 | `write_file`（安全——没有行号污染） | |
| 操作数据库 | `terminal` + `python3 -c "import sqlite3"` | |
