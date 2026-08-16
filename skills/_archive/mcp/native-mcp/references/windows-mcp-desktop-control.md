# Windows-MCP: WSL → Windows Desktop Control

## Architecture

```
Hermes (WSL/Linux) ──HTTP MCP──→ Windows-MCP (Windows) ──→ Desktop UI
                                 ↑ server on :8000/mcp
```

Hermes acts as the **MCP client** (via its native MCP client supporting streamable-http). Windows-MCP acts as the **MCP server**. Hermes can send desktop control commands (click, type, screenshot, app launch) without installing anything Windows-specific in WSL.

**Key distinction from `hermes-external-integration`:** That skill covers *Hermes as the integration target* (external apps connect TO Hermes). This covers *Hermes as the integration consumer* (Hermes connects TO an external service to gain desktop control capabilities).

## Prerequisites on Windows

- **Python 3.10+** — check with `python --version` in PowerShell
- **uv** — install with `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows-MCP installs via `uvx windows-mcp` (auto-downloads deps)

## Installation (Windows Side)

```powershell
# Install Windows-MCP (first run auto-installs, ~1-2 min)
uvx windows-mcp
# Or install as a standalone tool:
uv tool install windows-mcp
```

## Start the Server (Windows Side)

```powershell
# Streamable-http transport — required for WSL access
windows-mcp serve --transport streamable-http --host 0.0.0.0 --port 8000 --auth-key YOUR_SECRET_KEY
```

**⚠️ Critical: The endpoint is `/mcp`.** Hermes must connect to `http://<windows-ip>:8000/mcp`, not just the base URL.

**Transport options:**

| Transport | Command | Use For |
|-----------|---------|---------|
| `streamable-http` | `serve --transport streamable-http --host 0.0.0.0 --port 8000` | HTTP from WSL (recommended) |
| `sse` | `serve --transport sse --host 0.0.0.0 --port 8000` | Server-Sent Events (fallback) |
| `stdio` (default) | `serve` | Local-only (no WSL) |

**Persistence:** The server is a foreground process — it dies when the terminal/powershell session ends. Two options for persistence:

1. **Scheduled task (recommended for always-on):**
   ```powershell
   windows-mcp install   # creates a scheduled task 'windows-mcp-server'
   ```
2. **From WSL (ad-hoc):** Use `Start-Process` via `powershell.exe`:
   ```bash
   powershell.exe -Command "Start-Process -NoNewWindow -FilePath \"uvx\" -ArgumentList \"windows-mcp serve --transport streamable-http --host 0.0.0.0 --port 8000 --auth-key hermes123\""
   ```
   Or start it as a Hermes background process: `terminal(background=True)` running the powershell command.

## WSL Network Resolution

WSL can reach Windows via:

| Address | When It Works |
|---------|---------------|
| `host.docker.internal` | Most WSL2 setups (auto-resolves to the Windows host) |
| WSL gateway IP | Check with `ip route | grep default` (usually `172.x.x.1`) |
| Windows LAN IP | Always works (e.g. `192.168.1.100`) |

Test connectivity:
```bash
curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://host.docker.internal:8000/mcp -H "Authorization: Bearer YOUR_SECRET_KEY"
# Expect 406 (Not Acceptable) — server is alive, just wrong Accept header
# Expect 000 / timeout — server is down or port blocked
```

## Hermes Configuration (WSL Side)

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  windows-mcp:
    url: "http://host.docker.internal:8000/mcp"
    headers:
      Authorization: "Bearer YOUR_SECRET_KEY"
    timeout: 120
    connect_timeout: 30
```

Restart Hermes:
```bash
hermes gateway restart
# Or: hermes gateway stop && sleep 3 && hermes gateway start
```

On startup, Hermes connects to Windows-MCP and registers tools prefixed with `mcp_windows_mcp_*`.

**Proxy pitfall:** If Hermes has an HTTP proxy configured (e.g. `http_proxy=http://127.0.0.1:7890`), connections to the Windows host may route through the proxy and fail. Solutions:
- Set `no_proxy='*'` in Hermes env (most aggressive, disables proxy for all MCP connections)
- Or more selectively: `no_proxy='host.docker.internal,*.local,172.*,192.168.*'`
- Or use the Windows LAN IP directly instead of `host.docker.internal`

## Browser Automation Patterns

Windows-MCP's `Type` tool **requires coordinates** (`loc`) or an element label — it errors with `"Either loc or label must be provided"` when called with just text.

### Pattern: Shortcut + Clipboard (when coordinates unknown)
```bash
# Instead of: mcp_windows_mcp_Type(text="text_here")  ← FAILS without loc
mcp_windows_mcp_Clipboard(mode="set", text="https://example.com")
mcp_windows_mcp_Shortcut(shortcut="ctrl+l")      # focus address bar
mcp_windows_mcp_Shortcut(shortcut="ctrl+v")      # paste
mcp_windows_mcp_Shortcut(shortcut="enter")       # go
```

