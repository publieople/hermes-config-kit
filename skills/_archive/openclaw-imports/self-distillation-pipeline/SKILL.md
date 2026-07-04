---
name: self-distillation-pipeline
description: |
  Distill a user's own persona from their personal Notion workspace into a structured perspective SKILL.md.
  Uses the nuwa-skill methodology adapted for self-distillation: bulk Notion extraction → 6-dimension 
  content categorization → quantitative expression DNA analysis → triple verification → SKILL.md generation.
  Key difference from standard nuwa-skill: data source is Notion API (not web search), target is the user 
  themselves, special handling for self-cognition bias and personal content.
  Load when the user says "distill me from my Notion", "make a skill of me", "蒸发我自己" or similar.
---
# Self-Distillation Pipeline (from Notion)

> Adapted from nuwa-skill (alchaincyf/nuwa-skill) methodology for self-distillation use case.
> Extended with dot-skill (titanwings/colleague-skill) Persona/Work two-layer architecture.
> Data source: Notion API. Target: the user themselves.

## Prerequisites

- Notion API key at `~/.config/notion/api_key`
- Notion integration shared with target pages/databases
- `curl` available (NOT Python urllib — Python SSL often breaks in WSL for Notion API)

## Phase 1: Notion Content Discovery

Use curl-based approach:

```python
NOTION_KEY = open(os.path.expanduser("~/.config/notion/api_key")).read().strip()
def curl_post(url, data):
    cmd = ["curl", "-s", "-X", "POST", "-d", json.dumps(data),
        "-H", f"Authorization: Bearer {NOTION_KEY}",
        "-H", "Notion-Version: 2025-09-03",
        "-H", "Content-Type: application/json", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)
data = curl_post("https://api.notion.com/v1/search", {"page_size": 100})
```

### Page Categorization

| Category | Criteria | Examples |
|----------|----------|---------|
| **original** | User's own writing (parent=page_id, no ~ in title) | "如何提高工作效率" |
| **tool** | Tool/product curation (titles with ~ separator) | "Folo~次世代信息源聚合站" |
| **blog** | Blog database entries | Publieople's Blog entries |
| **workspace** | Top-level workspace pages | Dashboard, 编程, 教育 |
| **database** | Notion databases | 视频选题管理, 一言 |

## Phase 2: Content Extraction (Bulk)

**Use curl, not Python urllib** — Python ssl causes ConnectionResetError in WSL.

### Extraction Strategy

Simple flat extraction (no deep recursion — synced_block/column recursion causes timeouts):

```python
def get_all_blocks(block_id):
    results, cursor = [], None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        if cursor: url += f"&start_cursor={cursor}"
        data = curl_get(url)
        results.extend(data.get("results", []))
        if not data.get("has_more"): break
        cursor = data.get("next_cursor")
    return results

def extract_flat(block_id, max_depth=3):
    lines = []
    for block in get_all_blocks(block_id):
        text, btype, has_children = extract_text(block)
        lines.append((text, btype, depth))
        if has_children and btype in ("bulleted_list_item", "numbered_list_item", "toggle", "column_list"):
            lines.extend(extract_flat(block["id"], max_depth - 1))
    return lines
```

**Rate limiting**: ~3 req/s. Add `time.sleep(0.3)` between calls. ~3-5 min for 50 pages.

## Phase 3: Quantitative Expression DNA Analysis

Compute key metrics:

```python
chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
english_terms = len(set(re.findall(r'[a-zA-Z][a-zA-Z]+', text)))
first_person_wo = len(re.findall(r'(?<![也你他她])我(?!们)', text))
questions = len(re.findall(r'[?？]', text))
hedging = len(re.findall(r'可能|大概|也许|或许|建议|仅供参考|通常|一般', text))
certainty = len(re.findall(r'一定|必须|绝对|毫无疑问|当然|所有的', text))
slang = len(re.findall(r'主播|省流|干货|平替|鬼话|死磕|两条腿|木桶效应', text))
```

### Key Ratios
- `hedging / certainty`: >2.0 = cautious/advice-giving; <0.5 = authoritative
- `first_person / 1000_chars`: <5 = tutorial/impersonal style

## Phase 4: Mental Model Extraction + Triple Verification

Extract candidate mental models, verify each:

### 1. 跨域复现 (Cross-domain Recurrence)
Pattern appears in ≥2 domains? If yes, it's a genuine tendency, not one-off.

### 2. 生成力 (Generative Power)
Can it predict the user's position on a NEW un-written topic?

### 3. 排他性 (Exclusivity)
Not all smart people would think this. Does it distinguish the user?

**Verdict**: 3/3 → Core model | 1-2/3 → Downgrade to decision heuristic | 0/3 → Discard

## Phase 5: Skill Directory Structure

```
~/.hermes/skills/{user}-perspective/
├── SKILL.md                        # The perspective skill
├── work.md                         # Methods, workflows, judgment frameworks (dot-skill)
├── persona.md                      # Mental models, expression DNA, values (dot-skill)
├── meta.json                       # Structured metadata
├── backup.sh                       # Version management script
└── references/
    └── research/
        ├── 01-writings.md          # Article/writing analysis
        ├── 02-conversations.md     # Conversational style analysis
        ├── 03-expression-dna.md    # Quantitative expression analysis
        ├── 04-external-views.md    # (skip for self-distillation)
        ├── 05-decisions.md         # Decision patterns from content
        └── 06-timeline.md          # Timeline from article dates
```

