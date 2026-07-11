---
name: wikimedia-image-fetch
description: 从 Wikimedia Commons 抓取自由许可的真实图片素材(产品/物品/场景)。用于 U 盘素材准备、文档配图等需要真实照片但无 API key 的场景。
---

# Wikimedia Commons 图片抓取

> 无需 API key,无需登录,所有图片 CC 自由许可可直接商用。
> 适用:考试素材、产品图配图、博客配图等需要"真实图片"而非占位的场景。

## 何时用 vs 不用

**用**:需要真实物体照片、品牌原型、场景图,且没有 API key。
**不用**:需要矢量图 / 矢量 logo(用 Wikimedia 后缀会搜到 SVG 但渲染要 librsvg);或需要 Unsplash 风格的高质量摄影(用 source.unsplash.com 需 key)。

## 核心 API

### 1. 搜索 File 命名空间(图片搜图)

```python
import requests
PROXY = "http://127.0.0.1:7890"  # WSL 下走 Clash 代理
HEADERS = {"User-Agent": "HermesBot/1.0 (your@email.com)"}  # 真实 UA,默认 python-requests 会被拦

r = requests.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "query",
        "list": "search",
        "srnamespace": 6,  # File: 命名空间
        "srsearch": "your keywords",
        "srlimit": 15,
        "format": "json",
    },
    headers=HEADERS,
    proxies={"http": PROXY, "https": PROXY},
    timeout=15,
)
hits = r.json()["query"]["search"]  # [{"title": "File:XXX.jpg", ...}, ...]
```

### 2. 拿图片直链

```python
r = requests.get(
    "https://commons.wikimedia.org/w/api.php",
    params={
        "action": "query",
        "titles": "File:XXX.jpg",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 800,  # 缩略图宽度,无则原图
        "format": "json",
    },
    headers=HEADERS, proxies={"http": PROXY, "https": PROXY}, timeout=15,
)
url = r.json()["query"]["pages"][page_id]["imageinfo"][0]["thumburl"]
```

## ⚠️ 三个真实坑

### 坑 1: 搜结果包含 PDF/视频

`srsearch` 跨所有 File 类型,PDF/.svg/.webm/.ogv 都会出来。**必须过滤**:

```python
SKIP_EXT = (".pdf", ".svg", ".webm", ".ogv")
for h in hits:
    title = h["title"]
    if any(title.lower().endswith(ext) for ext in SKIP_EXT):
        continue
    return title  # 第一张可用
```

否则会下到 PDF 封面而不是产品图(实测:`bedside lamp` 搜到 `The Spirit lamp (serial) (IA spiritlampserial00doug).pdf`)。

### 坑 2: summary API 返回错的缩略图

`/api/rest_v1/page/summary/<title>` 返回的 `thumbnail.source` 经常不准确(Apple Watch Ultra 2 搜到 Series 3 图)。**直接用 search + imageinfo 两步法**别图省事用 summary。

### 坑 3: 429 Too Many Requests

`upload.wikimedia.org` 限流。实测 sleep 60s 后恢复正常。代码里用 `time.sleep(60)` 重试一次即可。

## 完整可运行模板

见 `scripts/fetch_wikimedia_images.py`。

## 关键词技巧

- **品牌 + 型号**:`"Sony WH-1000XM4"` 通常有图,但拼写要准
- **通用关键词**:`"modern lamp"` / `"side-by-side refrigerator"` 命中率高
- **避免词**:`"product image"`(太泛) / 纯品牌名(可能只搜到 logo SVG)

## 验证下载成功

```python
from PIL import Image
img = Image.open(local_path)
pixels = list(img.getdata())
assert len(set(pixels[:5000])) > 10, "可能是纯色占位"
```

unique pixel 数 < 10 = 纯色块,> 100 = 真图。

## 参考

- API 文档: https://www.mediawiki.org/wiki/API:Main_page
- Commons: https://commons.wikimedia.org/