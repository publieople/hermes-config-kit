# Tool Detail Reference

## mcp-jobs v1.4.0

- **npm**: `mcp-jobs@1.4.0` (ISC, 8 dependencies)
- **Last published**: ~mid-2025 (10 months ago from May 2026)
- **Maintainer**: tudamu `<603167546@qq.com>`
- **Dependencies**: @modelcontextprotocol/sdk, @types/cheerio, @types/node, cheerio, dotenv, playwright, ts-node, typescript
- **Unpacked size**: 58 kB
- **Platforms**: BOSS直聘, 猎聘, 智联招聘, 前程无忧
- **Integration**: MCP protocol (stdio transport, command `npx -y mcp-jobs`)
- **Tools registered** (server name `jobs`): `mcp_jobs_search_jobs`, etc.

## get_jobs (loks666/get_jobs)

- **License**: MIT
- **Build**: Gradle (wrapper included)
- **Java**: JDK 21 required
- **Browser**: Chrome (chromedriver.exe, Windows-oriented)
- **Platform-specific limits**:
  - BOSS: 150 hellos/day, auto-blacklist "not suitable" companies
  - 猎聘: unlimited hellos, must bind WeChat
  - 前程无忧: degrated, limited applies
  - 智联招聘: ~100 applies, broken, not recommended
- **Env vars**: HOOK_URL (WeChat webhook), BASE_URL/API_KEY/MODEL (LLM)
- **Cost**: ~$0.06/day with gpt-5-nano
- **QQ support group**: available in repo README

## JobClaw (slothsheepking/jobclaw)

- **License**: MIT
- **Python**: 3.11+
- **State**: PRs welcome, active development
- **LLM auth methods** (priority order):
  1. Claude OAuth (free, uses Claude Code subscription token)
  2. Anthropic API key
  3. OpenAI API key
- **Storage**: Cookies at `~/.jobclaw/cookies/`
- **Config**: `profiles/me.yaml` (skills, salary, city) + `.env`
- **Notification**: Telegram bot / Discord webhook
- **Anti-detection**: randomized apply delays (configurable min/max), HR inactivity filter (7d default)
- **Proxy**: `HTTP_PROXY` / `HTTPS_PROXY` env vars

## GeekGeekRun (geekgeekrun/geekgeekrun)

- **Commit count**: 857
- **Release count**: 27
- **Platform**: BOSS直聘 only
- **Tech**: Puppeteer + Electron
- **Packages**: .exe (Win), .deb (Linux), .dmg (macOS)
- **Features**: auto-chat, read-without-reply retry, zombie job cleanup, LLM template editor, config templates

## This User's Environment (Verified May 2026)

- Node.js: v26.1.0
- npm: 11.14.1
- Playwright: 1.59.0 (browsers: chromium-1217, chromium_headless_shell-1217, ffmpeg-1011)
- Python: 3.11.14
- Java: NOT installed
- OS: Arch Linux via WSL2
- Proxy: http://127.0.0.1:7890
- HF mirror: HF_ENDPOINT=https://hf-mirror.com
- Resume: `publieople/publieople` repo with `resume.json` (visiky/resume schema)
