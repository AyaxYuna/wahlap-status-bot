"""翻页记忆: 群级会话状态 (kind/page/per_page/updated_at).

刻意不用 AstrBot session_waiter: waiter 激活后会拦截该会话全部消息,
群级 waiter 等于在超时窗口内劫持全群. 翻页是被动查询, 用自维护 dict
(key 取 group_id, 私聊回退 unified_msg_origin, 与文档 CustomFilter 同思路)
+ 过期时间即可, 不影响其他消息.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

PagerKind = Literal["top", "chart"]


@dataclass
class PagerState:
    """某会话当前正在看的榜单."""

    kind: PagerKind
    page: int
    per_page: int
    updated_at: float


def session_key(event: Any) -> str:
    """群聊按群区分, 私聊按会话区分."""
    get_group = getattr(event, "get_group_id", None)
    if callable(get_group):
        try:
            group_id = get_group()
        except Exception:
            group_id = ""
        if group_id:
            return f"group:{group_id}"
    return f"dm:{getattr(event, 'unified_msg_origin', 'unknown')}"


def max_page(total: int, per_page: int) -> int:
    """总页数, 向上取整, 至少 1 页."""
    return max(1, -(-max(0, total) // max(1, per_page)))


def is_expired(state: PagerState, expire_seconds: float) -> bool:
    """状态是否过期."""
    return time.monotonic() - state.updated_at > expire_seconds


def turn_page(state: PagerState, total: int, direction: Literal["next", "prev"]) -> str | None:
    """翻页并更新 state; 到边界返回提示 (state 不动), 否则返回 None.

    返回 None 表示成功翻到 state.page; total 用于钳位 (数据可能变化).
    """
    pages = max_page(total, state.per_page)
    state.page = max(1, min(pages, state.page))
    if direction == "next":
        if state.page >= pages:
            return "已经是最后一页了"
        state.page += 1
        return None
    if state.page <= 1:
        return "已经是第一页了"
    state.page -= 1
    return None


def touch(state: PagerState) -> None:
    """刷新状态时间戳."""
    state.updated_at = time.monotonic()
