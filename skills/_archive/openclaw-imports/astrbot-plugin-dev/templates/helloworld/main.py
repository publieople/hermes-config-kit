"""AstrBot plugin skeleton — copy to ~/astrbot/data/plugins/astrbot_plugin_xxx/ then modify.

Verified against AstrBot 4.x (core/star/register/star_handler.py).
"""

import os
import asyncio
import logging
from typing import AsyncGenerator, Optional

from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import (
    llm_tool,
    command,
    event_message_type,
    EventMessageType,
)
from astrbot.api.message_components import Plain, Image
from astrbot.api import logger

logger = logging.getLogger(__name__)


@register(
    "astrbot_plugin_xxx",            # 插件唯一 id,必须 astrbot_plugin_ 前缀
    "YourName",                       # 作者
    "一句话描述",
    "v1.0.0",                         # 版本必须 v 前缀
    "https://github.com/you/repo",    # 仓库地址
)
class XxxPlugin(Star):
    def __init__(self, context: Context, config: Optional[dict] = None):
        super().__init__(context)
        # AstrBotConfig 在 v4 自动从 _conf_schema.json 注入,没文件就 None
        self.config = config or {}
        self.some_option = self.config.get("some_option", "default")

    async def initialize(self):
        """可选。插件加载后调用。"""
        logger.info("[xxx] initialized")

    async def terminate(self):
        """可选。插件卸载/停用时调用。"""

    # ---------- 命令 ----------

    @command("hi")
    async def cmd_hi(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """hi - 打个招呼"""
        yield event.plain_result(f"hi {event.get_sender_name()}")

    @command("看分类")
    async def cmd_list(self, event: AstrMessageEvent):
        """看分类 - 列出所有可用项"""
        yield event.plain_result("分类 1\n分类 2\n分类 3")

    # ---------- LLM 工具(让 AI 主动调用) ----------

    @llm_tool(name="do_xxx")
    async def llm_do_xxx(self, event: AstrMessageEvent, param: str = ""):
        """简短描述给 LLM 看,这个工具是干嘛的。

        什么时候调、效果是什么,写在这里。LLM 看到这段决定要不要调。

        Args:
            param(string): 参数说明(留空表示可选)
        """
        # 业务逻辑
        result_text = f"did it with {param}"
        # 1) yield 发消息给用户
        yield event.plain_result("处理中...")
        # 2) return 字符串给 LLM,让 LLM 总结回应
        return result_text

    # ---------- 消息事件钩子 ----------

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent) -> Optional[MessageEventResult]:
        """所有消息都会经过这里。返回 None 不回复,返回 MessageEventResult 自动回复。"""
        text = event.message_str.lower()
        if "触发词" in text:
            return event.plain_result("触发响应")
        return None
