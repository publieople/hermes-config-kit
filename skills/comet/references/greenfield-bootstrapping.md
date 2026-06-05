# Greenfield Project Bootstrapping with Comet

When applying the comet workflow to a **brand-new project** (no existing repo, no openspec init), follow this fallback path:

## Manual Artifact Template

```
<project-root>/
├── openspec/
│   ├── changes/
│   │   └── <change-name>/
│   │       ├── .openspec.yaml     # id, name, status, created_at, schema
│   │       ├── .comet.yaml        # <-- see schema below, NOT arbitrary fields
│   │       ├── proposal.md        # Problem, Goal, Scope, Non-goals
│   │       ├── design.md          # Architecture, decisions, data flow
│   │       └── tasks.md           # Checklist with task items
│   └── config.yaml               # Optional project-level config
├── docs/superpowers/
│   ├── specs/                    # Design docs (YYYY-MM-DD-topic.md)
│   └── plans/                    # Implementation plans
└── src/ etc.
```

## .comet.yaml Schema (Required by Guard Validator)

The `comet-yaml-validate.sh` script recognizes **only** these fields. Extra fields like `change`, `base_ref`, `tasks` are flagged as warnings and accepted but not semantically useful. Missing required fields cause the guard to **fail**.

### Required Fields

```yaml
workflow: full              # full | hotfix | tweak
phase: open                 # open | design | build | verify | archive
design_doc: ""              # path relative to project root; EMPTY at design start
plan: ""                    # path to implementation plan; can be empty
build_mode: ""              # subagent-driven-development | executing-plans | direct
isolation: ""               # branch | worktree
verify_mode: ""             # light | full
verify_result: pending      # pending | pass | fail
verified_at: ""             # ISO timestamp of verification pass
archived: false             # true | false
```

### Optional Fields

```yaml
branch_status: pending      # pending | handled
direct_override: false      # true | false (full workflow needs this for build_mode: direct)
build_command: ""           # project build command guard runs
verify_command: ""          # project verification command guard runs
```

### CRITICAL: design_doc Path Resolution

The guard validates `design_doc` path **relative to the working directory** (project root), NOT relative to the change directory. Example:

```yaml
# ✅ Correct — relative to project root
design_doc: docs/superpowers/specs/2026-06-01-topic-design.md

# ❌ Incorrect — relative to change dir, guard will say "does not exist on disk"
design_doc: ../../../docs/superpowers/specs/2026-06-01-topic-design.md
```

### Design Phase Entry Check: design_doc Must Be Empty

Before entering the **design** phase, `bash $COMET_STATE check <name> design` verifies that `design_doc` is empty/null. This is because the design phase is supposed to **produce** the design doc, not reference an existing one.

**Workflow:**
1. Open phase: set `design_doc: ""` initially (or omit — empty is the default)
2. Open → guard `--apply` passes, state advances to `phase: design`
3. Design phase starts: run entry check — OK because design_doc is empty
4. Create the actual design doc at `docs/superpowers/specs/YYYY-MM-DD-topic-design.md`
5. Set `design_doc` path: `bash $COMET_STATE set <name> design_doc "docs/superpowers/specs/..."`  
6. Run guard `--apply` to advance to build phase

## Phase Advancement Without openspec CLI

```bash
# Initialize state (only if .comet.yaml does NOT already exist)
bash $COMET_STATE init <change-name> full

# If .comet.yaml already exists (created manually), set phase directly:
bash $COMET_STATE set <change-name> phase <open|design|build|verify>

# Check entry conditions for a phase
bash $COMET_STATE check <change-name> design

# Guard check with auto-advance
bash $COMET_GUARD <change-name> <phase> --apply

# Semantic transition (alternative to --apply)
bash $COMET_STATE transition <change-name> open-complete
```

## Pitfalls

- **openspec CLI not required** — the state/guard scripts operate on `.comet.yaml` directly; they work without openspec installed
- **Scaffolding first** — create the Vite/project scaffold before setting comet state, so the project directory exists for the openspec directory
- **`--apply` still works** — run guard with `--apply` to auto-advance phase after guard checks pass
- **No existing git ref** — for `base-ref` in build plan, use `git rev-parse HEAD` after the first commit; if no commits exist, leave it blank and set it after `git init && git add && git commit`
- **Do NOT use `init` if `.comet.yaml` already exists** — `bash $COMET_STATE init` will error. Use `bash $COMET_STATE set <name> phase <phase>` instead
- **design_doc path must be relative to project root** — see path resolution section above
- **design_doc must be empty at design phase entry** — the check enforces this; set it only after writing the design doc
- **`tasks` is NOT a recognized field** in .comet.yaml — project guard yaml-validate will warn about it. Use tasks.md instead, referenced in `plan:` or kept as a standalone file

