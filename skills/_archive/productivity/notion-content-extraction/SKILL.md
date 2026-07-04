---
name: notion-content-extraction
description: Recursive extraction of structured text content from complex Notion pages — handles synced_blocks, column_lists, nested lists, toggles, and all rich text block types. Use when the user wants to export all content from a Notion page as structured data, migrate Notion data to another format, or build a JSON representation from nested Notion blocks.
---

# Notion Content Extraction — Recursive Block Tree Walker

Extract all text content from a Notion page, recursively traversing complex nested structures like `synced_block`, `column_list`, `column`, `toggle`, and nested bulleted lists.

## When to Use

- User says "get all content from my Notion page"
- User wants to export Notion page data to another format (JSON, resume schema, blog post, etc.)
- User asks you to read a Notion page that has complex nesting (columns, synced blocks, toggles)
- User asks to extract structured profile/resume data from Notion
- Data migration from Notion to a third-party system

## Setup

Requires Notion API key at `~/.config/notion/api_key`.

## ⚠️ WSL SSL Workaround (Notion API)

On WSL (Windows Subsystem for Linux), Python's `urllib.request` may fail with `ConnectionResetError: [Errno 104]` when calling the Notion API. This is a known SSL/TLS handshake issue between WSL's Python and Notion's API servers.

**Fix:** Use `curl` subprocess instead of `urllib.request` for all Notion API calls. The `subprocess` module wraps `curl` with the same headers, avoiding the SSL handshake problem entirely.

```python
import json, subprocess

NOTION_KEY = open(os.path.expanduser("~/.config/notion/api_key")).read().strip()
NOTION_VERSION = "2025-09-03"

def api_get(url, data=None):
    cmd = ["curl", "-s"]
    if data:
        cmd += ["-X", "POST", "-d", json.dumps(data)]
    cmd += [
        "-H", f"Authorization: Bearer {NOTION_KEY}",
        "-H", f"Notion-Version: {NOTION_VERSION}",
        "-H", "Content-Type: application/json",
        url
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def get_blocks(block_id, page_size=100):
    results = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size={page_size}"
        if cursor:
            url += f"&start_cursor={cursor}"
        data = api_get(url)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results
```

The `get_blocks` function above also adds pagination support (the urllib version was single-page only, which silently truncated content on pages with 100+ blocks).

**Detection:** If you get `ConnectionResetError` or `URLError: [Errno 104]` when calling Notion API, switch to the curl subprocess pattern above.

## Core Pattern: Recursive Block Walker

```python
import urllib.request, json

NOTION_KEY = open("/root/.config/notion/api_key").read().strip()
NOTION_VERSION = "2025-09-03"

def get_blocks(block_id):
    """Fetch children blocks from Notion API."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": NOTION_VERSION,
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("results", [])

def extract_text_from_block(block):
    """Extract plain_text from any block type. Returns (text, block_type, has_children)."""
    btype = block.get("type", "unknown")
    is_container = block.get("has_children", False)
    text = ""
    
    MAP = {
        "heading_1": "heading_1", "heading_2": "heading_2", "heading_3": "heading_3",
        "paragraph": "paragraph", "bulleted_list_item": "bulleted_list_item",
        "numbered_list_item": "numbered_list_item", "to_do": "to_do",
        "callout": "callout", "quote": "quote", "toggle": "toggle",
    }
    
    if btype in MAP:
        rich_text = block.get(btype, {}).get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich_text)
    elif btype == "divider":
        text = "---"
    elif btype == "image":
        text = "[IMAGE]"
    elif btype == "synced_block":
        is_container = True  # synced_block always has children
    elif btype == "column_list":
        is_container = True
    elif btype == "column":
        is_container = True
    
    return text, btype, is_container

def walk_blocks(parent_block_id, depth=0):
    """
    Recursively walk all blocks. Returns flat list of (text, type, depth, is_container).
    Handles: synced_block, column_list, column, toggle with children, nested lists.
    """
    results = []
    blocks = get_blocks(parent_block_id)
    
    for block in blocks:
        text, btype, has_children = extract_text_from_block(block)
        results.append((text, btype, depth, has_children))
        
        if has_children:
            child_results = walk_blocks(block["id"], depth + 1)
            results.extend(child_results)
    
    return results

# Usage example:
# lines = walk_blocks("your_page_id_or_block_id")
# for text, btype, depth, has_children in lines:
#     indent = "  " * depth
#     prefix = {"heading_1": "# ", "heading_2": "## ", "heading_3": "### ",
#               "bulleted_list_item": "- ", "numbered_list_item": "1. ",
#               "divider": "---", "toggle": "▸ "}.get(btype, "")
#     if text:
#         print(f"{indent}{prefix}{text}")
```

## Block Type Handling

