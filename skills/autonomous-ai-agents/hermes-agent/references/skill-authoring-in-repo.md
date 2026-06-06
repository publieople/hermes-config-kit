# Authoring Hermes-Agent Skills (In-Repo)

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo:** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- Adding a skill "in this branch / repo / commit"
- Committing a reusable workflow that should ship with hermes-agent
- Editing an existing skill under the repo's `skills/` tree

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars**.
- Non-empty body after the closing `---`.

```yaml
---
name: my-skill-name
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. If pushing past 20k, split into `references/*.md`.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. Survey peers in the target category: `ls skills/<category>/`
2. Read 2-3 peer SKILL.md files to match tone and structure.
3. Draft with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. Validate locally (check frontmatter, name, description, size).
5. Git add + commit.
6. Note: current session's skill loader is cached — `skill_view` won't see the new skill until a new session.

## Editing Existing In-Repo Skills

- **Small fix:** `skill_manage(action='patch')` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md.
- **Adding supporting files:** `write_file` to `references/`, `templates/`, or `scripts/`.
- **Always commit** the edit.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill** — it writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.
2. **Leading whitespace before `---`** — the validator checks `content.startswith("---")`.
3. **Description too generic** — start with "Use when ..." and describe the trigger class.
4. **Forgetting metadata block** — every peer has it.
5. **Writing a skill that duplicates a peer** — prefer extending an existing skill.
6. **Expecting current session to see new skill** — it won't; verify in a fresh session.
7. **Linking to skills that don't exist in-repo** — prefer only in-repo links in `related_skills`.