### The `javascript:` Protocol Technique
For authenticated API calls from the browser (bypasses CORS, has cookies):
```bash
mcp_windows_mcp_Clipboard(mode="set", text="javascript:fetch('https://api.example.com/data',{credentials:'include'}).then(r=>r.json()).then(d=>document.body.innerHTML='<pre>'+JSON.stringify(d)+'</pre>')")
mcp_windows_mcp_Shortcut(shortcut="ctrl+l")
mcp_windows_mcp_Shortcut(shortcut="ctrl+v")
mcp_windows_mcp_Shortcut(shortcut="enter")
mcp_windows_mcp_Wait(duration=5)
mcp_windows_mcp_Scrape(use_dom=True, url="current")
```
The `javascript:` protocol runs in the current page's security context with full cookie access. Wrap in IIFE — address bar can't handle `const`/`let` statements directly.

## Verification

```bash
hermes mcp list
# Should show both 'windows-mcp' and 'jobs' (or other servers) as ✓ enabled

hermes mcp test windows-mcp
# Should show: ✓ Connected (XXms), ✓ Tools discovered: N
# Lists all available tools
```

Expected output:
```
Testing 'windows-mcp'...
  Transport: HTTP → http://...:8000/mcp
    Authorization: Bear***ret
  ✓ Connected (109ms)
  ✓ Tools discovered: 18
```

## Tools Available

After connection, Hermes registers 18 tools (Windows-MCP v3.3.1+):

| MCP Tool Name | Description |
|---------------|-------------|
| `mcp_windows_mcp_Click` | Left/right/middle click at coordinates, single/double/hover |
| `mcp_windows_mcp_Move` | Move mouse cursor to position, with drag support |
| `mcp_windows_mcp_Type` | Type text into active input, with clear/append/press-enter |
| `mcp_windows_mcp_Scroll` | Scroll vertically/horizontally |
| `mcp_windows_mcp_Shortcut` | Execute keyboard shortcuts (ctrl+c, alt+tab, win+r) |
| `mcp_windows_mcp_Snapshot` | Screenshot + UI tree (interactive elements, coordinates) |
| `mcp_windows_mcp_Screenshot` | Fast screenshot-first capture (no UI tree) |
| `mcp_windows_mcp_App` | Launch/switch/resize/close application windows |
| `mcp_windows_mcp_PowerShell` | Execute any PowerShell command |
| `mcp_windows_mcp_FileSystem` | Read/write/copy/move/delete/search files |
| `mcp_windows_mcp_Wait` | Pause execution N seconds |
| `mcp_windows_mcp_Scrape` | Fetch web page content as text |
| `mcp_windows_mcp_Clipboard` | Get/set clipboard content |
| `mcp_windows_mcp_Process` | List/kill running processes |
| `mcp_windows_mcp_Notification` | Send Windows toast notification |
| `mcp_windows_mcp_Registry` | Read/write/delete Windows Registry keys |
| `mcp_windows_mcp_MultiSelect` | Ctrl+click multiple elements |
| `mcp_windows_mcp_MultiEdit` | Fill multiple input fields at once |

## Example Hermes Session

```
User: "Open Notepad on Windows, type 'Hello from Hermes', and take a screenshot"

Hermes will:
1. mcp_windows_mcp_App(mode="launch", name="Notepad")
2. mcp_windows_mcp_Wait(duration=1)          # wait for app to open
3. mcp_windows_mcp_Type(text="Hello from Hermes")
4. mcp_windows_mcp_Snapshot(use_vision=True) # screenshot + describe
5. Return result to user
```

## Pitfalls & Edge Cases

- **URL path `/mcp` is required.** The config `url: "http://host:8000"` (without `/mcp`) returns 404. Must be `url: "http://host:8000/mcp"`.
- **Streamable-http needs `Accept: application/json, text/event-stream`.** The Hermes MCP client handles this automatically. Only relevant for manual curl testing.
- **Auth mismatch is silent.** If the `Authorization` header is wrong/absent, the server returns 401 but Hermes may not surface this clearly. Verify with `hermes mcp test` first.
- **Firewall blocking.** Windows Defender may block inbound port 8000. Run PowerShell as Admin: `New-NetFirewallRule -DisplayName "Windows-MCP" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow`
- **Admin elevation.** Apps running as Administrator cannot be controlled by a non-elevated Windows-MCP. Run Windows-MCP elevated if needed.
- **Server lifecycle.** The `Start-Process` approach from WSL creates a detached process that survives the calling shell. But it may die on WSL reboot or Windows restart. Use `windows-mcp install` for scheduled-task persistence.
- **System language.** Windows-MCP `app` tool requires English Windows display language for app name matching. Non-English systems may fail on `App(mode="launch", name="...")`.
- **First run timeout.** The initial `uvx windows-mcp` call takes ~1-2 min to install dependencies. The command may timeout — just restart it.
