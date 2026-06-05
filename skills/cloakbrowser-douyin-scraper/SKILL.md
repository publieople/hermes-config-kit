---
name: cloakbrowser-douyin-scraper
description: 使用 CloakBrowser 绕过抖音反爬，获取真实视频 MP4 下载链接
version: 1.0.0
author: Hermes Agent
license: MIT
---

# CloakBrowser 抖音视频获取

## 环境

```bash
source ~/venvs/cloak/bin/activate  # Python venv, cloakbrowser 0.3.28
```

CloakBrowser 是一个 C++ 源码级修改指纹的 Chromium，reCAPTCHA v3 得分 0.9，可过 Cloudflare Turnstile。

## 核心流程

### 1. 启动浏览器 + 拦截 API

```python
from cloakbrowser import launch
browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({"width": 1920, "height": 1080})

all_videos = []

def handle_response(response):
    url = response.url
    if '/aweme/v2/web/module/feed/' in url:
        body = response.text()
        data = json.loads(body)
        for item in data.get('aweme_list', []):
            video = item.get('video', {})
            play_addr = video.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            mp4_url = [u for u in url_list if '.mp4' in u]
            if mp4_url:
                all_videos.append({
                    'desc': item.get('desc', '')[:100],
                    'author': item.get('author', {}).get('nickname', ''),
                    'mp4_url': mp4_url[0],
                    'cover': video.get('cover', {}).get('url_list', [''])[0],
                    'duration': item.get('duration', 0),
                    'digg_count': item.get('statistics', {}).get('digg_count', 0),
                })

page.on("response", handle_response)
```

### 2. 加载页面触发 API 调用

```python
page.goto("https://www.douyin.com/", timeout=30000, wait_until="domcontentloaded")
time.sleep(5)
# 滚动加载更多
for i in range(3):
    page.evaluate(f"window.scrollTo(0, {i * 800})")
    time.sleep(3)
```

### 3. 下载视频

```python
req = urllib.request.Request(mp4_url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.douyin.com/',
})
with urllib.request.urlopen(req, timeout=30) as resp:
    with open(output_path, 'wb') as f:
        f.write(resp.read())
```

## 关键 API 端点

| 端点 | 用途 |
|------|------|
| `/aweme/v2/web/module/feed/` | 推荐 Feed（count=20, 滚动翻页） |
| `/aweme/v1/web/aweme/detail/` | 单视频详情（参数: aweme_id） |
| `/aweme/v1/web/hot/search/list/` | 热搜榜单 |

## 实际抓取结果

### 推荐 Feed 的特点
- Feed API 端点: `/aweme/v2/web/module/feed/` (参数 `module_id=3003101`)
- 单次会话可抓取约 **85-100 条** 不同视频（约 15 次滚动后趋于饱和）
- **视频时长**: 1-15 分钟（不是 15-60 秒的短内容），多数为 5-15 分钟
- **内容类型**: 以娱乐内容为主（游戏、影视解说、美食、体育、音乐、搞笑），科技/知识类占比很低（<3%）
- 首页推荐流没有"科技区"或"教育区"的 filter，内容取决于推荐算法
- 搜索页面（`/search/{keyword}`）在 CloakBrowser 中会触发 **EPIPE 崩溃**（Node.js write EPIPE，原因可能是 WebSocket/SSE 连接被切断）

### 搜索 API 的局限性
Douyin 搜索 API (`/aweme/v1/web/general/search/single/`) 受到严格的 X-Bogus/A-Bogus 签名保护：

- 即使用有效的登录 cookies（`sessionid`、`sid_guard`、`passport_csrf_token`），未签名的请求也会返回 `verify_check` 验证码
- douyin-downloader 工具的 `--search` 功能同样受此限制（内部有签名逻辑但仍可能失败）
- **唯一可靠的方式是首页推荐流抓取**，因为 feed API 无需额外签名

### 下载注意事项
- **立即下载**: 视频 URL 包含 `x-expires` 参数，有时效性（通常几分钟到几小时）
- **文件大小**: 典型视频 40-400MB，大文件（>100MB）GitHub 无法接受
- **Referer Headers**: 下载时必须带 `Referer: https://www.douyin.com/`
- **Proxy 冲突**: 在 WSL 环境下 `no_proxy='*'` 会阻止 CloakBrowser 访问网络，删除 proxy 环境变量即可

- 视频 URL 有时效性签名（URL 中的 `x-expires` 参数），需即时下载
- 下载时需带 Referer 头 `https://www.douyin.com/`
- 首次启动 CloakBrowser 会自动下载 ~200MB Chromium 二进制到 `~/.cache/cloakbrowser/`
- 视频可能很大（10-100MB+），建议转码压缩后再用于 demo
