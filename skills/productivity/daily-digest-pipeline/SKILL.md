---
name: daily-digest-pipeline
description: "Daily content aggregation + video production pipeline. Collect tech news from Chinese curated sources (Readhub, 少数派) and open-source projects from GitHub Trending → format into a structured daily digest → optionally produce a web-video-presentation for Bilibili/YouTube. Semi-automated: cron handles morning collection, user reviews during the day, agent builds the video in the evening."
tags: [daily, content, aggregation, video, newsletter, trending]
---

# Daily Digest Pipeline

Daily tech news + open-source project aggregation → video production pipeline. Two-phase semi-automated workflow.

## Overview

```
08:00 ── cron: data collection ──→ user receives digest draft
白天   ── user reviews, edits   ──→ agent ready with finalized content
傍晚   ── agent: build video    ──→ web presentation ready for recording
```

## Phase 1: Morning Data Collection (Cron Job)

### Toolsets needed: `web`, `terminal`, `file`

### Schedule
- **Run at**: UTC `0 0 * * *` = China 08:00
- **Deliver to**: the Feishu/Telegram/Discord home channel so user sees it when they wake up

### Data Sources

**IMPORTANT — User preference: curated Chinese sources only.** Hacker News / English-language sources produce content that the user finds irrelevant or low-quality. Always prioritize Chinese curated sources.

**Source mix requirement**: The user wants both hard tech news (AI/semiconductor/infrastructure) AND consumer tech (phone/headphone/consumer electronics). Readhub covers the former, 少数派派早报 covers the latter. Both are mandatory — the user personally reads 少数派 and explicitly requested it be included ("少数派那种消费科技的早报也可以做进科技新闻里, 主要是我也经常要看").

1. **Readhub 每日早报** (readhub.cn/daily) — Primary source. Extract via `web_extract(urls=['https://readhub.cn/daily'])`. Covers AI, semiconductor, internet, and tech-business news. Content is typically fresh by 08:00 CST. The page returns clean LLM-summarized text — one of the easiest sources to extract.

2. **少数派 派早报** (sspai.com) — **RSS approach** (preferred). Use `terminal` with curl + Python:
   ```bash
   curl -s "https://sspai.com/feed" | python3 -c "
   import xml.etree.ElementTree as ET, sys
   tree = ET.parse(sys.stdin)
   for item in tree.findall('.//item'):
       title = item.findtext('title', '')
       link = item.findtext('link', '')
       pubDate = item.findtext('pubDate', '')
       author = item.findtext('author', '')
       if '派早报' in title:
           print(f'{pubDate}|{title}|{link}|{author}')
   "
   ```
   RSS feed URL: `https://sspai.com/feed` (HTTP 200, standard RSS 2.0). Focus on items with "派早报" in title — these are the editor-curated daily briefings. The 派早报 covers consumer tech (phones, audio, apps, services) which the user explicitly wants included alongside hard tech news. Fallback: `web_extract` on the sspai.com homepage.

3. **GitHub Trending** (past 24h) — Use `web_extract(urls=['https://github.com/trending'])`. Returns well-structured data with repo name, description, language, stars, and stars-today count. Supports up to 25 repos per page.

4. **极客早知道** (geekpark.net/column/74) — Supplementary. Extract via `web_extract`. **极客公园 has no public RSS feed** — attempts on http://www.geekpark.net/rss and /feed all failed (HTTP 000 or timeout). Use web_extract on their column page instead. Content is editor-curated daily headlines with a business/tech-angle slant.

5. **36kr RSS 不作为日常源**: `https://36kr.com/feed` returns full article HTML with images, too verbose for daily digest. Reserve for deep-dive reference only.

#### Fallback Chain
1. Readhub → 少数派 RSS → 极客早知道 → GitHub Trending
2. If Readhub unavailable: `web_search("今日科技新闻 2026")` in Chinese
3. **Avoid**: Hacker News (rejected by user), English-language sources

#### ⚠️ DO NOT use Hacker News
Past attempts showed HN top stories produce irrelevant content (politics, culture, general-interest) that the user explicitly rejected. Skip this source entirely.

### Output Format

Save to `~/projects/daily-tech/YYYY-MM-DD.md`:

