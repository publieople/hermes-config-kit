---
name: lab-server-deploy
description: Deploy self-hosted services (Docker + 1Panel reverse proxy) on the lab server. Use when deploying any new service behind the school's port-8080-only constraint.
---

## Trigger

When the user wants to deploy a new service (WebDAV, web app, API, etc.) on their lab server — the 4×A10 machine managed by 1Panel.

## Server Profile

| Item | Detail |
|------|--------|
| Hostname | `itbk` |
| OS | Ubuntu 24.04.4 LTS |
| Shell | **fish** (not bash!) |
| Access | `ssh -p 35043 po@3722d01e5a6f.ofalias.com` (OpenFRP tunnel) |
| Management | **1Panel** via OpenResty Docker container |
| Hardware | 2×Xeon Silver 4314, 4×A10 (23GB), 125GB RAM, 7.28TB data disk |
| Public port | **Only 8080** (school firewall) |
| Proxy | mihomo/clash on localhost:7890 |

## Public Access Model

```
User's PC ──→ 学校公网 IP:8080 ──→ 服务器 nginx (OpenResty) ──→ backend container
                                                            ──→ another container
```

- No direct WAN IP; school NAT forwards only port 8080
- FRP only carries SSH (22 → remotePort 35043)
- All HTTP services must go through the OpenResty nginx on port 8080, routed by domain or path

## Existing 1Panel Site Configs

Nginx configs live inside the Docker container `1Panel-openresty-Z8Gm` at `/usr/local/openresty/nginx/conf/conf.d/`:

| Config file | Purpose |
|-------------|---------|
| `127.0.0.1.conf` | Default / 1Panel admin |
| `ai.for-people.cn.conf` | AI service |
| `ollama.ai.for-people.cn.conf` | Ollama |
| `coze.ai.for-people.cn.conf` | Coze |
| `1panel.ai.for-people.cn.conf` | 1Panel panel |

Nginx main config at `/usr/local/openresty/nginx/conf/nginx.conf`.

## Deployment Pattern

### Step 0: Verify Docker mirror works

Before deploying anything, check the Docker daemon has working Chinese mirrors:

```bash
ssh host 'cat /etc/docker/daemon.json'
ssh host 'docker info | grep -A5 "Registry Mirrors"'
```

If only `docker.1ms.run` is present (unreliable), user should run:
```bash
sudo bash <(curl -sSL https://linuxmirrors.cn/docker.sh)
```

**Note:** `linuxmirrors.cn/docker.sh` is interactive and may NOT actually change mirrors (observed: still `docker.1ms.run` after running). If it fails, add mirrors manually to `/etc/docker/daemon.json` and `sudo systemctl restart docker`.

### Docker Daemon HTTP Proxy (separate from mirrors!)

Shell's `set -x HTTP_PROXY` / `export HTTP_PROXY` only affects curl/wget, NOT `docker pull`. The Docker **daemon** pulls images — it has its own independent proxy config.
**Verify with official docs** (Context7: `/docker/docs`) before making claims about daemon behavior.

**Daemon proxy via daemon.json (Docker 23.0+, cleanest):**
```json
{
  "registry-mirrors": ["https://docker.1ms.run"],
  "http-proxy": "http://127.0.0.1:7890",
  "https-proxy": "http://127.0.0.1:7890",
  "no-proxy": "localhost,127.0.0.1,docker.1ms.run"
}
```
Then `sudo systemctl restart docker`.

**Verify:** `docker info | grep -i proxy` or `sudo systemctl show --property=Environment docker`

**When to use:** Docker mirrors are slow/unreliable (common on school network), but Clash proxy is fast (curl Google works). Add daemon proxy to fall back to direct Docker Hub pull through Clash.

### Step 1: Deploy Docker container (via SSH)

Use **single SSH call + base64 piping** to avoid OpenFRP rate limits and fish shell issues:

```bash
# Encode commands locally
CMDS=$(echo 'docker rm -f <name> 2>/dev/null
docker pull <image>:<tag>
docker run -d --name <name> --restart always \
  -p 127.0.0.1:<host-port>:<container-port> \
  -v /data/<name>:/data \
  <image>:<tag>
sleep 5
docker logs <name> 2>&1 | head -20
docker ps --filter name=<name>' | base64 -w0)

# Single SSH call (wait 30-60s after last SSH)
sleep 30 && ssh host "echo $CMDS | base64 -d | bash"
```

Key: bind to `127.0.0.1` only — nginx reverse proxies to it, no direct exposure needed.

### Step 2: Add nginx reverse proxy (1Panel Web UI — REQUIRED)

