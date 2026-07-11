#!/usr/bin/env python3
"""
dump_comfyui_prompt.py — 拉取 ComfyUI 最近一次执行的完整 prompt JSON

用法:
    python3 dump_comfyui_prompt.py                              # 默认本地 :8188
    python3 dump_comfyui_prompt.py --port 8188 --items 5       # 拉最近 5 条
    python3 dump_comfyui_prompt.py --pid <uuid>                 # 指定 prompt_id
    python3 dump_comfyui_prompt.py --filter-clip                # 只显示 CLIPTextEncode 节点

关键点:
- /history?max_items=N 返回的 prompt 字段被 [truncated] 替换，没用
- /history/{prompt_id} 才是完整数据 (ComfyUI server 默认行为)
- CLIPTextEncode 节点 = 用户 prompt 实际落地的地方，看这个字段就够

不要修改 ComfyUI server 源码去关掉 truncation（这是默认安全行为，跨 session 用）。
"""
import argparse
import json
import sys
import urllib.request


def fetch(url, timeout=10):
    return json.loads(urllib.request.urlopen(url, timeout=timeout).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default=8188, type=int)
    ap.add_argument("--items", default=1, type=int, help="拉最近 N 条 (默认 1)")
    ap.add_argument("--pid", help="指定 prompt_id")
    ap.add_argument("--filter-clip", action="store_true", help="只显示 CLIPTextEncode 节点")
    args = ap.parse_args()

    base = f"http://{args.host}:{args.port}"

    if args.pid:
        history = {args.pid: fetch(f"{base}/history/{args.pid}")[args.pid]}
    else:
        history = fetch(f"{base}/history?max_items={args.items}")

    for pid, item in history.items():
        pj = item.get("prompt")
        if not pj or len(pj) < 3:
            print(f"[{pid}] no prompt field (history truncated)", file=sys.stderr)
            continue

        prompt_dict = pj[2]
        print(f"\n=== prompt_id: {pid} ===")

        if args.filter_clip:
            for nid, nd in prompt_dict.items():
                if nd.get("class_type") == "CLIPTextEncode":
                    text = nd.get("inputs", {}).get("text", "<missing>")
                    title = nd.get("_meta", {}).get("title", "")
                    print(f"  node {nid} {title!r}: {text!r}"[:300])
        else:
            print(json.dumps(prompt_dict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
