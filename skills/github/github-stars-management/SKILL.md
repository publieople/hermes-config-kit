---
name: github-stars-management
description: Organize GitHub stars with AI using starred tool.
tags: [github, stars, ai, organization, tool-discovery]
trigger: github stars|star管理|star分类|starred repos|整理star|star太多
category: github
---

# GitHub Stars Management

When user has 100s+ starred GitHub repos and wants AI to organize/categorize them.

## Decision: `amirhmoradi/starred`

After comparing 4 tools, **`starred`** is the recommended pick:

- **Python** — no extra runtime needed
- **Multi-provider** — Claude, GPT, or Gemini (auto-detects from available keys)
- **Free tier available** — Gemini 2.0 Flash is completely free
- **GitHub Actions** — set-and-forget, runs daily
- **Output** — `STARRED_REPOS.md` with TOC, categories, star counts + profile README integration

## Setup (GitHub Actions)

### 1. Fork

Fork https://github.com/amirhmoradi/starred

### 2. Create GH_PAT

https://github.com/settings/personal-access-tokens/new
**Required scope:** `starring:read` (NOT `repo` — won't work for stars API)

### 3. Add Repository Secrets

Settings → Secrets and variables → Actions → **Repository secrets** (not Environment secrets)

| Secret | Value | Required |
|--------|-------|----------|
| `GH_PAT` | PAT from step 2 | ✅ |
| `GEMINI_API_KEY` | From https://aistudio.google.com/apikey | Pick one |
| `ANTHROPIC_API_KEY` | From https://console.anthropic.com/ | Pick one |
| `OPENAI_API_KEY` | From https://platform.openai.com/api-keys | Pick one |

**Recommend Gemini** — free tier handles 800+ star classification at zero cost.

### 4. Run

Actions → "Update Starred Repos" → Run workflow. Result in `STARRED_REPOS.md`.

### 5. Ongoing

Workflow runs daily at 2 AM UTC. New stars auto-categorized.

## Provider Auto-Detection

Checks env vars in priority: `ANTHROPIC_API_KEY` → `OPENAI_API_KEY` → `GEMINI_API_KEY`. Only one key needed.

## Limitations

- **No custom base_url** — cannot use DeepSeek/OmniRoute. Three built-in providers only.
- **GitHub Lists sync** requires browser cookie (expires ~2 weeks).
- **Only public metadata** sent to AI (name, desc, language, README).

## Local CLI

```bash
git clone https://github.com/amirhmoradi/starred && cd starred
pip install -e ".[all]"
export GH_TOKEN=ghp_xxx GEMINI_API_KEY=***
starred fetch --username <user> --with-readme
starred categorize --provider gemini
```