**⚠️ CRITICAL: Do NOT manually write nginx config files to conf.d/ or proxy/*.conf.**  
1Panel's internal site manager overrides or ignores manually-created nginx configs. Even if `nginx -t` passes, requests get routed to the 1Panel welcome page instead of the backend. The ONLY reliable method is through the 1Panel web UI.

**Open 1Panel Web Panel → 网站 → 创建网站 → 反向代理：**

| 字段 | 值 |
|------|-----|
| 主域名 | `<subdomain>.<domain>` |
| 端口 | `8080` |
| 代理地址 | `http://127.0.0.1:<local-port>` |

Click **确认** — 1Panel auto-generates the conf.d server block, proxy config, log directories, and reloads nginx.

If you need WebDAV-specific tweaks (large uploads, no buffering), edit the proxy config via 1Panel's web editor for that website, or `docker exec` into the container and edit `/www/sites/<domain>/proxy/*.conf`, then reload.

For a new subdomain: user must add DNS record in Cloudflare pointing to the school's public IP. See Cloudflare DNS section.

### Step 3: Verify

```bash
curl -s -o /dev/null -w '%{http_code}' http://<domain>:8080/
```

## SSH Pitfalls

### Fish fastfetch banner + quote escaping breaks non-interactive SSH

The fish config has `fastfetch` in `~/.config/fish/config.fish`, printing a massive system-info banner on every login. This corrupts stdout. Worse, fish's quote parsing intercepts nested quotes in `bash -c` wrappers, causing "fish: Unexpected end of string" errors.

**Workarounds (in order of reliability):**

1. **Base64 pipe to bash** (best — bypasses fish entirely):
   ```bash
   # Encode locally
   echo 'cmd1; cmd2; cmd3' | base64 -w0
   # Decode on server
   ssh host 'echo BASE64STRING | base64 -d | bash'
   ```

2. **Single command with `RequestTTY=no`** (OK for short commands):
   ```bash
   ssh -o RequestTTY=no host 'cat /etc/docker/daemon.json'
   ```

3. **Grep-filter the output**:
   ```bash
   ssh host 'command' 2>/dev/null | grep -v "^│\|^┌\|^└\|^po@\|fastfetch"
   ```

4. **Permanent fix** (if user approves):
   ```bash
   ssh host "sed -i 's/^fastfetch/#fastfetch/' ~/.config/fish/config.fish"
   ```

### OpenFRP connection rate limiting

OpenFRP free tier **rate-limits connection frequency**. After one non-interactive SSH session ends, subsequent connections get "Connection closed by ..." immediately. **Wait 30–60 seconds between SSH terminal() calls.** This is NOT a normal SSH issue — the tunnel itself throttles reconnection.

### Docker pull slow on school network

Docker Hub is blocked/slow from Chinese school networks. The server's `daemon.json` may have a single mirror that's unreliable.

**First step — configure proper mirrors** (requires root, user runs once):
```bash
sudo bash <(curl -sSL https://linuxmirrors.cn/docker.sh)
```
This interactively sets up multiple Chinese Docker mirrors. After running, verify with:
```bash
cat /etc/docker/daemon.json | grep registry-mirrors
```

If `linuxmirrors.cn` script isn't desired, add mirrors manually to `/etc/docker/daemon.json`:
```json
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://docker.m.daocloud.io",
    "https://hub.rat.dev"
  ]
}
```

After changing mirrors: `sudo systemctl restart docker`

### Cloudflare DNS Management

DNS for `for-people.cn` is on Cloudflare. `cloudflare-cli` (npm package `cfcli`) is installed locally.

**Setup (~/.cfcli.yml):**
```yaml
defaults:
    token: <cloudflare-api-token>
    domain: for-people.cn
```

**Common commands:**
```bash
cfcli ls                              # List all DNS records
cfcli -t A add <name>.ai 117.144.13.81   # Add A record (server, proxied=false)
cfcli find <name>                     # Find specific records
cfcli rm <name>                       # Remove a record
```

The API token needs **Zone.DNS:Edit** permission on `for-people.cn`. Create at https://dash.cloudflare.com/profile/api-tokens.

**Server subdomain pattern:** All server services use `*.ai.for-people.cn` → `117.144.13.81`, proxied=false (WebDAV, API services can't go through CF proxy).

## Service-Specific Notes

### OpenList (WebDAV / cloud storage mount)

OpenList has a **domestic native install script** — prefer this over Docker. See `references/openlist-deploy.md` for full deploy guide including nginx reverse proxy, DNS, and TieZ client config.

**Destination header compatibility (⚠️ easy to misdiagnose as WAF):** OpenList's WebDAV MOVE endpoint rejects Destination headers with absolute URLs (e.g., `http://domain/dav/path`). It only accepts relative paths (`/dav/path`). Since TieZ sends absolute URLs, the nginx proxy MUST rewrite Destination before forwarding:

```nginx
set_by_lua_block $rewritten_dest {
    local dest = ngx.var.http_destination
    if dest then
        dest = dest:gsub("^https?://[^/]+", "")
    end
    return dest or ""
}
proxy_set_header Destination $rewritten_dest;
```

Without this rewrite, MOVE returns 502 (not logged to error.log — nginx treats it as a valid upstream response). This is easy to confuse with WAF blocking.

**General rule:** For ANY service that offers a native install script with domestic CDN mirror, use that instead of Docker on this server. Docker Hub is unreliable from the school network.

## User Preferences

### Verify claims against official docs BEFORE stating them

When making assertions about tool behavior (e.g., "Docker daemon needs proxy configured via systemd"), **always check Context7 or the official documentation first.** Do not state confident technical claims from memory — verify them. The user will call out unverified claims with "你真的查过了吗" or "你没幻觉吧". Context7 has Docker docs at `/docker/docs`, 1Panel at `/1panel-dev/docs`, OpenList at `/websites/doc_oplist`, and many more.

### Check config BEFORE operating, not after

When troubleshooting, always inspect the actual configuration state (e.g., `cat /etc/docker/daemon.json`, `docker info | grep -i proxy`) before proposing fixes. The user expects diagnosis before prescription. Avoid the pattern of suggesting fixes based on assumptions about what the config "should be."

## Common Pitfalls

### 1Panel: Container-host networking (`127.0.0.1` is the CONTAINER, not the host)

The 1Panel OpenResty **runs inside a Docker container**. When you set `proxy_pass http://127.0.0.1:PORT`, that `127.0.0.1` resolves to the **container's** localhost — not the host machine. Any service running natively on the host (not in Docker) must be accessed via:

- **`host.docker.internal`** — semantics are clear, but on Linux Docker requires a `/etc/hosts` entry (not auto-created like on Mac/Windows)
- **`172.17.0.1`** — the Docker bridge gateway IP (works universally but may change)

**Setup (run once, inside the OpenResty container):**

```fish
sudo docker exec 1Panel-openresty-Z8Gm sh -c 'grep -q host.docker.internal /etc/hosts || echo "172.17.0.1 host.docker.internal" >> /etc/hosts'
```

Then use `http://host.docker.internal:PORT` in all proxy_pass directives that target host-native services.

**To find the Docker bridge IP:**
```fish
ip addr show docker0 | grep inet
# → inet 172.17.0.1/16
```

**Verification** (from inside the container):
```fish
sudo docker exec 1Panel-openresty-Z8Gm curl -s -o /dev/null -w 'HTTP:%{http_code}\n' http://host.docker.internal:PORT/
```

### 1Panel: WAF methodWhite blocks non-standard HTTP methods (MOVE → 502, even with correct proxy config!)

**This is the #1 silent killer for WebDAV on 1Panel.** Even after fixing all proxy headers, MOVE/COPY/PROPFIND return 502 from external clients while working fine from inside the container. The culprit: **1Panel's WAF `methodWhite` rule** (enabled by default) only allows GET/POST/HEAD through for external requests.

**Diagnosis** (from inside container, bypass WAF):
```fish
# This works (localhost skips some WAF checks)
sudo docker exec 1Panel-openresty-Z8Gm curl -sv -X MOVE -u user:pass -H "Destination: http://..." http://localhost:8080/path 2>&1 | grep "< HTTP"
# → 200 OK ← PROVES it's WAF, not nginx proxy config
```

**Fix:** WAF config is at `/usr/local/openresty/1pwaf/data/conf/siteConfig.json` inside the OpenResty container. The container has no `python3`, use `resty` (OpenResty's Lua):

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

**Alternative (1Panel Web UI):** WAF → 网站设置 → 选站点 → 关掉 `methodWhite`、`header`、`xss` 三个规则，或者直接关闭该站点的 WAF 开关。WebDAV 有 HTTP Basic Auth，安全层面有保障。

**Rules that block WebDAV:**

| WAF Rule | Blocks | Why |
|----------|--------|-----|
| `methodWhite` | MOVE, PROPFIND, MKCOL, DELETE | Only GET/POST/HEAD in whitelist |
| `header` | MOVE (Destination header) | Header contains URL → triggers XSS filter |
| `xss` | XML responses | WebDAV PROPFIND returns XML |

### 1Panel: WAF config (`siteConfig.json`) structure

The global WAF config is at `/usr/local/openresty/1pwaf/data/conf/siteConfig.json` inside the container. Key sections:
- `waf.state` — master on/off
- `methodWhite.state` — blocks unknown HTTP methods (444 = drop connection)
- `header.state` — blocks suspicious headers
- `xss.state` — blocks XSS patterns
- `args.state` — blocks malicious query params

Per-site overrides (if any) would be in `/usr/local/openresty/1pwaf/data/conf/sites.json`.

### 1Panel: Default proxy config breaks WebDAV (MOVE → 502)

The 1Panel auto-generated reverse proxy has THREE issues that break WebDAV:

1. **`proxy_set_header Connection $http_connection;`** — passes the client's `Connection` header to the backend, breaking WebDAV MOVE
2. **Missing `Destination` header forwarding** — nginx does NOT forward the `Destination` header by default, which WebDAV MOVE/COPY operations require

**Symptom:** TieZ shows `webdav MOVE ... failed: 502 Bad Gateway` when trying to save files. Even after setting `Connection ""`, MOVE still fails until `Destination` is forwarded.

**Fix:** Edit the proxy config inside the OpenResty container:

```nginx
# ❌ Default 1Panel proxy config (breaks WebDAV)
proxy_set_header Connection $http_connection;
# Missing: Destination header not forwarded

# ✅ Required for WebDAV
proxy_set_header Connection "";
proxy_set_header Destination $http_destination;   # ← CRITICAL for MOVE/COPY
proxy_request_buffering off;
proxy_buffering off;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
client_max_body_size 0;
```

**Why Destination header is critical:** WebDAV MOVE and COPY use the `Destination` header to specify the target path. nginx does NOT forward custom headers by default, so `proxy_set_header Destination $http_destination` is mandatory. Without it, the backend receives a MOVE request with no target, returning various errors.

The config file is at `/www/sites/<domain>/proxy/root.conf` inside the `1Panel-openresty-Z8Gm` container. Edit via:

```fish
sudo docker exec 1Panel-openresty-Z8Gm sh -c "cat > /www/sites/<domain>/proxy/root.conf << 'EOF'
location ^~ / {
    proxy_pass http://127.0.0.1:<port>;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection \"\";
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
EOF"
```

Then `nginx -t` and `nginx -s reload`.

Note: `$host`, `$remote_addr` etc. must be escaped as `\$host` when inside `sh -c "..."`.

### 1Panel: Writes to container paths must use docker exec

`tee /usr/local/openresty/nginx/conf/conf.d/file.conf` writes to the **host** filesystem, not the Docker container. For nginx configs inside the 1Panel OpenResty container, always use `docker exec -i <container> tee <path>` or `docker exec <container> sh -c "cat > <path>"`.

### Fish heredoc alternative for `sh -c`

`sudo docker exec <container> sh -c "cat > file << 'EOF' ... EOF"` works because `sh` (not fish) handles the heredoc. The outer `"..."` from fish passes the whole block to `sh`.

### 1Panel: Manual nginx configs silently ignored

**Writing config files directly to conf.d/ or proxy/*.conf does NOT work.** Even though `nginx -t` passes and `nginx -s reload` shows no errors, 1Panel's internal site manager routes requests to its own default page instead of the backend. Observed: manually created `sync.ai.for-people.cn.conf` + `proxy/openlist.conf` passed syntax check but all requests returned "Welcome to 1Panel". Solution: always use 1Panel Web UI → 网站 → 创建网站 → 反向代理.

### fish shell: && / || don't work

fish uses `; and` and `; or` instead of bash's `&&` and `||`. Also `set -x VAR val` instead of `export VAR=val`. `2>/dev/null` works in fish but piping behavior differs.

```fish
# ❌ bash syntax (broken in fish)
cmd1 && cmd2
cmd1 2>/dev/null || cmd3

# ✅ fish syntax
cmd1; and cmd2
cmd1 2>/dev/null; or cmd3
```

**CRITICAL:** Every command given to the user for their SSH session MUST be fish-compatible. The lab server's default shell is fish and most users won't switch to bash. If you give bash syntax, the user will copy-paste and it will fail.

### fish shell: wildcard globbing differences

Fish's `*` glob fails if no files match (bash treats it literally). Use `.` instead:

```fish
# ❌ Fails in fish if dir is empty
sudo cp -a /src/* /dst/

# ✅ Works in fish
sudo cp -a /src/. /dst/
```

### fish shell: heredoc not supported

Fish does not support bash-style `cat > file << 'EOF' ... EOF`. Use `echo '...' | tee` instead, or base64 piping for complex configs.

### fish shell: quoting for docker exec

Fish treats `$host` inside single quotes literally. Use double quotes around the entire argument to `docker exec bash -c "..."`:

## Reference Files

- `references/webdav-alternatives.md` — Self-hosted and free WebDAV alternatives to 坚果云
- `references/openlist-deploy.md` — OpenList native deploy guide (no Docker needed)