```markdown
# 🗞️ 每日科技速报 · YYYY-MM-DD

> 今日收录 {N} 条科技新闻 + {M} 个开源项目

---

## 🔥 科技头条

### 1. [标题](链接)
**一句话**：...
**详情**：2-3 句
**来源**：...

### 2. ...

---

## ⭐ GitHub 热门项目

### 1. [项目名](链接) ⭐ N stars
**一句话**：...
**亮点**：...
**语言**：...

### 2. ...

---

## 💡 小发现
- ...
```

### Content Guidelines
- **3~5 news + 3~5 projects max** (total ≤ 10). Curate, don't dump.
- **Content quality is the #1 priority** — the user has a high bar. Every item must be genuinely interesting/valuable to a developer audience. Items that are "not even worth reading" (user's own assessment) should be cut without hesitation. Quality over quantity.
- **Prefer curated Chinese sources** (Readhub, 少数派) over unfiltered feeds. These sources have already done a curation pass — trust their editorial judgment.
- **Prefer practical/interesting OSS** over star-farming wrapper repos.
- **Human-readable summaries**, not machine translation. One-liner + 2-3 sentence detail per item.
- **Theme**: tech & developer focused. Skip general-interest items (politics, culture, non-tech business news) unless they have direct tech implications.
- **Style reference**: 少数派早报's editorial judgment + IT咖啡馆's GitHub summary format — concise, informative, personable.

## Phase 2: User Review (Daytime)

User reads the digest, makes edits to the `.md` file, and tells the agent:
- Any items to remove or add
- Tone/style adjustments
- Whether to proceed with video production

## Phase 3: Evening Video Production

**两个可选管线：**

- `web-video-presentation`（默认）— Vite + React 页面，用户用 OBS 录屏
- `HyperFrames` — 一行命令直接出 MP4，适合固定结构每日产出

### 管线选择

| 场景 | 推荐 |
|------|------|
| 结构固定、每日重复的视频 | HyperFrames（无需录屏，帧精确） |
| 需要丰富交互/动画定制 | web-video-presentation |
| 快速 demo / 概念验证 | HyperFrames |
| 需要配口播字幕/多轨道 | web-video-presentation |

选 HyperFrames 时，参考 `skill_view(name='daily-digest-pipeline', file_path='references/hyperframes-workflow.md')` 获取完整工作流。

### ⚠️ HyperFrames 内容 + 图片规范（关键）

用户对质量有明确要求，违反会导致返工：

1. **每条新闻必须调研核实**：不要凭印象写内容。搜索 → 访问至少 2 个独立来源 → 提取具体数字 → 标注来源。参考 `references/hyperframes-workflow.md` 的"内容调研"章节。
2. **图片必须真实**：不接受 SVG 示意图。从新闻页面 `browser_get_images` 发现图片 URL → `curl` 下载 → `file` 验证是否为真实 JPEG/PNG。参考工作流中的"图片素材获取"章节。
3. **样式必须丰富**：背景网格 + 顶部光条 + 分类标签色 + 卡片圆角 + 底部进度导航。纯文字卡片会被判定为"简陋"。

### Toolsets needed: `terminal`, `file`, `web` (and the `web-video-presentation` skill must be installed)

### Prerequisites
- `web-video-presentation` skill from ConardLi/garden-skills
- Node.js + npm (for the Vite + React scaffold)
- Optional: MiniMax CLI (`mmx`) for TTS audio synthesis

### Chapter Structure for Daily News Video

Default chapter breakdown for a ~4.5 min / 6 chapter / 19 step video:

```
Ch 1: hook        (2 steps, ~25s)   — 开场报头 + 三句预告
Ch 2: openai/topic (2-3 steps, ~45s) — 头条新闻深度
Ch 3: ai-race     (3-4 steps, ~60s) — AI 竞赛（Anthropic/Qwen/…）
Ch 4: big-money   (3-4 steps, ~50s) — 大厂动态/数字故事
Ch 5: github      (5 steps, ~75s)   — GitHub 项目 5 连
Ch 6: outro       (2 steps, ~20s)   — CTA + 明日预告
```

Follow `CHAPTER-CRAFT.md` for visual design. First chapter is forced anchor (must be built on main thread with full quality before proceeding).

### Dev Server Troubleshooting

