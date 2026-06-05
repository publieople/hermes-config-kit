---
name: bilibili-video-summary
description: Summarize Bilibili (B站) videos using opencli bilibili subtitle + summary + video commands. Extracts subtitles, official AI summary, and video metadata, then synthesizes into structured summaries, blog posts, or threads.
trigger: B站视频|bilibili视频|b23.tv|BV[a-zA-Z0-9]+|总结.*视频|视频.*总结|这个视频.*看看|bilibili.*总结|B站.*总结
version: 1.1.0
tags: [bilibili, video, summary, opencli, subtitle, transcript]
---

# Bilibili Video Summary

Summarize any B站 video by extracting subtitles, official AI summary, and metadata via `opencli bilibili`.

## Prerequisites

- **opencli** installed: `npm install -g @jackwener/opencli`
- If install fails with EACCES: `npm config set prefix ~/.npm-global && npm install -g @jackwener/opencli`
- **Chrome** running with B站 logged in
- **opencli Browser Bridge** Chrome extension installed

## Workflow

### 1. Resolve short link → BV号

If user shares a `b23.tv` short link, resolve it first:

```bash
curl -sI "https://b23.tv/XXXXX" | grep -i location | grep -oP 'BV[a-zA-Z0-9]+'
```

For direct `bilibili.com/video/BV...` links, extract the BV号 directly.

### 2. Parallel fetch — all three data sources at once

These three commands are independent and SHOULD be run in parallel (3 simultaneous terminal calls):

```bash
# Video metadata (title, author, duration, stats)
opencli bilibili video <bvid> -f json

# Official B站 AI summary (chapter outline + timestamps)
opencli bilibili summary <bvid> -f json

# CC subtitles (full transcript)
opencli bilibili subtitle <bvid> -f json
```

Running them in parallel saves 2 round-trips compared to sequential execution.

### 3. Synthesize

Priority order for synthesis:
1. **`summary`** → Use as the structural skeleton. It provides chapter-level outlines with timestamps — the highest-quality, most condensed source.
2. **`subtitle`** → Fill in details, key quotes, specific data points, and "金句" (memorable one-liners).
3. **`video`** → Header metadata: title, author, date, views/likes/favorites stats.

## Output Format (Chinese)

```markdown
## 📺 标题 — UP主

**BV号** | 时长 | 发布日期 | 播放量 · 点赞数 · 收藏数

---

### 🔑 核心观点（一句话提炼）

### 分段内容（按 summary 时间戳结构化展开，subtitle 补充细节）

### 💡 金句（从 subtitle 提取的 memorable quotes）

---

总结：（一句话收尾）
```

For long videos (20min+ with 600+ subtitle entries), synthesize by chapter rather than line-by-line.

## Fallback Paths

If `subtitle` returns nothing (no CC subtitles):

1. Use `summary` alone — the AI summary is often sufficient for an overview
2. Use `video` metadata (description + tags) for a lighter summary
3. Report to user that the video lacks captions

## Command Reference

| Command | What it gets |
|---------|-------------|
| `opencli bilibili video <bvid> -f json` | Title, author, duration, stats, description |
| `opencli bilibili summary <bvid>` | Official AI summary with chapter outline + timestamps |
| `opencli bilibili subtitle <bvid>` | CC subtitles (manual or auto-generated) |

All commands require Chrome running with B站 login.

## Pitfalls

- **No subtitles**: Many B站 videos lack CC subtitles. Fall back to `summary` + `video` metadata.
- **Browser not running**: opencli needs Chrome with the Browser Bridge extension. Error message will indicate connection failure.
- **Not logged in**: Some content (大会员, age-restricted) requires B站 login in Chrome.
- **Summary unavailable**: B站 AI summary is not available for all videos — it's a relatively new feature.
- **Rate limiting**: Avoid rapid-fire calls. Space commands a few seconds apart.
- **npm prefix**: If `npm install -g` fails with EACCES, run `npm config set prefix ~/.npm-global` first. The global prefix may drift to `/usr/lib` after system npm updates.

## References

- `references/opencli-bilibili-commands.md` — Full `opencli bilibili -h` output snapshot
