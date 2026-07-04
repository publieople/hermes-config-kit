---
name: notion-github-sync
description: 双向同步 Notion 知识库到 GitHub — 提取页面+数据库为结构化 Markdown（YAML frontmatter），维护映射追踪，设置 cron 定期同步。
---

# Notion ↔ GitHub Knowledge Base Sync

从 Notion 工作区提取内容（子页面 + 数据库条目）并同步到 GitHub 仓库作为 MD 文件，维护双向映射以便定期同步。

## When to Use

- 用户说"把我的 Notion 知识库同步到 GitHub"
- 用户想导出 Notion 内容为结构化 Markdown（保留标签、URL、分类等属性）
- 需要设置定期自动同步（cron job）
- 已有 Notion 内容体系，想建立 Git 版本备份
- 用户想从 GitHub 编辑 Markdown 后回写到 Notion

## 架构

```
repo/
├── articles/              ← 子页面 (child_page)
│   ├── 优雅的文件管理.md
│   └── 电脑高手速成班.md
├── curations/
│   ├── tools/             ← 工具数据库条目
│   └── communities/       ← 社区数据库条目
├── scripts/
│   └── sync.py            ← 核心同步脚本
├── _mapping.json           ← notion_id ↔ 文件路径映射（双向同步基础）
├── _sync_state.json        ← 文件哈希 + 最后同步时间
└── README.md
```

每个文件是 Markdown + YAML frontmatter：

```yaml
---
title: 优雅的文件管理
source: article
notion_id: b4266ad7...    # 用于反向同步回写
标签:                     # 数据库属性直接映射
  - 电脑基础
  - 文件管理
网址: "https://..."
last_edited_time: 2026-05-04
---
```

## 转换引擎选型

### 推荐方案：notion-to-md (npm) + Python 编排

Python 自实现的 `walk_blocks()` 无法正确处理：
- **粗体/斜体** 文字格式（丢失）
- **编号列表**（全部变成 `1. 1. 1.`）
- **图片链接**（只能输出 `[IMAGE]` 占位符）
- **Callout/Quote** 渲染（格式错误）