| Block Type | Rendered As | Children? |
|------------|-------------|-----------|
| `heading_1/2/3` | `# ## ###` | No |
| `paragraph` | Plain text | No |
| `bulleted_list_item` | `- list item` | Yes (nested lists) |
| `numbered_list_item` | `1. list item` | Yes (nested lists) |
| `to_do` | `[ ] task` | No |
| `callout` | Plain text | No |
| `quote` | Quoted text | No |
| `toggle` | Collapsible | Yes (children visible when opened) |
| `column_list` | `[COLUMN_LIST]` | Yes (contains `column` blocks) |
| `column` | `[COLUMN]` | Yes (contains content blocks) |
| `synced_block` | Transparent wrapper | Yes (synced copy of content) |
| `divider` | `---` | No |
| `image` | `[IMAGE]` | No |
| `equation` | `[EQUATION]` | No |
| `code` | Code block (plain_text has the code) | No |
| `bookmark` | `[BOOKMARK]` | No |
| `table` | `[TABLE]` | Yes (contains `table_row`) |
| `table_row` | Table cells (`| cell | cell |`) | No |
| `embed`/`video`/`file`/`pdf` | `[MEDIA: type]` | No |

## Key Implementation Details

1. **synced_block handling**: The block itself has no visible content — always walk its children
2. **column_list handling**: Contains `column` children. Each `column` contains the actual content blocks
3. **Nested bulleted lists**: A `bulleted_list_item` with `has_children=true` contains more list items as children — walk them recursively with increased depth
4. **toggle blocks**: The toggle heading itself has text; its children appear when expanded
5. **Note the difference**: `heading_1/2/3` have `has_children=false` in Notion. The block itself is a leaf

## Special Case: Notion-Version 2025-09-03

- Databases are called "data sources" in responses
- Page content still uses the same `/blocks/{id}/children` endpoint
- API rate limit: ~3 req/s
- Block IDs are UUIDs (with or without dashes — Notion accepts both)

## Distillation Pipeline: Notion → Persona/Character SKILL.md

When using Notion content as a data source to distill someone's thinking patterns (their mental models, decision heuristics, expression DNA) into a perspective-style SKILL.md, follow this workflow:

### Step 1: Workspace Survey

Search the workspace to identify **original content** (user's own writing) vs curated collections vs system pages:

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"page_size": 100, "sort": {"direction": "descending", "timestamp": "last_edited_time"}}'
```

Priority for distillation (high to low):
1. **Original articles & blog posts** (parent=page_id) — richest signal for thinking patterns
2. **Custom databases** with user-written entries — shows curation taste and domain expertise
3. **Project documentation** and personal notes — reveals decision-making process
4. **Tool/product reviews** (curated links) — shows evaluation criteria

### Step 2: Identify Self-Written Pages

Not all pages in a workspace are written by the user. Classify by parent type:
- `parent=page_id` with `!has_children` → likely a standalone article (high value)
- `parent=data_source_id` → a database entry (may be partially auto-generated)
- `parent=database_id` → a database/collection itself

### Step 3: Extract Full Content

Use the recursive block walker (curl subprocess version for WSL) to extract every page. Batch-process multiple pages for efficiency.

### Step 4: Analyze for Distillation Signals

After extraction, identify these patterns in the aggregated content:

| What to Look For | Where to Find It |
|-----------------|-----------------|
| **Mental models** (repeated patterns across domains) | Same concept appearing in 2+ unrelated articles |
| **Decision heuristics** (if-X-then-Y rules) | Recommended workflows, how-to instructions, troubleshooting steps |
| **Expression DNA** (sentence rhythm, word choice, formality) | Across all articles — look for sentence length, punctuation patterns, tech term mixing |
| **Core values** (what they praise/reject/emphasize) | Article introductions, conclusion sections, tool recommendation criteria |
| **Anti-patterns** (what they explicitly avoid/reject) | "不要..." warnings, "避免..." sections, tool comparisons |
| **Honest boundaries** (what they admit they don't know) | Self-deprecating remarks, "实际上基础并不牢固" confessions |
| **Learning style** (how they approach new domains) | Descriptions of their learning process ("偏好上手实践的体验式学习") |

### Step 5: Generate SKILL.md

The output should follow the nuwa-skill template format:
- Identity card (who they are, what they do)
- 3-7 mental models (each with: one-liner, cross-domain evidence, application, limitation)
- 5-10 decision heuristics (if-X-then-Y, with concrete examples)
- Expression DNA (sentence patterns, vocabulary, rhythm, humor, certainty level)
- Values & anti-patterns (what they pursue, what they reject, internal tensions)
- Honest boundaries (limitations of this distillation)
- Source appendix (which Notion pages were used)

This is the same format as the `*-perspective` skills in the openclaw-imports category (steve-jobs-perspective, paul-graham-perspective, etc.), adapted for Notion-sourced personal data instead of public-web research.

## Schema Transformation Pattern

After extracting content via `walk_blocks()`, you typically need to map it to a target schema. Common patterns:

### Profile/Resume Source Detection
When extracting a resume/profile page, look for structural cues:
- `heading_1` → page title
- `paragraph` with bold "姓名：" → name field
- `heading_2` → section headers (求职意向, 教育背景, 核心技能, 项目经历, etc.)
- `bulleted_list_item` after section headers → section content
- `column_list` → side-by-side contact info / personal details
- nested `bulleted_list_item` → sub-items in skill categories

### General Mapping Approach
1. Walk blocks recursively to get structured content tree
2. Identify sections by `heading_2` blocks
3. Group content blocks under their section heading
4. Map each section to the target schema's field
5. Handle special structures (column_lists, nested lists) manually
6. Build the output JSON/dict from the mapped sections
