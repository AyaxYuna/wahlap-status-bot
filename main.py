"""Wahlap 服务器实时状态 - AstrBot 插件.

数据源为免鉴权聚合接口, 文档见 https://maimai.imikufans.cn/docs.php.
v1.0 仅做查询展示, 不涉及上报 / 监听 / 播报 (上报需另外向站长申请签名密钥).
自然问法见 qa/prompt.py, 回复渲染见 qa/response.py.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star, register
from .qa.prompt import match_question, parse_hours, parse_rating_range, parse_top_n
from .qa.response import (
    AnswerContext,
    answer_question,
    render_chart145,
    render_fail,
    render_history,
    render_rating,
    render_rating_range,
    render_status,
    render_top100,
)

DEFAULT_BASE_URL = "https://maimai.imikufans.cn/api.php"
DEFAULT_SITE_URL = "https://maimai.imikufans.cn"
USER_AGENT = "Mozilla/5.0 (compatible; AstrBot-plugin-wlsrvstatus/1.0)"

# 本插件自己发出的回复标记, 自然问法监听时跳过, 避免自激循环
_SELF_MARKERS = ("【舞萌DX", "【服务可用性】", "【全服", "【高难谱面", "【Wahlap", "📡 数据来源")


RATING_USAGE = """查 rating 分布这样问: /wlrating [范围]
示例: /wlrating (全部分布) / /wlrating w0-w3 / /wlrating 10000-13000 / /wlrating w15
w 记法: w0=10000, w5=15000, w15=11500, 上限 w99=19900"""


HELP_TEXT = """【Wahlap 服务器状态·指令帮助】
/wlstatus 查看服务器实时状态
/wlhistory [小时数] 查看服务可用性(默认12, 范围1~48)
/wltop [条数] 全服游玩次数排行(默认20)
/wlrating 全服 Rating 分布
/wlchart [条数] 高难谱面越级排行(默认30)
/wlhelp 显示本帮助
📡 数据来源: maimai.imikufans.cn(聚合 isMaiDown by Chongxi)"""


@register("astrbot_plugin_wlsrvstatus", "AyaxYuna", "实时监测 Wahlap 服务器状态的插件", "1.0.0")
class WahlapStatusPlugin(Star):
    """查询展示华立(舞萌DX)服务器状态, 数据源为免鉴权聚合接口."""

    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        cfg: Any = config if config is not None else {}
        self._base_url: str = str(cfg.get("base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL)
        self._site_url: str = str(cfg.get("site_url", DEFAULT_SITE_URL) or DEFAULT_SITE_URL)
        self._timeout: int = int(cfg.get("timeout", 10) or 10)
        self._status_ttl: int = int(cfg.get("status_cache_ttl", 20) or 20)
        self._history_ttl: int = int(cfg.get("history_cache_ttl", 300) or 300)
        self._static_ttl: int = int(cfg.get("static_cache_ttl", 21600) or 21600)
        self._top_default: int = int(cfg.get("top_default_n", 20) or 20)
        self._chart_default: int = int(cfg.get("chart_default_n", 30) or 30)
        self._default_hours: int = int(cfg.get("history_default_hours", 12) or 12)
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._last_error: str = ""

    def _ttl_for(self, api: str) -> int:
        if api == "status":
            return self._status_ttl
        if api == "history":
            return self._history_ttl
        return self._static_ttl

    async def _fetch(self, api: str, extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """请求聚合接口, 命中缓存则直接返回; 失败返回 None 并记录原因到 _last_error."""
        query: dict[str, Any] = {"api": api}
        if extra:
            query.update(extra)
        cache_key = "&".join(f"{k}={v}" for k, v in sorted(query.items(), key=lambda kv: kv[0]))
        now = time.monotonic()
        hit = self._cache.get(cache_key)
        if hit is not None and now - hit[0] < self._ttl_for(api):
            return hit[1]
        self._last_error = ""
        try:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}, timeout=timeout) as session:
                async with session.get(self._base_url, params=query) as resp:
                    if resp.status != 200:
                        self._last_error = f"HTTP {resp.status}"
                        return None
                    data = await resp.json()
        except Exception as exc:
            self._last_error = str(exc) or type(exc).__name__
            logger.warning(f"wlsrvstatus: 请求 {api} 失败: {exc}")
            return None
        if not isinstance(data, dict):
            self._last_error = "响应格式异常"
            return None
        if "error" in data:
            # 上游抓取失败等情况不写入缓存, 下次调用直接重试
            self._last_error = str(data.get("error"))
            logger.warning(f"wlsrvstatus: 接口 {api} 返回错误: {self._last_error}")
            return None
        self._cache[cache_key] = (now, data)
        return data

    def _fail_text(self) -> str:
        return render_fail(self._last_error)

    def _answer_ctx(self) -> AnswerContext:
        return AnswerContext(
            fetch=self._fetch,
            site_url=self._site_url,
            last_error=lambda: self._last_error,
        )

    @filter.command("wlstatus")
    async def wlstatus(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查看华立(舞萌DX)服务器实时状态"""
        data = await self._fetch("status")
        if data is None:
            yield event.plain_result(self._fail_text())
            return
        yield event.plain_result(render_status(data, self._site_url))

    @filter.command("wlhistory")
    async def wlhistory(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查看服务可用性历史, 可附时间如 /wlhistory 24 /wlhistory 2d /wlhistory 30min"""
        hours = parse_hours(event.message_str, self._default_hours)
        data = await self._fetch("history", {"hours": hours})
        if data is None:
            yield event.plain_result(self._fail_text())
            return
        yield event.plain_result(render_history(data, self._site_url))

    @filter.command("wltop")
    async def wltop(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查看全服游玩次数排行, 可附条数如 /wltop 20"""
        top_n = parse_top_n(event.message_str, self._top_default)
        data = await self._fetch("top100")
        if data is None:
            yield event.plain_result(self._fail_text())
            return
        yield event.plain_result(render_top100(data, self._site_url, top_n))

    @filter.command("wlrating")
    async def wlrating(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查看全服 Rating 分布, 可附区间如 /wlrating w0-w3 / /wlrating 10000-13000"""
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            data = await self._fetch("ratinglist")
            if data is None:
                yield event.plain_result(self._fail_text())
                return
            yield event.plain_result(render_rating(data, self._site_url))
            return
        rating_range = parse_rating_range(event.message_str)
        if rating_range is None:
            yield event.plain_result(RATING_USAGE)
            return
        data = await self._fetch("ratinglist")
        if data is None:
            yield event.plain_result(self._fail_text())
            return
        yield event.plain_result(
            render_rating_range(
                data,
                self._site_url,
                rating_range.lo,
                rating_range.hi,
                rating_range.lo_text,
                rating_range.hi_text,
            )
        )

    @filter.command("wlchart")
    async def wlchart(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """查看高难谱面越级排行, 可附条数如 /wlchart 30"""
        top_n = parse_top_n(event.message_str, self._chart_default)
        data = await self._fetch("chart145")
        if data is None:
            yield event.plain_result(self._fail_text())
            return
        yield event.plain_result(render_chart145(data, self._site_url, top_n))

    @filter.command("wlhelp")
    async def wlhelp(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """显示本插件指令帮助"""
        yield event.plain_result(HELP_TEXT)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_natural_query(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, None]:
        """识别玩家常用问法并直接回答 (见 qa/prompt.py), 命中后截断事件避免重复回复."""
        text = (event.message_str or "").strip()
        if not text or text.startswith("/"):
            return
        if any(marker in text for marker in _SELF_MARKERS):
            return
        matched = match_question(
            text,
            hours_default=self._default_hours,
            top_default=self._top_default,
            chart_default=self._chart_default,
        )
        if matched is None:
            return
        event.stop_event()
        yield event.plain_result(await answer_question(matched, self._answer_ctx()))