**[souvikinator/notion-to-md](https://github.com/souvikinator/notion-to-md)** (1.5k+ stars, 45 releases) 是社区最成熟的 Notion→Markdown 转换库，以上问题全部解决。

### 双引擎架构

```
sync.py (Python)                    ← 编排：属性提取、frontmatter、git、cron
  ├── 文章页面 → 调用 n2m-convert.js (Node.js)     ← 高质量内容转换
  └── 数据库条目 → 使用 Python walk_blocks()       ← 数据库条目通常无 rich content
```

**n2m-convert.js** 是 Node.js wrapper，安装方式：
```bash
cd ~/notion-knowledge-base && npm install notion-to-md @notionhq/client
```

**n2m-convert.js 的核心逻辑：**
```javascript
const { NotionToMarkdown } = require("notion-to-md");
const { Client } = require("@notionhq/client");

const notion = new Client({ auth: NOTION_KEY, notionVersion: "2025-09-03" });
const n2m = new NotionToMarkdown({ notionClient: notion });

// Convert page to markdown blocks
const mdBlocks = await n2m.pageToMarkdown(pageId, 100);
const mdString = n2m.toMarkdownString(mdBlocks);
const content = mdString.parent || "";

// Post-process: clean excessive blank lines from notion-to-md
const cleaned = content
  .replace(/\n{3,}/g, "\n\n")   // 3+ blank lines → 2
  .replace(/^\n+/, "")
  .replace(/\n+$/, "")
  .trim();
```

**Python 端的集成：**
```python
n2m_script = os.path.join(SCRIPTS_DIR, "n2m-convert.js")
try:
    r = subprocess.run(
        ["node", n2m_script, page_id],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode == 0 and r.stdout.strip():
        md_content = r.stdout.strip()
    else:
        # Fallback to Python walker
        md_content = "\n".join(walk_blocks(page_id))
except Exception:
    md_content = "\n".join(walk_blocks(page_id))
```

### Python-only 方案（备选/数据库条目）

当 Node.js 不可用或处理无 rich content 的数据库条目时，回退到 `walk_blocks()`。

### 对比

| 特性 | Python walk_blocks | notion-to-md (npm) |
|------|-------------------|-------------------|
| 粗体/斜体 | ❌ 丢失 | ✅ 保留 `**text**` |
| 编号列表 | ❌ 全变 `1.` | ✅ 1. 2. 3. 正确 |
| 图片 URL | ❌ `[IMAGE]` | ✅ 实际 Notion CDN URL |
| Callout | ❌ 格式错误 | ✅ `> text` 正确渲染 |
| 方程 (LaTeX) | ⚠️ 基本 | ✅ 标准 `$$ ... $$` |
| 表格 | ⚠️ 基本 | ✅ Markdown table |
| 安装依赖 | 无 | Node.js + npm |

## 核心实现

### 1. API 连接（WSL 兼容）

WSL 上的 Python `urllib.request` 调用 Notion API 会 SSL 握手失败。**不推荐 curl 子进程**（每次新建连接，同样会超时/空响应）。
**最佳方案：** `http.client.HTTPSConnection` 连接池，重复使用同一个 TCP 连接：

```python
import http.client, ssl, socket

_conn = None
def _get_conn():
    global _conn
    if _conn is None:
        ctx = ssl.create_default_context()
        _conn = http.client.HTTPSConnection("api.notion.com", timeout=30, context=ctx)
    return _conn
```

### 2. 速率限制

Notion API 约 3 req/s，必须在每次 API 调用前 sleep：

```python
_last_call = 0.0
API_DELAY = 0.45

def api_call(url, data=None):
    global _last_call
    now = time.time()
    if now - _last_call < API_DELAY:
        time.sleep(API_DELAY - (now - _last_call))
    # ... make request
    _last_call = time.time()
```

### 3. 连接错误恢复

连接池连接可能因空闲太久或网络波动断开。捕获异常后重置 `_conn = None` 再重试：

```python
except (ConnectionResetError, http.client.RemoteDisconnected, OSError):
    _conn = None  # 强制重新连接
    # retry with exponential backoff
```

### 4. 数据库属性提取

`extract_database_properties()` 处理所有 Notion 属性类型到 Python 类型映射：

| Notion 类型 | Python/YAML 类型 |
|---|---|
| title | string |
| rich_text | string |
| multi_select | list[string] |
| select | string 或 null |
| url | string |
| created_time | string (YYYY-MM-DD) |
| unique_id | string (prefix-number) |
| checkbox | bool |
| number | int/float 或 null |
| date | dict {start, end} 或 null |
| status | string |

### 5. 文件命名

`file_safe_title(title)`: 移除特殊字符，用 `_` 替换空白，截断到 80 字符。

### 6. 同步状态追踪

`_sync_state.json` 记录每个文件的 MD5 哈希。反向同步时比对哈希以检测 GitHub 端的修改：

```python
state = {"last_sync": "...", "file_hashes": {"articles/foo.md": "md5hash..."}}
```

### 7. Cron 任务设置

使用 Hermes `cronjob` 工具，设置 `workdir=/home/po/notion-knowledge-base`：

```
cronjob action=create name="notion-sync" schedule="0 10 * * 0" \
  prompt="cd ~/notion-knowledge-base && python3 scripts/sync.py" \
  workdir=/home/po/notion-knowledge-base
```

## 同步脚本结构

```
sync.py
├── sync_notion_to_github()    # 正向: Notion → GitHub
│   ├── 提取子页面 (child_page)
│   │   └── 调用 n2m-convert.js (notion-to-md) 做内容转换
│   ├── 提取数据库条目 (query_database with pagination)
│   │   └── Python walk_blocks()（无 rich content 的数据库）
│   ├── 每个页面: YAML frontmatter + Git 操作
│   └── git add/commit/push
├── sync_github_to_notion()    # 反向: GitHub → Notion
│   ├── 加载 mapping + state
│   ├── 比对文件哈希
│   └── PATCH 更新 Notion 页面
└── git_commit_and_push()
```

## 2026-05-04 实战教训

### npm 依赖
- `notion-to-md` 需要 `@notionhq/client` 作为 peer dependency，两个都要装
- `node_modules/` 必须加入 `.gitignore`，否则 100+ 文件被提交
- 使用 `npm install notion-to-md @notionhq/client` 同时安装

### Python → Node.js 集成
- Python 用 `subprocess.run(["node", script, page_id], timeout=60)` 调用
- Node.js 脚本输出到 stdout，错误到 stderr（`process.stderr.write("N2M_ERROR: ...")`）
- Python 端判读 `returncode == 0 and r.stdout.strip()`，失败时 fallback 到 Python walker

### Web 搜索发现的不同工具方案
- **souvikinator/notion-to-md** (npm, 1.5k+ stars, 45 releases): 最成熟的转换库，推荐
- **byvfx/go-notion-md-sync** (Go CLI, 20+ stars): 双向同步 CLI，有 TUI 和 watch 模式，但需要 Go 环境
- **YouXam/Notion-GitHub-Sync** (GitHub Action): 简单但功能有限
- 结论：使用 notion-to-md 做转换引擎 + Python 做编排是可维护性最佳的方案

## 关键注意事项

### 页面内容提取 (walk_blocks)
- **synced_block**: 透传子节点，本身不产生输出
- **column_list/column**: 静默透传子节点，**不产生 `<!-- COLUMN -->` 标记**
- **toggle**: 转为 `<details><summary>...</summary>`（紧凑格式，无多余空白行）
- **image**: `*📷 caption*` 或 `*📷 图片*`，不生成 `IMAGE_PLACEHOLDER`
- **video/file/pdf**: `*[类型]*` 占位符
- **bookmark**: 有 caption 时 `[🔗 caption](url)`，无 caption 时 `<url>`
- **embed**: 提取 URL 为 `<url>`，不加描述文本
- **table**: 递归提取 table_row 为 `| cell | cell |` 格式
- **divider**: 跳过与上一行重复的 `---`，跳过紧跟在标题后的 `---`
- **child_database**: 静默跳过，不产生输出
- **未知 block 类型**: 静默跳过，**不产生 `<!-- UNKNOWN_TYPE -->` 注释**
- 404 错误（"Could not find block with ID"）可忽略 —— 通常是 synced_block 引用了 API 无权访问的页面

### 文件名冲突 vs 质量优化

**冲突处理：** 同名文件直接覆盖（`open(..., "w")`），不应创建 `_1.md` 副本。

**文件名安全：** `file_safe_title(title)` 只移除 Windows/Unix 非法字符 `\/:*"<>|`，保留 `~`、`?`、`^`、`()` 等常见字符：
```python
safe = title.strip().replace(" ", "_")
safe = re.sub(r'[\\/:*"<>|]', '', safe)
```

### Frontmatter 清理

YAML frontmatter 应只保留有意义的字段：
- 跳过空值：`None`, `""`, `[]`, `{}`
- 跳过内部字段：`在本项目中`, `created_time`(空), `名称`, `ID`
- 始终保留 `notion_id` + `synced_at`
- 使用 `synced_at` 而非 `notion_synced_at`（更简洁）

### 数据库查询
在 Notion-Version 2025-09-03 中使用 `data_sources` 端点（非 `databases`）：
```
POST /v1/data_sources/{data_source_id}/query
```

### 首次同步
34 篇文章 + 20-30 个工具/社区条目 ≈ 200+ API 调用，耗时 3-5 分钟。

## 相关 Skill

- `notion-content-extraction`：单次页面内容提取，不包含 Git 同步和数据库属性处理
- `notion`（openclaw-imports）：Notion API 原始调用参考