# GitHub Stars Management Tools Comparison

## Candidates (2026-07)

| Tool | Stars | Language | AI Backends | Output | Verdict |
|------|-------|----------|-------------|--------|---------|
| **starred** (amirhmoradi) | 54 | Python | Claude/GPT/Gemini | Markdown + GitHub Lists | **PICK** |
| Startidy (hellosunghyun) | 58 | TypeScript | Gemini only | GitHub Lists (32 cats) | Good, but single-provider |
| stargazer (rmdes) | 7 | Python | Claude only | Markdown + Lists | Too new, single-provider |
| Star Manager | — | Web (closed) | — | Dashboard | Closed source, unknown pricing |

## Selection Rationale

`starred` wins on:
- Multi-provider (not locked to one vendor)
- Python (user's native stack)
- Free tier via Gemini
- GitHub Actions automation (set-and-forget)
- MIT license
- Active maintenance (13 commits, Docker support)

## Rejected

- **Startidy**: Gemini-only, TypeScript runtime overhead, no profile README integration
- **stargazer**: Too new (7 stars), Claude-only, sparse docs
- **Star Manager**: Proprietary, can't audit code, unknown longevity