## Phase 6: SKILL.md Generation

Follow the nuwa-skill template structure:

1. **YAML frontmatter**: name, description with trigger conditions + companion file references + evolution mode note
2. **Evolution mode triggers**: "我有新文件" → append | "这不对" → correct | `/update-skill {slug}` → full update
3. **Answer workflow / Agentic Protocol**:
   - Question classification table with 5 types (efficiency, knowledge, technical decisions, writing/sharing, **meta-questions**)
   - Activation modes (full roleplay, reference-only, identity mode)
   - Boundary conditions with state machine (auto-restore after single off-topic, auto-exit after 3 consecutive, permanent exit on "退出")
   - Per-response checkpoint (style, scope, certainty, source)
4. **Identity card**: "我是谁" first-person intro
5. **3-7 mental models**: each with evidence (≥2 sources), application, limitation
6. **5-10 decision heuristics**: if-X-then-Y rules with concrete cases
7. **Expression DNA**: quantified style rules for roleplay
8. **Timeline**: key milestones
9. **Values & anti-patterns**: what I pursue, what I reject, internal tensions (≥2)
10. **Intellectual lineage**: who influenced me → who I influence
11. **Honest boundaries**: ≥3 specific limitations, research date
12. **Source appendix**: source count, co-author notes

## Phase 7: Quality Verification (Phase 4)

Run 3 independent tests with subagents:

### 1. 已知测试 (Known Question Test)
Pick 3 topics user HAS written about → answer using new Skill → compare with actual position.
- PASS: direction consistent, cites original source if relevant
- FAIL: contradicts known position

### 2. 边缘测试 (Edge Case Test)
Pick 1 topic user has NOT written about → observe uncertainty.
- PASS: acknowledges boundary ("没写过"), avoids categorical answers, gives framework-level advice, maintains voice
- FAIL: overconfident on unfamiliar topic

### 3. 风格测试 (Voice Check)
~150 words → evaluate 5 dimensions, all must pass:
- 句式: short paragraphs, "省流" opener, numbered lists
- 词汇: user's words, no foreign slang
- 节奏: conclusion→expand→advice→humble close
- 心智模型: 2+ models naturally applied
- 确定性: appropriate hedging, no absolute claims

### Pass Criteria Table
| Check | Standard |
|-------|----------|
| Mental models | 3-7, each with evidence |
| Each model's limitation | Clear failure conditions |
| Expression DNA recognition | Recognizable within 100 chars |
| Honest boundaries | ≥3 specific items |
| Internal tensions | ≥2 contradictions |
| Primary source ratio | >50% |

## Phase 8: Version Management (dot-skill)

### Companion Files

| File | Content | Purpose |
|------|---------|---------|
| `work.md` | Methods, workflows, tech stack, judgment frameworks | What the user does |
| `persona.md` | Mental models, expression DNA, values, tensions | Who the user is |
| `meta.json` | Structured metadata (name, role, tags, source stats) | Machine-readable catalog |
| `backup.sh` | Version backup script (keep last 20) | Rollback, diff, history |

### Version Backup

```bash
BACKUP_DIR="$SKILL_DIR/.versions/$(date +%Y%m%d_%H%M%S)_${COMMENT}"
mkdir -p "$BACKUP_DIR"
cp SKILL.md work.md persona.md references -t "$BACKUP_DIR" 2>/dev/null
ls -dt "$SKILL_DIR"/.versions/*/ | tail -n +21 | xargs rm -rf
```

## Pitfalls

### Notion API
- Use `curl` via subprocess, not Python urllib (SSL reset in WSL)
- Flat extraction with depth limit — avoid deep recursion
- Rate limit ~3 req/s
- Database entries may return 404 on blocks endpoint — skip gracefully
- Empty "关于我" pages are common — skip

### Co-authored Content Contamination ⚠️
- **Check 鸣谢 sections** for multi-author attribution before analysis
- **Cross-reference** 鸣谢 with content sections to identify author per section
- **Slang marker detection**: "主播" appearing only in one article → likely co-authored
- **Run DNA twice**: full corpus vs user-only. If stats shift >20%, contamination confirmed
- **Verify heuristic sourcing**: every heuristic must trace to a user-only section
- If a heuristic's only evidence is co-authored, exclude it unless independently verifiable

### Expression Analysis
- Strip code blocks and markdown markers before sentence counting
- Tutorial-style Chinese writing often has 0 first-person — use blog/personal articles for "我" count
- Hedging markers (可能, 建议, 仅供参考) are genre-typical for tutorials — don't over-interpret

### Self-Distillation Specific
- **Self-cognition bias**: note in honest boundaries
- **No conversations dimension**: no public interviews — note as info gap
- **No external views**: no third-party analysis — skip this research file
- **Privacy**: skip financial/personal pages

### Correction & Evolution
- Classification: is the correction Work (methods) or Persona (thinking/expression)?
- Record corrections to `corrections.json` — format: `{scene, wrong, correct}`
- Patch work.md or persona.md, not SKILL.md directly
- After correction, propagate to SKILL.md if mental models/heuristics changed
