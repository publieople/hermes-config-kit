---
name: hermes-external-integration
description: Integrate Hermes Agent with external desktop applications, IDEs, and AI tools — mapping their integration interfaces (custom API endpoints, MCP support, terminal hooks) to Hermes' built-in capabilities (API Server, MCP Server Mode, CLI spawning). Use when asked to "connect Hermes to X" or "make Hermes work with Y" for any third-party app.
version: 1.0.0
---

# Hermes External Application Integration

## When to Use

Use this skill when the user asks to integrate Hermes with an external application — desktop AI assistants, IDEs, note-taking apps, or any third-party tool. Triggers include:

- "Can you integrate Hermes into [AppName]?"
- "Can [AppName] use you as a backend?"
- "Make Hermes work with [AppName]"
- Any request to bridge Hermes with another application

## Methodology: 3-Step Mapping

### Step 1: Survey the Target App's Integration Points

Research the app's public interfaces. Common integration interfaces:

| Interface | What to Look For | Example Apps |
|-----------|-----------------|--------------|
| **Custom API Endpoints** | OpenAI-compatible endpoint config in settings | Everywhere, Open WebUI, LobeChat, LibreChat, NextChat |
| **MCP Client support** | Can it connect to external MCP servers? | Claude Desktop, Cursor, VS Code, Everywhere |
| **MCP Server** | Does it expose tools as an MCP server? | Hermes, some desktop assistants |
| **Plugin/Extension system** | Custom plugin APIs | Obsidian, VS Code, JetBrains |
| **Terminal/Script execution** | Can it run shell commands? | Everywhere, Alfred, Raycast |
| **Webhook/HTTP hooks** | Can it send/receive webhooks? | Many SaaS tools |

Always check:
- README / docs first
- Source code (especially settings/configuration classes)
- Search for: "custom endpoint", "MCP", "plugin", "API key"

### Step 2: Map to Hermes' Capabilities

Hermes offers these integration mechanisms:

| Hermes Feature | How It Works | Best For |
|----------------|-------------|----------|
| **API Server** `hermes gateway` | OpenAI-compatible `/v1/chat/completions` on port 8642 | Apps that support custom OpenAI-compatible endpoints. Full tool access (terminal, browser, web search, vision, memory, skills, cron, etc.) |
| **MCP Server Mode** `hermes mcp serve` | Exposes Hermes as an MCP server over stdio | Claude Desktop, Cursor, VS Code — but **limited to 4 session-browsing tools** (browse_conversations, read_messages, search_sessions, manage_attachments). NOT a tool execution backend. |
| **CLI Spawning** | `hermes chat -q '...'` or tmux PTY | Any app that can run shell commands. Simple but coarse integration. |
| **ACP Server** `hermes acp` | IDE protocol for Agent-to-IDE communication | VS Code, JetBrains — for inline code assistance. |

**Key Decision Tree:**

```
Target app is a messaging platform (QQ, etc.)?
  → Check if Hermes has a native platform adapter first (hermes gateway setup)
  → For QQ without official Bot API approval: use NapCat/OneBot bridge
    See references/napcat-qq-setup.md for the full workflow.

Target app supports Custom API Endpoint (OpenAI-compatible)?
  YES → Use API Server (most powerful, full Hermes toolset)
  
Target app is Claude Desktop / Cursor / VS Code?
  YES → Use MCP Server Mode (but limited to session browsing)
  
Target app can run terminal commands?
  YES → Use CLI spawning as fallback
  
Need full tool execution from MCP client?
  → Build a custom MCP server wrapping Hermes tools
```

### Step 3: Configure the Bridge

#### A) API Server Setup (Recommended for Most Cases)

```bash
# 1. Enable the API server
echo "API_SERVER_ENABLED=true" >> ~/.hermes/.env

# Optional: set auth key
echo "API_SERVER_KEY=your-secret-key" >> ~/.hermes/.env

# 2. Start the gateway
hermes gateway
# → Listening on http://127.0.0.1:8642/v1

# 3. In the target app, add a Custom API Endpoint:
#    - Type/Provider: OpenAI / OpenAI-compatible
#    - Endpoint URL: http://localhost:8642/v1
#    - API Key: (same as API_SERVER_KEY if set)
#    - Model: hermes-agent (auto-detected from /v1/models)
```

**What the target app gets:** Full access to Hermes' tools — terminal, file ops, web search, browser automation, vision, memory, skills, cron jobs, sub-agent delegation.

