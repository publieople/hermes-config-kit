---
name: notionnext-blog
description: 发布文章到 Publieople's Blog（NotionNext 驱动的博客）——搜索数据库、理解 schema、创建文章、验证上线。
category: productivity
---

# NotionNext 博客发布

## 触发条件
- 用户要求"写博客""发到博客""发布文章""post to my blog"
- 用户提到 blog.for-people.cn 或 NotionNext
- 需要查询/管理已有的博客文章

## 前置条件

Notion API key 在 `~/.config/notion/api_key`，格式 `ntn_...`。

## 博客数据库

- **名称**: Publieople's Blog
- **数据库 ID**: `02e0b2a07b164c37abb9cfc3db88c605`
- **NotionNext 配置中的 NOTION_PAGE_ID**: `097e5f674880459d8e1b4407758dc4fb`（blog.config.js）
- **博客地址**: https://blog.for-people.cn

## 数据库 Schema

| 属性 | 类型 | 可选值 |
|------|------|--------|
| `title` | title | — |
| `status` | select | Published, Invisible, Draft |
| `type` | select | Post, Page, Notice, Menu, SubMenu, Config |
| `category` | select | 技术分享, 心情随笔, 差生文具多, 知识分享, 资源整理, 项目经历, 折腾记录, 活动体验 |
| `slug` | rich_text | URL 路径（如 `tiez-webdav-debugging`） |
| `tags` | multi_select | 自由标签 |
| `summary` | rich_text | 文章摘要（用于 meta description） |
| `date` | date | 发布日期 |
| `password` | rich_text | 文章密码（可选） |
| `icon` | rich_text | 自定义图标 URL（可选） |

## 发布流程

### 1. 获取 key

```python
import subprocess
key = subprocess.run(["cat", "/home/po/.config/notion/api_key"], capture_output=True, text=True).stdout.strip()
```

### 2. 创建文章（Python + Notion API）

**不要用 shell curl**——API key 在终端中会被掩码为 `***` 导致 auth 失败。

```python
import json, urllib.request

DB = "02e0b2a07b164c37abb9cfc3db88c605"

markdown = """# 文章标题

文章内容（Notion-flavored Markdown）。
"""

payload = {
    "parent": {"database_id": DB},
    "properties": {
        "title": {"title": [{"text": {"content": "文章标题"}}]},
        "type": {"select": {"name": "Post"}},
        "status": {"select": {"name": "Published"}},
        "category": {"select": {"name": "折腾记录"}},
        "date": {"date": {"start": "2026-06-08"}},
        "slug": {"rich_text": [{"text": {"content": "url-slug"}}]},
        "tags": {"multi_select": [{"name": "Tag1"}, {"name": "Tag2"}]},
        "summary": {"rich_text": [{"text": {"content": "文章摘要"}}]}
    },
    "markdown": markdown
}

req = urllib.request.Request(
    "https://api.notion.com/v1/pages",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    page_id = result["id"]
    print(f"Published: https://notion.so/{page_id.replace('-','')}")
```

### 3. 验证上线

NotionNext 默认 revalidate 60 秒。验证：

```bash
curl -sI "https://blog.for-people.cn/article/{slug}" | grep HTTP
# HTTP/2 200  → 上线成功
```

## 文章写作风格

来自用户资料：
- **先结论后展开**：用 `<callout>` 把结论放在开头
- **精确、直接**：不讲故事，说事实
- **技术叙事**：按时间线展开调试过程，带代码片段
- **Notion 块**：善用 `<callout>`、`<details>`、代码块等 Notion-flavored Markdown

## 常见错误

### `comment is not a property that exists`
数据库中属性名是 `comment `（尾部有空格），但 API 要求精确匹配。忽略此属性即可，不影响发布。

### API key 失效（`unauthorized`）
终端 curl 命令中 `$NOTION_KEY` 被系统掩码为 `***`，导致 auth header 变成字面量 `Bearer ***`。**必须用 Python 脚本**读文件取 key。

### 数据库找不到（`Could not find database`）
两种可能：
1. 数据库未授权给 Hermes integration → 在 Notion 里 `...` → Connections → 添加 Hermes
2. ID 使用了 NOTION_PAGE_ID（page token）而非 database_id → 用 search API 搜索 "blog" 找到真正的 database_id
