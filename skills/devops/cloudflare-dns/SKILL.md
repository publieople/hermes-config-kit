---
name: cloudflare-dns
description: Manage Cloudflare DNS records via cfcli (npm cloudflare-cli). Use when adding, removing, editing, or listing DNS records for domains on Cloudflare.
---

## Trigger

When the user needs to manage DNS records — add/remove/edit/list A, CNAME, AAAA records on a Cloudflare-managed domain.

## Installation

Already installed globally:

```bash
npm install -g cloudflare-cli  # Already done
```

## Configuration

Config file at `~/.cfcli.yml`. For API Token auth (recommended):

```yaml
defaults:
    token: <cfut_xxx...>
    domain: for-people.cn
```

Multi-account format also supported (see `cfcli --help`).

**Getting a token**: user creates one at https://dash.cloudflare.com/profile/api-tokens → **编辑区域 DNS** template → select zone → copy token.

## Common Commands

```bash
# List all DNS records
cfcli ls

# Add an A record (no -a = Cloudflare proxy OFF)
cfcli -t A add <name> <ip>

# Add with Cloudflare proxy ON (orange cloud)
cfcli -a -t A add <name> <ip>

# Remove a record
cfcli rm <name>

# Find specific record
cfcli find <name>

# Edit a record
cfcli edit <name> <new-value>
```

## User's Domain Convention (for-people.cn)

| Pattern | Purpose | Proxy |
|---------|---------|-------|
| `*.ai.for-people.cn` | Server services (Ollama, Coze, WebDAV) | **false** |
| `*.for-people.cn` | Static sites (GitHub Pages, Vercel) | false |
| `a.for-people.cn` | Cactus server | true |

Server IP: `117.144.13.81` (中侨大学)
Always use `proxied=false` for server services — CF proxy breaks WebDAV, WebSocket, and non-HTTP protocols.

## Pitfalls

- **API Token vs API Key**: `cfcli` defaults to API Token mode when `email` is omitted from config. If using legacy API Key, include `email` in config.
- **Proxy for WebDAV**: Never `-a` (activate/proxy) WebDAV records. The CF proxy doesn't pass PROPFIND/PUT WebDAV methods correctly.
- **TTL**: Default is `1` (Auto). Lower TTL means faster DNS propagation when changing records.