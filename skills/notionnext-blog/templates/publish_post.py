#!/usr/bin/env python3
"""Publish a blog post to Publieople's Blog (NotionNext).
Usage: python3 publish_post.py
Edit the TITLE, SLUG, CATEGORY, TAGS, SUMMARY, and MARKDOWN below.
"""
import json, subprocess, urllib.request

# ── Configure ──────────────────────────────────────────
TITLE = "文章标题"
SLUG = "url-slug"
CATEGORY = "折腾记录"  # 技术分享|心情随笔|差生文具多|知识分享|资源整理|项目经历|折腾记录|活动体验
STATUS = "Published"   # Published | Draft | Invisible
DATE = "2026-06-08"
TAGS = ["Tag1", "Tag2"]
SUMMARY = "文章摘要，用于 meta description。"
MARKDOWN = """# 文章标题

文章内容（Notion-flavored Markdown）。
"""
# ── End config ──────────────────────────────────────────

DB = "02e0b2a07b164c37abb9cfc3db88c605"
key = subprocess.run(["cat", "/home/po/.config/notion/api_key"], capture_output=True, text=True).stdout.strip()

payload = {
    "parent": {"database_id": DB},
    "properties": {
        "title": {"title": [{"text": {"content": TITLE}}]},
        "type": {"select": {"name": "Post"}},
        "status": {"select": {"name": STATUS}},
        "category": {"select": {"name": CATEGORY}},
        "date": {"date": {"start": DATE}},
        "slug": {"rich_text": [{"text": {"content": SLUG}}]},
        "tags": {"multi_select": [{"name": t} for t in TAGS]},
        "summary": {"rich_text": [{"text": {"content": SUMMARY}}]}
    },
    "markdown": MARKDOWN
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

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        pid = result["id"]
        print(f"✅ {STATUS}: https://notion.so/{pid.replace('-','')}")
        print(f"   Blog: https://blog.for-people.cn/article/{SLUG}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body[:500]}")
