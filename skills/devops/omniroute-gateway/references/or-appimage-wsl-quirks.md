# OmniRoute AUR AppImage on WSL2 — full failure transcript

Session date: 2026-07-25. Host: WSL2 (kernel sealed/signed-readonly, no FUSE module). Distribution: Arch (yay). User had previously installed via `npm i -g omniroute`, then **uninstalled npm and reinstalled via AUR `omniroute-bin`** (community-maintained, ships as an Electron AppImage wrapper). This reference captures the 4-layer failure chain that resulted, the exact diagnostics that pinpointed each layer, and the recommended exit path.

---

## TL;DR

The AUR package works fine on bare-metal Arch. **It cannot be made to work reliably on WSL2** because:

1. The package ships no systemd unit (must author your own).
2. WSL2 has no FUSE kernel module (can't mount AppImages; use `--appimage-extract`).
3. systemd user manager has no `$DISPLAY`, so Electron-ozone SEGVs (must wrap with `xvfb-run`).
4. Even after all that, the AppImage's embedded Node is 22.2.10 — too old for `node:sqlite` (≥22.5) and with no bundled `better-sqlite3`, leaving sql.js WASM as the only fallback; that warmup does not complete before the first HTTP request lands, producing `[DB] Nenhum driver SQLite disponível ... sql.js WASM ainda não foi pré-inicializado` and HTTP 500 on every endpoint.

**Conclusion: on WSL2 stay on the npm install path.** `npm install -g --allow-scripts=omniroute,better-sqlite3,... omniroute` populates a real `better-sqlite3` native binary and uses host Node 26.x (or whatever the user runs), which satisfies the `>=22.22.2 <23 or >=24 <27` policy in `src/shared/utils/nodeRuntimeSupport.ts`.

---

## Layer-by-layer breakdown with exact diagnostics

### Layer 1 — Orphan user unit, `status=203/EXEC`

After `yay -S omniroute-bin && systemctl --user enable --now omniroute.service`:

```
Failed to enable unit: Unit omniroute.service does not exist
```

We had previously removed `~/.config/systemd/user/omniroute.service` (the old npm-era unit); AUR ships no replacement. The user re-ran the install, which doesn't touch the user unit dir.

After manually writing the unit and pointing `ExecStart=/usr/bin/omniroute` (the AppImage wrapper):

```
● omniroute.service ... active (auto-restart)
   Process: 175638 ExecStart=/usr/bin/omniroute (code=exited, status=127)
   Failed at step EXEC spawning /usr/bin/omniroute: No such file or directory
```

Wait — `status=127` here actually meant **script exited 127**, not "file not found". The wrapper `/usr/bin/omniroute` *is* present:

```bash
$ cat /usr/bin/omniroute
#!/usr/bin/env bash
exec /opt/omniroute-bin/OmniRoute.AppImage "$@"
```

So `127` was the **AppImage's own exit code** when it couldn't mount itself. The journal confirms:

```
omniroute[175606]: Cannot mount AppImage, please check your FUSE setup.
omniroute[175606]: You might still be able to extract the contents of this AppImage
omniroute[175606]: if you run it with the --appimage-extract option.
```

→ **Diagnostic technique**: when systemd shows `status=127` always check `journalctl --user -u omniroute.service -n 20`. "File not found" and "script ran and exited 127" look identical in `systemctl status`.

### Layer 2 — WSL2 kernel has no FUSE module

```
Cannot mount AppImage, please check your FUSE setup.
See https://github.com/AppImage/AppImageKit/wiki/FUSE
```

WSL2 kernel is a Microsoft-built sealed/signed-readonly image. `apt install fuse` (or here pacman) gives you userspace tools (`fusermount`, `libfuse3`) but **not** `fuse.ko`. `modprobe fuse` returns no such target.

Workaround: extract manually.

```bash
cd /home/po                           # ❗ cwd must be user-writable; /opt/... fails
/opt/omniroute-bin/OmniRoute.AppImage --appimage-extract
# creates ./squashfs-root/AppRun + ./squashfs-root/omniroute-desktop (~219 MB)
```

Point systemd at the extracted `AppRun`:

```ini
ExecStart=/home/po/squashfs-root/AppRun
```

Note: do **not** point at `omniroute-desktop` directly — `AppRun` does `readlink -f "$0"` to discover APPDIR and `exec "$APPDIR/omniroute-desktop"`. Skipping AppRun breaks `NODE_PATH` resolution for the unpacked resources.

### Layer 3 — Electron ozone/x11 SEGV under systemd

After pointing ExecStart at `AppRun`, the unit restarted in `Active: activating (auto-restart)` with:

```
status=11/SEGV
[176506:...] ERROR:ui/ozone/platform/x11/ozone_platform_x11.cc:257 Missing X server or $DISPLAY
[176506:...] ERROR:ui/aura/env.cc:246 The platform failed to initialize. Exiting.
```

systemd's user manager doesn't export `$DISPLAY`. Electron's default ozone platform is X11. Fix:

```bash
command -v xvfb-run  # → /usr/bin/xxvfb-run
```

```ini
ExecStart=/usr/bin/xvfb-run -a /home/po/squashfs-root/AppRun
```

Now the unit goes `Active: active (running)`. Process tree:

```
xvfb-run
├── /bin/sh -c xvfb-run -a ...
├── Xvfb :99 -screen 0 640x480x24 -nolisten tcp
├── omniroute-desktop --type=zygote ...
├── omniroute-desktop --type=zygote ...
├── omniroute-desktop --type=gpu-process --ozone-platform=x11 ...
├── omniroute-desktop --type=utility ...network_service...
└── omniroute (v16.2.10)
```

Journal confirms Next.js boots:

```
[Electron] Starting Next.js server on port 20128
[Electron] Server NODE_OPTIONS: --max-old-space-size=4096
[Server] ▲ Next.js 16.2.10
[Server] - Local:    http://localhost:20128
[Server] ✓ Ready in 0ms
```

### Layer 4 — SQLite driver unavailable

But `curl localhost:20128/v1/models` returns:

```
HTTP 500, 21 bytes, body: "Internal Server Error"
```

and the journal contains the smoking gun:

```
[Server:err] [DB] Could not probe existing DB: [DB] Nenhum driver SQLite disponível
para '/home/po/.omniroute/storage.sqlite'. Chame ensureDbInitialized() no startup.
Drivers testados: better-sqlite3 (falhou), node:sqlite (indisponível).
sql.js WASM ainda não foi pré-inicializado.
```

OmniRoute has a documented 5-step SQLite fallback chain (`docs/ops/SQLITE_RUNTIME.md`):

1. Bundled `better-sqlite3` (installed by npm with `--allow-scripts`).
2. Runtime-installed `better-sqlite3` at `~/.omniroute/runtime/` (postinstall hook).
3. `node:sqlite` (Node ≥22.5 stdlib).
4. `sql.js` (WASM).
5. (Documented as a final fallback; details not relevant here.)

On the AppImage install:
- **Step 1 fails**: AUR packaging didn't `npm rebuild better-sqlite3` and didn't ship the `.node` binary.
- **Step 2 fails**: `~/.omniroute/runtime/` doesn't exist; the postinstall hook never ran (no `npm install` ever happened).
- **Step 3 fails**: The embedded Electron Node is **22.2.10** (verified via `process.versions.node`); `node:sqlite` shipped in 22.5.
- **Step 4 partly works**: `sql-wasm.wasm` is bundled at `resources/app/node_modules/sql.js/dist/sql-wasm.wasm`, but `warmUpRuntimes()` is lazy and does not complete before the first HTTP request lands.

### What about waiting?

We let the service run for 7+ minutes and curled `/v1/models` every 10 seconds for a minute. Still 500 every time. The `sql.js WASM ainda não foi pré-inicializado` log line never updated to a success line. The warmup either hangs or never runs — we could not determine which without instrumenting the code.

### Host Node vs AppImage Node — important to keep separate

```
$ node --version
v26.5.0           # host shell node — used by npm if you reinstall the npm version
```

The AppImage contains its own Node:

```
/home/po/squashfs-root/omniroute-desktop --version
... [Electron] Starting Next.js server on port 20128
```

Version comes from the Electron binary's embedded V8/Node ABI (~22.2.10). **This Node is the one OmniRoute's runtime must support.** If a user tries `npm rebuild better-sqlite3` from their shell, the resulting `.node` is built against the host's Node 26.x and **will not load** in the AppImage's Node 22.x.

### Why this isn't worth patching locally

Each workaround individually is small. The chain as a whole is fragile:

- Bypass FUSE → extract manually
- Bypass ozone crash → xvfb-run
- Repair SQLite → ???

There's no clean downstream fix for SQLite; the only solid repairs are upstream packaging changes (bundle `better-sqlite3` in the AppImage, or upgrade Electron's Node to ≥22.5). So on WSL we recommend **uninstalling `omniroute-bin` and re-installing via npm**:

