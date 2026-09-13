# Hermes Skill-Management Ecosystem: Known Sources

When a user asks "what skills do you have for managing skills" or needs to install these on another agent.

## Publicly Available (installable on any agent)

| Skill | Source | Install Command |
|---|---|---|
| `skill-finder` / `skill-finder-cn` | `yfge/skill-finder` (GitHub) | `npx skills add yfge/skill-finder` |
| `skill-vetter` | ClawHub registry | `clawhub install skill-vetter` |
| `autoskill` | `K-Dense-AI/scientific-agent-skills` | git clone → symlink |
| `writing-skills` | Hermes Superpowers plugin (built-in) | Ships with Hermes; no install needed |

## Local-Only (not yet published to ClawHub/GitHub)

These skills exist in `publieople/hermes-workspace` but have no public source yet:

| Skill | Path in workspace | Status |
|---|---|---|
| `skill-publishing` | `devops/skill-publishing/` | Needs ClawHub publish |
| `hermes-external-skill-install` | `devops/hermes-external-skill-install/` | Needs ClawHub publish |
| `agent-skill-migration` | `devops/agent-skill-migration/` | Needs ClawHub publish |

## How skill sources were traced

1. `skill-vetter` — found in `_archive/openclaw-imports/`, listed on ClawHub as `clawhub install skill-vetter`
2. `skill-finder-cn` — web search found `yfge/skill-finder` on GitHub
3. `autoskill` — symlinked from `K-Dense-AI/scientific-agent-skills`
4. `writing-skills` — part of Superpowers plugin bundled with Hermes
5. Remaining three (`skill-publishing`, `hermes-external-skill-install`, `agent-skill-migration`) — not found on ClawHub or GitHub; confirmed local-only via web search

## Pitfall

Local `git remote -v` in the skills directory showed `publieople/hermes-workspace` for ALL skills — this is the local tracking repo, NOT the installation source. Never use local git remotes to determine skill origin. Always cross-reference with ClawHub, GitHub search, and session history.
