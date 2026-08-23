# Case Study: Open-Any Code Review (2026-06-22)

Applying the 5 mental models + 4 research dimensions to a real frontend project (~3.9K LOC TypeScript/React, 11 file handlers, PWA).

## Review Workflow

1. **Research first** — read all source: store, registry, 11 handlers, format detection, file ops, components, git log, test results
2. **Map findings to models** — each bug traced to a specific Linus mental model
3. **Present with evidence** — code citations not opinions
4. **User verification** — all 6 findings confirmed, none false positive
5. **Fix in priority order** — correctness bugs first, then feature, then perf

## Findings → Model Mapping

| # | Finding | Model | Root Cause |
|---|---------|-------|------------|
| 1 | Text handler clobbers specialized handlers (json/md/yaml) via last-write-wins in Map | Good Taste | Extension overlap + registration order = non-deterministic behavior |
| 2 | TOML mapped to YAML format | Never Break Userspace | Lying to user about format semantics |
| 3 | Language support claimed but not implemented (go, java, rb, php, sql, r, lua) | Code Talks, Bullshit Walks | Extension list not synced with CodeMirror language packs |
| 4 | Archive extraction dumps to `window.open()` instead of internal handler pipeline | Good Taste | Feature exists but doesn't integrate with own architecture |
| 5 | 12MB bundle, all handlers eager-imported, `registerLazy` unused | Pragmatism Over Ideology | Built lazy-loading infrastructure then didn't use it |
| 6 | `ArrayBuffer` in React Zustand store (perf + memory bomb for large files) | Good Taste | Data structure wrong — buffer should live in side Map outside render cycle |

## Fix Summary

| # | Fix | Lines Changed | Time |
|---|-----|--------------|------|
| 1 | Remove overlapping extensions from text handler + drop fake language support | ~15 lines | 5min |
| 2 | `toml: 'yaml'` → `toml: 'code'` (extension + MIME maps) | ~4 lines | 1min |
| 3 | Archive `handleOpenAsFile` → create FileTab + `openFile()` into handler pipeline | ~20 lines | 15min |
| 4 | `registerHandler` → `registerLazy` with dynamic `import()` for 9/11 handlers | ~40 lines | 15min |
| 5 | `FileTab.buffer` → `Map<string, ArrayBuffer>` side cache, all handlers updated | ~50 lines across 8 files | 10min |

**Result**: 215/215 tests pass, TypeScript compiles clean, initial bundle ~740K (down from ~3.5MB eagerly loaded).

## Reusable Patterns from This Review

### Handler Registry Collision Detection
When using a Map-based registry with extension→handler binding, always check for overlap between handlers. Last-write-wins silently kills earlier registrations. Mitigation: either (a) disallow overlap at registration time, (b) register general handlers FIRST and let specialized handlers overwrite, or (c) use priority ordering.

### Buffer Side-Map for React
For large binary data that shouldn't trigger React re-renders: keep a plain `Map<string, ArrayBuffer>` outside the component tree. Components read via `getFileBuffer(id)` inside `useMemo`/`useEffect` with stable deps `[id]`. The store's update action syncs both the React state (for UI) and the side Map (for data).

### Lazy Import with Named Exports
When using `registerLazy` with `import()`:
- `import('./foo')` returns `{ handler: FileHandler }` (named export), NOT `{ default: FileHandler }`
- The `loadLazy` method must handle both shapes: `mod.default ?? mod.handler`
- Or update `LazyHandler` type to allow both
