#!/usr/bin/env python3
"""
Bilibili Follow List Extractor — Hermes Automation Script

Extracts all followed users from a Bilibili account via Windows-MCP.
Usage:
    python3 bilibili-extract.py <uid>
    python3 bilibili-extract.py 324858924
"""
import subprocess, json, sys, re, time, os

MCP_HOST = "http://192.168.10.105:8000/mcp"
AUTH_KEY = "hermes123"
SESSION_FILE = "/tmp/mcp_session.txt"

def mcp_init():
    """Establish MCP session, return session_id."""
    cmd = f"""curl -v -s {MCP_HOST} \
      -H "Authorization: Bearer {AUTH_KEY}" \
      -H "Accept: application/json, text/event-stream" \
      -H "Content-Type: application/json" \
      -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2025-03-26","capabilities":{{}},"clientInfo":{{"name":"hermes-extractor","version":"1.0"}}}}}}' 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'mcp-session-id:' in line:
            sid = line.split('mcp-session-id:')[1].strip().strip('\r')
            with open(SESSION_FILE, 'w') as f:
                f.write(sid)
            print(f"✓ Session: {sid[:16]}...")
            return sid
    raise RuntimeError("Failed to establish MCP session")

def mcp_call(tool, args):
    """Call a Windows-MCP tool."""
    session_id = open(SESSION_FILE).read().strip()
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 2,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    # Escape for shell
    payload_b64 = subprocess.check_output(['base64'], input=payload.encode()).decode().strip()
    cmd = f"echo '{payload_b64}' | base64 -d | curl -s {MCP_HOST} -H 'Authorization: Bearer {AUTH_KEY}' -H 'Accept: application/json, text/event-stream' -H 'Content-Type: application/json' -H 'Mcp-Session-Id: {session_id}' -d @-"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def extract_json_result(raw):
    """Extract content from MCP SSE response."""
    for line in raw.split('\n'):
        if line.startswith('data: '):
            try:
                d = json.loads(line[6:])
                for item in d.get('result', {}).get('content', []):
                    if item.get('type') == 'text':
                        return item['text']
            except:
                continue
    return ""

def press_shortcut(key):
    result = mcp_call("Shortcut", {"shortcut": key})
    print(f"  ⌨️  {key}")
    time.sleep(1)

def set_clipboard(text):
    result = mcp_call("Clipboard", {"mode": "set", "text": text})
    print(f"  📋 Clipboard: {len(text)} chars")
    time.sleep(1)

def main():
    uid = sys.argv[1] if len(sys.argv) > 1 else input("Enter Bilibili UID: ")
    
    print("=== Bilibili Follow List Extractor ===\n")
    
    # 1. Init MCP session
    print("1/6 Establishing MCP session...")
    mcp_init()
    
    # 2. Navigate to Bilibili space
    print("2/6 Opening Bilibili space...")
    press_shortcut("ctrl+l")
    set_clipboard(f"https://space.bilibili.com/{uid}")
    press_shortcut("ctrl+v")
    press_shortcut("enter")
    time.sleep(4)
    
    # 3. Build and execute bookmarklet
    print("3/6 Building bookmarklet...")
    bookmarklet = f"""javascript:(async()=>{{let all=[];for(let p=1;p<=13;p++){{let r=await fetch("https://api.bilibili.com/x/relation/followings?vmid={uid}&pn="+p+"&ps=50",{{credentials:"include"}});let d=await r.json();if(d.code===0&&d.data?.list)all.push(...d.data.list)}}document.body.innerHTML="<pre>共 "+all.length+" 人\\n\\n"+all.map((u,i)=>(i+1)+". "+u.uname+" (UID:"+u.mid+")").join("\\n")+"</pre>";document.title=all.length}})()"""
    
    press_shortcut("ctrl+l")
    set_clipboard(bookmarklet)
    press_shortcut("ctrl+v")
    
    print("4/6 Executing bookmarklet...")
    press_shortcut("enter")
    print("  ⏳ Waiting for API calls (8s)...")
    time.sleep(8)
    
    # 4. Scrape results
    print("5/6 Scraping results...")
    raw = mcp_call("Scrape", {"use_dom": True, "url": f"https://space.bilibili.com/{uid}"})
    text = extract_json_result(raw)
    
    # Parse content section
    if 'Content:' in text:
        text = text.split('Content:', 1)[1].strip()
    
    # Extract user lines
    users = [l.strip() for l in text.split('\n') if re.match(r'^\d+\.\s', l.strip())]
    
    # 5. Save to file
    output_path = os.path.expanduser(f"~/bilibili_follow_{uid}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Bilibili Follow List\n")
        f.write(f"UID: {uid}\n")
        f.write(f"Total: {len(users)}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 40 + "\n\n")
        for u in users:
            f.write(u + '\n')
    
    print(f"\n6/6 Done!")
    print(f"  ✅ {len(users)} users extracted")
    print(f"  💾 Saved to: {output_path}")
    
    # Summary
    print(f"\n=== Summary ===")
    # Categorize
    ai_users = [u for u in users if 'AI' in u or '智能' in u or 'ComfyUI' in u]
    game_users = [u for u in users if any(k in u for k in ['游戏', '方舟', '炉石', 'Subnautica'])]
    print(f"  AI/Tech: {len(ai_users)}")
    print(f"  Gaming: {len(game_users)}")
    print(f"  First 10: ")
    for u in users[:10]:
        print(f"    {u}")

if __name__ == "__main__":
    main()
