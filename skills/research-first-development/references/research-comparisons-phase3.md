# Research Comparisons — open-any Phase 3

## Encoding Detection

| Candidate | Size | Browser | TS Types | Dependents | Verdict |
|-----------|------|---------|----------|------------|---------|
| `chardet` (2.2.0) | 22KB | ✅ Uint8Array | ✅ built-in | 1,477 | **WINNER** |
| `jschardet` (3.1.4) | larger | ✅ | .d.ts only | fewer | Good but heavier |

**Winner: chardet** — pure TS, smaller, more dependents, GB18030 explicitly supported (superset of GB2312/GBK).

## Compression / Archive

| Candidate | Size | Browser | ZIP | GZIP | TAR | Verdict |
|-----------|------|---------|-----|------|-----|---------|
| `fflate` (0.8.3) | 30KB | ✅ | ✅ unzipSync | ✅ gunzipSync | ❌ | **WINNER** |
| `JSZip` (3.x) | larger | ✅ | ✅ | ❌ | ❌ | Slower, bigger |
| `pako` (2.x) | medium | ✅ | ❌ | ✅ | ❌ | No ZIP support |
| `libarchive.js` | huge | ✅ | ✅ | ✅ | ✅ | Too heavy for PWA |

**Winner: fflate** — fastest pure-JS compression, ZIP+GZIP, 30KB. TAR support deferred.

## PDF Viewing

| Candidate | Size | Browser | Features | Verdict |
|-----------|------|---------|----------|---------|
| `react-pdf` (10.x) | ~50KB + 1MB CDN worker | ✅ | pages, zoom, text layer, annotations | **WINNER** |
| native `<iframe>` | 0KB | ✅ | bare rendering, no controls | Too minimal |
| `@react-pdf-viewer/core` | heavier | ✅ | more features | Too heavy |
| Nutrient (commercial) | — | ✅ | full editor | Not open-source |

**Winner: react-pdf** — React-native API, worker offloaded to CDN to avoid bundle bloat.

## Audio/Video

| Candidate | Size | Browser | Verdict |
|-----------|------|---------|---------|
| Native `<audio>` / `<video>` | 0KB | ✅ | **WINNER** |
| `video.js` | ~16KB | ✅ | Unnecessary for basic playback |

**Winner: Native HTML5** — zero dependencies, supports all common formats.

## Keyboard Shortcuts

| Candidate | Size | Weekly Downloads | API | Verdict |
|-----------|------|-----------------|-----|---------|
| `react-hotkeys-hook` (5.x) | <3KB | 2.5M | `useHotkeys('ctrl+s', fn)` | **WINNER** |
| `hotkeys-js` | ~8KB | less | imperative API | Good but heavier |

**Winner: react-hotkeys-hook** — smallest, most downloads, declarative hook API.

## i18n

| Candidate | Size | Browser | React Hooks | Verdict |
|-----------|------|---------|-------------|---------|
| `react-i18next` (17.x) | ~5KB gzip | ✅ | `useTranslation()` | **WINNER** |
| `@nanostores/i18n` | smaller | ✅ | different paradigm | Weaker ecosystem |
| `next-intl` | — | Next.js only | — | Doesn't apply (Vite project) |

**Winner: react-i18next** — ecosystem standard, hooks-native, namespaces, interpolation.

## Theme Toggle

| Candidate | Size | Verdict |
|-----------|------|---------|
| Tailwind v4 `@custom-variant dark` + Zustand | 0KB | **WINNER** |
| `next-themes` | ~2KB | Next.js only |
| CSS custom properties | 0KB | Works but more boilerplate |

**Winner: Tailwind v4 native** — already in project, zero extra deps.
