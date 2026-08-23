# Browser App Common Pitfalls

Condensed from root cause analysis of 9 bugs in a React PWA with 11 file handlers. Each entry: symptom → root cause classification → fix → prevention rule.

---

## 1. PDF Worker Loading (CDN version mismatch)

**Symptom:** All PDFs show "Failed to load PDF"

**Root cause:** My error — CDN URL construct `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs` assumes CDN mirrors exact npm version. CDN lags behind; version mismatch → 404.

**Fix:** Bundle worker from node_modules via Vite:
```ts
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();
```

**Rule:** Prefer `import.meta.url` + bundler over external CDN for critical runtime dependencies. CDNs are for optional assets, not worker threads.

---

## 2. Blob URL Premature Revocation

**Symptom:** Audio shows 0:00, cannot play. Video may also fail.

**Root cause:** My error — `useEffect(() => { return () => URL.revokeObjectURL(blobUrl); }, [blobUrl])` revokes the URL in component cleanup. Browser media elements load asynchronously; the URL is dead before metadata loads.

**Fix:** Don't revoke blob URLs actively. Browsers auto-reclaim on tab close. Memory cost of an unreclaimed blob URL is negligible for individual files.

**Rule:** Never call `URL.revokeObjectURL()` on blob URLs used by `<audio>`, `<video>`, `<img>`, or any async-loading element. Only revoke for `<a download>` click handlers.

---

## 3. State in useMemo Dependencies (editing focus loss)

**Symptom:** Input loses focus on every keystroke while editing inline.

**Root cause:** My architecture error — `editValue` state was in `useMemo` dependency array. Every keystroke → setState → memo re-computes → columns rebuilt → React destroys old input → creates new one → focus lost.

**Fix:** Replace `useState` for editing value with `useRef`:
```ts
const editValueRef = useRef('');

// Entering edit mode:
editValueRef.current = cellValue;

// In input:
<input defaultValue={editValueRef.current} onChange={e => { editValueRef.current = e.target.value; }} />

// On commit:
const newValue = editValueRef.current;
```

And REMOVE the edit state from useMemo deps.

**Rule:** High-frequency state (keystrokes, mouse moves, scroll position) that causes expensive re-computation must use refs, not state, when the value doesn't need to trigger re-render independently.

---

## 4. Hardcoded CSS Colors Break Theme Toggle

**Symptom:** Toggling dark/light theme has no effect on handler components.

**Root cause:** My architecture error — all handler components use hardcoded arbitrary values like `bg-[#1e1e1e]`, `text-gray-400`. Tailwind `dark:` variant cannot override arbitrary values; it only works with semantic utilities.

**Fix:** Replace hardcoded colors with CSS custom properties or Tailwind semantic colors:
```css
/* In global CSS */
:root { --bg-panel: #fff; --text-secondary: #6b7280; }
.dark { --bg-panel: #1e1e1e; --text-secondary: #9ca3af; }
```
```tsx
className="bg-[var(--bg-panel)] text-[var(--text-secondary)]"
```

**Rule:** If a component needs to support theme switching, use ONE of: (a) Tailwind semantic utilities + `dark:` variant, (b) CSS custom properties with `.dark` override, (c) `useThemeStore()` state in className. Never use hardcoded `bg-[#xxx]` for theming-dependent colors.

---

## 5. Browser-Reserved Keyboard Shortcuts

**Symptom:** `Ctrl+W` closes browser tab instead of file tab. `Ctrl+Tab` switches browser tab.

**Root cause:** Browser limitation — Chrome/Edge intercept `Ctrl+W` and `Ctrl+Tab` at the OS level before JS can `preventDefault()`. These are non-overridable.

**Fix:** Use alternatives that ARE preventable:
- Close tab: `Ctrl+Shift+W` (or `Ctrl+Q`)
- Next/prev tab: `Alt+ArrowRight` / `Alt+ArrowLeft`

