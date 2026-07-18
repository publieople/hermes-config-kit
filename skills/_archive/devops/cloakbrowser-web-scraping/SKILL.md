---
name: cloakbrowser-web-scraping
description: Use CloakBrowser (anti-detection Chromium) to access protected Chinese web platforms (Douyin/抖音, etc.) and extract structured data — intercepting API responses, extracting video/media URLs, and downloading content from sites that block standard Playwright/browser automation.
tags:
  - devops
  - browser
  - cloakbrowser
  - scraping
  - douyin
  - anti-detection
  - api-interception
triggers:
  - User needs to download video content from Douyin/抖音 or similar Chinese short-video platforms
  - User needs to access a site protected by Cloudflare, reCAPTCHA, or bot detection (FingerprintJS, etc.)
  - Standard browser_navigate or Playwright fails on a target site (blocked by anti-bot)
  - User asks "能不能获取到抖音的..." or similar platform-specific content
  - Need to extract data from a site that requires login but CloakBrowser can access without auth
  - Any task where the source is a Chinese web platform with strong anti-bot protection
---

# CloakBrowser Web Scraping

## Overview

CloakBrowser is a C++-patched Chromium that passes bot detection (Cloudflare, reCAPTCHA v3 score 0.9, FingerprintJS). Use it to access Chinese web platforms that block standard Playwright/headless Chrome.

This skill covers the **full scraping workflow**: intercepting API calls from the page to extract structured data (video URLs, metadata, etc.) and downloading the content.

## Prerequisites

```bash
# CloakBrowser must be installed in a venv
source ~/venvs/cloak/bin/activate
python3 -c "from cloakbrowser import launch; print('OK')"
```

If not installed, see `playwright-browser-diagnostics` skill for installation steps.

## Workflow

### Step 1: Launch Browser with Network Interception

```python
from cloakbrowser import launch
import time, json

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({"width": 1920, "height": 1080})

# Set up response interception
captured_data = []

def handle_response(response):
    url = response.url
    # Filter for target API endpoints
    if 'target-endpoint' in url and 'avoid-blocks' in url:
        try:
            body = response.text()
            ct = response.headers.get('content-type', '')
            captured_data.append({
                'url': url[:250],
                'type': ct[:50],
                'size': len(body),
                'body': body
            })
        except:
            pass

page.on("response", handle_response)
```

**Key pattern for Douyin specifically:**

```python
# Douyin's feed API endpoints
def handle_response(response):
    url = response.url
    if '/aweme/v2/web/module/feed/' in url or '/aweme/v1/web/aweme/detail/' in url:
        try:
            body = response.text()
            data = json.loads(body)
            aweme_list = data.get('aweme_list', [])
            # ... extract video info
        except:
            pass
```

### Step 2: Navigate and Trigger API Calls

```python
page.goto("https://target-site.com", timeout=30000, wait_until="domcontentloaded")
time.sleep(3)  # Wait for JS to initialize and make API calls

# Scroll to trigger lazy-loaded content
for i in range(3):
    page.evaluate(f"window.scrollTo(0, {i * 800})")
    time.sleep(2)

# Or trigger specific interactions
# page.click('.some-button')
# page.evaluate('document.querySelector(".tab").click()')
```

### Step 3: Extract Video/Media URLs from Captured Data

**Douyin video extraction pattern:**

```python
def extract_video(item):
    """Extract video URL and metadata from a Douyin aweme item."""
    video = item.get('video', {})
    
    # Try play_addr first, then download_addr, then bit_rate
    play_addr = video.get('play_addr', {})
    url_list = play_addr.get('url_list', [])
    
    if not url_list:
        url_list = video.get('download_addr', {}).get('url_list', [])
    if not url_list:
        bit_rates = video.get('bit_rate', [])
        if bit_rates and len(bit_rates) > 0:
            url_list = bit_rates[0].get('play_addr', {}).get('url_list', [])
    
    author = item.get('author', {})
    return {
        'desc': item.get('desc', '')[:100],
        'author': author.get('nickname', 'unknown'),
        'mp4_url': url_list[0] if url_list else None,
        'cover': item.get('video', {}).get('cover', {}).get('url_list', [''])[0],
        'digg_count': item.get('statistics', {}).get('digg_count', 0),
    }
```

### Step 4: Download Videos

Douyin's MP4 URLs are **time-signed** (expire after a few hours). Download immediately:

```python
import urllib.request
import os

def download_video(video_info, output_path):
    url = video_info.get('mp4_url')
    if not url:
        return False
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.douyin.com/',  # REQUIRED for Douyin CDN
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        with open(output_path, 'wb') as f:
            f.write(data)
    return True
```

## Douyin-Specific Details

### Key API Endpoints (confirmed working)

| Endpoint | Data | Size | 
|----------|------|------|
| `/aweme/v2/web/module/feed/` | Feed video list (20 videos/call) | ~1.4-2.9MB |
| `/aweme/v1/web/aweme/detail/` | Single video detail | ~109KB |
| `/aweme/v1/web/hot/search/list/` | Hot search trending | ~67KB |