```bash
# 1. tear down AUR packaging
yay -Rns omniroute-bin
sudo rm -rf /home/po/squashfs-root      # extracted dir
# 2. keep our hand-rolled unit; just point ExecStart back at npm binary
sed -i 's|ExecStart=.*|ExecStart=/home/po/.npm-global/bin/omniroute|' ~/.config/systemd/user/omniroute.service

# 3. npm install (with native-binding scripts!)
npm install -g --allow-scripts=omniroute,better-sqlite3,keytar,tls-client-node,onnxruntime-node,sharp,core-js,esbuild,@parcel/watcher,@swc/core,protobufjs,koffi omniroute

# 4. start
systemctl --user daemon-reload
systemctl --user restart omniroute.service
sleep 8
curl -o /dev/null -w "%{http_code}\n" http://localhost:20128/v1/models    # expect 200
```

---

## Verification matrix

| Symptom | Likely layer | Quick check |
|---|---|---|
| `code=exited, status=203/EXEC` | 1 (unit path wrong) | `journalctl --user -u omniroute.service -n 5` |
| `code=exited, status=127` + "Cannot mount AppImage" | 2 (FUSE) | `cat /usr/bin/omniroute`, look for AppImage message |
| `code=killed, signal=SEGV` + "Missing X server" | 3 (ozone) | `echo $DISPLAY` (will be empty in systemd) |
| All start lines OK but `/v1/*` returns 500 | 4 (SQLite) | `journalctl --user -u omniroute.service -n 30`; look for `[DB] Nenhum driver` |
| 200 on `/v1/models`, MCP says disabled | not our concern | see `references/or-mcp-curl-smoke.sh` |

## Files generated / referenced this session

- `~/.config/systemd/user/omniroute.service` — final state (xvfb + AppImage path). If you keep the AppImage install, this is what works for layers 1–3.
- `/home/po/squashfs-root/` — extracted AppImage contents, user-owned 700 tree, ~700 MB.
- `~/.omniroute/` — preserved (provider configs, audit logs, storage.sqlite, OAuth tokens, encryption key). All untouched across reinstalls.
- `~/.npm-global/lib/node_modules/omniroute/` — npm-era leftovers from the first install. Not used by AppImage; safe to remove after switching back via `npm rm -g omniroute`.
