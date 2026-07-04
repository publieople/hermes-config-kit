#!/usr/bin/env python3
"""
Notion → Distillation Extractor
Extract all text content from a Notion page for persona distillation.
Uses curl subprocess (WSL-safe SSL fix) with pagination support.

Usage:
  python3 notion-distill-extractor.py <page_id> [output_file]

If output_file is omitted, prints to stdout.
"""
import json, os, subprocess, sys

NOTION_KEY = open(os.path.expanduser("~/.config/notion/api_key")).read().strip()
NOTION_VERSION = "2025-09-03"

def api(url, data=None):
    cmd = ["curl", "-s"]
    if data:
        cmd += ["-X", "POST", "-d", json.dumps(data)]
    cmd += [
        "-H", f"Authorization: Bearer {NOTION_KEY}",
        "-H", f"Notion-Version: {NOTION_VERSION}",
        "-H", "Content-Type: application/json",
        url
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def get_blocks(block_id, page_size=100):
    results = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size={page_size}"
        if cursor:
            url += f"&start_cursor={cursor}"
        data = api(url)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results

def extract(block):
    btype = block.get("type", "unknown")
    text = ""
    leaf = {"paragraph", "heading_1", "heading_2", "heading_3",
            "bulleted_list_item", "numbered_list_item", "to_do",
            "callout", "quote", "toggle", "code"}
    has_children = block.get("has_children", False)

    if btype in leaf:
        content = block.get(btype, {})
        rich_text = content.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich_text)
        if btype == "code":
            lang = content.get("language", "")
            text = f"```{lang}\n{text}\n```"
    elif btype == "divider":
        text = "---"
    elif btype == "image":
        text = "[IMAGE]"
    elif btype in ("table", "synced_block", "column_list", "column"):
        has_children = True
    return text, btype, has_children

def walk(page_id, depth=0):
    results = []
    for block in get_blocks(page_id):
        text, btype, has_children = extract(block)
        results.append((text, btype, depth, has_children, block["id"]))
        if has_children:
            results.extend(walk(block["id"], depth + 1))
    return results

def format_markdown(lines):
    out = []
    for text, btype, depth, _, _ in lines:
        indent = "  " * depth
        prefix = {
            "heading_1": "# ", "heading_2": "## ", "heading_3": "### ",
            "bulleted_list_item": "- ", "numbered_list_item": "1. ",
            "to_do": "[ ] ", "callout": "> ", "quote": "> ", "divider": "---",
        }.get(btype, "")
        if text:
            out.append(f"{indent}{prefix}{text}")
    return "\n".join(out)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <page_id> [output_file]", file=sys.stderr)
        sys.exit(1)
    page_id = sys.argv[1]
    lines = walk(page_id)
    output = format_markdown(lines)
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w") as f:
            f.write(output)
        print(f"Written to {sys.argv[2]}")
    else:
        print(output)
