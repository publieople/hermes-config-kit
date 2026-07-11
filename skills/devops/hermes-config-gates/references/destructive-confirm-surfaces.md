# Destructive slash-command confirmation — surface split

The `[/new, /clear, /reset, /undo]` "are you sure" dialog has THREE
independent gates, one per runtime surface. Choosing the wrong gate is
the #1 reason "I disabled the prompt and it still appears".

## Surface identification (read from screenshot, not description)

| User sees | Surface | What controls it |
|-----------|---------|------------------|
| Buttons: "Approve Once" / "Always Approve" / "Cancel" | Classic CLI (prompt_toolkit) OR Gateway (Telegram/Discord/Slack) | `approvals.destructive_slash_confirm: false` in `~/.hermes/config.yaml` |
| Buttons: "No, keep going" / "Yes, start a new session" (or "Yes, clear the session") | TUI (Ink overlay) | `HERMES_TUI_NO_CONFIRM=1` env var |

Both render the SAME intent ("this discards your conversation") but
incompatible button labels. If the user pastes a screenshot, the button
text alone tells you which gate to flip.

## Code locations

- **CLI gate** — `cli.py:10578` `_confirm_destructive_slash()`. Reads
  `load_cli_config()["approvals"]["destructive_slash_confirm"]` (default
  `True`). Inline-skip escape hatch: `now`, `--yes`, `-y` as args.
  Persisted via `save_config_value("approvals.destructive_slash_confirm", False)`.
- **TUI gate** — `ui-tui/src/config/env.ts:52`
  `NO_CONFIRM_DESTRUCTIVE = truthy(process.env.HERMES_TUI_NO_CONFIRM)`,
  used at `ui-tui/src/app/slash/commands/core.ts:195` to short-circuit
  before `patchOverlayState({ confirm: ... })`.
- **Gateway gate** — `gateway/run.py:14156` `_request_slash_confirm()`.
  Native yes/no buttons per platform; "Always Approve" persists the
  same `approvals.destructive_slash_confirm` key.

## Why the env var (not config.yaml) for TUI

The TUI is a Node process spawned by Python via `os.execvp` from
`hermes_cli/main.py:_launch_tui`. Config.yaml stays in Python land; the
Node bundle only sees what arrives in `process.env`. TUI therefore has
its own opt-out channel that doesn't depend on parsing YAML in JS.

Source of truth for this design:
`hermes_cli/config.py:2542-2548`:
> TUI has its own modal overlay (HERMES_TUI_NO_CONFIRM=1 to opt out there).

## WSL + fish + bashrc trap (the second-order bug)

Symptom: user sets `HERMES_TUI_NO_CONFIRM=1` in `~/.bashrc`, opens a new
TUI window, the modal still appears.

Cause chain:

1. Machine has `fish` installed; `~/.bashrc` line ~13 does `exec fish`
   for interactive bash. The shell the user actually sees is fish, not
   bash. Fish does not read `~/.bashrc`.
2. Even if it did, `~/.bashrc` typically has `[[ $- != *i* ]] && return`
   at the top (line ~5-6). Any non-interactive subshell — including the
   bash that `hermes` Python launches into for shell-command tool calls —
   exits before reaching any later `export`.
3. Setting in current shell via `export HERMES_TUI_NO_CONFIRM=1` works
   for that one shell, but a fresh TUI window is a NEW fish process that
   re-evaluates its own startup files independently.

Fix:

- `~/.config/fish/config.fish`: add `set -x HERMES_TUI_NO_CONFIRM 1`
  (this is what the user actually runs).
- `~/.bashrc`: optionally add `export HERMES_TUI_NO_CONFIRM=1` AFTER the
  interactive guard, so plain bash sessions also see it.
- After editing: close ALL TUI windows and open a new one. The env
  inside a running TUI is frozen at process start; config.yaml reload
  does NOT refresh `process.env` in the running Node bundle.

## Verification checklist

Before telling the user "fixed":

- [ ] `tail ~/.config/fish/config.fish | grep HERMES_TUI_NO_CONFIRM`
      shows the line.
- [ ] New fish tab: `env | grep HERMES_TUI_NO_CONFIRM` returns
      `HERMES_TUI_NO_CONFIRM=1`.
- [ ] New TUI window, run `/new` — no modal.
- [ ] If a CLI flag was also touched: `grep destructive_slash_confirm
      ~/.hermes/config.yaml` shows `false`.

## Reproduction (minimal)

```bash
# Pre-fix
hermes                                    # TUI launches
/new                                      # shows "Start a new session?" modal

# Fix
echo 'set -x HERMES_TUI_NO_CONFIRM 1' >> ~/.config/fish/config.fish
# close all TUI windows, open new fish tab
hermes
/new                                      # no modal, session rotates
```

Time saved: 30+ minutes of "why isn't my env var working" if the
agent first identifies the right surface (TUI vs CLI), then knows
where the user's shell actually reads from.
