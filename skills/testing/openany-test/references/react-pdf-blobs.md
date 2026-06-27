# React-PDF Blob URL Anti-Pattern

## Root cause

react-pdf's `<Document>` component loads PDFs via a PDF.js Web Worker. When you pass a `blob:` URL, the worker thread tries to `fetch()` that URL. **Web Workers cannot access blob URLs created in the main thread** — they live in different execution contexts. The fetch returns status 0, and react-pdf shows "Failed to load PDF".

## Wrong

```tsx
// ❌ Blob URLs are NOT accessible from Web Workers
const blobUrl = URL.createObjectURL(new Blob([file.buffer]));
return <Document file={blobUrl} />;
```

## Correct

```tsx
// ✅ Pass raw buffer — transferred via structured clone (postMessage-safe)
const pdfSource = { data: new Uint8Array(file.buffer) };
return <Document file={pdfSource} />;
```

## Also correct (Vite-specific)

```tsx
// Bundle worker from node_modules — no CDN needed
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();
```

## Why CDN URLs also fail

1. `pdfjs.version` is the bundled version, but cdnjs may not have that exact version
2. CDN worker has the same blob URL access problem as a bundled worker
3. Vite's `new URL(..., import.meta.url)` handles static asset copying automatically

## Root cause discovery method

The console error was: `ResponseException: Unexpected server response (0) while retrieving PDF "blob:..."`. Status code 0 in fetch means the connection was refused or the resource is unavailable. Combined with the knowledge that Web Workers have their own context, the diagnosis was straightforward.
