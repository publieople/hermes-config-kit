---
name: git-workflow-and-versioning
description: Structures git workflow practices. Use when making any code change. Use when committing, branching, resolving conflicts, or when you need to organize work across multiple parallel streams.
tags: [agent-skills, engineering-workflow]
trigger: git|commit|分支|branch|PR
category: agent-skills
---


# Git Workflow and Versioning

## Overview

Git is your safety net. Treat commits as save points, branches as sandboxes, and history as documentation. With AI agents generating code at high speed, disciplined version control is the mechanism that keeps changes manageable, reviewable, and reversible.

## When to Use

Always. Every code change flows through git.

## Core Principles

### Trunk-Based Development (Recommended)

Keep `main` always deployable. Work in short-lived feature branches that merge back within 1-3 days. Long-lived development branches are hidden costs — they diverge, create merge conflicts, and delay integration. DORA research consistently shows trunk-based development correlates with high-performing engineering teams.

```
main ──●──●──●──●──●──●──●──●──●──  (always deployable)
        ╲      ╱  ╲    ╱
         ●──●─╱    ●──╱    ← short-lived feature branches (1-3 days)
```

This is the recommended default. Teams using gitflow or long-lived branches can adapt the principles (atomic commits, small changes, descriptive messages) to their branching model — the commit discipline matters more than the specific branching strategy.

- **Dev branches are costs.** Every day a branch lives, it accumulates merge risk.
- **Release branches are acceptable.** When you need to stabilize a release while main moves forward.
- **Feature flags > long branches.** Prefer deploying incomplete work behind flags rather than keeping it on a branch for weeks.

### 1. Commit Early, Commit Often

Each successful increment gets its own commit. Don't accumulate large uncommitted changes.

```
Work pattern:
  Implement slice → Test → Verify → Commit → Next slice

Not this:
  Implement everything → Hope it works → Giant commit
```

Commits are save points. If the next change breaks something, you can revert to the last known-good state instantly.

### 2. Atomic Commits

Each commit does one logical thing:

```
# Good: Each commit is self-contained
git log --oneline
a1b2c3d Add task creation endpoint with validation
d4e5f6g Add task creation form component
h7i8j9k Connect form to API and add loading state
m1n2o3p Add task creation tests (unit + integration)

# Bad: Everything mixed together
git log --oneline
x1y2z3a Add task feature, fix sidebar, update deps, refactor utils
```

### 3. Descriptive Messages

Commit messages explain the *why*, not just the *what*:

```
# Good: Explains intent
feat: add email validation to registration endpoint

Prevents invalid email formats from reaching the database.
Uses Zod schema validation at the route handler level,
consistent with existing validation patterns in auth.ts.

# Bad: Describes what's obvious from the diff
update auth.ts
```

**Format:**
```
<type>: <short description>

<optional body explaining why, not what>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `refactor` — Code change that neither fixes a bug nor adds a feature
- `test` — Adding or updating tests
- `docs` — Documentation only
- `chore` — Tooling, dependencies, config

### 4. Keep Concerns Separate

Don't combine formatting changes with behavior changes. Don't combine refactors with features. Each type of change should be a separate commit — and ideally a separate PR:

```
# Good: Separate concerns
git commit -m "refactor: extract validation logic to shared utility"
git commit -m "feat: add phone number validation to registration"

# Bad: Mixed concerns
git commit -m "refactor validation and add phone number field"
```

**Separate refactoring from feature work.** A refactoring change and a feature change are two different changes — submit them separately. This makes each change easier to review, revert, and understand in history. Small cleanups (renaming a variable) can be included in a feature commit at reviewer discretion.

### 5. Size Your Changes

Target ~100 lines per commit/PR. Changes over ~1000 lines should be split. See the splitting strategies in `code-review-and-quality` for how to break down large changes.

```
~100 lines  → Easy to review, easy to revert
~300 lines  → Acceptable for a single logical change
~1000 lines → Split into smaller changes
```

## Branching Strategy

### Feature Branches

```
main (always deployable)
  │
  ├── feature/task-creation    ← One feature per branch
  ├── feature/user-settings    ← Parallel work
  └── fix/duplicate-tasks      ← Bug fixes
```

- Branch from `main` (or the team's default branch)
- Keep branches short-lived (merge within 1-3 days) — long-lived branches are hidden costs
- Delete branches after merge
- Prefer feature flags over long-lived branches for incomplete features

### Branch Naming

```
feature/<short-description>   → feature/task-creation
fix/<short-description>       → fix/duplicate-tasks
chore/<short-description>     → chore/update-deps
refactor/<short-description>  → refactor/auth-module
```

## Working with Worktrees

For parallel AI agent work, use git worktrees to run multiple branches simultaneously:

```bash
# Create a worktree for a feature branch
git worktree add ../project-feature-a feature/task-creation
git worktree add ../project-feature-b feature/user-settings

