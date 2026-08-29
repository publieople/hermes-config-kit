# Browser Library Pitfalls — OpenAny Phase 4 Root Cause Analysis

9 bugs found in browser testing. All code was "correct" at build time but failed at runtime.
This document captures WHY — so the next integration doesn't repeat them.

## 1. PDF: blob URL + Web Worker = silent failure

**Symptom:** "Failed to load PDF" for every file
**Initial wrong fix:** Changed CDN worker URL → `import.meta.url` bundling
**Real cause:** Web Workers (pdfjs-dist) cannot access blob URLs created in the main thread via `URL.createObjectURL()`. The worker's `fetch(blobUrl)` returns status 0.
**Correct fix:** Pass `{ data: new Uint8Array(buffer) }` — react-pdf transfers the data to the worker via `postMessage` structured clone, not URL fetch.

## 2. Audio: blob URL revoked too early

**Symptom:** Audio shows 0:00, can't play, metadata never loads
**Cause:** `useEffect(() => { return () => URL.revokeObjectURL(blobUrl); }, [blobUrl])` — cleanup runs before the `<audio>` element has fetched the blob and parsed metadata.
**Fix:** Don't revoke. Blob URLs are automatically garbage-collected when the page closes. For small files, memory cost is negligible.

## 3. CSV: editValue in useMemo deps = focus loss

**Symptom:** Every keystroke in CSV inline editor causes input to lose focus
**Cause:** `editValue` was in `columns` useMemo dependency array. Each keystroke → new value → columns rebuild → React unmounts old input → creates new input → focus lost.
**Fix:** Replace `useState(editValue)` with `useRef(editValueRef)`. The ref doesn't trigger re-renders. Remove `editValue` from useMemo deps.

## 4. Image: overflow-hidden conflicts with TUI Image Editor

**Symptom:** Scrollbar scrolls the whole page instead of just the editor area; zoom/hand tools unresponsive
**Cause:** `overflow-hidden` on the editor container div prevents TUI Image Editor from managing its own internal scroll context. TUI creates its own canvas layers inside the container.
**Fix:** Change `overflow-hidden` → `min-h-0` (flex child constraint). Let TUI handle overflow internally.

## 5. Keyboard: Ctrl+W / Ctrl+Tab are reserved by Chrome

**Symptom:** Ctrl+W closes the browser tab instead of the file tab; Ctrl+Tab switches browser tabs
**Cause:** Chrome intercepts these before the page JS receives the keydown event. `e.preventDefault()` has no effect — this is a browser-level security feature, not a JS bug.
**Fix:** Use Chrome-safe alternatives: `Ctrl+Shift+W` for close, `Alt+ArrowLeft/Right` for tab navigation.

## 6. Multi-file: chardet full-buffer analysis blocks main thread

**Symptom:** Dropping multiple files (or one large file) causes multi-second UI freeze
**Cause:** `chardet.analyse(new Uint8Array(buffer))` scans the entire buffer. 10 files × 1MB = 10MB synchronous analysis = main thread blocked.
**Fix:** Sample only the first 64KB: `new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 65536))`. Chardet accuracy is maintained with 64KB samples.

## 7. Archive: unzipSync blocks main thread on large ZIPs

**Symptom:** Opening a ZIP file causes a noticeable freeze before the file list appears
**Cause:** fflate's `unzipSync()` is synchronous and designed for Node.js. In the browser, it runs entirely on the main thread.
**Fix:** Use async `unzip(buffer, callback)` which supports multi-threading. Parse results in the callback.

## 8. SVG: single-line minified SVGs are uneditable

**Symptom:** Minified SVG (no line breaks, >100 chars) shows as one long line in CodeMirror
**Cause:** No formatting applied before loading into the editor. CodeMirror's XML mode doesn't auto-format.
**Fix:** Before loading into CodeMirror, apply simple regex formatting: `content.replace(/></g, '>\n<').replace(/></g, '>\n</')` for single-line SVGs.

## 9. Theme: hardcoded hex colors don't respond to dark: variant

**Symptom:** Theme toggle changes `html.dark` but handler components stay dark
**Cause:** Handlers used hardcoded colors like `bg-[#1e1e1e]`, `text-gray-400`. Tailwind's `dark:` variant can't override arbitrary values.
**Fix:** Use Tailwind v4 `@theme` design tokens in CSS:
```css
@theme { --color-surface: #1e1e1e; }
.dark { --color-surface: #f8fafc; }
```
Then use `bg-surface` in components — no per-component dark: logic needed.
