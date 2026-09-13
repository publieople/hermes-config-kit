---
name: hermes-source-archaeology
description: Reverse-engineer user-visible Hermes behavior by reading `~/.hermes/hermes-agent/` source — locate the source of a slash command, config key, confirmation modal, or UI element, then explain root cause and (when applicable) the bypass. Use when a user asks "why does X happen", "how do I turn off Y", "where is Z implemented", or "what's the config key for W" and the answer isn't in the docs site.
---

# Hermes Source Archaeology

Hermes docs cover CLI usage, config keys, and slash command lists — but NOT the *implementation* of any of it. When a user asks "why does `/new` show a confirmation", "where does the approval modal get rendered", or "how does `/clear` decide what to clear", the answer is in the Python source at `~/.hermes/hermes-agent/`.

This skill is the workflow for that lookup. It is NOT a contribution guide (see `hermes-agent` skill) and NOT a debugging skill for broken behavior (see `debugging-hermes-tui-commands`). It is the read-only "explain this to me" path.

## When to Use

- User asks "why does X happen" / "why does X require confirmation"
- User asks "how do I disable Y" / "what's the config key for Y" and the docs don't say
- User asks "where in the code is Z implemented"
- A bug/feature explanation requires citing the actual source line, not a docs paraphrase

**Don't use for**: fixing bugs (use `debugging-hermes-tui-commands`), contributing code (use `hermes-agent`), or when the answer IS in `https://hermes-agent.nousresearch.com/docs/`.

## Step 1 — Confirm the Source Tree Exists

```bash
hermes --version
# Linux install: ~/.hermes/hermes-agent/ (git checkout)
# pip install: site-packages — different layout, harder to grep
```

If `Install method: git` and `Install directory: /home/po/.hermes/hermes-agent` — full source available. If pip/site-packages, fall back to `web_extract` on the GitHub raw URL (e.g. `https://raw.githubusercontent.com/NousResearch/hermes-agent/main/cli.py`).

## Step 2 — Map the File Layout (30 seconds)

```bash
ls ~/.hermes/hermes-agent/
```

Mental model:

| Directory | What lives here |
|---|---|
| `cli.py` | The interactive `HermesCLI` class — TUI/REPL, all `/command` dispatch, modals, banners |
| `gateway/run.py` | Gateway-side command handlers (mostly mirror `cli.py` but for messaging platforms) |
| `hermes_cli/commands.py` | `COMMAND_REGISTRY` — the source of truth for `/command` definitions, aliases, tab-completion |
| `hermes_cli/config.py` | `DEFAULT_CONFIG` — every config key's default and type |
| `agent/` | Conversation loop, prompt builder, context compression, memory, skill dispatch |
| `tools/` | One file per tool; registry imports them automatically |
| `gateway/platforms/` | Per-platform adapters (telegram, discord, slack, …) |

**Rule of thumb**: TUI/REPL behavior → `cli.py`. Gateway/DM behavior → `gateway/run.py`. Slash command catalog → `hermes_cli/commands.py`. Config defaults → `hermes_cli/config.py`.

## Step 3 — Grep the Right Anchor

Use `search_files` with a precise anchor. The fastest anchors are usually:

| User's question | Anchor pattern |
|---|---|
| "Why does `/new` show X" | `canonical == "new"` in `cli.py` |
| "How do I disable confirmation Y" | `_confirm_<thing>` in `cli.py` |
| "Where is config key Z defined" | `^Z:` or `Z = ` in `hermes_cli/config.py` |
| "Why does the gateway do X" | `_handle_<thing>` in `gateway/run.py` |
| "What sends this message" | `send_message` / `send_text` in `gateway/platforms/<platform>.py` |

**Bad anchors to avoid** (too noisy):
- `def /class` (matches thousands)
- The user's word-for-word question (matches comments, not code)
- A bare string like `"new"` (matches 200+ places)

## Step 4 — Read the Call Site, Not Just the Definition

When you find the anchor, read 20–50 lines around it. Common things to look for:

