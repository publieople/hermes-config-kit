---
name: mcp-python-patterns
description: 编写 Python MCP stdio server 并从 Hermes 接入的模板和坑 — 当需要把任意 Python 库包装成 MCP 工具时使用
version: 1.0.0
author: Hermes + Publieople
---

# Python MCP Server 编写 & Hermes 接入模板

## 何时使用

- 想把一个 Python 库暴露给 Hermes 当工具用，但没有现成的 MCP server
- GitHub 上的 MCP 二进制在国内下不动，需要自己写 Python 版桥接
- 需要给 MCP server 传环境变量（代理、镜像地址等）

## 最小可用模板

```python
#!/usr/bin/env python3
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

async def main():
    server = Server("my-server")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="my_tool",
                description="工具描述",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "参数说明"},
                    },
                    "required": ["param"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "my_tool":
            result = do_something(arguments["param"])
            return [TextContent(type="text", text=result)]
        return [TextContent(type="text", text=f"未知工具: {name}")]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

## 接入 Hermes

### 基础接入（非交互式）

```bash
echo "Y" | hermes mcp add <server-name> --command python3 --args /path/to/server.py
```

**关键**：`hermes mcp add` 是交互式的（会问 `Enable all N tools? [Y/n/select]`），用 `echo "Y" |` 管道自动化。

### 带环境变量

```bash
hermes mcp remove <server-name>   # 先删旧的
echo "Y" | hermes mcp add <server-name> \
  --command python3 \
  --args /path/to/server.py \
  --env KEY1=value1 KEY2=value2
```

环境变量在 server 脚本里用 `os.environ.get("KEY")` 读取。

### 验证

```bash
hermes mcp list   # 确认状态为 ✓ enabled
```

### 本地测试（不依赖 Hermes 重启）

```python
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

async def test():
    params = StdioServerParameters(
        command="python3",
        args=["/path/to/server.py"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("tool_name", {"param": "value"})
            print(result.content[0].text)

asyncio.run(test())
```

## 常见坑

### GitHub 二进制下不动 → PyPI + 自己写桥接

国内 GitHub Releases 下载经常超时。优先检查 PyPI 是否有同名或功能类似的 Python 包（如 `annas-py`），然后用模板包一层 MCP server。

### 库硬编码了不可达的 URL → monkey-patch

```python
import some_lib
import os
override = os.environ.get("SOME_BASE_URL", "")
if override:
    some_lib.BASE_URL = override  # 或 some_lib.extractors.BASE_URL
```

### `hermes config edit` 被拒 → 用 `hermes mcp add/remove`

Hermes 不允许 agent 直接改 config.yaml。MCP 配置必须走 `hermes mcp` 子命令。

## 高级坑：Monkey-Patch & 代理

### Monkey-patch 要打对模块

Python 的 `from X import func` 在导入时捕获函数引用。patch `X.func` 不影响已导入模块的局部引用。必须 patch 实际使用该函数的模块：

```python
# ❌ 错误：只 patch 顶层模块
import requests
requests.get = patched_get  # 不影响 annas_py.utils.get

# ✅ 正确：patch 实际使用该函数的模块
import annas_py.utils
annas_py.utils.get = patched_get
```

字符串属性同理——`from . import BASE_URL` 捕获的是字符串引用，必须 patch 所有 import 该值的模块。

### Clash MITM 代理导致 SSL 验证失败

国内用户常通过 Clash 代理访问外网，MITM 模式导致 `requests` SSL 验证失败。在 MCP server 脚本中 patch：

```python
_skip_verify = os.environ.get("SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes")
if _skip_verify:
    import target_pkg.utils
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _orig_get = target_pkg.utils.get
    def _patched_get(url, **kwargs):
        kwargs.setdefault('verify', False)
        return _orig_get(url, **kwargs)
    target_pkg.utils.get = _patched_get
```

注册时传 `--env SKIP_SSL_VERIFY=1`。

### WSL 代理配置

用户环境：WSL2，Clash 代理在 Windows 宿主机（`localhost:7890`）。MCP server 需要代理时：

```bash
--env HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890
```

详细 monkey-patch 陷阱与修复模式见：`references/monkey-patch-patterns.md`

## 参考

- `references/monkey-patch-patterns.md` — 详细的 monkey-patch 陷阱与修复模式
- 完整示例：`references/annas-mcp-server.py` — 包装 `annas-py` 的 MCP server，含搜索+下载两个工具
- 官方 MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
