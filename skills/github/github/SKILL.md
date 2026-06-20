---
name: github
description: Complete GitHub workflow — auth, PRs, code review, issues, repo management. Works with gh CLI or git+curl fallback.
version: 2.0.0
tags: [GitHub, Git, Pull-Requests, Code-Review, Issues, Repositories, CI/CD]
---

# GitHub

Unified GitHub workflow. Each section shows `gh` CLI first, then `git` + `curl` fallback for environments without `gh` installed. All sections share the same auth bootstrap (see §Auth).

## Detecting Auth Method

At the start of any GitHub workflow, determine what's available:

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH=***  AUTH=***
fi
# Fallback: extract token from env, ~/.hermes/.env, or ~/.git-credentials
if [ -z "$GITHUB_TOKEN" ]; then
  if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
    GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
    GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  fi
fi
```

Extract owner/repo from git remote:
```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

## §Auth — Authentication Setup

### Git-Only (HTTPS Token)

1. User creates a **personal access token** at https://github.com/settings/tokens with `repo`, `workflow`, `read:org` scopes
2. Set up credential helper: `git config --global credential.helper store`
3. Do a test operation that triggers auth — username is their GitHub username, password is the token
4. Configure identity: `git config --global user.name "Name"` and `git config --global user.email "email"`

### Git-Only (SSH)

```bash
ssh-keygen -t ed25519 -C "email" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add to https://github.com/settings/keys
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI Auth

```bash
echo "<token>" | gh auth login --with-token
gh auth setup-git
```

### Helper script

`scripts/gh-env.sh` — reusable auth detection script.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use personal access token as password, not GitHub password |
| `gh` commands return `EOF` on WSL with proxy | Prefix with `no_proxy='*'` |
| Credentials not persisting | Check `git config --global credential.helper` |

## §PR — Pull Request Workflow

### Complete PR Lifecycle

```bash
# 1. Branch
git checkout main && git pull origin main
git checkout -b feat/description

# 2. Commit (Conventional Commits)
git add <files>
git commit -m "feat: short description

- Detail 1
- Detail 2"

# 3. Push
git push -u origin HEAD

# 4. Create PR
gh pr create --title "feat: ..." --body "...\nCloses #42"
# Or curl: POST /repos/$OWNER/$REPO/pulls with head=<branch> base=main
```

**Branch naming:** `feat/`, `fix/`, `refactor/`, `docs/`, `ci/`

**Commit format:** See `references/conventional-commits.md`

### Monitoring CI

```bash
gh pr checks
gh pr checks --watch  # poll until done
```

**Auto-fix CI loop:** Check status → read failure logs → fix code → commit+push → re-check (max 3x). See `references/ci-troubleshooting.md`.

### Merging

```bash
# Squash merge
gh pr merge --squash --delete-branch
# Auto-merge when checks pass
gh pr merge --auto --squash --delete-branch
```

### WSL Proxy Pitfall

When running `gh` in WSL with local HTTP proxy (`http://127.0.0.1:7890`), prefix all `gh` and `curl` GitHub API calls with `no_proxy='*'`. Git operations (push/pull/clone) work fine — only `gh`'s REST/GraphQL API calls need this.

### PR Body Templates

- `templates/pr-body-feature.md`
- `templates/pr-body-bugfix.md`

## §Review — Code Review

### Pre-Push Review (git only)

```bash
git diff main...HEAD --stat
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|debugger"
```

### PR Review Workflow

1. Gather context: `gh pr view N`, `gh pr diff N --name-only`, `gh pr checks N`
2. Check out locally: `git fetch origin pull/N/head:pr-N && git checkout pr-N`
3. Review against the checklist below
4. Post review:

```bash
gh pr review N --approve --body "LGTM!"
gh pr review N --request-changes --body "See inline comments."
```

### Review Checklist

- **Correctness:** Does it do what it claims? Edge cases?
- **Security:** No hardcoded secrets, input validation, no SQLi/XSS
- **Code Quality:** Clear naming, DRY, single responsibility
- **Testing:** New paths tested? Happy + error cases?
- **Performance:** No N+1 queries, appropriate caching
- **Documentation:** Public APIs documented, README updated

**Output format:** See `references/review-output-template.md`

## §Issues — Issue Management

### View and Create

```bash
gh issue list --state open --label "bug"
gh issue view 42
gh issue create --title "..." --body "..." --label "bug,backend" --assignee "username"
```

### Manage

```bash
gh issue edit 42 --add-label "priority:high" --add-assignee @me
gh issue comment 42 --body "..."
gh issue close 42 --reason "not planned"
gh issue reopen 42
```

### Templates

- `templates/bug-report.md`
- `templates/feature-request.md`

## §Repo — Repository Management

### Common Operations