**WSL background server issue**: In this WSL+Arch environment, background processes (`terminal(background=true)` or `process`) consistently report "running" but produce zero stdout and never bind to ports for both `vite` and `python3 -m http.server`.

**Working workaround** — use `execute_code` + `timeout`:
```python
from hermes_tools import terminal
# Runs in foreground with long timeout
terminal("cd dist && timeout 300 python3 -u -m http.server 5173", timeout=10)
```
The server stays alive for 300s and responds to browser requests.

**Fallback**: Ask user to manually run `npm run dev` in their terminal — works normally.

### Pipeline Steps

1. **Load the skill**: `skill_view(name='web-video-presentation')`
2. **Create project directory**: `mkdir -p ~/projects/daily-tech-video/YYYY-MM-DD && cd $_`
3. **Copy the daily digest** as `article.md`
4. **Phase 1 — Content**: Generate `script.md` (口播稿) + `outline.md` (development plan) using SCRIPT-STYLE.md and OUTLINE-FORMAT.md from the skill's references
5. **Skip Checkpoint Plan** (if user already approved content during daytime review) — log the theme decision
6. **Phase 2 — Scaffold**: Run `scaffold.sh` with chosen theme (recommended: `newsroom` for news vibe, `midnight-press` for dev aesthetic)
7. **Phase 2 — Chapters**: Implement each chapter following CHAPTER-CRAFT.md. For a typical daily digest:
   - Ch 1: Introduction / headline news
   - Ch 2: Tech news deep-dive
   - Ch 3-4: Open source projects showcase
   - Ch 5: Wrap-up / what to watch
8. **Checkpoint Audio**: Offer the user audio synthesis (optional)
9. **Phase 3 — Audio**: If approved, run `extract-narrations` + `synthesize-audio` pipelines
10. **Deliver**: Provide the dev server URL (`localhost:5173`) so the user can screen-record with OBS

### Theme Recommendations for Tech News

| Theme | Vibe | Best For |
|-------|------|----------|
| **newsroom** 🏆 | Newspaper cream + red serif heads | Most natural for news reporting |
| **midnight-press** | Dark warm + orange accent | Film noir, dev aesthetic |
| **terminal-green** | Black + green phosphor | Hardcore tech/CLI demos |
| **blueprint** | Navy + cyan + engineering lines | System architecture deep-dives |
| **chalk-garden** | Dark slate + chalk yellow | Classroom tutorial style |

## Pitfalls

- **Readhub unavailable**: If readhub.cn/daily fails to load or returns no content, fall back to `web_search("今日科技新闻 2026")` in Chinese. Avoid falling back to English-language sources.
- **GitHub API rate limiting**: Unauthenticated requests are capped at 60/hr. The cron runs once daily so it's usually fine. Prefer `web_extract` on `https://github.com/trending` over the API — it's more reliable.
- **Weekend/weekday variation**: GitHub sees fewer repos on weekends. The cron can widen the search window to 3-7 days on Saturdays.
- **极客公园无 RSS**: Attempts on http://www.geekpark.net/rss and /feed all failed. Use `web_extract` on their column page instead.
- **36kr RSS 可用但内容太长**：`https://36kr.com/feed` 有 RSS 但返回完整文章 HTML，不适合每日速报的简洁格式。仅在需要额外深度内容时使用。
- **web-video-presentation is heavy**: The full pipeline generates a complete Vite project with per-chapter TSX/CSS. Budget ~30 min for first-time setup on a new theme, ~10-15 min for subsequent days.
- **Scaffold path**: Use absolute path to scaffold.sh: `bash ~/.hermes/skills/openclaw-imports/garden-skills/skills/web-video-presentation/scripts/scaffold.sh`
- **First-run overhead**: The scaffold installs npm deps — expect a ~30s delay on first build per theme.
- **Content drift**: Over time, the cron job may drift toward stale sources if Readhub changes its URL structure or format. Verify the output file is non-trivial after each cron run.
- **Dev server in WSL**: Background process tool doesn't capture server stdout or bind ports reliably. Use `execute_code` + `timeout 300 python3 -u -m http.server` workaround or ask user to run `npm run dev` manually.
- **Cron job ID**: `85e3114a8294` — the active data-collection cron job. View with `cronjob(action='list')`. Runs daily at UTC 0:00 (China 08:00).