## WSL Background Process Workaround (Uvicorn)

When running the **greenfield project's backend server** as a background process during build verification, the default Hermes `terminal(background=true)` may fail on WSL with:

```
bash: 无法设定终端进程组 (-1): 对设备不适当的 ioctl 操作
bash: 此 shell 中无任务控制
```

**Root cause:** Hermes's bash wrapper cannot create process groups for background jobs in this WSL environment. Every background process goes through the same bash wrapper, so `terminal(background=true)`, `&` in foreground, `nohup`, `disown`, and `setsid` all fail with the same error.

**Fix:** Run the server inside a **single foreground** `timeout bash -c '...'` command with the server launched via `&` inside the `-c` string. The outer foreground process is `timeout`, which Hermes can track; the inner `&` is invisible to Hermes's process guard.

```bash
# ✅ Works — server runs inside timeout, tested via curl, killed on exit
timeout 120 bash -c '
.venv/bin/uvicorn brain_game.main:app --host 127.0.0.1 --port 8002 &
SPID=$!
sleep 3
curl -s http://127.0.0.1:8002/api/health
echo ""
# Optionally start frontend dev server in same session:
cd ../frontend && node ./node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 &
sleep 2
wait
'
```

**Caveats:**
- The server stops when `timeout` expires. Use a generous timeout value.
- `Ctrl+C` kills both server and client (they share the same PID namespace).
- For persistent development, **start uvicorn in a dedicated terminal** (outside Hermes).

## FastAPI SPA Catch-all Routing Quirks

When serving a React SPA from FastAPI (single-port production), the catch-all route `/{full_path:path}` must be registered **last** — after all API routes and health checks — or it will intercept them first.

**Correct pattern:**

```python
# 1. API routes (registered first — FastAPI matches in order)
app.include_router(api_router)

# 2. Health check routes
@app.get("/")
async def root():
    return {"status": "ok"}

# 3. SPA fallback (registered LAST — catches only unmatched paths)
SPA_INDEX = STATIC_DIR / "index.html"
if SPA_INDEX.exists():
    @app.api_route("/{full_path:path}", methods=["GET"])
    async def serve_spa(full_path: str):
        frontend_routes = ("play/", "dashboard", "favicon", "icons")
        if full_path.startswith(frontend_routes):
            return FileResponse(str(SPA_INDEX))
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Not found"}, status_code=404)
```

**Key insight:** Unlike `app.mount()` which has its own priority, `@app.api_route("/{full_path:path}")` uses Starlette's `path` converter, which matches **every** path including `/api/health`. It only works as a fallback because Starlette checks routes in registration order — specific routes registered before the catch-all win.

**Pitfall:** The `full_path` parameter for root `/` is `""` (empty string), so the handler must handle this case. In the pattern above, `"".startswith(frontend_routes)` is `False`, so root requests return 404 correctly — the real root handler registered in step 2 handles them first.

## Vite 8 Build Quirks

When the greenfield project uses **Vite 8** (Rolldown bundler), note these differences from earlier Vite versions:

- **Manual chunks**: `build.rollupOptions.output.manualChunks` does NOT work in Vite 8. Use `build.rolldownOptions.output.manualChunks` as a **function**, not an object:
  ```typescript
  build: {
    rolldownOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/react')) return 'vendor-react'
        },
      },
    },
  }
  ```
- **Build command**: Running `npx vite build` may be detected as a long-lived process by the agent session manager. Use the direct node path as a reliable fallback:
  ```bash
  node ./node_modules/vite/bin/vite.js build
  ```
- **Code splitting recommended**: Without manualChunks, Vite 8 produces a single ~2.3MB JS chunk that exceeds PWA's default 2MB cache limit. Add manualChunks and raise the PWA limit:
  ```typescript
  VitePWA({
    workbox: { maximumFileSizeToCacheInBytes: 4 * 1024 * 1024 }
  })
  ```

## npm 11 Package Resolution Quirks

npm 11 (shipped with Node 26) has a critical bug: **devDependencies listed in package.json are silently skipped** during `npm install`. They appear in the resolved `package-lock.json` manifest but their directories are **not created** in `node_modules/`. Affected packages observed: `typescript`, `vite`, `@vitejs/plugin-react`, `tailwindcss`, `@tailwindcss/vite`, eslint, and all `@types/*` typings.

**Detection:**
```bash
npm ls <pkg>     # shows "(empty)"
ls node_modules/<pkg>   # directory not found — 3-5 deps only (react, react-dom, scheduler)
```

### ❌ Workarounds That DID NOT Work

