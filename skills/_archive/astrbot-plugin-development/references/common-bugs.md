# Common bugs hit in real sessions

## `@register` is on the class, not a function

When AST-walking `main.py` to verify the plugin, include `ast.ClassDef` in the filter, not just `FunctionDef`:

```python
# WRONG — misses @register
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef):
        ...

# RIGHT
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for d in n.decorator_list:
            ...
```

Symptom: verification script reports `@register` missing even though it's there in source.

## Ad-hoc script can't check its own existence

If your `/tmp/hermes-verify-*.py` checks "is this script itself on disk" with `os.path.exists(__file__)`, the answer is always True (the running process holds it). Use `os.path.abspath(__file__)` and compare:

```python
this_script = os.path.abspath(__file__)
for s in stray:
    s_abs = os.path.abspath(s)
    if s_abs == this_script:
        chk(f"is self", True)  # skip — expected
    else:
        chk(f"no leftover {s}", not os.path.exists(s))
```

## `ast.literal_eval` works for dict/list literals but not for `dict[str, str]` annotations

A class field like `_ALIAS: dict[str, list[str]] = { ... }` — the AST node for the right-hand side is a `Dict`, which `ast.literal_eval` handles. But **the annotation** `dict[str, list[str]]` is a `Subscript` node, and `ast.literal_eval` does NOT evaluate subscript annotations. Just skip the annotation when walking the AST and look at the value only.

## System python lacks httpx/aiohttp; AstrBot's venv has them

Use `~/.local/share/uv/tools/astrbot/bin/python3` for any ad-hoc script that needs to exercise the plugin's HTTP code. System python's `python3` will fail with `ModuleNotFoundError: No module named 'httpx'`.

## `git add -A` before `rm -f` commits the deleted file

Sequence matters when you have a test script you want to clean up before committing:

```bash
# WRONG — script ends up in the commit
git add -A
rm -f /tmp/...test.py
git commit ...

# RIGHT
git add -A
git commit ...
rm -f /tmp/...test.py
```

Even better: keep test scripts outside the repo entirely (in /tmp), never in the plugin dir, so the question never arises.

## AstrBot logs are in journalctl, not in a logfile

v4.x sends everything to systemd journal. `~/astrbot/logs/` may be empty (or just old). Use:

```bash
sudo journalctl -u astrbot --since '30 seconds ago' --no-pager | grep -iE '<plugin>|error|exception|traceback'
```

A successful load looks like:

```
[Core] [INFO] [star.star_manager:1078]: Loading plugin <name> ...
[Core] [INFO] [provider.func_tool_manager:388]: Added llm tool: <tool_name>   (if applicable)
[Core] [INFO] [star.star_manager:1162]: Plugin <name> (v<ver>) by <author>: <desc>
```

A failed load has `Traceback (most recent call last):` somewhere in the same window. **Mismatched plugin_id between `metadata.yaml` and `@register` will fail load with no obvious clue** — check that first.

## AstrBot downloads images to local temp; Image.url/file/path are ALL local paths

**Critical finding (v4.26 + NapCatQQ, confirmed via live logger output):** AstrBot downloads images to `data/temp/` and sets **all three fields** to the **same local absolute path**:

```
Image: file='/home/po/astrbot/data/temp/media_image_xxx.jpg'
       url='/home/po/astrbot/data/temp/media_image_xxx.jpg'
       path='/home/po/astrbot/data/temp/media_image_xxx.jpg'
```

There is NO `https://gchat.qpic.cn/...` CDN URL in any field. You **cannot** pass `Image.url` or `Image.file` to a third-party API expecting a public HTTP URL.

**Extract the local path:**

```python
src = c.path or c.file or ""   # always a local filesystem path
```

**Then use multipart file upload instead of URL param:**

```python
# WRONG — fails for local paths (no public URL to give the API)
r = await client.get(url, params={"models": "genai", "url": src})

# RIGHT — uses file upload for local, URL param for remote
if src.startswith(("http://", "https://")):
    r = await client.get(url, params={"models": "genai", "url": src})
else:
    async with aiofiles.open(src, "rb") as f:
        content = await f.read()
    r = await client.post(url, data={"models": "genai"},
                          files={"media": (os.path.basename(src), content)})
```

`aiofiles` is bundled with AstrBot — no extra pip install.

**Why this happens:** AstrBot's media pipeline downloads all images to disk before event delivery. On aiocqhttp, the adapter's `convert_message` also calls `get_group_file_url` / `get_private_file_url` for file segments, but for Image segments the original `url` from napcat's message data is overwritten by the local temp path during framework processing. The intent is for plugins to read from disk or re-upload via file service, not to forward CDN URLs.

## Reply.chain contains the quoted message's Image

When a user quotes a message (e.g. `[引用消息] /鉴图`), the event contains a `Reply` component. Its `.chain` field (`list[BaseMessageComponent]`) holds the full quoted message including Image segments. Scan it:

```python
for comp in event.get_messages():
    if isinstance(comp, Reply) and comp.chain:
        url = _first_image_url(comp.chain)
        if url:
            return url
```

Import: `from astrbot.core.message.components import Image, Reply`

## Third-party API free tier rarely gives you per-model scores

`sightengine genai` only returns `ai_generated` (0-1) on free tier. Per-generator scores require contacting sales. Don't fake them in your plugin output — just say "AI probability: 0.99" and stop. Honest > impressive.
