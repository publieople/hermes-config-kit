---
name: openany-test
description: Run OpenAny unit tests + Playwright E2E tests — both handlers and browser rendering
trigger: 测试 open-any|openany test|run e2e|px test
---

# OpenAny Testing

## Pre-flight (before ANY work on this project)

1. **UI changes**: load `design-taste-frontend` skill first. The LILA RULE applies — no purple/blue AI gradients, no decorative glassmorphism, no BorderBeam/particles on a tool-grade app. Tool-grade aesthetic: zinc-neutral palette, single accent, MOTION_INTENSITY 3-4, VISUAL_DENSITY 5-6. If you catch yourself writing `indigo-500` or `cyan-400` or `from-#818cf8 to-#06b6d4`, stop and re-read the design skill.
2. **Design Read required**: before any UI work, declare a one-line "Design Read" per `design-taste-frontend` Section 0.B. For this project: "Reading this as: desktop file viewer tool for developers, VS Code / Linear tool-grade aesthetic, Tailwind + restrained motion." Any component that doesn't fit this read is wrong.
3. **New features**: research existing solutions before implementing (user's core principle — `research-first-development`).
4. **File handling**: check `references/react-pdf-blobs.md` — Web Workers can't access blob URLs from the main thread.

## Two testing strategies

### A. Playwright E2E (CI / local CLI)
```bash
cd ~/projects/open-any

# Start dev server (Hermes terminal can't background npm run dev — use subprocess)
python3 -c "
import subprocess, time
p = subprocess.Popen(['npm','run','dev'], stdout=subprocess.DEVNULL)
time.sleep(3)
print('Server ready')
"

# Run E2E — MUST use env var to point to existing Chromium
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$HOME/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome \
npx playwright test --reporter=list
```

### B. Agent browser tools (zero install, real-time debug)
Use Hermes' built-in `browser_navigate`, `browser_console`, `browser_snapshot`:
```js
// browser_console expression to drop a file programmatically
(async () => {
  const resp = await fetch('/test-package.json');
  const blob = await resp.blob();
  const file = new File([blob], 'test.json', { type: 'application/json' });
  const dt = new DataTransfer(); dt.items.add(file);
  const dropDiv = document.querySelector('[class*=\"border\"]') as HTMLElement;
  if (!dropDiv) throw new Error('No drop zone');
  const dragover = new DragEvent('dragover', { bubbles: true, cancelable: true });
  Object.defineProperty(dragover, 'dataTransfer', { value: dt });
  dropDiv.dispatchEvent(dragover);
  const drop = new DragEvent('drop', { bubbles: true, cancelable: true });
  Object.defineProperty(drop, 'dataTransfer', { value: dt });
  dropDiv.dispatchEvent(drop);
  await new Promise(r => setTimeout(r, 2000));
  return document.body.innerText.includes('test.json') ? 'OK' : 'FAIL';
})()
```

## Architecture

- **Unit tests**: 218 vitest tests (formatDetect, registry, store, handlers)
- **E2E tests**: 14 Playwright tests in `e2e/handlers.spec.ts`
  - Drops test files via programmatic DragEvent (fetch → Blob → File → DataTransfer → dispatchEvent)
  - Test files in `public/test-*` and `test-files/`
  - Uses existing Chromium 1217 binary (Hermes browser backend)

## CI

Two jobs: `check` (lint → test → build) → `e2e` (Playwright)

## Pitfalls

- **Dev server (WSL)**: `npm run dev` now runs `vite --host 0.0.0.0`. Without `--host`, the Windows browser cannot reach the WSL2 dev server — `localhost` on Windows does not point to WSL2. Use the Network URL shown by Vite (e.g. `http://172.x.x.x:5173/`).
- **Dev server (Hermes)**: Hermes `terminal(background=true)` silently kills `npm run dev`. Use `execute_code` with `subprocess.Popen` instead.
- **Playwright version mismatch**: `@playwright/test` 1.61.0 expects `chromium_headless_shell-1228`, but the system has `chromium-1217`. Use `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` env var to point to the existing binary. In CI (GitHub Actions), the `npx playwright install --with-deps chromium` step handles this automatically.
- **Playwright webServer config**: Setting `webServer` in playwright.config.ts causes timeouts in Hermes' environment. Use local-only mode with the env var and let CI handle its own server start.
- **Test file refresh**: Copy from `test-files/` to `public/` when adding new test data.
- **npm install proxy**: In WSL (China), npm needs `HTTP_PROXY=http://127.0.0.1:7890`. If Clash is not running, npm registry connections time out. `npm install` succeeds locally but silently skips some packages.

## Test file refresh

If test files need updating, copy from test-files to public:
```bash
cp test-files/02-data/package.json public/test-package.json
cp test-files/06-pdf/icml2026-paper.pdf public/test-paper.pdf
# ...etc
```