```bash
# Create
gh repo create my-project --public --clone

# Clone
git clone https://github.com/owner/repo.git
git clone --depth 1 https://github.com/owner/repo.git

# Fork
gh repo fork owner/repo --clone
git remote add upstream https://github.com/owner/repo.git

# Secrets
gh secret set API_KEY --body "value"
gh secret list

# Releases
gh release create v1.0.0 --title "v1.0.0" --generate-notes

# CI/Actions
gh workflow list
gh run list --limit 10
gh run view <ID> --log-failed
gh run rerun <ID>
```

### Fork Sync

#### Quick Diagnostics

Before syncing, check the fork's relationship to upstream:

```bash
# Check if behind/ahead (no local clone needed)
no_proxy='*' gh api repos/$OWNER/$REPO/compare/NousResearch:main...main \
  --jq '{status, ahead_by, behind_by}'

# Try GitHub's native fork sync (only works when cleanly behind)
no_proxy='*' gh api repos/$OWNER/$REPO/merge-upstream -X POST -f branch=main
```

#### Manual Sync (local clone)

```bash
git fetch upstream && git rebase upstream/main && git push --force-with-lease origin main
```

Use `rebase` + `--force-with-lease` instead of `merge` to keep history clean when the fork has its own commits (workflows, patches). The fork's commits stay on top.

**Check branch protection first** — force push fails on protected branches:
```bash
gh api repos/$OWNER/$REPO/branches/main/protection
# HTTP 404 → not protected → force push OK
# 200 → protected → either disable protection or use merge strategy
```

#### Automated Sync via GitHub Actions

For forks that should stay continuously synced, use a scheduled workflow. Create it directly on the fork via the API (no local clone needed):

```bash
# Create workflow file via API
cat > /tmp/sync.yml << 'EOF'
name: Sync Upstream
on:
  schedule:
    - cron: "0 3 * * *"   # daily at 3 AM UTC
  workflow_dispatch:       # manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    if: github.repository == 'OWNER/REPO'   # guard: only run on fork
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - run: |
          git remote add upstream https://github.com/UPSTREAM_OWNER/UPSTREAM_REPO.git
          git fetch upstream main
          BEHIND=$(git rev-list --count HEAD..upstream/main)
          if [ "$BEHIND" -eq 0 ]; then
            echo "Already up to date"
            exit 0
          fi
          echo "Syncing $BEHIND commit(s)..."
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git rebase upstream/main
          git push --force-with-lease origin main
EOF

CONTENT=$(base64 -w0 /tmp/sync.yml)
no_proxy='*' gh api --method PUT \
  repos/OWNER/REPO/contents/.github/workflows/sync-upstream.yml \
  -f message="ci: add upstream auto-sync" \
  -f content="$CONTENT" \
  -f branch="main"

# Trigger immediately to verify
gh workflow run sync-upstream.yml -R OWNER/REPO
sleep 15 && gh run view $(gh run list -R OWNER/REPO --workflow sync-upstream.yml --limit 1 --json databaseId -q '.[0].databaseId') -R OWNER/REPO --log | grep -E "(Already|Syncing)"
```

**Default branch not protected** is required on the fork for `--force-with-lease`. The `if: github.repository` guard prevents the workflow from accidentally running in the upstream repo.

#### Creating/Updating Files via gh API

When you need to write a file to a repo without cloning it locally:

```bash
# Create (no sha param):
CONTENT=$(base64 -w0 file.txt)
gh api --method PUT repos/OWNER/REPO/contents/path/to/file \
  -f message="commit message" -f content="$CONTENT" -f branch="main"

# Update (requires sha of current file):
SHA=$(gh api repos/OWNER/REPO/contents/path/to/file --jq '.sha')
gh api --method PUT repos/OWNER/REPO/contents/path/to/file \
  -f message="update" -f content="$CONTENT" -f sha="$SHA" -f branch="main"
```

See `references/fork-sync-workflow.yml` for the ready-to-use template.

### GitHub Pages Subdirectory Pitfall

When deploying to `https://<user>.github.io/<repo>/`, asset paths MUST include the repo name as a prefix. For Next.js: `basePath: "/repo-name"` in `next.config.ts`.

### API Cheatsheet

See `references/github-api-cheatsheet.md` for full REST API reference.

## Quick Reference

| Action | gh | curl |
|--------|-----|------|
| List PRs | `gh pr list` | `GET /repos/{o}/{r}/pulls` |
| View PR diff | `gh pr diff N` | `git diff main...HEAD` |
| Create PR | `gh pr create ...` | `POST /repos/{o}/{r}/pulls` |
| Merge PR | `gh pr merge --squash` | `PUT /repos/{o}/{r}/pulls/N/merge` |
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| Close issue | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |
| Create repo | `gh repo create name` | `POST /user/repos` |
| Fork | `gh repo fork o/r` | `POST /repos/o/r/forks` |
| Create release | `gh release create v1` | `POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rerun ID` | `POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `PUT /repos/o/r/actions/secrets/KEY` |
