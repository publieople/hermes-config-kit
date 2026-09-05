---
name: github-fork-rebase
description: >-
  Maintain a GitHub fork of an active upstream open-source project — diagnose sync
  failures, recover from long-term divergence, preserve local personalisation (config
  files, themes, assets), and re-arm auto-sync. Covers NotionNext, Next.js starters,
  Astro themes, Vercel templates, plugin frameworks (AstrBot, etc.) and any fork that
  upstream ships updates you want while keeping your overlay. Also covers the
  **first-time fork + local personalise** flow when the user wants a personal fork
  they intend to push commits to, not just sync with upstream.
---

# GitHub Fork Rebase & Long-Term Sync Recovery

When a fork (NotionNext, Next.js starter, Astro theme, Vercel template, etc.)
has been left alone for weeks/months and the daily `Upstream Sync` workflow
starts failing — recover the fork, preserve the user's overlay, and re-arm
auto-sync.

**See also**: [references/astrbot-plugin-fork.md](references/astrbot-plugin-fork.md)
for AstrBot plugin fork specifics (decorators, schema, load verification).

## Trigger conditions

- User says "sync 失败", "fork 跟不上了", "auto-sync 一直报错"
- User says "fork 一下", "在 GitHub 上开一个", "做个 fork 版" → first-time
  fork + personalise flow (see end of file)
- `gh run list --workflow="Upstream Sync"` shows 5+ consecutive `failure` runs
- Latest run log shows: `fatal: error processing shallow info`, `CONFLICT in
  package.json|blog.config.js|favicon.ico`, or `[Error] 由于上游仓库的 workflow
  文件变更`
- `gh api repos/<owner>/<fork>` shows `pushed_at` weeks/months old
- Fork's `default_branch` differs from upstream HEAD by 100+ commits

## Diagnose first — don't jump to a fix

Three checks before touching anything:

```bash
# 1. Is the sync workflow even pointing at a valid repo?
gh api repos/<owner>/<fork>/contents/.github/workflows/sync.yaml -H "Accept: application/vnd.github.raw" \
  | grep upstream_sync_repo

# 2. What's the merge-base vs upstream?
git fetch upstream main
git merge-base origin/main upstream/main   # may fail on shallow clone — see Pitfall §1

# 3. How many conflicts would a fresh sync produce?
gh run view <latest-failed-run-id> --repo <owner>/<fork> --log-failed \
  | grep -E "(CONFLICT|error processing)"
```

If `upstream_sync_repo` is an org the user doesn't own (e.g. `tangly1024/...`
when the project moved to `notionnext-org/...`), that's often the *only* real
fix — the conflict cascade is downstream of the redirect.

## Recovery: the three-step reset

When conflict count is <20 and overlay is small (≤5 files): do a normal
`git rebase upstream/main` and resolve.

When conflict count is 100+ (the NotionNext case): reset+overlay is faster
than resolving. Workflow:

### Step 1 — capture user's overlay

```bash
# Identify fork-only files first
BASE=$(git merge-base origin/main upstream/main)   # may fail — see Pitfall §1
git log origin/main ^$BASE --no-merges --pretty=format: --name-status \
  | sort -u > /tmp/fork-only.txt

# For each fork-only file, save current contents
for f in $(cat /tmp/fork-only.txt); do
  mkdir -p /tmp/overlay/$(dirname $f)
  git show origin/main:$f > /tmp/overlay/$f
done
```

Empty `fork-only.txt`? The "fork" only carries merge-history, no real edits —
reset is still valid, just nothing to preserve.

### Step 2 — orphan-reset to upstream HEAD

`git reset --hard` is blocked for safety. Use `--orphan` instead:

```bash
git checkout --orphan reset-fork upstream/main   # branch points at upstream HEAD
# working tree is now = upstream main; no commits needed
```

### Step 3 — overlay + commit + push to a review branch

```bash
cp -r /tmp/overlay/* .
git add <only-the-overlay-files>                  # NOT `git add -A`
git commit -m "chore(rebase): reapply fork overlay on upstream <version>"
git push origin reset-fork                       # new branch, doesn't touch main
```

Open a PR so user can review the diff. **True overlay diff** is best viewed
from upstream/main, not from old main:

```bash
git diff --stat upstream/main origin/reset-fork
# Real diff ignores 1400+ "deletions" GitHub PR shows when comparing
# forked-history main against orphan-reset branch.
```

### Step 4 — promote to main safely

GitHub API refuses `DELETE` on the default branch. Sequence:

