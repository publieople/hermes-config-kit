# OpenList on Lab Server

OpenList is the community fork of AList (after AList was sold to 不够科技 in 2025).
It provides WebDAV + 40+ cloud storage mounts. Installed natively (not Docker).

## Why Native (NOT Docker)

OpenList offers a **domestic one-click install** via `res.oplist.org.cn`, completely bypassing
Docker Hub which is unreliable from the school network. **Always prefer native install scripts
with domestic CDN over Docker for services on this server.**

## Install

The install script downloads from GitHub which is blocked. Must pass Clash proxy:

```fish
curl -fsSL https://res.oplist.org.cn/script/v4.sh -o /tmp/install-openlist-v4.sh
and sudo --preserve-env=HTTP_PROXY,HTTPS_PROXY \
  HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 \
  bash /tmp/install-openlist-v4.sh
```

The script is interactive — select option 1 (install). When prompted for a GitHub proxy, hit Enter to skip (Clash handles it).

After install:
- Service: systemd `openlist`
- Config: `/opt/openlist/data/config.json`
- Port: 5244
- CLI: `openlist` or `openlist-manager`
- Installed version will be shown after install (e.g., v4.2.2)

## Post-Install

Set `site_url` and restart:

```fish
sudo sed -i 's|"site_url".*|"site_url": "https://sync.ai.for-people.cn:8080",|' /opt/openlist/data/config.json
sudo systemctl restart openlist
# Verify
sudo grep site_url /opt/openlist/data/config.json
and curl -s -o /dev/null -w 'HTTP:%{http_code}\n' http://127.0.0.1:5244/
and sudo systemctl is-active openlist
```

## Storage Setup (REQUIRED — NOT optional)

OpenList shows "failed get storage: storage not found; please add a storage first" on first visit.
**This is expected.** You MUST add at least one storage driver for files to exist.

### Adding Local Storage

Open browser to the OpenList admin panel, then:

1. Click **存储 (Storage)** → **添加 (Add)**
2. Driver: **本地存储 (Local)**
3. Fill only these two fields:

| Field | Value |
|-------|-------|
| 挂载路径 (Mount path) | `/tiez-sync` |
| 根文件夹路径 (Root folder) | `/data/openlist/storage` |

4. Leave all other settings at defaults (thumbnail, cache, webdav_policy, etc.)
5. Create the folder on disk first: `sudo mkdir -p /data/openlist/storage`
6. Click **添加 (Add)**

### Other Local Storage Settings (reference only — leave at defaults)

| Field | Default | Purpose |
|-------|---------|---------|
| 缩略图 (Thumbnail) | off | Generate image thumbnails — not needed for clipboard sync |
| 显示隐藏文件 (Show hidden) | off | Show dotfiles |
| 新建目录权限 (mkdir perm) | — | Linux permissions for new folders |
| 缓存过期 (Cache expiration) | 30min | Directory listing cache TTL |
| WebDAV 策略 | native_proxy | native_proxy=direct, use_proxy_url=proxy |
| 签名 (Sign) | off | Sign download URLs for hotlink protection |

## Nginx Reverse Proxy (1Panel Web UI)

**Do NOT manually create nginx configs** — 1Panel's internal site manager overrides them.
Even if `nginx -t` passes, manually-created configs get swallowed by the 1Panel default server.

Instead, open **1Panel Web Panel → 网站 → 创建网站 → 反向代理**：

| 字段 | 值 |
|------|-----|
| 主域名 | `sync.ai.for-people.cn` |
| 端口 | `8080` |
| 代理地址 | `http://host.docker.internal:5244` ⚠️ |

**⚠️ IMPORTANT:** The proxy address must be `http://host.docker.internal:5244` — NOT `http://127.0.0.1:5244`. The nginx runs in a Docker container, so its `127.0.0.1` is the container's own localhost, not the host. OpenList runs natively on the host, so it must be accessed via Docker's host gateway.

**Before creating the site, add the host.docker.internal alias** to the OpenResty container (run once):

