---
name: vercel-deploy-diagnostics
description: Diagnose Vercel deployments — read build errors, list prod/preview status, query project settings via REST API. Use when production is broken, a GitHub commit triggered an ERROR build, or you need to inspect logs without the Vercel dashboard.
version: 1.0.0
tags: [Vercel, Deployment, CI/CD, Build-Errors]
---

# Vercel Deployment Diagnostics

Read-only debugging for Vercel-projected apps. Not for deploying. When a user's site breaks, a `gh` push triggers a yellow `ERROR` deployment, or you need to confirm "is production serving what I think it is" — this skill is the right entry.

## §Auth — Reuse the existing `vercel` CLI login

`vercel login` (via device OAuth) stores the token at `~/.vercel/auth.json`. Read it back for use as a Bearer token:

```bash
TOKEN=$(python3 -c "import json; print(json.load(open(os.path.expanduser('~/.vercel/auth.json')))['token'])")
# Note: requires `import os` first or use shell expansion:
TOKEN=$(python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/.vercel/auth.json')))['token'])")
```

Or just `vercel whoami` — confirms login and shows the user ID (e.g. `2631792752`).

**Do NOT re-trigger `vercel login`** if `~/.vercel/auth.json` already exists — the device flow will start again and need user interaction. If token is missing or expired, only then.

## §List Projects

```bash
TOKEN=$(python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/.vercel/auth.json')))['token'])")
curl -s -H "Authorization: Bearer $TOKEN" "https://api.vercel.com/v9/projects?limit=10" \
  | python3 -c "import sys,json; [print(p['id'], p['name'], p.get('framework','?')) for p in json.load(sys.stdin)['projects']]"
```

Note the project ID (`prj_...`). Most other endpoints need it as `projectId=<id>`.

For team-scoped projects: `?teamId=<team-slug>`. Vercel's `gh`-equivalent CLI: `vercel project ls`, but it's slow under timer so prefer the raw API.

## §List Deployments

```bash
TOKEN=$(...)
PROJ="prj_<your-project-id>"

# Production only
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.vercel.com/v6/deployments?projectId=$PROJ&limit=10&target=production" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for x in d['deployments'][:10]:
    sha = x.get('meta',{}).get('githubCommitSha','?')[:12]
    state = x.get('state','?')
    err = x.get('errorCode','-')
    print(f\"  state={state:10} sha={sha:12} err={err}\")
"
```

States you'll see:
- `READY` — running, served to users
- `BUILDING` — building
- `ERROR` — build failed (read `errorMessage` + `errorCode`)
- `CANCELED` — manually canceled or superseded
- `QUEUED` — waiting

The errorCode is the high-level category. **Read `errorMessage` and the events log for the actual stack trace** — errorCode alone is not enough.

`errorMessage` often contains the user's last terminal-line error verbatim (e.g. `Command "yarn run build" exited with 1`). To get the full log:

```bash
TOKEN=(...)
DID="dpl_<id>"  # from deployments.uid field, NOT from the GitHub deployment ID

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.vercel.com/v1/deployments/$DID/events" > /tmp/events.json

# Filter to error lines
python3 << 'PY'
import json
d = json.load(open('/tmp/events.json'))
for e in d:
    if not isinstance(e, dict):
        continue
    txt = e.get('text','') or ''
    if any(k in txt for k in ['module', 'Cannot find', 'MODULE_NOT_FOUND', 'Error:', 'error ', 'Failed', 'TypeError']):
        print(f'--- [{e.get("type","?")}] ---')
        print(txt[:1500])
PY
```

Don't pipe the events to head — events can be 1000+ lines and the real error is often near the end.

## §Is production serving my code?

Don't trust the GitHub-side "production deployment succeeded" check alone. Confirm the live URL:

```bash
curl -sLI https://your-site.example.com 2>&1 | grep -E "HTTP|x-vercel-cache|content-type"
```

A site whose `x-vercel-cache: STALE` is fine (cached), `MISS` is fresh-rebuilt. If `server: Vercel` is missing, you're not hitting Vercel. To find the deployment serving the live domain, walk back via `deployment.aliasAssigned` in the deployments list — the READY one with `target=production` and matching alias.

## §When Vercel data is insufficient

The `vercel inspect` CLI gives a deeper read of a single deployment:

```bash
vercel inspect dpl_<id> --logs
```

But `vercel inspect` is interactive and slow. Use it only when API log was incomplete.

## §Common errorCode meanings

| errorCode | Means | Where to look |
|-----------|-------|---------------|
| `module_not_found` | npm/yarn install or build couldn't resolve | events log: `Cannot find module 'X'` or `MODULE_NOT_FOUND` |
| `reference_error` | runtime variable undefined | events log: `ReferenceError: X is not defined` |
| `build_failed` | generic build fail | events log: most useful first line is `errorMessage` |
| `lambda_compressed_size_exceeded` | bundle > 50MB | check if a new huge dep was added |
| `forbidden` / `unauthorized` | deployment protection on | check project settings: `vercel project ls` shows `passwordProtection` |
| `no_free_inode` / `out_of_memory` | infra issue | rare; retry once before debugging |

## §Pitfalls

- **GitHub-side "Deployment has failed" status comes from Vercel's webhook, not the same thing as the API deployments list.** The GitHub `gh run view <id>` / `gh api repos/<owner>/<repo>/deployments/<id>/statuses` may show "failure" while the actual Vercel deployment status is still `BUILDING`. Trust the Vercel API over the GitHub status.
- **Preview URLs behind Vercel SSO** are not publicly cURL-able. `vercel login` then accessing the URL from your session is the only path. Don't waste time curl-ing preview URLs to inspect them.
- **Don't `vercel deploy` from a session accidentally.** The CLI sits on its token and will deploy whatever you point at. If the user asks for diagnostics, do not switch into deploy mode without confirmation.
- **`vercel logs --follow` is a long-running command** — use `process(background=true)`, not foreground.

## §Quick Reference

| Action | Command |
|--------|---------|
| Confirm login | `vercel whoami` |
| List projects | `curl -H "Authorization: Bearer $TOKEN" 'https://api.vercel.com/v9/projects?limit=10'` |
| List prod deployments | `...v6/deployments?projectId=$PROJ&limit=10&target=production` |
| Get deployment log | `...v1/deployments/$DID/events` |
| Inspect single build | `vercel inspect $DID --logs` |
| Promote preview to prod | (UI: open URL → Promote to Production button) |
| Trigger redeploy | `vercel deploy --prod` (only with user confirm) |
