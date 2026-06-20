# MCP FastMCP 现行 API

截至 2026-06，`mcp` 包版本约 1.3+，`FastMCP` 的 API：

## 三种传输方式

### Stdio（默认，最简单）
```python
mcp = FastMCP("server-name")
# ... register tools ...
mcp.run()  # 默认 transport="stdio"
```

### SSE
```python
import uvicorn
mcp = FastMCP("server-name")
# mcp.run(transport="sse") 不接受 host/port！

app = mcp.sse_app()  # 返回 Starlette app
uvicorn.run(app, host="0.0.0.0", port=18080)
```
客户端连接 `http://localhost:18080/sse`

### Streamable HTTP
```python
import uvicorn
mcp = FastMCP("server-name", stateless_http=False)

app = mcp.streamable_http_app()  # 返回 Starlette app
uvicorn.run(app, host="0.0.0.0", port=18090)
```
客户端连接 `http://localhost:18090/mcp`

## 关键方法

- `mcp.tool()` — 注册工具函数
- `mcp.resource("file://path")` — 注册资源
- `mcp.prompt()` — 注册提示词模板
- `mcp.sse_app()` — 获取 SSE Starlette app
- `mcp.streamable_http_app()` — 获取 Streamable HTTP Starlette app

## 客户端连接

```python
# Stdio
from mcp.client.stdio import stdio_client
params = StdioServerParameters(command=sys.executable, args=[server_path])

# SSE
from mcp.client.sse import sse_client
async with sse_client(url="http://localhost:18080/sse") as (r, w):

# Streamable HTTP
from mcp.client.streamable_http import streamablehttp_client
async with streamablehttp_client(url="http://localhost:18090/mcp") as (r, w, _):
```