```fish
sudo docker exec 1Panel-openresty-Z8Gm sh -c 'grep -q host.docker.internal /etc/hosts || echo "172.17.0.1 host.docker.internal" >> /etc/hosts'
```

(`172.17.0.1` is the Docker bridge gateway; verify with `ip addr show docker0 | grep inet`)

After site creation, the proxy config at `/www/sites/sync.ai.for-people.cn/proxy/root.conf` inside the OpenResty container needs WebDAV-specific fixes:

```fish
# The default proxy config has Connection $http_connection which breaks WebDAV MOVE → 502
# Also: nginx does NOT forward the Destination header by default (needed for WebDAV MOVE/COPY)
# Also: proxy_pass must use host.docker.internal because nginx runs in Docker, not on the host
sudo docker exec 1Panel-openresty-Z8Gm sh -c "cat > /www/sites/sync.ai.for-people.cn/proxy/root.conf << 'EOF'
location ^~ / {
    proxy_pass http://host.docker.internal:5244;
    proxy_set_header Host \\$host;
    proxy_set_header X-Real-IP \\$remote_addr;
    proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \\$scheme;
    proxy_set_header Destination \\$http_destination;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \\$http_upgrade;
    proxy_set_header Connection \\\"\\\";
    proxy_buffering off;
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
EOF"
sudo docker exec 1Panel-openresty-Z8Gm nginx -t
and sudo docker exec 1Panel-openresty-Z8Gm nginx -s reload
```

Key differences from 1Panel default:
- `proxy_pass http://host.docker.internal:5244;` — NOT `127.0.0.1` (container≠host)
- `proxy_set_header Destination $http_destination;` — forwards MOVE/COPY target (CRITICAL)
- `proxy_set_header Connection "";` — NOT `$http_connection` (breaks WebDAV MOVE)
- `proxy_buffering off;` — required for WebDAV streaming
- `proxy_request_buffering off;` — required for WebDAV large PUT operations
- `client_max_body_size 0;` — no upload size limit
- `proxy_read_timeout/send_timeout 300s;` — long timeouts for file transfers

## DNS

```bash
cfcli -t A add sync.ai 117.144.13.81
```

Proxied must be `false` — WebDAV PROPFIND/PUT/PROPPATCH don't work through Cloudflare proxy.

## TieZ Client Config

**⚠️ Critical: The WebDAV root `/dav/` cannot be written to directly.** Point the sync directory
to the mounted storage subpath, not `/dav/` itself. Getting 404 on `/dav/` or 405 MKCOL on
`/dav/dav/` means the path is wrong.

Correct TieZ configuration:

```
WebDAV URL:     http://sync.ai.for-people.cn:8080/dav/
Sync directory: tiez-sync      ← NOT empty, NOT "/", NOT "dav"
Username:       admin
Password:       SRJFasXS       ← from install output
```

### Common TieZ Errors & Causes

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` when sync dir is empty or `/` | OpenList `/dav/` root is read-only; can't PROPFIND/MKCOL on bare root | Set sync directory to storage mount path (`tiez-sync`) |
| `405 MKCOL failed for /dav/dav/` | Sync directory set to `dav`, doubling the path | Change sync dir to storage name, not `dav` |
| `502 Bad Gateway` (all requests from external, but OK from container-internal `curl localhost:8080`) | 1Panel WAF `methodWhite` rule blocks non-GET/POST/HEAD methods silently (code 444 → nginx sees 502) | Disable methodWhite + header in WAF siteConfig.json (see Troubleshooting: WAF Method Blocking section) |
| `502 Bad Gateway on MOVE` (after `Connection ""` fix, after WAF methodWhite disabled) | nginx does NOT forward the `Destination` header by default; WebDAV MOVE/COPY requires it | Add `proxy_set_header Destination $http_destination;` to proxy config |
| `502 Bad Gateway` (all requests) | `proxy_pass http://127.0.0.1:5244` in Docker — `127.0.0.1` is the container, not the host | Use `proxy_pass http://host.docker.internal:5244` + add hosts entry |
| `502 Bad Gateway` after data migration | `/data/openlist/` permissions are 700 root, OpenList process can't write | `sudo chmod 755 /data/openlist/` |
| `failed get storage: storage not found` on homepage | No storage driver added — OpenList doesn't auto-create storage | Add Local storage via web UI with mount path + root folder path |

