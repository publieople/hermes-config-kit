#!/usr/bin/env python3
"""
Notion 记账 — 安全版创建账单
功能：幂等检查 + 选项验证 + 审核模式
用法：
  ./create-bill-safe.py --title "外卖" --amount 19.07           # 直接创建（自动验证）
  ./create-bill-safe.py --title "外卖" --amount 19.07 --review  # 审核模式
"""

import argparse, json, sys, urllib.request, re
from pathlib import Path
from datetime import date, datetime

NOTION_KEY = Path.home().joinpath(".config/notion/api_key").read_text().strip()
DATABASE_ID = "12366ad7-c9c4-8141-8f05-e335b3d0cb5b"
DATA_SOURCE_ID = "12366ad7-c9c4-81d6-9cbc-000bcd11a4d0"
PEOPLE_DB_ID = "1f766ad7-c9c4-8007-a335-d4f650b7217f"
PEOPLE_DATA_SOURCE_ID = "1f766ad7-c9c4-809b-b8aa-000b9c738b61"
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

# ---- 缓存 ----
_metadata_cache = None

# ---- 工具函数 ----

def notion_post(endpoint, body):
    url = f"https://api.notion.com/v1/{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def notion_get(endpoint):
    url = f"https://api.notion.com/v1/{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def notion_patch(endpoint, body):
    url = f"https://api.notion.com/v1/{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_db_metadata():
    """获取数据库字段元数据（缓存）"""
    global _metadata_cache
    if _metadata_cache:
        return _metadata_cache
    meta = notion_get(f"data_sources/{DATA_SOURCE_ID}")
    _metadata_cache = meta.get("properties", {})
    return _metadata_cache

def validate_select_option(field_name, value, metadata):
    """验证 select 选项是否存在"""
    field = metadata.get(field_name)
    if not field:
        return False
    ftype = field.get("type")
    if ftype == "select":
        options = [o["name"] for o in field.get("select", {}).get("options", [])]
        return value in options
    elif ftype == "multi_select":
        options = [o["name"] for o in field.get("multi_select", {}).get("options", [])]
        return value in options
    elif ftype == "status":
        groups = field.get("status", {}).get("options", [])
        options = []
        for g in groups:
            for o in g.get("options", []):
                options.append(o.get("name", ""))
        options += [g.get("name") for g in groups]
        return value in options
    return False

def check_idempotent(title, amount, date_str):
    """检查最近 50 条是否已有相同记录（幂等检查）"""
    body = {"query": title}
    results = notion_post("search", body).get("results", [])
    for r in results:
        if r.get("object") != "page":
            continue
        props = r.get("properties", {})
        # 检查金额
        r_amount = None
        if "金额" in props and props["金额"].get("type") == "number":
            r_amount = props["金额"].get("number")
        # 检查日期
        r_date = None
        if "交易日期" in props and props["交易日期"].get("type") == "date":
            r_date = props["交易日期"]["date"]["start"] if props["交易日期"]["date"] else None
        if r_amount == amount and r_date == date_str:
            page_id = r.get("id", "?")
            url = r.get("url", "?")
            return True, page_id, url
    return False, None, None

def search_person(name):
    """搜索人脉"""
    body = {"query": name}
    results = notion_post("search", body).get("results", [])
    matches = []
    for r in results:
        props = r.get("properties", {})
        for k, v in props.items():
            if v.get("type") == "title":
                title_text = "".join(t.get("plain_text", "") for t in v.get("title", []))
                if name.lower() in title_text.lower():
                    matches.append({
                        "id": r["id"],
                        "name": title_text,
                        "url": r.get("url", ""),
                    })
    return matches

def determine_meal_tag():
    """根据当前时间确定餐食标签"""
    now = datetime.now()
    h = now.hour
    if 6 <= h < 10:
        return "早餐"
    elif 11 <= h < 14:
        return "午餐"
    elif 17 <= h < 21:
        return "晚餐"
    else:
        return "夜宵"

# ---- 账单预览 ----

def preview_bill(args):
    """生成账单预览文本"""
    lines = []
    lines.append(f"📋  账单预览")
    lines.append(f"项目：{args.title}")
    lines.append(f"金额：¥{args.amount}")
    lines.append(f"日期：{args.date}")
    lines.append(f"大项：{args.category}")
    lines.append(f"小项：{args.sub_category}")
    lines.append(f"渠道：{args.channel}")
    if args.platform:
        lines.append(f"平台：{args.platform}")
    lines.append(f"标签：{', '.join(args.tags)}")
    lines.append(f"图标：{args.icon}")
    if args.person:
        lines.append(f"相关人员：{args.person}")
    return "\n".join(lines)

