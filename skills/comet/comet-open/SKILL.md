---
name: comet-open
description: "Comet Phase 1: Open. Invoke with /comet-open. Explore ideas through OpenSpec and create change structure (proposal + design + tasks)."
---

# Comet Phase 1: Open

## Prerequisites

- No active change, or user wishes to create a new change

## Steps

### 0. Locate Comet Scripts

**⚠️ Greenfield project (no openspec CLI):** If `openspec` is not installed (`which openspec` fails), skip CLI-based steps and **create artifacts manually**:
- Create `openspec/changes/<name>/` with `.openspec.yaml`, `.comet.yaml`, `proposal.md`, `design.md`, `tasks.md`
- Use `bash "$COMET_STATE" set <name> phase <phase>` to advance phases
- The guard scripts (`comet-guard.sh`, `comet-state.sh`) still work without openspec CLI — they operate on `.comet.yaml` directly
- For full details, see the comet umbrella skill's reference: `references/greenfield-bootstrapping.md`

Locate scripts before creating state:

```bash
COMET_SEARCH_ROOTS=("." "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.cursor/skills")
COMET_STATE="${COMET_STATE:-$(find "${COMET_SEARCH_ROOTS[@]}" -path '*/comet/scripts/comet-state.sh' -type f -print -quit 2>/dev/null)}"
COMET_GUARD="${COMET_GUARD:-$(find "${COMET_SEARCH_ROOTS[@]}" -path '*/comet/scripts/comet-guard.sh' -type f -print -quit 2>/dev/null)}"

if [ -z "$COMET_STATE" ] || [ -z "$COMET_GUARD" ]; then
  echo "ERROR: Comet scripts not found. Ensure the comet skill is installed." >&2
  return 1
fi
```

### 1. Explore Idea

**Immediately execute:** Use the Skill tool to load the `openspec-explore` skill. If the user has already completed thorough analysis (prior research, document review, full codebase inspection), you may proceed directly to step 2 after loading the skill — but do not skip the load attempt.

**Fallback when openspec-explore is unavailable:** If `skill_view(name='openspec-explore')` returns not-found, treat this as a greenfield-no-CLI scenario: skip exploration and proceed directly to step 2 (manual artifact creation). Document your analysis in `proposal.md` directly.

After the skill loads (if available), freely explore the problem space following its guidance.

### 2. Create Change Structure

**Immediately execute:** Use the Skill tool to load the `openspec-propose` skill. If user intent is unclear and needs exploration first, load `openspec-explore` instead, then follow up with `openspec-propose`.

**Fallback when unavailable:** If `openspec-propose` is not found in the skill library, create change artifacts **manually** — same as the no-CLI greenfield path below.

**Note:** `openspec-new-change` is not available — use `openspec-propose` which serves the same purpose.

When openspec CLI is not installed (or the skills above are unavailable), create change artifacts **manually** under `openspec/changes/<name>/` following the template in the comet umbrella skill's greenfield bootstrapping reference.

Confirm the following artifacts have been created:

```
openspec/changes/<name>/
├── .openspec.yaml
├── .comet.yaml
├── proposal.md       # Why + What: problem, goals, scope
├── design.md         # How (high-level): architectural decisions, solution selection
└── tasks.md          # Task checklist (checkboxes)
```

### 3. Initialize Comet State

Initialize Comet state file:

```bash
bash "$COMET_STATE" init <name> full
```

### 4. Content Completeness Check

Confirm the three documents have complete content:
- **proposal.md**: problem background, goals, scope, non-goals
- **design.md**: high-level architectural decisions, solution selection, data flow
- **tasks.md**: task list, each task has a clear description

## Exit Conditions

- proposal.md, design.md, and tasks.md are all created with complete content
- **Phase guard**: Run `bash "$COMET_GUARD" <change-name> open --apply`; after all PASS, state automatically advances to the next phase

You must use `--apply` before exiting. Otherwise `.comet.yaml` stays at `phase: open`, and the next phase entry check will fail.

```bash
bash "$COMET_GUARD" <change-name> open --apply
```

Full workflow advances to `phase: design`; hotfix/tweak presets advance to `phase: build`.

## Automatic Transition

After exit conditions are met, **proceed immediately to the next phase without waiting for user input**:

> **REQUIRED NEXT SKILL:** Invoke `comet-design` skill to enter the deep design phase.