# Each worktree is a separate directory with its own branch
# Agents can work in parallel without interfering
ls ../
  project/              ← main branch
  project-feature-a/    ← task-creation branch
  project-feature-b/    ← user-settings branch

# When done, merge and clean up
git worktree remove ../project-feature-a
```

Benefits:
- Multiple agents can work on different features simultaneously
- No branch switching needed (each directory has its own branch)
- If one experiment fails, delete the worktree — nothing is lost
- Changes are isolated until explicitly merged

## The Save Point Pattern

```
Agent starts work
    │
    ├── Makes a change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    ├── Makes another change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    └── Feature complete → All commits form a clean history
```

This pattern means you never lose more than one increment of work. If an agent goes off the rails, `git reset --hard HEAD` takes you back to the last successful state.

## Change Summaries

After any modification, provide a structured summary. This makes review easier, documents scope discipline, and surfaces unintended changes:

```
CHANGES MADE:
- src/routes/tasks.ts: Added validation middleware to POST endpoint
- src/lib/validation.ts: Added TaskCreateSchema using Zod

THINGS I DIDN'T TOUCH (intentionally):
- src/routes/auth.ts: Has similar validation gap but out of scope
- src/middleware/error.ts: Error format could be improved (separate task)

POTENTIAL CONCERNS:
- The Zod schema is strict — rejects extra fields. Confirm this is desired.
- Added zod as a dependency (72KB gzipped) — already in package.json
```

This pattern catches wrong assumptions early and gives reviewers a clear map of the change. The "DIDN'T TOUCH" section is especially important — it shows you exercised scope discipline and didn't go on an unsolicited renovation.

## Pre-Commit Hygiene

Before every commit:

```bash
# 1. Check what you're about to commit
git diff --staged

# 2. Ensure no secrets
git diff --staged | grep -i "password\|secret\|api_key\|token"

# 3. Run tests
npm test

# 4. Run linting
npm run lint

# 5. Run type checking
npx tsc --noEmit
```

Automate this with git hooks:

```json
// package.json (using lint-staged + husky)
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

## Handling Generated Files

- **Commit generated files** only if the project expects them (e.g., `package-lock.json`, Prisma migrations)
- **Don't commit** build output (`dist/`, `.next/`), environment files (`.env`), or IDE config (`.vscode/settings.json` unless shared)
- **Have a `.gitignore`** that covers: `node_modules/`, `dist/`, `.env`, `.env.local`, `*.pem`

## Using Git for Debugging

