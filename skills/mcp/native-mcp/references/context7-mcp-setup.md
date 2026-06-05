# Context7 MCP — Up-to-Date Library Docs

**Repo:** `@upstash/context7-mcp` (npm)  
**Website:** https://context7.com/  
**No API key required** for basic usage (higher rate limits available at context7.com/dashboard).

## What it does

Context7 fetches **version-specific** documentation straight from the source and injects it into the LLM context. This prevents hallucinated APIs when the model's training data is out of date.

Two tools are exposed:

| Tool | Description |
|------|-------------|
| `resolve-library-id` | Resolves a package/product name to a Context7-compatible library ID |
| `query-docs` | Retrieves and queries up-to-date documentation and code examples |

## Installation

### Via `hermes mcp add` (stdio)

```bash
hermes mcp add context7 \
  --command npx \
  --args='-y' \
  --args='@upstash/context7-mcp@latest'
```

> **Note on `--args` syntax:** Each argument must be a separate `--args=` flag. The `-y` flag is not a Hermes CLI flag in this context — `--args=` passes it through to npx.

On success it prints:
```
✓ Connected! Found 2 tool(s) from 'context7':
  resolve-library-id  Resolves a package/product name to a Context7-compatible lib...
  query-docs          Retrieves and queries up-to-date documentation and code exam...
```

Then it asks to enable all tools — answer `Y`.

### With API key (higher rate limits)

```bash
hermes mcp add context7 \
  --command npx \
  --args='-y' \
  --args='@upstash/context7-mcp@latest' \
  --args='--api-key' \
  --args='YOUR_API_KEY'
```

### Manual config.yaml entry

Equivalent config in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  context7:
    command: "npx"
    args: ["-y", "@upstash/context7-mcp@latest"]
    timeout: 120
    connect_timeout: 60
```

With API key:

```yaml
mcp_servers:
  context7:
    command: "npx"
    args: ["-y", "@upstash/context7-mcp@latest", "--api-key", "YOUR_API_KEY"]
    timeout: 120
    connect_timeout: 60
```

## Usage

After `/reset` (new session), the tools are available as `mcp_context7_resolve_library_id` and `mcp_context7_query_docs`.

Prompt examples:

> "Use context7 to look up the latest Next.js 15 middleware documentation"
> "Query context7 for React 19 use() hook API"
> "用 context7 查一下 Tailwind CSS v4 的 `@theme` 指令用法"

The agent will:
1. Call `resolve-library-id` to find the correct library ID
2. Call `query-docs` with the ID and version to get the actual docs

## Verification

```bash
hermes mcp list
# Should show: context7    npx @upstash/context7-mcp...    all    ✓ enabled

hermes mcp test context7
# Tests the connection
```

## Troubleshooting

- **`npx -y` fails:** Ensure Node.js and npm are installed and on PATH.
- **No tools appear:** Run `/reset` to start a new session — MCP tools load at session start, not mid-conversation.
- **Rate limited:** Get a free API key from https://context7.com/dashboard and add the `--api-key` arg.