**Rule:** Before assigning keyboard shortcuts, check Chrome's [keyboard shortcuts list](https://support.google.com/chrome/answer/157179). `Ctrl+W`, `Ctrl+T`, `Ctrl+N`, `Ctrl+Tab`, `Ctrl+Shift+N` are permanently reserved and cannot be intercepted.

---

## 6. Encoding Detection on Full Buffer (UI freeze)

**Symptom:** Opening multiple files causes multi-second UI freeze.

**Root cause:** My error — `chardet.analyse(uint8)` analyzes entire buffer synchronously. 10 files × 1MB each = 10MB of synchronous frequency analysis = main thread blocked.

**Fix:** Sample only first 64KB:
```ts
const sampleSize = Math.min(buffer.byteLength, 65536);
const uint8 = new Uint8Array(buffer, 0, sampleSize);
const results = chardet.analyse(uint8);
```

**Rule:** chardet (and similar statistical detectors) only need a representative sample. 64KB is the sweet spot. Never pass the full buffer to encoding detection.

---

## 7. Synchronous API in Browser (archive extraction)

**Symptom:** Opening a ZIP file freezes the UI for seconds.

**Root cause:** My error — used `fflate.unzipSync()` which is synchronous and blocks the main thread. Designed for Node.js.

**Fix:** Use async API:
```ts
import { unzip } from 'fflate';

unzip(uint8Data, (err, files) => {
  if (err) { /* handle */ }
  // files is Record<string, Uint8Array>
});
```

**Rule:** Always check if a library has both sync and async variants. In browser contexts, NEVER use the sync variant for I/O-bound operations (compression, parsing, encoding). The async variant often uses Web Workers internally.

---

## 8. Component Type in Tests (React 19 + vitest + jsdom)

**Symptom:** `render()` from @testing-library/react throws `TypeError: React.act is not a function`.

**Root cause:** React 19 CJS build doesn't export `act`. @testing-library/react v16 needs `act` from `react-dom/test-utils`, which in CJS imports from `react` — which lacks it.

**Workaround:** Test JSX element structure directly without `render()`:
```ts
const el = handler.Viewer({ file: makeFile() });
expect(typeof el.type).toBe('function');
expect(el.props.children).toHaveLength(2);
```

**Rule:** In React 19 + vitest + jsdom environments, prefer testing component OUTPUT (JSX element structure) over DOM rendering. Use `render()` only when you need actual DOM interaction (click events, form submission). For structural tests, direct element inspection avoids the CJS/ESM act compatibility issue.

---

## 9. CSS Overflow Conflicts with Third-Party Editors

**Symptom:** Third-party editor's internal scrollbars cause parent page to scroll. Editor tools (zoom, hand) unresponsive.

**Root cause:** My CSS error — `overflow-hidden` on the editor container conflicts with the library's internal scroll management.

**Fix:** Use `min-h-0` instead of `overflow-hidden` for flex children hosting third-party editors:
```tsx
<div ref={containerRef} className="flex-1 min-h-0" />
```

**Rule:** When embedding a third-party editor that manages its own scrolling (CodeMirror, TUI Image Editor, Monaco), the parent flex container should use `min-h-0` to allow the child to shrink, but should NOT set `overflow-hidden` — let the editor control its own overflow.

---

## Prevention Checklist

Before implementing any new handler or integration:

- [ ] Async APIs for I/O (unzip, parse, detect) — never sync in browser
- [ ] Encoding detection: sample first 64KB max
- [ ] Blob URLs: never `revokeObjectURL` for media elements
- [ ] Keyboard shortcuts: check against browser reserved list
- [ ] Theme colors: CSS custom properties or Tailwind semantic, never hardcoded hex
- [ ] State in memo deps: high-frequency values use refs
- [ ] CDN dependencies: bundle via bundler, never rely on external CDN version matching
- [ ] Third-party editor containers: `min-h-0`, no `overflow-hidden`