- **Skip tokens / escape hatches** (e.g. `_DESTRUCTIVE_SKIP_TOKENS = {"now", "--yes", "-y"}` for destructive commands)
- **Config gates** (`approvals.destructive_slash_confirm`, `approvals.mcp_reload_confirm`)
- **`save_config_value(...)` calls** — these tell you what persists and what doesn't
- **Sub-handlers** named like `_<verb>_<noun>` — read the top-level dispatch first, then the helper
- **Comments starting with `# Pitfall` or `# Inline-skip`** — usually answer the user's exact question

## Step 5 — Write the Answer

Format that worked:

1. **Root cause** — one line with file:line citation
2. **Why** — 1–3 lines explaining the design intent (often in the comment right above the code)
3. **Bypass** — the actual command/config to skip it, with both the inline (per-call) and persistent (config) options
4. **Recommendation** — 1 line on which to use (e.g. "Always Approve if annoying, `-y` if scripting")

Skip: full architecture diagrams, exhaustive option lists, "you might also want to consider…" tangents. The user wants to know WHY and HOW TO DISABLE. That's it.

## Worked Example: `/new` Confirmation Modal

**User question**: "Why does `/new` show a confirmation?"

**Step 1**: `hermes --version` → `Install directory: /home/po/.hermes/hermes-agent`, `Install method: git` ✓

**Step 2**: `ls ~/.hermes/hermes-agent/` confirms `cli.py` exists.

**Step 3**: 
- `search_files --pattern 'canonical == "new"'` in `cli.py` → line 8611
- Read 8611–8624: dispatch calls `self._confirm_destructive_slash("new", ...)`
- `search_files --pattern 'def _confirm_destructive_slash'` → line 10578
- Read 10578–10663: see the three-option modal (`once` / `always` / `cancel`), the gate `approvals.destructive_slash_confirm`, the inline skip tokens `now`/`--yes`/`-y`, and `save_config_value("approvals.destructive_slash_confirm", False)` on Always Approve.

**Step 4**: The `Always Approve` branch tells you the persistent bypass; `_DESTRUCTIVE_SKIP_TOKENS` tells you the per-call bypass.

**Step 5 — Answer** (under 20 lines):

```
根因: cli.py:8617 → 10578 (`_confirm_destructive_slash`)
设计意图: 避免 /new /clear /reset /undo 误触丢对话。
关掉:
  永久: 选 Always Approve,或配置 approvals.destructive_slash_confirm: false
  临时: /new now  /  /new --yes 标题  /  /new -y
```

## Pitfalls

1. **`gateway/run.py` mirrors `cli.py`** — for slash command behavior, prefer `cli.py` unless the user is in a messaging platform. The gateway has its own `new_session`-style handlers that are often more complex (cleanup threads, session key handling) and harder to cite.
2. **Inline skip tokens are NOT in the docs** — they are an escape hatch documented only in the source. If the user is in a TUI and annoyed by a modal, check `_DESTRUCTIVE_SKIP_TOKENS` first; the per-call skip is often the right answer.
3. **`approvals.*` config keys are NOT in the public config docs** — they are internal gates for confirmation modals. Find them by grepping `approvals.` in `cli.py` and reading the gate checks.
4. **Don't quote the implementation in your answer** — the user wants the *why* and the *escape hatch*, not a 50-line code excerpt. One line with file:line is enough; let them click through.
5. **Hero skill `hermes-agent` has the project layout** — if you forget which directory holds what, read its "Project Layout" section first.
6. **If the install is pip/site-packages**, don't try to grep — use `web_extract` on the GitHub raw URL. The file structure is identical so the line numbers will match `main`; warn the user if their version may diverge.

## Verification

For destructive commands especially, after citing the source, mentally run the bypass:
- Inline: would `/new now` parse correctly through `_split_destructive_skip`?
- Config: would `save_config_value("approvals.destructive_slash_confirm", False)` actually persist?

If you're not sure, cite the source line and say "verify by running `…`" — don't claim a bypass works without checking.
