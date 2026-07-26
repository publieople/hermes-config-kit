---
name: bilibili-follow-extractor
description: Extract complete Bilibili follow/subscription list (all pages, 630+ users) via browser JavaScript injection + Windows-MCP, 100x faster than manual scrolling.
version: 1.0.0
author: Hermes Agent (Publieople)
tags: [bilibili, social-media, data-extraction, windows-mcp, browser-automation]
---

# Bilibili Follow List Extractor

Extract all ~630 followed users from a Bilibili account in ~10 seconds, without manually scrolling through 27 pages.

## How It Works

1. **Windows-MCP** opens Chrome and navigates to the user's Bilibili space
2. A `javascript:` bookmarklet URL is pasted into the address bar, executing JavaScript in the page context
3. The script calls `api.bilibili.com/x/relation/followings` with the user's auth cookies (auto-included via `credentials: "include"`)
4. Fetches all 13 pages (50 users/page) in sequence, concatenates the results
5. Displays the full list as plain text on the page
6. **Hermes scrapes** the page DOM to save the data

## Prerequisites

- **Windows-MCP** running on Windows (`streamable-http` mode)
- **Hermes MCP client** connected to Windows-MCP (see `windows-mcp-setup` skill)
- User must be **logged into Bilibili** in Chrome

## Step-by-Step

### 1. Get User's Bilibili UID

From the profile page URL: `space.bilibili.com/{UID}`

Or extract from the Snapshot UI tree - look for links containing "关注数" or "粉丝数".

### 2. Navigate to Bilibili Space

Using Windows-MCP tools:

```bash
# Open address bar
mcp_exec "Shortcut" '{"shortcut":"ctrl+l"}'
sleep 1

# Paste URL
mcp_exec "Clipboard" '{"mode":"set","text":"https://space.bilibili.com/{UID}"}'
sleep 1

# Navigate
mcp_exec "Shortcut" '{"shortcut":"ctrl+v"}'
sleep 1
mcp_exec "Shortcut" '{"shortcut":"enter"}'
sleep 4
```

### 3. Execute JavaScript Bookmarklet

The key trick: paste a `javascript:` URL into Chrome's address bar. This executes in the page context where auth cookies are available.

**One-liner script (paste as-is):**

```javascript
javascript:(async()=>{let all=[];for(let p=1;p<=13;p++){let r=await fetch("https://api.bilibili.com/x/relation/followings?vmid={UID}&pn="+p+"&ps=50",{credentials:"include"});let d=await r.json();if(d.code===0&&d.data?.list)all.push(...d.data.list)}document.body.innerHTML="<pre>共 "+all.length+" 人\n\n"+all.map((u,i)=>(i+1)+". "+u.uname+" (UID:"+u.mid+")").join("\n")+"</pre>";document.title=all.length})()
```

**Execution:**

```bash
# Focus address bar
mcp_exec "Shortcut" '{"shortcut":"ctrl+l"}'
sleep 1

# Paste bookmarklet
mcp_exec "Clipboard" '{"mode":"set","text":"<the bookmarklet code above>"}'
sleep 1
mcp_exec "Shortcut" '{"shortcut":"ctrl+v"}'
sleep 1

# Execute
mcp_exec "Shortcut" '{"shortcut":"enter"}'

# Wait for API calls (13 pages × ~0.5s = ~7s)
sleep 8
```

### 4. Scrape the Results

The page now contains the full list as plain text. Extract it:

```bash
# Save to file
mcp_exec "Scrape" '{"use_dom":true,"url":"https://space.bilibili.com/{UID}","query":"列出页面上所有用户信息行（数字. 用户名 (UID:数字)）"}'
```

Parse the `Content:` section of the response to get the full list.

### 5. Save to File

```python
import re
text = response_content
users = [l.strip() for l in text.split('\n') if re.match(r'^\d+\.\s', l.strip())]
print(f'Total: {len(users)} users')
with open('bilibili_follow_list.txt', 'w') as f:
    f.write(text)
```

## Helper: mcp_exec Function

Use this wrapper to call Windows-MCP tools:

```python
import subprocess, json

SESSION_FILE = '/tmp/mcp_session.txt'

def mcp_call(tool, args):
    """Call a Windows-MCP tool via the HTTP MCP server."""
    session_id = open(SESSION_FILE).read().strip()
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 2,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    cmd = f"""curl -s http://192.168.10.105:8000/mcp \
      -H "Authorization: Bearer hermes123" \
      -H "Accept: application/json, text/event-stream" \
      -H "Content-Type: application/json" \
      -H "Mcp-Session-Id: {session_id}" \
      -d '{payload}'"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout
```

## Session Management

Windows-MCP sessions expire after a few minutes. Re-establish before use:

```bash
SID=$(curl -v -s http://192.168.10.105:8000/mcp \
  -H "Authorization: Bearer hermes123" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"hermes","version":"1.0"}}}' 2>&1 | grep -i "mcp-session-id" | head -1 | sed 's/.*mcp-session-id: //' | tr -d '\r')
echo "$SID" > /tmp/mcp_session.txt
```

## Pitfalls

- **API rate limiting**: Bilibili may throttle if you fetch too fast. The 13-page loop with sequential fetch is safe.
- **javascript: protocol stripped**: Chrome may strip `javascript:` from pasted text. If so, manually type `javascript:` then paste the rest.
- **CORS**: Trying to call the API from the DevTools Console won't work (different origin). The `javascript:` bookmarklet bypasses this by executing in-page.
- **UID changes**: If the user changes their Bilibili username/UID, update the UID in the script.
- **Page count**: 630 users / 50 per page = 13 pages. Adjust `p<=13` if the follow count changes.
- **Scrape truncation**: The Scrape tool caps at ~5000 chars for large pages. Use the `query` parameter to extract only user lines, or save the full text output.

## References

See `references/javascript-bookmarklet.md` for the general technique of using `javascript:` protocol to bypass CORS and execute authenticated API calls from the browser address bar, applicable to any site (not just Bilibili).
