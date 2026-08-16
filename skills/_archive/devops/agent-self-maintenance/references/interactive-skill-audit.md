# Interactive Skill Audit Methodology

When the user asks to "list skills" or "clean up unused/low-usage skills", follow this workflow.

## Step 1: List All Skills (filesystem, not API)

```bash
find ~/.hermes/skills -name "SKILL.md" -maxdepth 5 | wc -l  # count
find ~/.hermes/skills -name "SKILL.md" -maxdepth 5 | sed 's|/home/po/.hermes/skills/||' | sort
```

**Why not `skills_list`?** The tool output gets truncated at ~129K chars for large skill sets (274 skills). Filesystem `find` gives the complete list.

## Step 2: Analyze Modification Time (staleness proxy)

```bash
# Oldest first (stale candidates)
find ~/.hermes/skills -name "SKILL.md" -maxdepth 4 -printf "%T+ %p\n" | sort | head -60

# Newest first (recently active)
find ~/.hermes/skills -name "SKILL.md" -maxdepth 4 -printf "%T+ %p\n" | sort -r | head -40
```

Mtime is the best proxy for usage because:
- Agent logs don't record which skill name was passed to `skill_view` in a greppable format
- The skill name is embedded in JSON tool-call payloads, not on the log line itself
- Even when found, `grep` on `agent.log` needs `-a` (it's falsely detected as binary)

## Step 3: Categorize by Domain Relevance

For a user whose work is **frontend + AI + devops + QQ bot**:

| Category | Verdict | Examples |
|----------|---------|----------|
| **Science** (bio/chem/phys/quantum/neuro) | 🚫 Disable | adaptyv, scanpy, rdkit, cirq, etc. (~120 skills) |
| **OpenCLI tools** (user uses Hermes, not OpenCLI) | 🚫 Disable | opencli-*, cli-anything, smart-search (~10) |
| **Feishu/Lark** (user uses Notion, not Feishu) | 🚫 Disable | lark-* (22 skills) |
| **Nuwa perspectives** (entertainment, unused 3+ months) | 🚫 Disable | nuwa-skill/examples/* (16) |
| **_archive/** (already archived) | 🗑️ Delete | All 15+ |
| **taste-skill old version** (superseded by open-design) | 🚫 Disable | creative/taste-skill/* (13) |
| **Core dev/ops/QQ/frontend** | ✅ Keep | hermes-napcat-qq, comet/*, superpowers/*, etc. (~90) |

## Step 4: Present Categorization Before Acting

Group into a clear table:
- 🗑️ **Delete** (already archived)
- 🚫 **Disable** (move to _archive — reversible)
- ✅ **Keep**

Always get user approval before moving/deleting. The `_archive/` directory serves as a soft-delete: skills moved there can be restored if needed.

## Pitfalls

- `grep -oP 'skill_view.*?"name":\s*"[^"]*"'` on agent.log doesn't work — skill names are in JSON payloads, not plain text lines.
- `skills_list` output gets silently truncated at ~129K — use `find` for completeness.
- Domain relevance matters more than age: a 3-month-old devops skill is more valuable than a 1-week-old bioinformatics skill.
- Never just delete — always move to `_archive/` first. The user can permanently delete later.
