"""答案: 把意图识别结果变成回复文本."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .pager import PagerState, max_page, touch
from .prompt import QAMatch
from .tips import get_tip, resolve_tip

SOURCE_TAG = "数据来源: maimai.imikufans.cn(聚合 isMaiDown by Chongxi)"

VERDICT_MAP = {
    "normal": "🟢 一切正常",
    "recovering": "🟡 部分服务性能恢复",
    "degraded": "🟠 部分服务性能下降",
    "outage": "🔴 部分服务宕机",
    "maintenance": "🔧 服务器维护中",
    "nodata": "⚪ 无数据",
}

STATE_MAP = {
    "ok": "🟢",
    "down": "🔴",
    "degraded": "🟠",
    "recovering": "🟡",
    "maintenance": "🔧",
    "nodata": "⚪",
}

# 难度编号: 标准 0-4 = BASIC/ADVANCED/EXPERT/MASTER/Re:MASTER (绿/黄/红/紫/白).
# 注意镜像文档此处写反了 (3=EXP/4=MAS/0=特殊); 实测潘多拉 (4,15.0) 正是
# Re:MASTER 15.0 (maimai 首个 Lv15), 系ぎて (4,15) 即 reM15, 故 4=ReM/3=MAS.
# 本接口定数 14.5 起, 实际只会出现 3/4, 其余映射为完整性保留.
LEVEL_MAP = {
    0: "BAS",
    1: "ADV",
    2: "EXP",
    3: "MAS",
    4: "ReM",
}


def _block(value: Any) -> str:
    """把单小时可用率映射为一个文本方块, 无数据用中点表示."""
    if value is None:
        return "·"
    if isinstance(value, bool):
        return "·"
    if not isinstance(value, (int, float)):
        return "·"
    if value >= 99.5:
        return "█"
    if value >= 90:
        return "▓"
    if value >= 50:
        return "▒"
    if value > 0:
        return "░"
    return "✕"


def _bucket_key(bucket: dict[str, Any]) -> int:
    """rating 分档排序键, 非整数 bucket 视为 0."""
    value = bucket.get("bucket")
    return value if isinstance(value, int) else 0


def select_version_view(data: dict[str, Any], version: str) -> dict[str, Any] | None:
    """按版本取数据视图; 空版本取 current; 未收录返回 None."""
    if not version:
        return data.get("current") or {}
    want = version.lower()
    for entry in data.get("versions") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("key", "")).lower() == want or str(entry.get("label", "")).lower() == want:
            return entry
    return None


def render_version_hint(data: dict[str, Any], version: str) -> str:
    """版本未收录时的提示, 列出可用版本."""
    labels = [str(v.get("label", "?")) for v in data.get("versions") or [] if isinstance(v, dict)]
    known = "、".join(labels) if labels else "暂无"
    return f"暂未收录 {version} 的数据，可用版本：{known}\n📡 {SOURCE_TAG}"


def render_rating(data: dict[str, Any], site_url: str, tip: str | None = None) -> str:
    """渲染 GET ?api=ratinglist 的全量纯文本回复."""
    current = data.get("current") or {}
    label = current.get("label", "?")
    total = current.get("total", "--")
    lines = [f"【全服 Rating 分布·{label}】", f"收录玩家 {total} 人(每100分一段)", ""]
    buckets = current.get("data") or []
    rows: list[dict[str, Any]] = [b for b in buckets if isinstance(b, dict)]
    rows.sort(key=_bucket_key)
    for b in rows[:15]:
        bucket = b.get("bucket", "?")
        count = b.get("count", "--")
        if isinstance(bucket, int):
            lines.append(f"{bucket}~{bucket + 100}: {count}人")
        else:
            lines.append(f"{bucket}: {count}人")
    if len(rows) > 15:
        lines.append(f"…等共 {len(rows)} 档")
    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


def render_rating_range(
    data: dict[str, Any],
    site_url: str,
    lo: int,
    hi: int,
    lo_label: str = "",
    hi_label: str = "",
    tip: str | None = None,
) -> str:
    """渲染 rating 区间查询: 汇总区间人数与占比, 并列出命中的百分段 (最多 30 档)."""
    current = data.get("current") or {}
    label = current.get("label", "?")
    total = current.get("total", 0)
    span = f"{lo_label or lo}~{hi_label or hi}"
    lines = [f"【全服 Rating 分布·{label}｜{span}】"]
    if span != f"{lo}~{hi}":
        lines.append(f"({lo}~{hi})")
    buckets = current.get("data") or []
    rows: list[dict[str, Any]] = []
    for b in buckets:
        if not isinstance(b, dict):
            continue
        bucket = b.get("bucket")
        if not isinstance(bucket, int):
            continue
        if bucket < hi and bucket + 100 > lo:
            rows.append(b)
    rows.sort(key=_bucket_key)
    in_range = sum(int(b.get("count", 0)) for b in rows)
    if isinstance(total, int) and total > 0:
        lines.append(f"区间人数 {in_range} 人, 占全服 {in_range / total * 100:.1f}%")
    else:
        lines.append(f"区间人数 {in_range} 人")
    lines.append("")
    for b in rows[:30]:
        bucket = b.get("bucket", "?")
        count = b.get("count", "--")
        lines.append(f"{bucket}~{bucket + 100 if isinstance(bucket, int) else '?'}: {count}人")
    if len(rows) > 30:
        lines.append(f"…等共 {len(rows)} 档")
    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


def render_fail(reason: str) -> str:
    """接口失败时的统一回复."""
    return f"获取失败({reason or '未知错误'}), 请稍后重试\n📡 {SOURCE_TAG}"
    """接口失败时的统一回复."""
    return f"获取失败({reason or '未知错误'}), 请稍后重试\n📡 {SOURCE_TAG}"


def render_status(data: dict[str, Any], site_url: str, tip: str | None = None) -> str:
    """渲染 GET ?api=status 的纯文本回复."""
    verdict = str(data.get("verdict", "nodata"))
    verdict_text = str(data.get("verdict_text", "未知状态"))
    lines = [
        "【舞萌DX·华立服务器状态】",
        f"{VERDICT_MAP.get(verdict, '❓ 未知')}({verdict_text})",
        "",
        "【服务状态】",
    ]
    services = data.get("services") or []
    for svc in services:
        if not isinstance(svc, dict):
            continue
        name = str(svc.get("name", "?"))
        state = str(svc.get("state", "nodata"))
        latency = svc.get("latency")
        lat_str = f"{latency}ms" if isinstance(latency, (int, float)) else "--"
        line = f"{STATE_MAP.get(state, '⚪')} {name} {lat_str}"
        duration = str(svc.get("duration_text") or "")
        if duration:
            line += f"({duration})"
        lines.append(line)

    latency_info = data.get("latency") or {}
    current_ms = latency_info.get("current_ms", "--")
    load_text = latency_info.get("load_text", "--")
    vol_text = latency_info.get("volatility_text", "--")
    lines += [
        "",
        f"⏱ 当前延迟: {current_ms}ms｜负载: {load_text}｜延迟{vol_text}",
    ]

    reports = data.get("reports") or {}
    anomaly = reports.get("anomaly_count", 0)
    normal = reports.get("normal_count", 0)
    if not anomaly and not normal:
        lines.append("💬 近期无玩家上报")
    elif not normal:
        lines.append(f"💬 近期有{anomaly}条异常上报, 无正常上报")
    elif not anomaly:
        lines.append(f"💬 近期有{normal}条正常上报, 无异常")
    else:
        lines.append(f"💬 近期{anomaly}条异常, {normal}条正常上报")

    logs = data.get("recent_logs") or []
    shown = 0
    for log in logs:
        if shown >= 3 or not isinstance(log, dict):
            continue
        lines.append(f"• {log.get('time_ago', '--')} {log.get('region', '--')} {log.get('type', '--')}")
        shown += 1

    broadcast = data.get("broadcast") or {}
    msg = str(broadcast.get("msg") or "")
    if msg:
        lines += ["", f"📢 {msg}"]

    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


def render_history(data: dict[str, Any], site_url: str, tip: str | None = None) -> str:
    """渲染 GET ?api=history 的纯文本回复, 对返回形状漂移做兼容."""
    hours = data.get("hours", "?")
    points = data.get("points")
    title = f"【服务可用性】过去 {hours} 小时"
    if isinstance(points, int):
        title += f"(共{points}个采样点)"
    lines = [title]
    services = data.get("services") or []
    for svc in services:
        if not isinstance(svc, dict):
            continue
        name = str(svc.get("name", "?"))
        uptime = svc.get("uptime")
        uptime_str = f"{uptime}%" if isinstance(uptime, (int, float)) else "无数据"
        hourly = svc.get("hourly") or []
        if len(hourly) > 48:
            hourly = hourly[-48:]
        bar = "".join(_block(v) for v in hourly)
        latencies = [v for v in (svc.get("latency") or []) if isinstance(v, (int, float))]
        if latencies:
            avg_lat = sum(latencies) / len(latencies)
            lines.append(f"{name} 可用率 {uptime_str} 均延迟 {avg_lat:.0f}ms")
        else:
            lines.append(f"{name} 可用率 {uptime_str}")
        lines.append(bar if bar else "·(无数据)")
    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


def _tip_line(tip: str | None) -> list[str]:
    """Tip 行: None 走默认均匀抽取, 空串不显示, 否则显示给定内容."""
    if tip is None:
        tip = get_tip()
    if not tip:
        return []
    return [f"Tip: {tip}"]


def _pager_footer(page: int, pages: int) -> list[str]:
    """翻页脚: 当前页码 + 翻页提示."""
    return [
        f"当前页码：{page}/{pages}",
        "翻页请发送 下一页 / 上一页 (或 /wlnextpage / /wlprevpage)",
    ]


def render_top100(
    data: dict[str, Any], site_url: str, page: int = 1, per_page: int = 20, tip: str | None = None
) -> str:
    """渲染 GET ?api=top100 的纯文本回复 (分页, 排名为全局名次)."""
    total = data.get("totalPlays", "--")
    songs = [s for s in (data.get("songs") or []) if isinstance(s, dict)]
    pages = max_page(len(songs), per_page)
    page = max(1, min(pages, page))
    start = (page - 1) * per_page
    lines = ["【全服游玩次数 Top100】", f"全服总游玩 {total} 次", ""]
    for i, song in enumerate(songs[start : start + per_page]):
        lines.append(f"{start + i + 1}. {song.get('name', '?')} — {song.get('plays', '--')}次")
    lines += ["", *_pager_footer(page, pages)]
    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


def render_chart145(
    data: dict[str, Any], site_url: str, page: int = 1, per_page: int = 20, tip: str | None = None
) -> str:
    """渲染 GET ?api=chart145 的纯文本回复 (分页, rank 字段本身即全局名次)."""
    total = data.get("totalPlayers", "--")
    songs = [s for s in (data.get("songs") or []) if isinstance(s, dict)]
    pages = max_page(len(songs), per_page)
    page = max(1, min(pages, page))
    start = (page - 1) * per_page
    lines = ["【高难谱面越级排行(14.5~15.0)】", f"合计游玩 {total} 人次", ""]
    for song in songs[start : start + per_page]:
        level_raw = song.get("level")
        level_key = level_raw if isinstance(level_raw, int) else -1
        level_text = LEVEL_MAP.get(level_key, str(level_raw))
        lines.append(
            f"{song.get('rank', '?')}. {song.get('name', '?')} "
            f"[{song.get('rate', '?')}·{level_text}] "
            f"{song.get('players', '--')}人 均{song.get('avg', '--')}%"
        )
    lines += ["", *_pager_footer(page, pages)]
    lines += ["", f"🔗 详情 {site_url}", f"📡 {SOURCE_TAG}", *_tip_line(tip)]
    return "\n".join(lines)


# 插件的数据请求函数签名 (api 名 + 附加参数 -> 响应 dict / 失败 None)
class FetchFunc(Protocol):
    async def __call__(self, api: str, extra: dict[str, Any] | None = ...) -> dict[str, Any] | None: ...


@dataclass
class AnswerContext:
    """回答问题所需的插件侧能力与配置."""

    fetch: FetchFunc
    site_url: str
    last_error: Callable[[], str]
    tip_enabled: bool = True
    tip_bias: str = "不设置"


async def answer_question(match: QAMatch, ctx: AnswerContext) -> tuple[str, PagerState | None]:
    """按意图拉取数据并渲染, 失败时返回统一失败文本 (永不抛异常).

    返回 (回复文本, 翻页状态): top/chart 意图在成功时附带第 1 页状态,
    调用方按会话存下即可翻页; 其余意图状态为 None.
    """
    tip = resolve_tip(ctx.tip_enabled, ctx.tip_bias)
    try:
        if match.intent == "status":
            data = await ctx.fetch("status", None)
            if data is not None:
                return render_status(data, ctx.site_url, tip), None
        elif match.intent == "history":
            data = await ctx.fetch("history", {"hours": match.hours})
            if data is not None:
                return render_history(data, ctx.site_url, tip), None
        elif match.intent == "top":
            data = await ctx.fetch("top100", None)
            if data is not None:
                state = PagerState(kind="top", page=1, per_page=match.top_n, updated_at=0.0)
                touch(state)
                return render_top100(data, ctx.site_url, 1, match.top_n, tip), state
        elif match.intent == "chart":
            data = await ctx.fetch("chart145", None)
            if data is not None:
                state = PagerState(kind="chart", page=1, per_page=match.top_n, updated_at=0.0)
                touch(state)
                return render_chart145(data, ctx.site_url, 1, match.top_n, tip), state
        elif match.intent == "rating":
            data = await ctx.fetch("ratinglist", None)
            if data is not None:
                view = select_version_view(data, match.version)
                if view is None:
                    return render_version_hint(data, match.version), None
                scoped = {"current": view}
                if match.lo == 0 and match.hi == 0:
                    return render_rating(scoped, ctx.site_url, tip), None
                return render_rating_range(
                    scoped, ctx.site_url, match.lo, match.hi, match.lo_label, match.hi_label, tip
                ), None
    except Exception:
        pass
    return render_fail(ctx.last_error()), None