# ---- 创建账单 ----

def create_bill(args):
    """执行创建账单"""
    tags = [{"name": t} for t in args.tags]
    properties = {
        "项目": {"title": [{"text": {"content": args.title}}]},
        "金额": {"number": args.amount},
        "交易日期": {"date": {"start": args.date}},
        "交易渠道": {"select": {"name": args.channel}},
        "大项": {"select": {"name": args.category}},
        "小项": {"select": {"name": args.sub_category}},
        "标签": {"multi_select": tags},
        "状态": {"status": {"name": "已结算"}},
    }
    if args.platform:
        properties["平台"] = {"select": {"name": args.platform}}

    body = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties,
        "icon": {"type": "emoji", "emoji": args.icon},
    }

    # 如果有相关人员，先搜索
    if args.person:
        persons = search_person(args.person)
        if persons:
            print(f"  找到人脉：{persons[0]['name']} ({persons[0]['id']})")
            body["properties"]["相关人员"] = {"relation": [{"id": persons[0]["id"]}]}

    result = notion_post("pages", body)
    page_id = result.get("id", "?")
    page_url = result.get("url", "?")
    print(f"\n✅ 账单已创建")
    print(f"  ID: {page_id}")
    print(f"  URL: {page_url}")
    return result

# ---- 主流程 ----

def main():
    parser = argparse.ArgumentParser(description="安全创建账单")
    parser.add_argument("--title", default="外卖", help="项目名称")
    parser.add_argument("--amount", type=float, required=True, help="金额")
    parser.add_argument("--date", default=date.today().isoformat(), help="日期 (YYYY-MM-DD)")
    parser.add_argument("--category", default="饮食", help="大项")
    parser.add_argument("--sub-category", default="外卖", help="小项")
    parser.add_argument("--channel", default="微信零钱", help="交易渠道")
    parser.add_argument("--platform", default=None, help="平台")
    parser.add_argument("--tags", nargs="+", default=None, help="标签")
    parser.add_argument("--icon", default="🥡", help="图标 emoji")
    parser.add_argument("--person", default=None, help="相关人员姓名")
    parser.add_argument("--review", action="store_true", help="审核模式：先展示确认再执行")
    parser.add_argument("--no-verify", action="store_true", help="跳过选项验证（不推荐）")

    args = parser.parse_args()

    # 自动填充标签
    if args.tags is None:
        meal_tag = determine_meal_tag()
        args.tags = ["外卖", meal_tag]

    # 1. 选项验证
    if not args.no_verify:
        print("🔍 验证选项...")
        metadata = get_db_metadata()

        checks = {
            "大项": args.category,
            "小项": args.sub_category,
            "交易渠道": args.channel,
        }
        if args.platform:
            checks["平台"] = args.platform

        errors = []
        for field, value in checks.items():
            if not validate_select_option(field, value, metadata):
                errors.append(f"❌ [{field}] '{value}' 不在有效选项中")

        if errors:
            print("\n".join(errors))
            print("\n⚠️  请修正后重试。选项信息可通过数据库元数据获取。")
            sys.exit(1)

        # 验证标签
        for tag in args.tags:
            if not validate_select_option("标签", tag, metadata):
                print(f"⚠️  标签 '{tag}' 不在预选项中，仍可创建（multi_select 可新增）")

        print("✅ 选项验证通过")

    # 2. 幂等检查
    print("🔍 检查重复记录...")
    is_dup, page_id, page_url = check_idempotent(args.title, args.amount, args.date)
    if is_dup:
        print(f"⚠️  发现重复记录：{page_url}")
        print("是否仍然创建？(y/N): ", end="")
        resp = input().strip().lower()
        if resp != "y":
            print("已取消")
            sys.exit(0)

    # 3. 审核模式
    if args.review:
        print()
        print(preview_bill(args))
        print()
        print("确认创建？(Y/n): ", end="")
        resp = input().strip().lower()
        if resp == "n":
            print("已取消")
            sys.exit(0)

    # 4. 创建
    create_bill(args)

if __name__ == "__main__":
    main()
