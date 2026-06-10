#!/usr/bin/env python3
"""
Bangumi 番剧订阅管理脚本
用法:
  python3 bangumi.py list                      # 列出订阅
  python3 bangumi.py add <subject_id> <name>   # 添加订阅
  python3 bangumi.py remove <subject_id>       # 移除订阅
  python3 bangumi.py update <subject_id> <ep>  # 更新已通知到第几话
  python3 bangumi.py get <subject_id>          # 获取订阅信息
"""
import json, sys, os

DATA_FILE = os.path.expanduser("~/.hermes/bangumi_subscriptions.json")

def load():
    if not os.path.exists(DATA_FILE):
        return {"subscriptions": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_subs():
    data = load()
    subs = data.get("subscriptions", [])
    if not subs:
        print("暂无订阅")
        return
    print(f"共 {len(subs)} 部订阅:\n")
    for s in subs:
        sid = s.get("subject_id", "?")
        name = s.get("name", "?")
        last = s.get("last_notified_ep", 0)
        total = s.get("total_eps", "?")
        print(f"  [{sid}] {name} - 已通知到第{last}话 / 共{total}话")

def add(subject_id, name):
    data = load()
    for s in data["subscriptions"]:
        if s["subject_id"] == subject_id:
            print(f"已存在: [{subject_id}] {name}")
            return
    data["subscriptions"].append({
        "subject_id": subject_id,
        "name": name,
        "last_notified_ep": 0,
        "total_eps": "?"
    })
    save(data)
    print(f"已添加: [{subject_id}] {name}")

def remove(subject_id):
    data = load()
    before = len(data["subscriptions"])
    data["subscriptions"] = [s for s in data["subscriptions"] if s["subject_id"] != subject_id]
    after = len(data["subscriptions"])
    save(data)
    if before > after:
        print(f"已移除订阅: {subject_id}")
    else:
        print(f"未找到订阅: {subject_id}")

def update(subject_id, ep, total_eps=None):
    data = load()
    for s in data["subscriptions"]:
        if s["subject_id"] == subject_id:
            s["last_notified_ep"] = ep
            if total_eps is not None:
                s["total_eps"] = total_eps
            save(data)
            print(f"已更新 [{subject_id}] 通知到第{ep}话")
            return
    print(f"未找到订阅: {subject_id}")

def get(subject_id):
    data = load()
    for s in data["subscriptions"]:
        if s["subject_id"] == subject_id:
            print(json.dumps(s, ensure_ascii=False))
            return
    print(f"未找到订阅: {subject_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        list_subs()
    elif cmd == "add":
        if len(sys.argv) < 4:
            print("用法: python3 bangumi.py add <subject_id> <name>")
            sys.exit(1)
        add(int(sys.argv[2]), sys.argv[3])
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("用法: python3 bangumi.py remove <subject_id>")
            sys.exit(1)
        remove(int(sys.argv[2]))
    elif cmd == "update":
        if len(sys.argv) < 4:
            print("用法: python3 bangumi.py update <subject_id> <ep> [total_eps]")
            sys.exit(1)
        total = int(sys.argv[4]) if len(sys.argv) > 4 else None
        update(int(sys.argv[2]), int(sys.argv[3]), total)
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("用法: python3 bangumi.py get <subject_id>")
            sys.exit(1)
        get(int(sys.argv[2]))
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
