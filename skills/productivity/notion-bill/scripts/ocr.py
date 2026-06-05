#!/usr/bin/env python3
"""
OCR 截图工具 — 基于百炼 qwen3.5-plus 视觉模型
用法：
  ./ocr.py screenshot.png                   # 识别图片内容
  ./ocr.py screenshot.png "只提取数字"       # 带提问
  ./ocr.py wechat.jpg "用JSON输出每笔交易"    # 指定输出格式
"""

import base64, json, sys, os

API_KEY = "sk-sp-8f4fefecd903402f89c80216d6c5a9c3"
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3.5-plus"

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def ocr(image_path, question="请详细描述这张图片中的所有文字和数字内容"):
    img_b64 = encode_image(image_path)
    
    import urllib.request
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/webp;base64,{img_b64}"}}
                ]
            }
        ],
        "max_tokens": 500,
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: ./ocr.py <图片路径> [提问]")
        sys.exit(1)
    
    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"文件不存在: {img_path}")
        sys.exit(1)
    
    question = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片中的所有文字和数字内容"
    
    result = ocr(img_path, question)
    print(result)
