---
name: notionnext-content-sync-diagnostics
description: NotionNext 博客文章未同步诊断。当用户说"文章没有同步""文章少了""内容没更新""missing posts""draft not showing"时加载。
version: 1.0.0
author: Hermes Agent
tags: [notionnext, notion, blog, sync, troubleshooting]
---

# NotionNext 博客内容同步诊断

NotionNext 使用 Notion 数据库作为数据源。文章能否显示取决于数据库里每篇文章的 `status` 和 `type` 属性值。当用户报告文章缺失时，这是最常中的排查路径。

## 触发时机

用户提到以下任一情况时加载本 skill：
- "文章少了" / "很多文章没同步" / "文章不见了"
- "内容没更新" / "新写的文章不显示"
- "Notion 更新了但博客没变" / "missing posts"
- "draft 不显示" / "只有几篇文章"

## 快速诊断流程

### 1. 确认 Notion API 可用

检查是否有 Notion API key：

```bash
cat ~/.config/notion/api_key
```

如果不存在，需要用户从 https://www.notion.so/my-integrations 创建 integration 并获取 key。

### 2. 查找博客数据库

用 NOTION_PAGE_ID 环境变量（或在 blog.config.js 中）定位数据库：

```bash
NOTION_KEY=$(cat ~/.config/notion/api_key)

# 查看数据库 schema（确认属性名）
curl -s "https://api.notion.com/v1/databases/{database_id}" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-28"
```

关键属性（默认名称，可通过 Vercel env vars 自定义）：
- `status` — 发布状态：`Published`（显示）、`Draft`（不显示）、`Invisible`
- `type` — 类型：`Post`（博文）、`Page`（单页）、`Menu`（菜单）、`Notice`（公告）
- `date` — 发布日期
- `slug` — URL 别名

### 3. 查询所有条目并统计

```python
import urllib.request, json

# 分页查询所有条目
has_more = True
cursor = None
all_pages = []

while has_more:
    payload = {"page_size": 100}
    if cursor:
        payload["start_cursor"] = cursor
    
    req = urllib.request.Request(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {NOTION_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    all_pages.extend(data.get('results', []))
    has_more = data.get('has_more', False)
    cursor = data.get('next_cursor')

for page in all_pages:
    props = page.get('properties', {})
    title = ''.join([t.get('plain_text','') for t in props.get('title',{}).get('title',[])])
    status = props.get('status',{}).get('select',{}).get('name','N/A')
    ptype = props.get('type',{}).get('select',{}).get('name','N/A')
    # 标记状态
    badge = "✅" if (status == "Published" and ptype == "Post") else "❌"
    print(f'{badge} [{ptype:8}] {title[:40]:40}  status={status}')
```

### 4. 结果判断

| 状态 | 含义 | 操作 |
|------|------|------|
| `status = "Published"` 且 `type = "Post"` | 应该显示 | 如果还没显示，检查缓存或 revalidate 配置 |
| `status = "Draft"` | 草稿，不显示 | 改为 Published 即可发布 |
| `status = "Invisible"` | 隐藏，不显示 | 改为 Published 可见 |
| `status = "Published"` 但 `type ≠ "Post"` | 其他类型（Menu/Page/Notice） | 视为导航/单页，不是博文 |

### 5. 批量发布草稿

```python
import urllib.request, json

for page in draft_pages:
    page_id = page['id']
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps({
            "properties": {
                "status": {"select": {"name": "Published"}}
            }
        }).encode(),
        method="PATCH",
        headers={
            "Authorization": f"Bearer {NOTION_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
```

### 6. 缓存说明

NotionNext 默认 `NEXT_REVALIDATE_SECOND = 60`（在 blog.config.js 或 Vercel env 中配置）。改为更小的值（如 `5`）可加速同步，或在 Vercel 手动触发重新部署。

## 常见陷阱

- **属性名自定义了** — 用户可能通过 Vercel env vars 修改了 `NEXT_PUBLIC_NOTION_PROPERTY_STATUS_PUBLISH` 等，查询 schema 时要注意实际值
- **NOTION_PAGE_ID 指向的是 view 而非数据库根** — Notion database URL 中的 view ID 不是数据库 ID，要取 `?v=` 之前的部分
- **集成未授权** — Notion Integration 需要手动在数据库页面的 "Connect to" 中授权，否则 API 查询会返回空
- **速率限制** — Notion API 约 3 req/s，批量操作时建议加延迟