### Video URL Format

```
https://v26-web.douyinvod.com/{hash}/{timestamp}/video/tos/cn/tos-cn-ve-15/{video_id}/?a=6383&ch=26&...
```

**Important:** URLs are time-signed and expire. Download immediately after capture.

### Notes
- CloakBrowser passes Douyin's Cloudflare protection automatically
- No login required for feed access
- Videos average 12-113MB each at original quality
- For hackathon demos, consider compressing to 540p or shorter clips
- The `Referer: https://www.douyin.com/` header is REQUIRED for video CDN access
- Network proxy (http://127.0.0.1:7890) may be needed for the initial binary download, but CloakBrowser itself accesses Chinese sites without proxy

## Project Integration: Swapping Videos Into zyronon/douyin Clone

After scraping real Douyin videos, integrate them into the Vue-based Douyin clone for demo:

### Data Flow Architecture

```
CloakBrowser scrape → public/videos/dy_N.mp4 (local files)
                   → src/assets/data/ai_videos.json (structured metadata)
                   → src/mock/index.ts (import swap)
                   → axios-mock-adapter → browser renders feed
```

### Step-by-Step

1. **Scrape and download** (steps above):
   - Extract `aweme_list` from `/aweme/v2/web/module/feed/` API
   - Download MP4 URLs immediately (time-signed, expire in hours)

2. **Create `src/assets/data/ai_videos.json`** with project-compatible schema:
   ```json
   {
     "aweme_id": "ai_001",
     "desc": "AI/tech themed description #hashtag",
     "video": {
       "play_addr": {
         "url_list": ["/videos/dy_0.mp4"],
         "width": 1080, "height": 1920
       },
       "cover": {"url_list": [""], "width": 720, "height": 720},
       "poster": "",
       "duration": 556415  // in milliseconds, from ffprobe
     },
     "author": {
       "nickname": "Channel Name",
       "avatar_168x168": {"url_list": []},
       "avatar_300x300": {"url_list": []},
       "cover_url": [{"url_list": []}]
     },
     "statistics": {
       "digg_count": 128000,
       "comment_count": 23400,
       "share_count": 45600
     },
     "duration": 556415,
     "status": {"is_delete": false, "allow_share": true, "is_prohibited": false, ...},
     "text_extra": [],
     "is_top": 0,
     "share_info": {"share_url": "", "share_link_desc": ""}
   }
   ```
   - Required minimum fields for the renderer: `video.play_addr.url_list[]`, `duration`, `desc`
   - `author.nickname` and `statistics` shown in the UI overlay
   - Duration must be in **milliseconds** (feed player reads it from item.video.duration)

3. **Get accurate duration with ffprobe:**
   ```bash
   python3 -c "
   import json, subprocess
   r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
       '-of','json', 'public/videos/dy_0.mp4'], capture_output=True, text=True)
   dur = float(json.loads(r.stdout)['format']['duration']) * 1000
   print(int(dur))
   "
   ```

4. **Swap the import in `src/mock/index.ts`:**
   ```typescript
   // Change this line:
   import posts6 from '@/assets/data/posts6.json'
   // To:
   import posts6 from '@/assets/data/ai_videos.json'
   ```

5. **Handle file permission issues** (common after git reverts on WSL):
   ```bash
   # If files become root-owned (permission denied on write):
   rm src/mock/index.ts     # Works because directory is owned by user
   # Then create new one with your content
   ```

6. **Verify**: `pnpm dev`, open browser at localhost:3000, press F12 → Ctrl+Shift+M for mobile view

### Notes
- The original `posts6.json` contains 6 entries with real Douyin CDN URLs that may be expired
- The mock layer slices `allRecommendVideos` with `start` and `pageSize` params
- Videos can be long (1-15 min). For a tighter demo, consider compressing with ffmpeg or using only short scenes
- Descriptions and author names are freely editable — they only determine the UI overlay text
- Author avatars are optional (empty `url_list` gives no avatar, which is fine for demo)
- The `/videos/` path references files in `public/videos/`, which Vite copies verbatim to `dist/videos/`

## Pitfalls

- **Expiring URLs**: Don't store the video URLs for later — download immediately
- **Large files**: Original Douyin videos can be 100MB+. For demos, consider ffmpeg compression
- **No audio in headless**: By default headless mode captures video; audio requires headed mode or additional flags
- **Rate limiting**: Don't hammer the API — occasional scrolling is fine, but rapid-fire requests may trigger secondary checks
- **Page rendering**: Douyin uses heavy client-side rendering. Some content only loads after user interaction (scrolling, tab clicks). Scroll multiple times and wait between scrolls
- **CloakBrowser vs browser_navigate**: CloakBrowser is a separate binary from Hermes' built-in browser tool. Use it via Python, not via Hermes' browser tool
