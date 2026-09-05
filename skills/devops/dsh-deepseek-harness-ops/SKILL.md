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

### 4. Browser "bundle script /plugins/<pkg>/client.js?rev=… failed to load" — the named plugin is usually innocent
`dsh-client-modules` loads every client bundle via `<script src="/plugins/<id>/client.js?rev=<sha1-12>">`; a script `error` event (HTTP 404/connection refused) surfaces as `client-modules: bundle script … failed to load` and the UI blames the first plugin in the boot manifest. The `/plugins/*` route 404s when `clientPath` isn't in the registry — which happens when **host boot died earlier on another plugin's import error**, so nothing got registered. The rev is `sha1(bundle).slice(0,12)`; verify the bundle itself is fine by hashing `lib/client.js` — if it matches the URL's rev, stop suspecting that plugin.

**Fix:** reproduce host-side to see the real exception:
```bash
cd ~/.dsh/profiles/web && timeout 30 dsh web --host 127.0.0.1 --port 3081 --no-open
# look for: "plugin tree failed to load: failed to import loader entry <id> (<pkg>): <real error>"
```
Observed root cause: a plugin linked into the profile (`node_modules/@scope/pkg -> /home/user/projects/pkg`) whose `lib/index.js` imports a peer dep (`@deepseek-ai/schemastery`) — pnpm's strict layout resolves a linked package's peers against its **real path**, not the profile's node_modules, so the peer is invisible.

**Verified fix paths (2026-08-31):**
- `dsh plugin --profile web add link:<path>` — **does NOT fix it**. pnpm 11 `link:` is a pure symlink, no peer wiring, same error after reinstall.
- Working: symlink the missing peers into `<project>/node_modules/` yourself. Profile root only has `@deepseek-ai/{cordis,schemastery,cosmokit}`; the rest (`dsh-settings`, `dsh-host-webserver`, `dsh-client-runtime`, `dsh-client-ui-settings`, `dsh-client-locale`, `dsh-web`, …) live under the global dsh install: `~/.npm-global/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/<pkg>`. Link the whole peerDependencies list in one pass — fixing one at a time just surfaces the next.
- Verify by actually booting and curling the bundle, not just process-alive: `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:<port>/plugins/<@scope>/<pkg>/client.js` → 200. dsh web needs a TTY; under Hermes `background=true` it dies silently, wrap with `execute_code` + `subprocess.Popen(..., start_new_session=True)` to health-check.

### 5. dsh 升级到 0.1.2-rc.x 后 linked 插件 `disabled: true` 也炸 boot（"plugin(s) failed to load: <name>, <name>"）
新版 dsh-app-boot 的 `assertEntriesLoaded` 审计所有 fiber 为空的 entry；linked 插件（`link:` dep）在升级后 fiber 永远为空，**即使 patch 里 `disabled: true` 也一样**（dump-config 显示 entry 正常、disabled 生效，但 boot 仍 reject，且名字重复出现两次）。这不是配置写错，是上游 loader 回归。

**Fix（2026-09-05 验证）：** 别试图在 cordis.patch.yml 里 disable —— 直接把插件从 `~/.dsh/profiles/<profile>/package.json` 的 `dependencies` 和 `dsh.profile.bundles` 两处删掉，再删掉 patch 里对应的 disabled entry。`dsh web` 试 boot 验证。

**同类：** `@nanmicoder/dsh-agent-teams` ≤0.1.15 调 `ctx.subagents.registerContinuableSetup`（新版 dsh 已移除）——同样必须整个移除，patch disable 无效。升级 dsh 后所有第三方 bundle 都要按这个模式过一遍：boot 挂 → 看 journal 里 "failed to apply loader entry <id>" → 从 package.json 两处删掉。

**同类：** 两个插件注册同一个 webserver 路由前缀也会整个炸 boot（`webserver: duplicate prefix route "<prefix>"`，例：套件包里的子插件与 `dsh-better-sidebar` 同抢 `/sidebar/api`）——无法 disable 其一绕过，同样整个移除冲突的那方。另外手动 `dsh web` 测试实例与 systemd 实例共用 `$DSH_HOME` 会触发 `dsh-im-gateway 检测到另一个 DSH 进程…并发写坏 session log` —— 测试 boot 必须设独立 `DSH_HOME`。

**同类：** 插件 import 的命名导出被新版 dsh 子包删掉（`The requested module '@deepseek-ai/<pkg>' does not provide an export named '<x>'`）——不是配置问题，是插件版本 < dsh 版本。查该插件 npm 新版是否已修（`npm view <pkg> peerDependencies` 看 range 是否覆盖当前 dsh 版本），有就升，没有就移除。例：dshmarket ≤1.36 import `installSettingsSection`（dsh-settings 0.1.2 已删），1.37+ 修好。

**pnpm `minimumReleaseAge` 拦截：** pnpm 11 该策略会拒装/拒验证最近发布的包，报错 `was published at ... within the minimumReleaseAge cutoff`，且 `pnpm config get` 各处都显示 undefined（来源不明，行为在）。一次性绕过：`pnpm install --config.minimumReleaseAge=0`（此 flag 是 dshmarket 自己的 `RELEASE_AGE_OVERRIDE` 用的同一个，安全）。

**link: 插件的 peer symlink 会在 profile `pnpm install` 后失效**——peer symlink 若指向 profile 的 `node_modules/@deepseek-ai/<pkg>`，重装即被清。一律指向全局 dsh 安装目录 `~/.npm-global/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/<pkg>`（随 dsh 本体存在，稳定）。

### 6. "401 authentication required" ≠ 坏了 —— token 是一次性登录，不是每次都要
用户报"又进不去了"时先区分 401 和 crash loop：`curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3080/` 返回 **401 表示服务健康**（只是要登录），别去翻 plugin 错误。dsh-client-connection 的认证流程：launch token 只在 `GET /` 被接受一次，验证后签发 **30 天有效**的签名 cookie（`cookieMaxAgeDays: 30`，密钥存 `~/.dsh/.credentials.yaml`，重启不变），然后 302 到干净的 `/`。所以正确姿势是带 token 开一次 → 之后收藏裸 `http://127.0.0.1:3080/`。需要重登的触发条件只有：cookie 过期（30 天）、清了浏览器 cookie、删了 `.credentials.yaml`。不要建议关认证——它是防 DNS rebinding 的唯一屏障。取当前 token 一行：`journalctl --user -u dsh-web --no-pager | grep "dsh web: http" | tail -1 | grep -oP 'http\S+'`。

## Diagnostic order (fastest first)
0. **先分清 401 vs crash**：`curl -sS -o /dev/null -w "%{http_code}\n" --max-time 3 http://127.0.0.1:3080/` 返回 401 = 服务健康（只是要登录），问题在 token/cookie，不翻 plugin 错误；000/拒绝连接 = 真崩了，继续往下。
1. `curl ...`（同上）— is it even up?
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