**Transparent system prompt layering:** The API Server merges any frontend-provided system prompt on top of Hermes' core system prompt — tools, memory, and skills remain intact.

#### B) MCP Server Mode Setup (For IDE Integration)

```bash
# Check which tools are available
hermes mcp serve --help

# In Claude Desktop config (macOS):
# ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}

# For Cursor/VS Code MCP config, add equivalent stdio entry
```

**Limitation:** Only session-browsing tools are exposed, not Hermes' execution tools.

#### C) CLI Spawning (Simple Fallback)

For apps that support terminal/script execution (Everywhere, Alfred, Raycast):

```bash
# One-shot query
hermes chat -q "{{USER_QUERY}}" --quiet

# With context piped in
echo "{{CONTEXT}}" | hermes chat -q "Process this: {{CONTEXT}}" --quiet
```

## Installing Platform Adapters from Unmerged PRs

Some platform adapters exist in open PRs but haven't been merged to main. To use them, switch your Hermes git checkout to the PR branch:

```bash
cd ~/.hermes/hermes-agent

# Add the PR author's fork
git remote add <author> https://github.com/<author>/hermes-agent.git
git fetch <author> <branch>

# Stop gateway, switch branch, restart
hermes gateway stop
git checkout -b <local-name> <author>/<branch>
hermes gateway start

# Verify the platform code exists
ls gateway/platforms/<platform>.py
```

> ⚠️ `hermes update` will return to upstream main — you'll need to `git checkout <local-name>` again after updates.
> The branch switch is safe: gateway service restarts cleanly with the new code.

**Current known PR adapters:**
| Platform | PR | Author | Branch | Files |
|----------|-----|--------|--------|-------|
| NapCat (QQ/OneBot) | [#17917](https://github.com/NousResearch/hermes-agent/pull/17917) | MoeOver | `moeover/main` | `gateway/platforms/napcat.py`, `tools/napcat_tool.py`, `skills/messaging/napcat/SKILL.md` |

## Pitfalls

- **Gateway connects platforms sequentially — slow platforms block faster ones** — The gateway iterates through enabled platforms and connects them one at a time. A slow/stuck platform (e.g. Telegram timing out for 30+ seconds) delays all subsequent platforms. If a newly-added platform's port isn't listening immediately after `hermes gateway start`, check the logs with `tail -f ~/.hermes/logs/gateway.log | grep -E 'platform|connected'` and wait for the line `Gateway running with N platform(s)` to confirm all platforms are up. **Workaround:** if `hermes gateway restart` hangs, use `kill -9 $(pgrep -f 'hermes_cli.main gateway run')` then `hermes gateway start` instead.
- **Platform adapters with allowlists silently reject unauthorized users** — Many platform adapters default to allowlist mode. For group chat platforms, messages from unauthorized users generate a `WARNING` log (`Unauthorized user`) but are silently dropped — the sender gets no feedback. Check each platform's authorization env vars:
  - Per-platform allow-all: `<PLATFORM>_ALLOW_ALL_USERS=true` (e.g. `NAPCAT_ALLOW_ALL_USERS=true`)
  - Per-platform user allowlist: `<PLATFORM>_ALLOWED_USERS=id1,id2`
  - Group/chat-level allowlist: `<PLATFORM>_ALLOWED_GROUPS=id1,id2`
- **Proxy interferes with localhost health checks** — If Hermes is behind an HTTP proxy (Clash, etc.), `curl http://127.0.0.1:8642/health` goes through the proxy and returns 502/timeout instead of reaching the API server. Always use `curl --noproxy '*'` for localhost checks.
- **Gateway process may not have API_SERVER_ENABLED in /proc/PID/environ** — The env var is loaded by Python's `load_dotenv()` at runtime, not inherited from systemd. It won't appear in `/proc/PID/environ` even though `os.getenv()` sees it correctly. Check with `ss -tlnp | grep 8642` instead of relying on /proc/PID/environ.
- **Systemd restart with API_SERVER_ENABLED** — After adding `API_SERVER_ENABLED=true` to `.env` and running `hermes gateway restart`, the process exits with code 75 (TEMPFAIL) by design. Systemd auto-restarts it with the new config. Wait a few seconds, then verify with `ss -tlnp | grep 8642`.
- **Port conflict detection** — The API server pre-checks port availability by attempting a socket connect. If port 8642 is already in use, it logs an error and returns False from `connect()`. Change port with `API_SERVER_PORT` env var.
- **API Server binds to 127.0.0.1 by default** — if the external app runs on Windows and Hermes in WSL, Windows can reach `127.0.0.1:8642` via WSL port forwarding (usually auto-forwarded on modern WSL2). If not, set `API_SERVER_HOST=0.0.0.0` and use the WSL VM's IP.
- **MCP Server Mode ≠ tool execution** — do not recommend `hermes mcp serve` when the user expects full tool access. It only exposes session history tools.
- **API Server is stateless** via `/v1/chat/completions` — use `/v1/responses` with `previous_response_id` for stateful multi-turn conversations.
- **Firewall/Antivirus** on Windows may block WSL port forwarding. Check with `wsl --list --verbose` to find the WSL IP.
- **Proxy conflicts** — if Hermes uses proxy (Clash/etc.), the API Server's listening address needs to be explicitly set, not relying on automatic routing.
- **API Server rejected invalid API key after Hermes update or restart** — The Everywhere extension (and other API Server clients) caches the API key. After a Hermes update, the key may appear unchanged in `.env` but the client's cached key is stale or misconfigured. **Diagnosis:** `grep "rejected invalid API key" ~/.hermes/logs/gateway.log` — if the `user_agent` includes `Everywhere/X.Y.Z`, the Everywhere extension is using a wrong key. **Fix:** (1) Find the current key with `grep API_SERVER_KEY ~/.hermes/.env`, (2) verify it works with `curl -s http://127.0.0.1:8642/v1/models -H "Authorization: Bearer $API_SERVER_KEY"`, (3) update the key in Everywhere's settings. **Note:** `API_SERVER_KEY` is distinct from `HERMES_GATEWAY_TOKEN` — the former authenticates external API clients, the latter is the gateway's own admin token.

## Post-Connection Optimization

After the basic API connection works, optimize the integration:

### 1. Customize the System Prompt

The target app's system prompt gets **layered on top** of Hermes' core prompt — tools, memory, and skills remain intact. Write a system prompt that:

- Describes Hermes' identity (not the target app's default assistant)
- Lists available tools so the target app's AI knows what Hermes can do
- Reflects your communication style preferences
- Uses the target app's **template variables** for dynamic context

