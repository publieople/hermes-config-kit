#!/usr/bin/env python3
"""
Notion 查账 — 查看最近账单
用法：
  ./query-bills.py               # 最近 20 条
  ./query-bills.py --limit 5     # 最近 5 条
  ./query-bills.py --search "外卖"  # 按关键词搜索
"""

import argparse, json, sys, urllib.request
from pathlib import Path
from datetime import datetime

NOTION_KEY = Path.home().joinpath(".config/notion/api_key").read_text().strip()
DATABASE_ID = "12366ad7-c9c4-8141-8f05-e335b3d0cb5b"
DATA_SOURCE_ID = "12366ad7-c9c4-81d6-9cbc-000bcd11a4d0"
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

def notion_post(endpoint, body):
    url = f"https://api.notion.com/v1/{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def safe_get(obj, *keys, default="?"):
    """安全地链式取值"""
    for k in keys:
        if obj is None or not isinstance(obj, dict):
            return default
        obj = obj.get(k)
    return obj if obj is not None else default

def format_page(page):
    props = page.get("properties", {})

    # Title
    title = "?"
    for k, v in props.items():
        if isinstance(v, dict) and v.get("type") == "title":
            title = "".join(t.get("plain_text", "") for t in v.get("title", []) if isinstance(t, dict))
            break

    amount = safe_get(props, "金额", "number", default=None)
    category = safe_get(props, "大项", "select", "name", default="?")
    sub_cat = safe_get(props, "小项", "select", "name", default="?")
    date_val = safe_get(props, "交易日期", "date", "start", default="?")
    channel = safe_get(props, "交易渠道", "select", "name", default="?")
    platform = safe_get(props, "平台", "select", "name", default="")
    tags = [t.get("name") for t in (safe_get(props, "标签", "multi_select", default=[]))]
    icon = safe_get(page, "icon", "emoji", default="")
    url = page.get("url", "")
    page_id = page.get("id", "")[:8]

    amount_str = f"¥{amount:.2f}" if amount is not None else "?"
    return {
        "title": title, "amount": amount_str, "amount_raw": amount,
        "category": category, "sub_category": sub_cat,
        "date": date_val, "channel": channel, "platform": platform,
        "tags": tags, "icon": icon, "url": url, "id": page_id,
    }

def query_recent(limit=20):
    """通过 data_source 查询近期账单"""
    body = {
        "sorts": [{"property": "交易日期", "direction": "descending"}],
        "page_size": limit,
    }
    result = notion_post(f"data_sources/{DATA_SOURCE_ID}/query", body)
    bills = []
    for r in result.get("results", []):
        bills.append(format_page(r))
    return bills

def query_by_search(query, limit=20):
    """通过 search API 搜索"""
    body = {"query": query}
    results = notion_post("search", body).get("results", [])
    bills = []
    for r in results:
        if r.get("object") != "page":
            continue
        # 简单判断是否在账本数据库
        parent = r.get("parent", {})
        if parent.get("type") == "database_id" and parent.get("database_id") == DATABASE_ID:
            bills.append(format_page(r))
        elif parent.get("type") == "data_source" and parent.get("data_source_id") == DATA_SOURCE_ID:
            bills.append(format_page(r))
        elif parent.get("database_id") == DATABASE_ID:
            bills.append(format_page(r))
        if len(bills) >= limit:
            break
    return bills

def get_month_total(bills, month):
    """计算指定月份总支出"""
    total = 0
    count = 0
    for b in bills:
        if b["date"] and b["date"].startswith(f"2026-{month:02d}"):
            if b["amount_raw"] is not None and b["amount_raw"] > 0:
                # 只看支出类
                total += b["amount_raw"]
                count += 1
    return total, count

def print_bills(bills):
    if not bills:
        print("没有找到记录")
        return

    # 统计
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"📊 Notion 收支记录 — {today}")
    print(f"共 {len(bills)} 条")
    print()

    header = f"{'':>2} {'日期':<12} {'金额':<10} {'项目':<24} {'大项/小项':<20} {'渠道':<14} {'标签':<20}"
    print(header)
    print("-" * 110)
    for i, b in enumerate(bills, 1):
        icon = b.get("icon", "")
        title = f"{icon} {b['title']}" if icon else b["title"]
        tags = ", ".join(b.get("tags", []))[:20]
        cat_sub = f"{b['category']}/{b['sub_category']}"
        print(f"{i:>2} {b['date']:<12} {b['amount']:<10} {title:<24} {cat_sub:<20} {b['channel']:<14} {tags}")

def main():
    parser = argparse.ArgumentParser(description="查账")
    parser.add_argument("--limit", type=int, default=20, help="条数")
    parser.add_argument("--search", default=None, help="关键词搜索")
    parser.add_argument("--month", type=int, default=None, help="筛选月份")
    args = parser.parse_args()

    if args.search:
        bills = query_by_search(args.search, args.limit)
    else:
        bills = query_recent(args.limit)

    if args.month:
        bills = [b for b in bills if b["date"] and b["date"].startswith(f"2026-{args.month:02d}")]

    print_bills(bills)

if __name__ == "__main__":
    main()