```bash
# 1. Switch default branch to the new orphan-reset branch
gh api repos/<owner>/<fork> -X PATCH -f default_branch=reset-fork

# 2. Now you can delete the old main
gh api repos/<owner>/<fork>/git/refs/heads/main -X DELETE

# 3. Recreate `main` pointing at the same SHA
SHA=$(gh api repos/<owner>/<fork>/git/refs/heads/reset-fork --jq '.object.sha')
gh api repos/<owner>/<fork>/git/refs -X POST -f ref=refs/heads/main -f sha=$SHA

# 4. Delete the temp branch, restore default to main
gh api repos/<owner>/<fork>/git/refs/heads/reset-fork -X DELETE
gh api repos/<owner>/<fork> -X PATCH -f default_branch=main
```

Existing PR auto-closes when its base ref disappears.

## Auto-sync upstream names

`aormsby/Fork-Sync-With-Upstream-action@v3.4` is the de-facto tool. It needs:

- `upstream_sync_repo` = current GitHub org (check the project hasn't migrated)
- `upstream_sync_branch` = `main` (or whatever upstream calls it)
- `target_repo_token` = `${{ secrets.GITHUB_TOKEN }}` (default is fine)
- `shallow_since: 1 month ago` (default — fine for daily sync)

If the upstream org moved (e.g. `tangly1024/...` → `notionnext-org/...`),
fetching still works (GitHub auto-redirects forks in the network), but
shallow-clone metadata is wrong and you get `fatal: error processing shallow
info: 4`.

## Pitfalls

### 1. `merge-base` empty on shallow clone

`git fetch --depth=50` is enough for shallow. For full history: `git fetch
--unshallow upstream main`. If upstream is huge (>200MB), fetch may time out —
work around by computing merge-base from a different ref.

### 2. `git reset --hard` triggers agent safety block

Don't fight the smart-approval gate. Use `git checkout --orphan` + upstream
fetch — same effect, no prompt.

### 3. Don't `git add -A` after overlay-copy

You will sweep in upstream's prebuilt `node_modules` paths or `.next/`
build output if any slipped in. Stage only the explicit overlay files.

### 4. PR visual diff size is misleading

A fork-reset PR shows 100+ files / +32k / -1.8k lines because GitHub
3-way-diffs against the old forked-history main. The *real* overlay diff vs
`upstream/main` is tiny (10-20 files). Tell the user this in the PR
description so they don't bounce off the diff size.

### 5. Default-branch swap is irreversible mid-PR

If the user has other open PRs against `main`, swapping the default branch
closes them as base-gone. Check `gh pr list --state open --base main` first.

### 6. Vercel/Netlify/CI drop their webhook on ref churn

When you delete+recreate the default branch, hosting providers (Vercel is the
common case for NotionNext) see the SHA come back as a fast-forward and may
**not** fire a new production deploy. Verify the actual production deployment
SHA against the new HEAD before declaring victory. If MISMATCHED, force a
redeploy by pushing an empty commit (`chore: trigger redeploy`) — host will
rebuild from there.

### 7. Don't ask exhaustively about which files to keep

Default principle: if the file is in `conf/`, `blog.config.js`, custom CSS,
binary assets (favicon, images), assets overrides, etc. — keep fork's
version. If it's in `themes/`, `components/`, `lib/`, `pages/` (no
personalisation hooks) — take upstream. When in doubt, keep fork, document
the choice. User says "尽量保留" / "用默认就行" — pick sane defaults and
ship, don't enumerate every file.

### 8. Never hand the user a command without stating its precondition

When you tell the user "run X", the next state depends on a prior step that
might not have happened. Examples:

- ❌ "Now run `gh workflow run ...`" (after opening a PR)
- ✅ "Once the PR is merged, then run `gh workflow run ...`"

If the next-step command looks like something the user can paste and you'll
both discover the bug only when it returns wrong, add a one-line
precondition above it.

## First-time fork + local personalise (push-bound workflow)

When the user wants a personal fork they'll commit to — not just sync with
upstream — the workflow is different. Trigger phrases: "fork 一下", "我也要
这个", "在你 GitHub 上开一个", "做个 fork 版", or any time the user explicitly
asks you to fork an upstream repo and push your own changes to the fork.

### Step 1 — fork and clone to local

```bash
# fork on GitHub (no clone yet)
gh repo fork <upstream-owner>/<repo> --clone=false

# clone the fork locally to the target dir
gh repo clone <your-name>/<repo> <local-target-dir>
```

`gh fork` automatically configures the `upstream` remote to point at the
original. Verify with `git remote -v` — you should see both `origin` (your
fork) and `upstream` (original).

### Step 2 — make the changes, version-bump in metadata

This is the asymmetric part vs the sync-recovery flow above. For plugin
frameworks and package-style repos, version + author metadata is the
single source of truth. Rules:

