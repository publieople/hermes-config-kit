# Self-Testing File-Upload Web Apps via browser_console

Pattern developed for open-any (React + Vite file viewer PWA). The agent uses
built-in `browser_console` with `expression` to programmatically test file
handlers without Playwright or external tools.

## Why This Works

The agent's browser tools (`browser_navigate`, `browser_console`, `browser_snapshot`,
`browser_click`, `browser_console`) can interact with a real Chrome instance. For
file-upload testing, the key insight is: **you can create File objects in JS and
dispatch DOM events to trigger the app's existing file handlers.**

No need for Playwright, Selenium, or chrome-devtools-mcp. The built-in tools suffice.

## Pattern: Multi-File Drop Test

```js
// In browser_console expression:
(async () => {
  // 1. Copy test files to public/ or serve them from the dev server
  const files = [
    ['/test-package.json', 'pkg.json', 'application/json'],
    ['/test-cover.png', 'img.png', 'image/png'],
  ];

  // 2. Fetch files and create File objects
  const dt = new DataTransfer();
  for (const [url, name, type] of files) {
    const resp = await fetch(url);
    const blob = await resp.blob();
    dt.items.add(new File([blob], name, { type }));
  }

  // 3. Find the drop zone (FilePicker's border-dashed div)
  const div = document.querySelector('.border-dashed');
  if (!div) return { error: 'No drop zone' };

  // 4. Dispatch dragover + drop events with the DataTransfer
  const dragover = new DragEvent('dragover', { bubbles: true, cancelable: true });
  Object.defineProperty(dragover, 'dataTransfer', { value: dt });
  div.dispatchEvent(dragover);

  const drop = new DragEvent('drop', { bubbles: true, cancelable: true });
  Object.defineProperty(drop, 'dataTransfer', { value: dt });
  div.dispatchEvent(drop);

  // 5. Wait for React to process files
  await new Promise(r => setTimeout(r, 3000));

  // 6. Verify results
  const body = document.body.innerText;
  return {
    allLoaded: files.every(([,name]) => body.includes(name)),
    hasErrors: body.includes('Failed to load'),
    bodyPreview: body.substring(0, 200)
  };
})()
```

## Key Gotchas

1. **`Object.defineProperty` on DragEvent** — DragEvent's `dataTransfer` is read-only by spec. You MUST use `Object.defineProperty(event, 'dataTransfer', { value: dt })` to inject a real DataTransfer.

2. **Multi-file: drop zone disappears** — After the first file(s) load, the FilePicker is replaced by the editor view. You can't drop more files onto a drop zone that doesn't exist. Solution: drop ALL files at once in a single DataTransfer, or refresh between tests.

3. **Don't use `location.reload()` in console expressions** — The CDP connection drops when the page navigates. Use `browser_navigate` for refreshes.

4. **Put test files in `public/`** — They need to be fetchable from the dev server. `cp` them before testing.

## Verification Checklist

After dropping files:
- [ ] `browser_console` to check for JS errors
- [ ] `browser_snapshot` to see rendered DOM (tabs, content)
- [ ] Click through tabs with `browser_click` to verify each handler
- [ ] Test theme toggle click
- [ ] Test language toggle click
