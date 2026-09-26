# User Reconnaissance Report — Template

When a user says "let's discuss my X plan" (internship, side project, paper), DO NOT start planning. First produce a reconnaissance report that reconciles stated intent vs observed artifacts, then ask for A-E clarifications.

## When to use

Trigger: user opens a planning conversation about themselves (career, learning path, project direction). Skip if the conversation is purely about a third-party decision ("which X to buy", "where to live").

## Four sources to cross-check

Always pull these for 冯周杰 / Publieople. For other users, adapt to whatever exists.

1. **GitHub** — `gh api /users/{login}/repos?per_page=100&type=owner` then sort by stars × updated_at. The repo *size* in KB and `last_pushed_at` are higher-signal than stars (which are often 0 for niche/early work).
2. **Resume JSON** — `raw.githubusercontent.com/{login}/{login}/main/resume.json` (visiky/resume schema). Stated `positionTitle` is a claim, not a fact.
3. **Notion** — list `data_source`s via `/v1/search?filter.value=data_source`. Search for `求职意向`, `目标`, `意向`, `想去的` to find the user's own ranked company table. This is the *single highest-signal artifact* — they ranked companies themselves.
4. **Blog** — `curl https://blog.for-people.cn/feed` (NotionNext ships `/feed`). Article topics over the last 6 months reveal actual focus.

Skip sources the user hasn't exposed (Notion without sharing, locked GitHub orgs, etc.). Don't fabricate data.

## Report structure (4 sections, no preamble)

### 1. 已确认画像 (Confirmed profile)
- Identity: name, year/major, contact (email/QQ/phone)
- Skills: AI/Agent | 编程 | 运维 | 知识管理 (whichever the user actually has)
- Main project table: name | star rating | one-line description. Star rating rule: ★★★★ = ship-able to recruiters; ★★★ = complete tech depth; ★★ = works but rough; ★ = small plugin / fork.
- Honors: only list what was actually verified in resume.json. Don't pad.

### 2. 求职意向表的真正信号
Quote the user's own data_source verbatim (company, location, reason). Then extract the pattern in 1-2 sentences:
- "All WLB-first (955/965), zero China-internet-996"
- "100% 上海/北京/Remote/苏州/杭州 — 排除深圳"
- "Direction cluster: backend/cloud/payment, not algorithm"

### 3. 4 个尖锐问题 (4 sharp inconsistencies)
Number them. Make each one a single concrete contradiction between two sources. The user MUST address these, not deflect:
- Example: "resume.json says AI 工具链 but 求职意向 says 后端/AWS — which is true?"
- Example: "award list says 数模二等, but project depth shows AI infra — both can't be the lead"

### 4. 5 个事实问题 (A-E, must answer before planning)
Pick 5 questions that gate planning. Don't ask what you can infer. Each question has a small set of choices the user can answer in 1 line:

| Letter | Question pattern |
|---|---|
| A | Direction: real intent or wishful list? |
| B | Time window: when can you start, how long, days/week? |
| C | Geography: hard constraint or negotiable? |
| D | Credential anxiety: fix via projects or via GPA/awards? |
| E | Resume freshness: is resume.json current, are recent projects added? |

## What NOT to do

- Don't recommend "you can do both AI and backend" — that's avoiding the question.
- Don't pad with motivational language. The user prefers "真实证据 > fake 答案" (per mem0).
- Don't move to "next step" before user answers A-E. Saving a half-baked plan is worse than not planning.
- Don't list all 41 repos. Pick top 5-8 that map to the lead direction.

## Example

See session 2026-07-25 in `career-job-hunting` — that conversation produced a 4-section report from this template and led to "Phase 0" being added to the SKILL.md. Reproduce that report's structure when the trigger fires again.