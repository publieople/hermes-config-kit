---
name: html-video-rendering
description: HTML-to-MP4 video rendering via HyperFrames (heygen-com/hyperframes). Write HTML+CSS+GSAP, render to deterministic MP4 with one CLI command. Covers setup, composition rules, WSL+China workarounds, and known pitfalls.
---

# HTML Video Rendering (HyperFrames)

Write HTML. Render video. Built for agents.

HyperFrames turns HTML + CSS + GSAP into deterministic frame-by-frame MP4 via Chrome headless + FFmpeg. No screen recording, no build step, no proprietary format.

## Quick Start

```bash
npx hyperframes init my-video --non-interactive --example blank
cd my-video
npm run dev        # browser preview (hot reload)
npm run render     # render to MP4
```

Prerequisites: **Node.js >= 22**, **FFmpeg**, **`which`** installed.

## Composition Rules

Every HyperFrames composition is a single `index.html`:

```html
<div id="root" data-composition-id="my-video" data-start="0" data-duration="10" data-width="1920" data-height="1080">
  <!-- Each timed element needs: -->
  <h1 id="title" class="clip"
      data-start="0" data-duration="5" data-track-index="0"
      style="font-size:72px; color:white; position:absolute; left:100px; top:100px;">
    Hello
  </h1>
</div>

<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });
  tl.from("#title", { opacity: 0, y: -30, duration: 0.6 }, 0);
  window.__timelines["my-video"] = tl;
</script>
```

**Hard rules:**
- Every timed element: `class="clip"` + `data-start` + `data-duration` + `data-track-index`
- Clips on the same track cannot overlap in time — use different `data-track-index` for simultaneous elements
- GSAP timeline must be **paused** and registered on `window.__timelines["composition-id"]`
- No `Date.now()`, `Math.random()`, or network fetches — only deterministic logic
- GSAP library must be bundled locally (CDN blocked in China)
- Use `font-family: sans-serif` or bundled web fonts — Segoe UI, Arial, Helvetica are unavailable in headless Linux Chrome
- `-webkit-background-clip: text` with `-webkit-text-fill-color: transparent` does NOT work in headless Chrome — use solid text colors

## Rendering

```bash
hyperframes render --output demo.mp4         # standard quality
hyperframes render --output demo.mp4 --quality high  # higher bitrate for text readability
hyperframes render --output demo.mp4 --workers 3     # limit workers (auto may crash on 16GB systems)
hyperframes render --format webm -o out.webm         # transparent WebM
```

**Quality matters:** Standard quality at 1920×1080 produces ~145 kbps which crushes text detail. Always use `--quality high` for videos with text content (~2700 kbps).

**Worker limit:** Auto-detects 16 cores and spawns 6 workers which can crash headless Chrome. Use `--workers 3` for reliable rendering.

## Snapshot (Debugging)

```bash
hyperframes snapshot --at 1.0,3.5 /path/to/project
```

Takes PNG screenshots at specified timestamps. Use to verify visual content without a full render. If snapshots show content but MP4 doesn't, the issue is bitrate/encoding — increase quality.

## CLI Reference

| Command | Purpose |
|---------|---------|
| `init` | Scaffold project |
| `preview` | Browser live preview (dev server, keep running) |
| `render` | Render to MP4/WebM |
| `lint` | Validate composition structure |
| `snapshot` | Capture PNG screenshots at timestamps |
| `doctor` | Check system dependencies |
| `browser ensure` | Download Chrome headless shell |

## Diagnostics & Common Fixes

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `root_missing_composition_id` lint error | Lint checks before parser sees attributes | Usually false positive — check compiled metadata confirms correct parsing |
| `beginFrame unavailable` | Chrome build mismatch or resource files missing | Ensure `icudtl.dat`, `locales/`, `v8_context_snapshot.bin` are in the cache dir |
| Video blank / text invisible | Low bitrate or headless incompatibility | Use `--quality high`, solid text colors, local fonts |
| CDN script timeout | GFW blocks jsdelivr/CDNs | Bundle GSAP (and other libs) locally in project |
| Chrome download stuck | Proxy may corrupt Puppeteer's downloader | Use `curl -L` with same proxy to download manually, unzip to cache dir |
| `which` not found | Arch Linux doesn't ship it | `sudo pacman -S which` |

## WSL + China Setup

See [`references/hyperframes-setup.md`](references/hyperframes-setup.md) for the complete WSL setup guide, Chrome headless manual install, proxy config, and first-render walkthrough.
