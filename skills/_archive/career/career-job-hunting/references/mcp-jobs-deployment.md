# mcp-jobs Deployment Reference

**Package:** `mergedao/mcp-jobs` v1.4.0  
**npm:** `mcp-jobs`  
**License:** MIT  
**Last published:** ~August 2025  

## Why npx Doesn't Work

The package.json has `"main": "dist/index.js"` but **no `bin` field**. `dist/index.js` is a library module (exports `searchJobList`, `crawlJobDetail`, etc.), not a standalone server.

The actual MCP server entry point is `dist/mcp.js` (has `#!/usr/bin/env node` shebang), but since there's no `bin` in package.json, `npx -y mcp-jobs` fails with:
```
npm error could not determine executable to run
```

## Installation

```bash
# Use npm mirror for speed (China)
npm install -g mcp-jobs --registry=https://registry.npmmirror.com

# Find install location
npm root -g
# → /home/po/.npm-global/lib/node_modules
```

## Running

```bash
# Direct node execution
node /home/po/.npm-global/lib/node_modules/mcp-jobs/dist/mcp.js
```

On startup it outputs:
```
正在初始化职位搜索服务...
{"method":"notifications/message","params":{"level":"info","data":"职位搜索服务初始化成功"},"jsonrpc":"2.0"}
职位搜索服务已启动，正在运行中...
```

## Hermes Config

```yaml
mcp_servers:
  jobs:
    command: "node"
    args: ["/home/po/.npm-global/lib/node_modules/mcp-jobs/dist/mcp.js"]
```

## Registered MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `mcp_jobs_mcp_search_job` | Search jobs by keyword across platforms | `keyword` (req), `city`, `salary`, `workYear`, `page` |
| `mcp_jobs_mcp_job_detail` | Fetch full detail from a job URL | `url` (req) |

## Verification

After Hermes restart, the agent can call these tools. Test with:
- "帮我搜上海AI实习岗"
- "搜北京的Python岗位"
- Look for the `mcp_jobs_` prefixed tools in available tool lists.

## Proxy Considerations

If behind HTTP proxy, the MCP subprocess inherits a filtered environment from Hermes (only PATH, HOME, USER, etc.). To pass proxy to the Playwright crawler:

```yaml
mcp_servers:
  jobs:
    command: "node"
    args: ["/home/po/.npm-global/lib/node_modules/mcp-jobs/dist/mcp.js"]
    env:
      http_proxy: "http://127.0.0.1:7890"
      https_proxy: "http://127.0.0.1:7890"
```

## Playwright Browser Requirement

mcp-jobs depends on Playwright with Chromium. Verify:
```bash
playwright --version
# Should output v1.59.0+
ls ~/.cache/ms-playwright/
# Should contain chromium-*
```

If missing: `npx playwright install chromium`

## Tool Comparison Context

| Tool | Type | Platforms | Tech |
|------|------|-----------|------|
| **mcp-jobs** (this) | Search/aggregation (MCP) | 猎聘, BOSS, 智联, 51job | Node.js + Playwright |
| **get_jobs** | Auto-apply bot | BOSS, 前程无忧, 猎聘, 智联 | Java + Gradle + Selenium |
| **JobClaw** | LLM match + auto-apply | BOSS, LinkedIn | Python + Playwright |
| **牛人快跑** | Desktop auto-chat | BOSS only | Electron + Puppeteer |
