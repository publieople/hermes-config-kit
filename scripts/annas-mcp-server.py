#!/usr/bin/env python3
"""MCP server wrapping annas-py for Anna's Archive access.

Tools:
  - anna_search: Search books/articles by query
  - anna_get_info: Get download links for a search result

Environment:
  - ANNAS_BASE_URL: Override Anna's Archive base URL (default: annas-archive.org)
  - HTTP_PROXY / HTTPS_PROXY: Proxy settings (respected by requests library)
"""

import asyncio
import json
import os
import sys

# --- Monkey-patch annas-py base URL ---
import annas_py.extractors
import annas_py.extractors.search
import annas_py.extractors.download
_override_url = os.environ.get("ANNAS_BASE_URL", "")
if _override_url:
    annas_py.extractors.BASE_URL = _override_url
    annas_py.extractors.search.BASE_URL = _override_url
    annas_py.extractors.download.BASE_URL = _override_url

# --- Monkey-patch annas-py to skip SSL verify (Clash MITM proxy) ---
_skip_verify = os.environ.get("ANNAS_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes")
if _skip_verify:
    import annas_py.utils
    import requests as _requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    _orig_get = annas_py.utils.get
    def _patched_get(url, **kwargs):
        kwargs.setdefault('verify', False)
        return _orig_get(url, **kwargs)
    annas_py.utils.get = _patched_get

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


async def main():
    server = Server("annas-mcp")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="anna_search",
                description="搜索 Anna's Archive 上的书籍/文档。支持按标题、作者、主题搜索。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词（书名、作者、主题等）",
                        },
                        "language": {
                            "type": "string",
                            "description": "语言过滤（如 en=英文, zh=中文, 留空=不限）",
                            "default": "",
                        },
                        "file_type": {
                            "type": "string",
                            "description": "文件类型过滤（如 pdf, epub, mobi, 留空=不限）",
                            "default": "",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量（默认 5，最大 20）",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="anna_get_info",
                description="获取搜索结果的详细信息，包括下载链接。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "md5_id": {
                            "type": "string",
                            "description": "搜索结果中的 id（MD5 哈希）",
                        },
                    },
                    "required": ["md5_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        import annas_py
        from annas_py.models.args import Language, FileType

        if name == "anna_search":
            query = arguments.get("query", "")
            lang_str = arguments.get("language", "")
            ft_str = arguments.get("file_type", "")
            limit = min(arguments.get("limit", 5), 20)

            language = Language(lang_str) if lang_str else Language.ANY
            file_type = FileType(ft_str) if ft_str else FileType.ANY

            try:
                results = annas_py.search(query, language=language, file_type=file_type)
            except Exception as e:
                return [TextContent(type="text", text=f"搜索失败: {e}")]

            if not results:
                return [TextContent(type="text", text=f"未找到与 '{query}' 相关的结果。")]

            output = []
            for i, r in enumerate(results[:limit], 1):
                output.append(
                    f"**{i}. {r.title}**\n"
                    f"  - ID: `{r.id}`\n"
                    f"  - 作者: {r.authors or '未知'}\n"
                    f"  - 格式: {r.file_info.extension}\n"
                    f"  - 大小: {r.file_info.size}\n"
                    f"  - 语言: {r.file_info.language or '未知'}\n"
                    f"  - 出版社: {r.publisher or '未知'}\n"
                    f"  - 出版日期: {r.publish_date or '未知'}"
                )

            total = len(results)
            header = f"找到 {total} 个结果，显示前 {min(limit, total)} 个:\n\n" if total > 0 else ""
            return [TextContent(type="text", text=header + "\n\n".join(output))]

        elif name == "anna_get_info":
            md5_id = arguments.get("md5_id", "")
            try:
                info = annas_py.get_informations(md5_id)
            except Exception as e:
                return [TextContent(type="text", text=f"获取信息失败: {e}")]

            urls_text = "\n".join(
                f"  - [{u.title}]({u.url})" for u in info.urls
            )

            output = (
                f"**{info.title}**\n"
                f"  - 作者: {info.authors or '未知'}\n"
                f"  - 格式: {info.file_info.extension}\n"
                f"  - 大小: {info.file_info.size}\n"
                f"  - 描述: {info.description or '无'}\n"
                f"  - 出版社: {info.publisher or '未知'}\n"
                f"  - 出版日期: {info.publish_date or '未知'}\n\n"
                f"**下载链接:**\n{urls_text or '无可用下载链接'}"
            )
            return [TextContent(type="text", text=output)]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