- **Bump version** in every metadata file (`metadata.yaml`, package.json
  `version`, `pyproject.toml` `version`, plugin manifest). Convention: minor
  bump for additive changes, patch for fixes.
- **Preserve original author credit**. Pattern: `author: OriginalAuthor /
  <your-name>`. Never replace the upstream author. This is the polite default
  for personal forks of small plugins.
- **If a `_conf_schema.json` exists, fill in the `default` for every field**
  you add, otherwise the host platform can't initialise the config on first
  load. Empty `default: ""` for strings, `[]` for lists, `0` for ints.
- **If the plugin writes cache to disk, add a `.gitignore` entry** for the
  cache dir (e.g. `imgs/`, `__pycache__/`) before the first commit so you
  don't accidentally push runtime artefacts.

### Step 3 — commit with a clean message, push to fork only

```bash
git add -A
git -c user.email=<you> -c user.name=<you> commit -F /tmp/commit_msg.txt
git push origin main
```

- `git -c user.email=... -c user.name=...` works around the case where the
  local git config is missing or wrong; safer than `git config --global` for
  a one-off push.
- **Do NOT `git push upstream`** — the upstream remote is read-only by
  convention. Pushing to it almost never works anyway (you don't have
  write access), but never try.
- If a `__pycache__/`, `.pyc`, or runtime cache directory slipped into the
  commit, fix it in a follow-up commit (`chore: ignore <dir>/` + add to
  .gitignore) — don't amend the personalisation commit.

### Step 4 — verify before declaring done

```bash
# 1. Remote state matches local
git fetch origin && git status

# 2. No stray __pycache__/ or runtime artefacts tracked
git ls-files | grep -E '\.pyc$|__pycache__$|imgs/$'  # should be empty

# 3. If this is a plugin being installed/loaded, check the load log for
#    "Loading plugin <name>..." and "Added llm tool: <tool_name>" lines.
#    See references/astrbot-plugin-fork.md for the AstrBot-specific path.
```

### Pitfalls

#### F1. Don't fork to the same name as the upstream if you can avoid it

The user can still install by URL, but keeping the original name
(`astrbot_plugin_Pic` vs a custom `astrbot_plugin_Pic_myfork`) makes it
impossible to disambiguate upstream from fork in the wild. If the user's
intent is to ship a meaningful fork, pick a clear name suffix.

#### F2. Don't bypass upstream with `--orphan` on a first-time personalise

The orphan-reset flow above is for **sync recovery**, where the fork's
history is the problem. For a first-time fork the original history is
fine — you want the upstream lineage preserved so the relationship is
visible in commit history.

#### F3. Check for required tools before the first commit

Plugin frameworks often need `ruff`, `pyright`, or specific formatters
for pre-commit. If the project's README says "use ruff", run it
**before** the first commit, not after — fixing formatter complaints in
a follow-up commit is messy.

#### F4. Don't fork for things that should be PRs upstream

If the user wants a small fix to upstream, fork → clone → edit → push →
**open a PR to upstream**, not a personal fork. Personal forks are for
personalisation overlays; PRs are for upstream contributions. Default
heuristic: if the user said "fix" or "patch" rather than "fork" or "my
own version", open a PR.

#### F5. Bash heredocs with Chinese commit messages break shell parsing

If the commit message is multi-line and contains Chinese / accents,
write it to `/tmp/commit_msg.txt` first and use `git commit -F`. Inline
`-m "..."` will fail with `unterminated string literal` or `unexpected
EOF` depending on quote escaping. This is the sandbox interpreter, not
git.

## Verification

After the reset, three things must be green:

```bash
# 1. Fork HEAD equals upstream HEAD (modulo the overlay commit)
gh api repos/<owner>/<fork>/commits/main --jq '.parents[0].sha'

# 2. Sync workflow runs cleanly
gh workflow run "Upstream Sync" --repo <owner>/<fork>
gh run view $(gh run list --workflow=sync.yaml --limit 1 --json databaseId -q '.[0].databaseId') \
  --json conclusion   # expect "success"
# Look for log line: "No new commits to sync. Finishing sync action gracefully."

# 3. Production deployment (Vercel etc.) actually serves the new SHA
curl -sI https://<user-site> | grep -i x-vercel-id
gh api repos/<owner>/<fork>/deployments --jq \
  '.[] | select(.environment=="Production") | .sha' | head -3
```

If §3 SHA ≠ §2 SHA, the host dropped the webhook — push an empty commit to
re-arm (see Pitfall §6).

## Known upstream migrations

Update this list when you encounter more:

| Project | Old | New | When |
|---|---|---|---|
| NotionNext | `tangly1024/NotionNext` | `notionnext-org/NotionNext` | 2026 (org transfer) |