None of these resolve the devDeps bug — tested on npm 11.14.1 + Node 26.2.0 on Arch WSL:

- `npm install --install-strategy=nested` — still 3 packages
- `npm install --install-strategy=hoisted` — still 3 packages
- `npm install --legacy-peer-deps` — still 3 packages
- `npm install --no-cache` — still 3 packages
- `npm install --prefer-online` — still 3 packages
- `npm install --include=dev` — still 3 packages (npm 11 ignores this)
- `node-linker=hoisted` in `.npmrc` — "Unknown project config" warning, no effect
- `npm config set cache <new-path>` + clean reinstall — no effect
- `npm install -D <pkg>@<version>` — claims "up to date, audited N packages" but directory never created
- `npm cache clean --force` — no effect (resolved lockfile is correct, install pass just doesn't run)
- Using `npx -p npm@10 npm install` — 17 packages instead of 3, but still far short of 50+ (lockfile corrupted from initial npm 11 resolution)
- Creating a fresh project (`npm init` in new temp dir) with packages as dependencies works fine — confirming the bug is specifically about devDependencies vs dependencies, not about npm 11's resolution capability entirely

### ✅ Working Fix: Move All Packages to `dependencies`

**Root cause:** npm 11@11.14.1 (Arch Linux) does not physically install `devDependencies` into `node_modules/`, even with `--include=dev`. The resolution pass succeeds (package-lock.json is correct), but the install pass silently skips them.

**Fix:**

1. **Delete all cached state:**
   ```bash
   rm -rf node_modules package-lock.json .package-lock.json .npmrc
   ```

2. **In `package.json`, merge all `devDependencies` into `dependencies`:**
   ```json
   {
     "dependencies": {
       "react": "^19.2.6",
       "react-dom": "^19.2.6",
       "vite": "^8.0.12",
       "typescript": "^5.8.3",
       "tailwindcss": "^4.1.6",
       "@tailwindcss/vite": "^4.1.6",
       "@vitejs/plugin-react": "^6.0.1",
       "@types/react": "^19.2.14",
       "@types/react-dom": "^19.2.3",
       ...
     }
   }
   ```

3. **Install:**
   ```bash
   npm install
   ```
   Expected: ~50+ packages installed instead of ~3.

4. **Verify:**
   ```bash
   ls node_modules/ | wc -l     # should be 50+
   npx vite build               # or: node ./node_modules/vite/bin/vite.js build
   ```

**Caveat:** This bypasses npm's production/development separation. In CI/CD or Docker builds, use `npm install --production` cautiously — all packages are `dependencies` so nothing gets pruned. For a cleaner separation, you can split them back out once the ecosystem updates past this bug, or pin an older npm version.

### Create-Vite Scaffold Note

The `npm create vite@latest . --template react-ts` command generates a `package.json` with tooling in `devDependencies`. On npm 11, this produces a broken lockfile. **Always merge devDeps → deps immediately after scaffolding, or use `npm init` → manually add packages instead.**

### Vite IPv6 Binding on WSL

On WSL, Vite's dev server may bind to `[::1]:5173` (IPv6 localhost) by default instead of `127.0.0.1` (IPv4). Browsers accessing `localhost:5173` resolve via IPv4 and fail to connect silently.

**Fix**: Explicitly set `host` in Vite config:
```typescript
// vite.config.ts
server: {
  host: '127.0.0.1',   // Force IPv4 — required on WSL
  port: 5173,
}
```
**Also fix the proxy target** — use `127.0.0.1` instead of `localhost` to avoid IPv6 resolution ambiguity:
```typescript
proxy: {
  '/api': { target: 'http://127.0.0.1:8010', changeOrigin: true },
  '/ws':  { target: 'ws://127.0.0.1:8010', ws: true },
}
```

## React 19 + Legacy JS Libraries

When a vanilla JS library's React wrapper has a peer dependency on an older React version (e.g. `@toast-ui/react-image-editor` requires React 17 but the project uses React 19):

1. **Install the vanilla JS library directly** (skip the React wrapper):
   ```bash
   npm install --legacy-peer-deps tui-image-editor
   ```
2. **Write a custom React wrapper** using `useRef` + `useEffect` to mount/destroy the library instance
3. **Handle lifecycle**: destroy the instance on unmount, revoke blob URLs, clean up event listeners
4. **Example pattern**:
   ```typescript
   const containerRef = useRef<HTMLDivElement>(null);
   const editorRef = useRef<EditorInstance | null>(null);
   useEffect(() => {
     if (!containerRef.current) return;
     const editor = new EditorClass(containerRef.current, { ... });
     editorRef.current = editor;
     return () => { editor.destroy(); editorRef.current = null; };
   }, [file.id]);
   ```
