# Config Export & Self-Sync Pattern

How to export Hermes agent config as a public GitHub repo and keep it auto-synced.

## Canonical Repo

[publieople/hermes-config-kit](https://github.com/publieople/hermes-config-kit) — 238 skills, full config, self-syncing.

## Exporting Config (Redaction)

When exporting `~/.hermes/config.yaml` to a public repo, sanitize ALL sensitive fields:

```python
import re

content = read_file("/home/po/.hermes/config.yaml", ...)["content"]

# API keys — any form
content = re.sub(r"api_key:\s*'.*'", "api_key: 'YOUR_API_KEY'", content)
content = re.sub(r'api_key:\s*".*"', 'api_key: "YOUR_API_KEY"', content)
content = re.sub(r"api_key:\s*\S+", "api_key: YOUR_API_KEY", content)

# Bearer tokens in headers
content = re.sub(r"Authorization: Bearer\s+\S+", "Authorization: Bearer YOUR_TOKEN", content)

# IP addresses (skip localhost)
content = re.sub(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?!\.)", "REDACTED_IP", content)
# Then restore 127.0.0.1
content = content.replace("REDACTED_IP", "127.0.0.1")  # only if 127.0.0.1 was the original

# Feishu channel IDs (pattern: oc_ + 28 hex chars)
content = re.sub(r"oc_[a-f0-9]{28}", "YOUR_FEISHU_CHANNEL_ID", content)

# Mem0 user IDs
content = re.sub(r"user_[a-f0-9]+", "YOUR_MEM0_USER_ID", content)

# Emails
content = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                  "YOUR_EMAIL@example.com", content)
```

### sed equivalent (for bash scripts)

```bash
sed -E \
    -e "s/(api_key:\s*['\"])[^'\"]*(['\"])/\1YOUR_API_KEY\2/g" \
    -e "s/(api_key:\s*)[^[:space:]].*/\1YOUR_API_KEY/g" \
    -e "s/(Authorization: Bearer\s+)\S+/\1YOUR_TOKEN/g" \
    -e "s/([0-9]{1,3}\.){3}[0-9]{1,3}/REDACTED_IP/g" \
    -e "s/oc_[a-f0-9]{28}/YOUR_FEISHU_CHANNEL/g" \
    config.yaml > config.redacted.yaml
```

## Skills Inventory

To identify which skills to export:

- **`.bundled_manifest`**: hash → skill name mapping. Skills in this file came with Hermes installation. 90 entries.
- **`.usage.json`**: per-skill usage stats, creation metadata. `created_by: "agent"` = self-built.
- **`.curator_state`**: curator metadata (pinned, archived, patch count).
- **`.hub/`**: ClawHub installation cache. Skills installed via `hermes skills install`.

Export strategy: rsync everything, exclude metadata files (`.hub/`, `.bundled_manifest`, `.usage.json`, `.curator_state`).

## Embedded .git Pitfall

When copying `~/.hermes/skills/`, subdirectories from openclaw-imports may contain their own `.git` directories (cloned repos like `dot-skill`, `garden-skills`, `nuwa-skill`). These cause:

```
warning: adding embedded git repository: skills/openclaw-imports/dot-skill
```

**Fix**: Remove all nested `.git` dirs before `git add`:

```bash
find skills/ -name ".git" -type d -exec rm -rf {} + 2>/dev/null
git add -A
```

## Sync-Back Cron Pattern

Use `no_agent: true` + script mode for a cron job that syncs back to the repo:

```bash
cronjob action=create \
  name="hermes-config-sync" \
  schedule="0 6 * * 0" \
  script="sync-back.sh" \
  no_agent=true \
  deliver="origin" \
  enabled_toolsets='["terminal","file"]'
```

The script must be in `~/.hermes/scripts/` (cron `script` field only accepts filenames, not absolute paths).

### sync-back.sh logic

1. Copy `~/.hermes/config.yaml` → redact → overwrite repo `config.yaml`
2. rsync `~/.hermes/skills/` → repo `skills/` (exclude metadata)
3. rsync `~/.hermes/scripts/` → repo `scripts/`
4. `git diff --stat` — silent exit if no changes
5. `git add -A && git commit -m "sync: $(date -Iseconds)" && git push`

### CI Validation

GitHub Actions workflow to catch leaked secrets:

```yaml
- name: Check for leaked secrets
  run: |
    # API keys: sk- followed by 20+ alphanumeric chars
    if grep -n "sk-[a-zA-Z0-9]\{20,\}" config.yaml; then exit 1; fi
    # Real IPs (not placeholder)
    if grep -nE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' config.yaml \
      | grep -v "127.0.0.1" | grep -v "YOUR_WINDOWS_IP"; then exit 1; fi
    # Real emails
    if grep -rE '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}' config.yaml SOUL.md \
      | grep -v "YOUR_EMAIL"; then exit 1; fi
```
