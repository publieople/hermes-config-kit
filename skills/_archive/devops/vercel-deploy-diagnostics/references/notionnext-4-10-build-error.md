# Reference: NotionNext 4.10.0 schema-fail-fast bug

## Symptom

`yarn run build` exit 1 on a fork of `notionnext-org/NotionNext` at ~4.10.0. Build log shows:

```
[article/<slug>-<ts>] [resolvePostProps] processPostData failed TypeError: t.block[l].value.content is not iterable
Error: Error serializing `.prev` returned from `getStaticProps` in "/[prefix]/[slug]"
Command "yarn run build" exited with 1
```

Vercel `errorCode` is misleadingly `module_not_found` (or `build_failed` on production). Real cause: `processPostData` iterates `block.value.content` without `Array.isArray` guard. Notion block types whose `value.content` is null/`string`/missing (e.g. `callout`, `column_list`, certain toggles) trigger the throw.

## Provenance (source-first check that did NOT find an upstream issue/PR fix)

Performed during 2026-07-04 debug session:

```
gh issue list -R notionnext-org/NotionNext --search "value.content is not iterable"  → 1 closed 2022 issue #472 (older family, different error)
gh search commits "value.content is not iterable" -R notionnext-org/NotionNext    → 0
gh issue list -R notionnext-org/NotionNext --search "processPostData"             → 0
gh search commits "processPostData" -R notionnext-org/NotionNext                  → 0
gh pr list -R notionnext-org/NotionNext --search "is not iterable" --state all    → 0 hits on the empty-content path
```

Conclusion: bug is **novel**, not a regression of a known fixed issue. Upstream 4.10.0 release notes (changelog 4.10.0) advertise page-data perf optimization; the `processPostData` strict-mode side effect was not flagged in changelog.

## Diagnosis recipe (reusable for any NotionNext build fail)

1. Find the failing deployment via Vercel API (see SKILL.md §List Deployments).
2. Pull `errorMessage` and `https://api.vercel.com/v1/deployments/<dpl_id>/events`.
3. Look for the last `[resolvePostProps]` / `processPostData` / `Error serializing` lines — those pin the file path in `lib/blog/`.
4. If multiple posts list their slugs (e.g. `[article/elegant_file_management-…]`), the block-level issue is consistent across posts → guard the schema, don't patch per-post.

## Lazy fix on the fork

In `lib/blog/processPostData.js` (or wherever `block.value.content` is iterated):

```js
- for (const c of block.value.content) {
+ if (Array.isArray(block?.value?.content)) {
+   for (const c of block.value.content) {
+     // ...existing body
+   }
+ }
```

One-line guard per iteration site. The schema-fail was the only thing blocking production rebuild. With this guard pushed to fork HEAD, Vercel production transitioned from `ERROR` to `READY` on the next build.

When to delete: once upstream ships a fix (track via `gh issue list -R notionnext-org/NotionNext --search "processPostData"` periodically). When upstream ships, the fork's guard becomes redundant and can be removed in the next sync.

## Lesson

Upstream Release-quality ≠ GA-quality for NotionNext's quarterly-cadence 4.x releases. After any merge from upstream (`workflow_dispatch` of `Upstream Sync` workflow), always check that the resulting production deployment is still `READY` before declaring the sync done. A green "No new commits to sync" log does not guarantee green production.