## Context7 Docs

Context7 has OpenList docs at `/websites/doc_oplist` (361 snippets) and `/openlistteam/openlist` (281 snippets).
Use `mcp_context7_query_docs` for API/config reference.

## Data Directory Migration

OpenList installs data to `/opt/openlist/data/` (on the 98GB system disk). Move to the 7TB `/data/` disk:

```fish
sudo systemctl stop openlist
sudo cp -a /opt/openlist/data/. /data/openlist/
sudo rm -rf /opt/openlist/data
sudo ln -s /data/openlist /opt/openlist/data
sudo chmod 755 /data/openlist/    # ← REQUIRED: parent dir must be readable by the openlist process
sudo systemctl start openlist
sudo ls -la /opt/openlist/ | grep data
# Expected: data -> /data/openlist
```

**Fish note:** `cp -a /src/* /dst/` fails in fish if directory is empty. Use `cp -a /src/. /dst/` instead.

**Permissions pitfall:** The data directory ends up with 700 (drwx------) root, preventing the `po` user from accessing `storage/` subdirectory, which causes 502 when OpenList tries WebDAV operations. Always run `chmod 755` on `/data/openlist/` after migration.

## Verified Deployment (2026-06-07)

Successfully deployed v4.2.2 on lab server with the full chain:
1. Native install via `res.oplist.org.cn` (Clash proxy for GitHub download)
2. DNS (`sync.ai.for-people.cn` → `117.144.13.81`)
3. Local storage added at `/tiez-sync` → `/data/openlist/storage`
4. Data migrated to `/data/` disk with `chmod 755` permissions fix
5. 1Panel reverse proxy (`:8080` → `host.docker.internal:5244`) with WebDAV-safe config:
   - `Connection ""` (not `$http_connection`)
   - `Destination $http_destination` (nginx doesn't forward by default)
   - `proxy_buffering off` + `proxy_request_buffering off`
6. **1Panel WAF methodWhite disabled** — the WAF's default method whitelist blocks MOVE/PROPFIND/MKCOL
7. TieZ configured with `http://sync.ai.for-people.cn:8080/dav/` + sync dir `tiez-sync`

Verified HTTP 200 from public endpoint, WebDAV PROPFIND 207 Multi-Status, MKCOL 201 Created, MOVE 201 Created (after WAF + Destination header fix).

## Troubleshooting: WAF Method Blocking

**Symptom:** MOVE/COPY return 502 from external clients, but work fine when called from inside the container (`curl localhost:8080` → 200). PROPFIND and MKCOL may also fail intermittently.

**Root cause:** 1Panel WAF's `methodWhite` rule only allows GET/POST/HEAD by default. It silently drops non-standard HTTP methods with code 444 (connection close), causing nginx to report 502.

**Fix** — edit WAF config inside the OpenResty container (no Python available, use Resty/Lua):

```fish
sudo docker exec 1Panel-openresty-Z8Gm resty -e '
local cjson = require "cjson"
local f = io.open("/usr/local/openresty/1pwaf/data/conf/siteConfig.json", "r")
local cfg = cjson.decode(f:read("*a"))
f:close()
cfg.methodWhite.state = "off"
cfg.header.state = "off"
f = io.open("/usr/local/openresty/1pwaf/data/conf/siteConfig.json", "w")
f:write(cjson.encode(cfg))
f:close()
print("methodWhite=" .. cfg.methodWhite.state .. " header=" .. cfg.header.state)
'
sudo docker exec 1Panel-openresty-Z8Gm nginx -s reload
```

Or disable WAF for this site entirely through 1Panel Web UI: WAF → 网站设置 → 选站点 → 关掉 WAF 开关.