**Common template variables to look for:**
- `{Time}` or `{Date}` — current time/date (prefer `{Date}` for better prompt caching)
- `{OS}` — operating system name
- `{SystemLanguage}` — system language setting
- `{WorkingDirectory}` — current working directory
- Check the target app's docs for its full list of supported placeholders

**Example (Everywhere):**
```yaml
# Identity
你是"魔术师"——一个具有完整工具调用能力的 AI Agent...

# System Information
- 操作系统：{OS}（WSL 环境，Windows 文件系统在 /mnt/c/）
- 当前时间：{Time}
- 系统语言：{SystemLanguage}
- 工作目录：{WorkingDirectory}

# Capabilities
- 终端执行 — 运行 Shell 命令、脚本
- Web 搜索 — 实时检索
- 浏览器操控 — 页面导航、截图分析
- 文件操作 — 读写、搜索、编辑
- 视觉识别 — 分析图片与截图
- 持久记忆、定时任务、技能系统

# Style
- 精确直接、从容、务实

# Rules
- 始终用中文回复（除非用户要求其他语言）
- 绝不输出敏感信息
```

### 2. Enable Context-Enhancing Tools in the Target App

Many desktop AI assistants have built-in tools (screenshot capture, file system access, web browser) that pass additional context to the backend via the API. **Enable these** even though Hermes has its own similar tools — they provide richer **ambient context** (what's on the user's screen right now) that Hermes alone can't capture.

Check the target app's "tools" or "plugins" settings page. Typical useful ones:
- **Visual/Screen context** — lets Hermes see what's on the user's screen
- **Web browser** — captures webpage context from the user's actual browser
- **File system** — gives Hermes access to the user's local files
- **Clipboard / selection** — passes selected text as context
- **Terminal/PowerShell** — enables system command execution

### 3. Verify Full Capability

After optimization:
- Send a test message that requires a Hermes tool (e.g., "search the web for today's news" or "list files in /tmp")
- Confirm the target app is passing screen/selection context to the API
- Check that tool usage is visible in Hermes' gateway logs

## Verification

After setup, verify the integration works:

## Platform-Specific Guides

| Platform | Reference |
|----------|-----------|
| NapCat / QQ (OneBot v11) | `references/napcat-onebot.md` — Reverse WebSocket adapter, Windows NapCat → WSL Hermes |