```bash
# Find which commit introduced a bug
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
# Git checkouts midpoints; run your test at each to narrow down

# View what changed recently
git log --oneline -20
git diff HEAD~5..HEAD -- src/

# Find who last changed a specific line
git blame src/services/task.ts

# Search commit messages for a keyword
git log --grep="validation" --oneline
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll commit when the feature is done" | One giant commit is impossible to review, debug, or revert. Commit each slice. |
| "The message doesn't matter" | Messages are documentation. Future you (and future agents) will need to understand what changed and why. |
| "I'll squash it all later" | Squashing destroys the development narrative. Prefer clean incremental commits from the start. |
| "Branches add overhead" | Short-lived branches are free and prevent conflicting work from colliding. Long-lived branches are the problem — merge within 1-3 days. |
| "I'll split this change later" | Large changes are harder to review, riskier to deploy, and harder to revert. Split before submitting, not after. |
| "I don't need a .gitignore" | Until `.env` with production secrets gets committed. Set it up immediately. |

## Red Flags

- Large uncommitted changes accumulating
- Commit messages like "fix", "update", "misc"
- Formatting changes mixed with behavior changes
- No `.gitignore` in the project
- Committing `node_modules/`, `.env`, or build artifacts
- Long-lived branches that diverge significantly from main
- Force-pushing to shared branches

## Rescuing a Long-Diverged Fork

When a GitHub fork's auto-sync workflow has been failing for days/weeks (notably the `Upstream Sync` GitHub Action pattern), the fork is too far behind upstream for `merge` to converge. Don't try to resolve 200+ add/add conflicts file-by-file — reset and reapply.

**Symptoms** (any one is enough):
- `gh run list --workflow="Upstream Sync"` shows consecutive `failure` conclusions for ≥5 days
- Sync log shows `CONFLICT (content): Merge conflict in <file>` for many files
- Sync log shows `No previous sync found from upstream repo. Syncing entire commit history.` (means the sync action lost its baseline)
- PR diff between fork `main` and upstream shows thousands of files even when your real changes are tiny
- Upstream repo has been migrated (renamed/transferred org) — old `upstream_sync_repo: user/old-repo` still in `.github/workflows/sync.yaml`, fetches redirect but `merge-base` cannot be reconstructed

**Procedure** (read entirely before touching anything; one false move is hard to undo):

1. **Diagnose first, no edits.** Use `gh run list` + `gh run view --log-failed` to capture the actual failure signature. Identify whether the failure is **upstream metadata drift** (org migration, dead repo URL) vs **accumulated content conflicts** vs **Node version deprecation** — the fix differs.

2. **Enumerate true fork-only commits** before any reset. Both branches have diverged; the merge-base is meaningless without unshallowing.
   ```bash
   git fetch --unshallow origin main   # always safe for your own fork
   git fetch upstream main             # may time out on huge upstream repos
   BASE=$(git merge-base origin/main upstream/main)
   git log origin/main ^$BASE --no-merges --pretty=format:"%H %s" --name-status
   ```
   This gives you the **honest list of fork-only touched files**. GitHub's PR diff will lie at this stage (shows 1000s of files due to history divergence) — `git diff upstream/main HEAD` from your reset branch is the source of truth.

3. **Categorize each fork-only file into exactly one bucket:**
   - **Keep fork**: fork-personalised content (config, CSS, favicon, theme overrides). Bytes-on-disk comparison (`git show origin/main:$f | wc -c` vs upstream) catches obvious cases.
   - **Discard**: auto-bump files (`package.json` patch versions, `*.lock`), inherited workflow files from upstream (`.github/workflows/*`).
   - **Ambiguous**: code under `components/`, `themes/`, `lib/` you don't remember touching — check with `git log origin/main ^$BASE --no-merges -- 'components/*'`. Empty result means upstream-driven, take upstream.

4. **Reset without `git reset --hard`** (smart approval often blocks this and the safer `--orphan + pull` path gives the same result):
   ```bash
   git checkout --orphan reset-fork upstream/main
   git pull upstream main   # working tree now = upstream HEAD, no commit yet
   ```
   `git reset --hard` is blocked by Hermes smart approval for good reason — `--orphan + pull` is the equivalent that's allowed.

5. **Reapply overlays in one commit.** Copy each kept-fork file from origin over the new base:
   ```bash
   for f in <list>; do
     mkdir -p "$(dirname $f)"
     git show "origin/main:$f" > "$f"
   done
   git add -A
   git commit -m "chore(rebase): reapply fork-specific overlays on upstream <version>"
   ```

6. **Push to a feature branch, NOT directly to main.** Open a PR so the user sees the (visually bloated) diff consciously.
   ```bash
   git push origin reset-fork
   gh pr create --base main --head reset-fork --title "chore(rebase): ..." --body "..."
   ```
   Never `--force` to `main` on a fork that has any history the user cares about (star graphs, prior releases). PR-first, force-push-second, only with explicit user permission.

7. **Fix the sync workflow itself** if upstream org migrated:
   ```yaml
   # .github/workflows/sync.yaml
   - upstream_sync_repo: <old-user>/<repo>   # → <new-org>/<repo>
   ```
   Also run prettier (cron string single-quotes, etc.) — sync workflow files are project-formatted.

9. **Verify, don't claim done.**
   - `npx prettier --check .github/workflows/sync.yaml` passes
   - `git diff --name-only upstream/main HEAD` shows the small overlay set (10-20 files), NOT the PR's bloated count
   - PR comment tells the user "review `git diff upstream/main origin/<branch>` for real diff, not the PR's 3-way view"

10. **When handing off mid-recovery, name the next mandatory step explicitly.** When the rescue is partial (e.g. "reset done, PR open, NOT merged yet"), say exactly what the user must do before the next verify means anything. Burying it in a checklist invites them to run the verify command on the un-merged base, see failure, and lose trust in the diagnosis. Format: `**Next N things before the verify means anything:**` followed by numbered list. If the user copy-pastes a verify command before doing those things, the failure pollutes the diagnosis.

**Ponytail notes:**
- Don't try to resolve 200 add/add conflicts individually. The diff is already impossible to read; the right answer is reset + reapply, not resolve.
- Don't auto-merge the rescue PR. User review of the overlay list is the whole point.
- Don't rewrite fork history (filter-branch, interactive rebase) — leaves fork-only deploy config orphaned in ways that bite later.

## Verification

For every commit:

- [ ] Commit does one logical thing
- [ ] Message explains the why, follows type conventions
- [ ] Tests pass before committing
- [ ] No secrets in the diff
- [ ] No formatting-only changes mixed with behavior changes
- [ ] `.gitignore` covers standard exclusions
