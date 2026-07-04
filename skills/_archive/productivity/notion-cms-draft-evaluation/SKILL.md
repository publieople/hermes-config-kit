---
name: notion-cms-draft-evaluation
description: "Evaluate draft content completeness in a Notion-based CMS (NotionNext, Nobelium) and expand using a writing persona. Covers querying drafts, fetching block content, scoring readiness with block-level metrics, batch publishing, and persona-guided content expansion back into Notion."
version: 1.0.0
author: Hermes Agent
tags: [notion, cms, draft, content, evaluation, writing, publishing]
---

# Notion CMS Draft Evaluation & Content Expansion

Evaluate draft articles in a Notion database by analyzing their block-level content (word count, section structure, headings, images, code blocks). Decide publish-readiness, batch-publish ready articles, and expand incomplete drafts using an author persona (perspective skill).

## When to Use

Load this skill when:

- User says "帮我完善这几篇文章" / "帮我看看哪些可以发"
- User wants to evaluate their Notion-based blog draft queue and recommend what to publish
- User wants to batch-publish drafts that pass a quality threshold
- User wants to expand draft content in their own writing style

**Prerequisite:** `notionnext-content-sync-diagnostics` covers the initial discovery phase (finding drafts). This skill picks up from there.

## Setup

Requires Notion API key at `~/.config/notion/api_key`.

## Workflow

### Phase 1: Discover Drafts

Query the database for all entries with `status = "Draft"` and `type = "Post"`:

```python
import urllib.request, json

NOTION_KEY = open(os.path.expanduser("~/.config/notion/api_key")).read().strip()
DB_ID = "your_database_id"

def query_filtered(filter_props, page_size=100):
    has_more = True
    cursor = None
    results = []
    
    while has_more:
        payload = {"page_size": page_size, "filter": filter_props}
        if cursor:
            payload["start_cursor"] = cursor
        
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{DB_ID}/query",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {NOTION_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        results.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        cursor = data.get('next_cursor')
    
    return results

drafts = query_filtered({
    "and": [
        {"property": "status", "select": {"equals": "Draft"}},
        {"property": "type", "select": {"equals": "Post"}}
    ]
})
```

### Phase 2: Evaluate Completeness

Fetch the first N blocks (30-50 is enough) and extract key metrics:

```python
def get_page_blocks(page_id, limit=50):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size={limit}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get('results', [])

def evaluate_draft(blocks):
    block_types = {}
    total_chars = 0
    headings = []
    flags = {'image': False, 'code': False, 'bullet': False, 'numbered': False}
    
    for b in blocks:
        bt = b.get('type', '?')
        block_types[bt] = block_types.get(bt, 0) + 1
        
        if bt in ('paragraph', 'heading_1', 'heading_2', 'heading_3',
                  'bulleted_list_item', 'numbered_list_item', 'quote', 'callout', 'toggle'):
            texts = b.get(bt, {}).get('rich_text', [])
            text = ''.join([t.get('plain_text', '') for t in texts])
            total_chars += len(text)
            if bt.startswith('heading'):
                headings.append(text[:60])
        elif bt == 'image':    flags['image'] = True
        elif bt == 'code':     flags['code'] = True
        elif bt == 'bulleted_list_item':  flags['bullet'] = True
        elif bt == 'numbered_list_item':  flags['numbered'] = True
    
    if total_chars > 800 and len(blocks) > 20:
        tier = "ready"
    elif total_chars > 300 and len(blocks) > 8:
        tier = "partial"
    elif total_chars > 50:
        tier = "skeleton"
    else:
        tier = "empty"
    
    return {
        "total_blocks": len(blocks),
        "total_chars": total_chars,
        "headings": headings,
        "has_image": flags['image'],
        "has_code": flags['code'],
        "has_bullet": flags['bullet'],
        "has_numbered": flags['numbered'],
        "tier": tier
    }
```

**Completeness Tiers:**

| Tier | Threshold | Meaning |
|------|-----------|---------|
| `ready` | >800 chars, >20 blocks, has headings | Ready to publish after quick proofread |
| `partial` | 300-800 chars, 8-20 blocks | Has framework + some content, needs ~50% more |
| `skeleton` | 50-300 chars | Headings/framework only, body empty |
| `empty` | <50 chars | Title only or intro sentence |

### Phase 3: Batch Publish

For `ready` articles, ask user for confirmation then publish:

```python
def publish_draft(page_id):
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps({
            "properties": {"status": {"select": {"name": "Published"}}}
        }).encode(),
        method="PATCH",
        headers={
            "Authorization": f"Bearer {NOTION_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

### Phase 4: Expand Content Using a Persona

When expanding drafts in the author's voice:

1. **Load the perspective/persona skill** (e.g. `publieople-perspective`) to understand their:
   - Writing style (sentence length, vocabulary, formality)
   - Mental models (how they frame problems)
   - Expression DNA (use of "省流：", "仅供参考", list vs prose preference)
   - Anti-patterns (things they explicitly reject)

2. **Read full existing content** (all blocks) to understand current structure.

3. **Identify sections needing expansion:**
   - Sections with only a heading (most common gap)
   - Placeholder content (just links, one-liner descriptions)
   - Missing examples or usage tips

4. **Write in the author's style:**
   - Short paragraphs (under 5 lines)
   - Numbered lists and bullets for actionable content
   - Practical examples over abstract theory
   - "先看设置" / "先加后减" framing where applicable
   - "仅供参考" / "推荐使用" qualifiers (not authoritative claims)
   - Cross-reference existing articles where relevant

5. **Append to Notion** (note: appends to the END of the page, not mid-page):

```python
new_blocks = [
    {"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": "your text here"}}]
    }}
]

req = urllib.request.Request(
    f"https://api.notion.com/v1/blocks/{page_id}/children",
    data=json.dumps({"children": new_blocks}).encode(),
    method="PATCH",
    headers={
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
)
with urllib.request.urlopen(req) as resp:
    json.loads(resp.read())
```

### Phase 5: Verify

After publishing, verify by:
- Checking the live blog URL for the new article
- Looking at the article list page for the updated count
- For NotionNext with `NEXT_REVALIDATE_SECOND = 5`, new articles appear within seconds

## Notion API Block Formatting Reference

```python
# Paragraph
{"type": "paragraph", "paragraph": {
    "rich_text": [{"type": "text", "text": {"content": "text"}}]
}}

# Heading 2
{"type": "heading_2", "heading_2": {
    "rich_text": [{"type": "text", "text": {"content": "Title"}}]
}}

# Bulleted list
{"type": "bulleted_list_item", "bulleted_list_item": {
    "rich_text": [{"type": "text", "text": {"content": "item"}}]
}}

# Toggle with children
{"type": "toggle", "toggle": {
    "rich_text": [{"type": "text", "text": {"content": "Title"}}],
    "children": [
        {"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "hidden content"}}]}}
    ]
}}
```

## Pitfalls

- **Deleting blocks via API is unreliable** — Notion may return 200 but blocks persist. Prefer appending.
- **Toggle children limit** — max 100 child blocks per toggle.
- **No mid-page insertion** — Notion API only appends to the end. For proper placement, either delete-and-recreate or let the user rearrange in Notion UI.
- **Rate limiting** — ~3 req/s. Add `time.sleep(0.5)` between batch requests.
- **WSL SSL issue** — `urllib.request` may fail with `ConnectionResetError: [Errno 104]` on WSL. Use `curl` subprocess as fallback (see `notion-content-extraction` skill).
- **Property name customization** — Users may override Notion property names via env vars. Always verify the database schema first.
