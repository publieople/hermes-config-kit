---
name: dsh-deepseek-harness-ops
description: Operate dsh on WSL systemd — boot, autostart, market proxy.
---

# DeepSeek Harness (dsh) operations

DeepSeek Harness (`dsh`, installed at `~/.npm-global/bin/dsh`, versioned e.g. `0.1.1-rc.2`) is a Cordis-based agent harness. On this box it runs as a **user systemd service** (`~/.config/systemd/user/dsh-web.service`), web UI on `127.0.0.1:3080`. WSL user manager has `Linger=yes`, so it starts at boot without any login session.

## The three recurring failure modes (and root causes)

### 1. `dsh web` exits instantly when launched from Hermes/background/non-TTY shell
`dsh` boot loads a `dsh-tui` plugin (`@deepseek-harness-tui/dsh-tui`) which refuses to load unless `process.stdout.isTTY`:
```
Error: dsh-tui requires an interactive terminal (stdout must be a TTY).
```
Only visible with `pty=true` in Hermes — with `background=true` (no TTY) the process dies silently and the error is swallowed.

**Fix (permanent):** disable `dsh-tui` via the profile patch layer `~/.dsh/profiles/web/cordis.patch.yml`:
```yaml
- id: dsh-tui
  disabled: true
```
`dsh web --dump-config` shows entry ids (`- id: dsh-tui`). This is the documented seam ("Edit cordis.patch.yml, not cordis.yml").

### 2. Plugin market "插件目录加载失败，稍后重试 / The operation was aborted due to timeout (30s, 2 attempts)"
dshmarket fetches its catalog from `https://awesome-dsh-plugin.com/plugins.json`. Two traps:
- **Node's global `fetch` IGNORES `HTTP_PROXY`/`HTTPS_PROXY` entirely.** dshmarket's `marketFetch` (in `node_modules/dshmarket/lib/net.js`) deliberately routes through undici's `EnvHttpProxyAgent` — but ONLY when those env vars are present (`configuredProxy()` reads them). Unset → falls back to bare global `fetch` (direct connection).
- **systemd user services do NOT inherit exported proxy env from your shell.** The service runs with only the env you hardcode via `Environment=`.

So a service started from an interactive shell that happens to have proxy env exported works; one started by systemd with no `Environment=` lines has neither proxy nor a reliable direct route and times out.

**Fix:** add to `~/.config/systemd/user/dsh-web.service`:
```
Environment=HTTP_PROXY=http://127.0.0.1:7890
Environment=HTTPS_PROXY=http://127.0.0.1:7890
```
then `systemctl --user daemon-reload && systemctl --user restart dsh-web`. Env is read once at process start.

**Verify** without screenshotting the UI — hit the registry endpoint directly:
```
curl -sS http://127.0.0.1:3080/dsh-market/registry -w "%{http_code} %{time_total}s\n"
# expect 200, fast — ~0.4s — and a JSON blob with "count":1884
```
The catalog is fetched fresh (no bundled fallback) — network failure returns HTTP 502 with the message, matching the UI error.

### 3. Duplicate enabled services → EADDRINUSE crash loop
Two units had both been `enabled` against `default.target` (`dsh.service` old + `dsh-web.service` new); both try port 3080. The loser restarts forever with `listen EADDRINUSE`. A shell-launched orphan can also hold the port and starve systemd.

**Fix:** inspect `systemctl --user is-enabled <unit>`, remove the stale unit's symlink + file, `daemon-reload`, confirm only one `enabled`. Kill any orphan `node .../dsh web` not owned by systemd before checking status.

## Diagnostic order (fastest first)
1. `curl -sS -o /dev/null -w "%{http_code}\n" --max-time 3 http://127.0.0.1:3080/` — is it even up?
2. `systemctl --user is-active dsh-web; systemctl --user is-enabled dsh-web`
3. `journalctl --user -u dsh-web -n 30 --no-pager` — crash reason (EADDRINUSE vs plugin-load vs TTY)
4. `ss -tlnp | grep 3080` + `lsof -i :3080` — who holds the port (orphan node vs systemd)

## Health commands
```bash
systemctl --user status dsh-web --no-pager    # active/running + Main PID
loginctl show-user po | grep Linger           # must be yes for boot autostart
```

## Support files
- `references/node-proxy-and-systemd-env.md` — the Node-fetch-ignores-proxy lesson generalized (any service whose child reads HTTP_PROXY from env, not as `Environment=`).
- `references/cli-plugin-add-failures.md` — three traps when `dsh plugin add` fails: pnpm-store version, lockfile `resolution: {integrity}` missing for GitHub-release tarballs, and `dsh plugin` CLI not forwarding `RELEASE_AGE_OVERRIDE` (with the `AbortSignal.timeout(string)` landmine).

## Pitfalls
- `dsh web` from Hermes `background=true` dies silently (no TTY). Use `pty=true` for a one-shot foreground check.
- Proxy env is read at process start; `export` after start (or `systemctl restart` without env) won't help. Confirm via `/proc/<pid>/environ`.
- `cordis.patch.yml` uses `!!js` for expressions — a `disabled: !!js !process.stdout.isTTY` YAML-parse error was hit ("duplication of a tag property") — use plain `disabled: true`.
- Don't strip `--no-open` in systemd ExecStart or the server tries to launch a browser.
- **`dsh plugin add` errors are deceptively generic ("pnpm failed").** Three independent root causes (store version, lockfile integrity, missing CLI override) all surface the same exit. See the reference for triage — start with `pnpm --version` and `grep '^    resolution:' pnpm-lock.yaml | grep -v integrity`.
- **`--config.fetchTimeout=<ms>` in pnpm 11 traps you** — pnpm passes the value as a string to `AbortSignal.timeout()`, which throws `ERR_INVALID_ARG_TYPE` and retries forever. Do not add this flag to override lists; pnpm's default 60s is fine.
- **`dsh plugin` CLI gap vs dshmarket UI:** `bin.js` does not forward `--config.minimumReleaseAge=0`. UI routes do (see `dshmarket/src/install.ts`). CLI users get hit by `pnpm-workspace.yaml`'s 1-day cutoff. Until upstream patches this, `bin.js` needs a local override (see reference).

## Pitfalls
- `dsh web` from Hermes `background=true` dies silently (no TTY). Use `pty=true` for a one-shot foreground check.
- Proxy env is read at process start; `export` after start (or `systemctl restart` without env) won't help. Confirm via `/proc/<pid>/environ`.
- `cordis.patch.yml` uses `!!js` for expressions — a `disabled: !!js !process.stdout.isTTY` YAML-parse error was hit ("duplication of a tag property") — use plain `disabled: true`.
- Don't strip `--no-open` in systemd ExecStart or the server tries to launch a browser.