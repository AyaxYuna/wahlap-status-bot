"""问题: 舞萌玩家常用问法 -> 查询意图.

语料来源: 玩家群聊黑话 (灰网/绿网/炸了/变游客/卡 logo/冯飞了...),
NoneBot 插件 nonebot-plugin-maimaimonitor 的关键词表, 以及 B 站相关讨论.
v1 仅覆盖查询类问法; 上报类 (被发票/扫号/小黑屋/罚站...) 不在范围内.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Intent = Literal["status", "history", "top", "chart", "rating"]
PageTurn = Literal["next", "prev"]


@dataclass(frozen=True)
class QAMatch:
    """意图识别结果, 按需填充 hours / top_n / rating 区间 / 版本."""

    intent: Intent
    hours: int = 0
    top_n: int = 0
    lo: int = 0
    hi: int = 0
    lo_label: str = ""
    hi_label: str = ""
    version: str = ""


@dataclass(frozen=True)
class RatingRange:
    """rating 区间: 数值 + 原文写法 (w0 / 10000 / 1.5w), has_w 表示含圈内 w 记法."""

    lo: int
    hi: int
    lo_text: str
    hi_text: str
    has_w: bool = False


# rating 上限: w99 = 19900, 日服暂无人达到, 先定为 cap
RATING_MAX = 19900


# 主语: 玩家对服务器 / 机台的常见称呼
_SUBJECT_RE = re.compile(r"(华立|舞萌|舞萌DX|maimai|服务器|机台|框体|NET|net|SEGA|世嘉|乌萌|乌蒙|乌蒙地插|洗衣机|官号|公众号|二维码|会员|标题)")

# 状态问法: 疑问式 (怎么了/咋样/能不能玩...) + 陈述式 (炸了/挂了/灰网...)
# 注意 "炸了" 在饭圈语境也可夸歌 ("这首歌真炸了"), 见 _GAP_BLOCKERS
_STATUS_QUERY_RE = re.compile(
    r"(炸了吗|死了吗|挂了吗|崩了吗|寄了吗|炸没炸|死没死|寄没寄"
    r"|怎么了|咋了|咋样|怎么样|如何|还好吗|好不好"
    r"|能不能玩|可以玩吗|能玩吗|能玩不|恢复了吗|恢复了没|好了吗|好了没"
    r"|正常吗|正常不|活着吗|还活着吗|什么情况|什么状况|啥情况|出问题了吗"
    r"|是不是又|又炸了|又挂了|又死了|又崩了|又寄了|又灰了"
    r"|炸了|挂了|死了|崩了|寄了|灰了|灰网|炸网"
    r"|卡logo|卡死|登不上|登录不上|上不去|扫不上|刷不出|打不开|连不上"
    r"|抽风了|发病了|萎了)"
)

# 主语与状态词之间出现这些词时, 视为在聊歌/成绩而非服务器 (如 "舞萌这首歌真炸了")
_GAP_BLOCKERS_RE = re.compile(r"(歌|曲|谱面|成绩|理论|收歌|笑|哈哈|combo|FC|AP|SSS|鸟|推分|出勤|段位)")

# 无需主语的完整问法 (全句匹配, 避免 "我炸了吗" 这类误伤)
_STATUS_EXACT = {"网咋样", "网怎么样", "炸了吗", "华立服务器死了吗"}

# 历史问法三要素: 时间范围 + 主语 + 状态追问
_HISTORY_NEAR_RE = re.compile(r"(最近|这|过去|今天|今日)")
_HISTORY_SUBJECT_RE = re.compile(r"(华立|舞萌|服务器|机台|NET|net|SEGA|世嘉|(?<!上)网)")
_HISTORY_STATE_RE = re.compile(
    r"(怎么样|如何|怎么了|咋样|咋了|稳定吗|稳不稳|稳吗|炸过吗|挂过吗"
    r"|死过吗|崩过吗|寄过吗|正常吗|还好吗|什么情况|啥情况|好不好)"
)

# 排行问法
_TOP_HOT_RE = re.compile(r"(推荐|热门|人气).{0,4}(乐曲|歌曲|歌|曲目)")
_TOP_RANK_RE = re.compile(r"(乐曲|歌曲|歌|全服|游玩|次数).{0,6}(排行|榜|排名|top)", re.IGNORECASE)
# 乐曲分组必填: 裸 top 数字可能是越级排行 ("越级谱面top15"), 交给 chart 意图
_TOP_NUM_RE = re.compile(r"(乐曲|歌曲|歌)\s*top\s*\d+", re.IGNORECASE)
_TOP_PLAY_RE = re.compile(r"(大家.{0,6}玩什么|玩什么歌|什么歌最火|最火的歌)")

# 越级排行问法 (145 这类数字必须搭配排行词, 否则 "这个 145 好难" 会误伤)
_CHART_WORD_RE = re.compile(r"(越级|高难|上位|魔王曲|144|143|142)")
_CHART_RANK_RE = re.compile(r"(排行|榜|排名|top)", re.IGNORECASE)
_CHART_RATE_RE = re.compile(r"(14\.5|145|15\.0)")
_CHART_CHART_RE = re.compile(r"谱面.{0,4}(排行|榜|top)", re.IGNORECASE)

# 时间表达式: 数字 + 单位 (阿拉伯数字优先, 中文数字兜底).
# 尾部用 (?![a-zA-Z]) 而非 \b: CJK 字符之间不存在 \b, 会把 "3小时怎么样" 误杀.
_TIME_RE = re.compile(
    r"(\d+)\s*(分钟|分|min(?:ute)?s?|m|小时|时|h|天|日|d)(?![a-zA-Z])", re.IGNORECASE
)
_CN_TIME_RE = re.compile(r"([一二三四五六七八九十两]{1,3})\s*个?\s*(分钟|分|小时|时|天|日)")

_CN_DIGITS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

_TOP_NUM_RE2 = re.compile(r"(?:top\s*(\d+))|(?:前\s*(\d+))", re.IGNORECASE)
_BARE_NUM_RE = re.compile(r"(\d+)")


def _cn_number(text: str) -> int | None:
    """解析一~九十九的中文数字 (含两/十), 失败返回 None."""
    if not text:
        return None
    if "十" in text:
        left, _, right = text.partition("十")
        if left == "":
            tens = 1
        elif len(left) == 1 and left in _CN_DIGITS:
            tens = _CN_DIGITS[left]
        else:
            return None
        if not right:
            return tens * 10
        if len(right) == 1 and right in _CN_DIGITS:
            return tens * 10 + _CN_DIGITS[right]
        return None
    if len(text) == 1 and text in _CN_DIGITS:
        return _CN_DIGITS[text]
    return None


def parse_hours(text: str, default: int) -> int:
    """从文本解析小时数: 支持 {num}分钟/小时/天、中文数字、今天/今日, 钳位 1~48."""
    match = _TIME_RE.search(text)
    if match is not None:
        num = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("min") or unit == "m" or "分钟" in unit or unit == "分":
            hours = -(-num // 60)  # 向上取整, 不足 1 小时按 1 小时
        elif unit in ("天", "日", "d"):
            hours = num * 24
        else:
            hours = num
        return max(1, min(48, hours))
    cn_match = _CN_TIME_RE.search(text)
    if cn_match is not None:
        cn_num = _cn_number(cn_match.group(1))
        if cn_num is not None:
            unit = cn_match.group(2)
            if "分钟" in unit or unit == "分":
                hours = -(-cn_num // 60)
            elif unit in ("天", "日"):
                hours = cn_num * 24
            else:
                hours = cn_num
            return max(1, min(48, hours))
    if "今天" in text or "今日" in text:
        return 24
    return default


def parse_top_n(text: str, default: int, maximum: int = 30) -> int:
    """从文本解析排行条数: 优先 topN / 前N, 其次首个裸数字, 钳位 1~maximum."""
    match = _TOP_NUM_RE2.search(text)
    num_text: str | None = None
    if match is not None:
        num_text = match.group(1) or match.group(2)
    if num_text is None:
        bare = _BARE_NUM_RE.search(text)
        if bare is not None:
            num_text = bare.group(1)
    if num_text is None:
        return default
    return max(1, min(maximum, int(num_text)))


def _match_status(text: str) -> QAMatch | None:
    if text in _STATUS_EXACT:
        return QAMatch(intent="status")
    for subject in _SUBJECT_RE.finditer(text):
        window = text[subject.end() : subject.end() + 10]
        query = _STATUS_QUERY_RE.search(window)
        if query is None or query.start() > 6:
            continue
        if _GAP_BLOCKERS_RE.search(window[: query.start()]) is not None:
            continue
        return QAMatch(intent="status")
    return None


def _match_history(text: str, hours_default: int) -> QAMatch | None:
    if (
        _HISTORY_NEAR_RE.search(text) is None
        or _HISTORY_SUBJECT_RE.search(text) is None
        or _HISTORY_STATE_RE.search(text) is None
    ):
        return None
    return QAMatch(intent="history", hours=parse_hours(text, hours_default))


# rating 语境: rating 本体 + 圈内代称 (底力/底分, 见 B 站底力提升系列视频)
_RATING_WORD_RE = re.compile(r"(rating|R值|r值|底力|底分|分段|分档)", re.IGNORECASE)
_RATING_COUNT_RE = re.compile(r"(有多少人|多少人|几人|人数|分布|统计|占比|几个)")

# rating 表达式三形态 (优先级 w > 万 > 裸数字, 重叠时 w 优先):
#   w 记法: wD = 1.D 万 (w0=10000, w5=15000, w15=11500, w99=19900 封顶)
#   万记法: 1.5w / 1.5万 = 15000, 1w5 / 1万5 = 15000 (尾数按小数位读)
#   裸数字: 10000 / 14000 (4~5 位, 避免把 145/15 误吞)
_W_TOKEN_RE = re.compile(r"[wW](\d{1,2})(?![0-9])")
_WAN_TOKEN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[wW万]\s*(\d{1,2})?(?![0-9])")
_NUM_TOKEN_RE = re.compile(r"(?<![\d.])(\d{4,5})(?![\d.])")
_RANGE_SEP_RE = re.compile(r"(到|至|[-~～—])")


def w_to_rating(token: str) -> int | None:
    """w 记法转 rating 数值: w0=10000, w5=15000, w15=11500, 超过 w99 返回 None."""
    match = re.fullmatch(r"[wW](\d{1,2})", token.strip())
    if match is None:
        return None
    digits = match.group(1)
    value = 10000 + int(digits) * 10 ** (4 - len(digits))
    return min(value, RATING_MAX)


def _clamp_rating(value: int) -> int:
    return max(0, min(RATING_MAX, value))


def parse_rating_range(text: str) -> RatingRange | None:
    """解析 rating 区间: 从w0到w3 / w11-w5 / 10000-14000 / 1.5w-1.8w / 单个 w15.

    无表达式返回 None; 双表达式需分隔符 (到/至/-), 否则只取首个.
    """
    spans: list[tuple[int, int]] = []

    def blank(start: int, end: int) -> None:
        spans.append((start, end))

    def overlaps(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in spans)

    exprs: list[tuple[int, int, int, str, bool]] = []  # pos, value, raw_end, label, has_w
    for match in _W_TOKEN_RE.finditer(text):
        value = w_to_rating(match.group(0))
        if value is None:
            continue
        exprs.append((match.start(), _clamp_rating(value), match.end(), match.group(0), True))
        blank(match.start(), match.end())
    for match in _WAN_TOKEN_RE.finditer(text):
        if overlaps(match.start(), match.end()):
            continue
        base = float(match.group(1))
        frac = match.group(2) or ""
        if frac:
            base += int(frac) / 10 ** len(frac)
        value = _clamp_rating(int(base * 10000))
        exprs.append((match.start(), value, match.end(), match.group(0), False))
        blank(match.start(), match.end())
    for match in _NUM_TOKEN_RE.finditer(text):
        if overlaps(match.start(), match.end()):
            continue
        exprs.append(
            (match.start(), _clamp_rating(int(match.group(1))), match.end(), match.group(1), False)
        )
    if not exprs:
        return None
    exprs.sort(key=lambda e: e[0])
    if len(exprs) >= 2:
        gap = text[exprs[0][2] : exprs[1][0]]
        if _RANGE_SEP_RE.search(gap) is not None:
            ( _, lo, _, lo_text, w1) = exprs[0]
            ( _, hi, _, hi_text, w2) = exprs[1]
            if lo > hi:
                lo, hi, lo_text, hi_text = hi, lo, hi_text, lo_text
            return RatingRange(lo=lo, hi=hi, lo_text=lo_text, hi_text=hi_text, has_w=w1 or w2)
    (_, value, _, label, has_w) = exprs[0]
    return RatingRange(lo=value, hi=value, lo_text=label, hi_text=label, has_w=has_w)


def _match_rating(text: str) -> QAMatch | None:
    version, cleaned = extract_version(text)
    has_word = _RATING_WORD_RE.search(cleaned) is not None
    has_count = _RATING_COUNT_RE.search(cleaned) is not None
    rating_range = parse_rating_range(cleaned)
    if rating_range is None:
        # 全量: "rating分布" / "DX2025的rating分布"
        if has_word and has_count:
            return QAMatch(intent="rating", version=version)
        return None
    if not (has_word or has_count):
        return None
    if not rating_range.has_w and not has_word:
        # 裸数字区间 ("10000-14000有多少人") 必须有 rating 词, 否则太像别的话题
        return None
    return QAMatch(
        intent="rating",
        lo=rating_range.lo,
        hi=rating_range.hi,
        lo_label=rating_range.lo_text,
        hi_label=rating_range.hi_text,
        version=version,
    )


# 版本别名: 国服写法 / 日服代号 / 牌名 / 曲库字 / 玩家代称 -> 国服 canonical label.
# 曲库字与日服对照 (萌娘百科): 华=DX+ / 爽=Splash / 煌=Splash+ / 宙=UNiVERSE /
#   星=UNiVERSE+ / 祭=FESTiVAL / 祝=FESTiVAL+ / 双=BUDDiES / 镜=PRiSM / 宴≈BUDDiES+.
# 牌名: 爽煌=DX2021 / 宙星=DX2022 / 祭祝=DX2023 / 双宴=DX2024.
# 注意 "祝" 同时出现在 DX2023 牌名(祭祝) 与 DX2024 曲库(祝+双) 中,
# 按"有祝曲的版本"归属 DX2024 ("打完祝代双代曲"即指 DX2024).
_VERSION_ALIASES: dict[str, str] = {
    "dx2021": "DX2021",
    "dx2022": "DX2022",
    "dx2023": "DX2023",
    "dx2024": "DX2024",
    "dx2025": "DX2025",
    "dx2026": "DX2026",
    "festival": "DX2023",
    "festival plus": "DX2024",
    "buddies": "DX2024",
    "buddies plus": "DX2025",
    "prism": "DX2025",
    "prism plus": "DX2026",
    "universe": "DX2022",
    "universe plus": "DX2023",
    "splash": "DX2021",
    "splash plus": "DX2022",
    "爽煌": "DX2021",
    "宙星": "DX2022",
    "祭祝": "DX2023",
    "双宴": "DX2024",
    "华": "DX2021",
    "爽": "DX2021",
    "煌": "DX2022",
    "宙": "DX2022",
    "星": "DX2023",
    "祭": "DX2023",
    "祝": "DX2024",
    "双": "DX2024",
    "镜": "DX2025",
    "宴": "DX2025",
    "华代": "DX2021",
    "爽代": "DX2021",
    "煌代": "DX2022",
    "宙代": "DX2022",
    "星代": "DX2023",
    "祭代": "DX2023",
    "祝代": "DX2024",
    "双代": "DX2024",
    "镜代": "DX2025",
    "宴代": "DX2025",
}

# 版本提及: 多字别名可裸匹配; 单字与裸年份必须带 版本/版/代 后缀
# (裸 "2023" 仍视为 rating 数字, 避免吞掉区间).
_VERSION_RE = re.compile(
    r"(dx\s?20\d{2}"
    r"|舞萌\s?dx?\s?20\d{2}"
    r"|国服\s?20\d{2}"
    r"|20\d{2}\s*(?:版本|版|代)"
    r"|(?:dx|舞萌|国服)?\s*[华爽煌宙星祭祝双镜宴]\s*(?:版本|版|代)"
    r"|festival\s*(?:plus|\+|＋)?|buddies\s*(?:plus|\+|＋)?|prism\s*(?:plus|\+|＋)?"
    r"|universe\s*(?:plus|\+|＋)?|splash\s*(?:plus|\+|＋)?"
    r"|爽煌|宙星|祭祝|双宴"
    r"|华代|爽代|煌代|宙代|星代|祭代|祝代|双代|镜代|宴代)",
    re.IGNORECASE,
)


def extract_version(text: str) -> tuple[str, str]:
    """识别版本并返回 (canonical label, 抹掉版本词后的文本); 无版本返回 ("", 原文)."""
    match = _VERSION_RE.search(text)
    if match is None:
        return "", text
    key = match.group(0).lower().replace("+", " plus").replace("＋", " plus")
    key = re.sub(r"\s+", " ", key).strip()
    key = re.sub(r"^(?:dx|舞萌\s?dx?|国服)\s*", "", key)
    key = re.sub(r"\s*(?:版本|版|代)$", "", key)
    canonical = ""
    if re.fullmatch(r"20\d{2}", key):
        canonical = f"DX{key}"
    else:
        canonical = _VERSION_ALIASES.get(key, "")
    if not canonical:
        return "", text
    cleaned = text[: match.start()] + " " + text[match.end() :]
    return canonical, cleaned


def _match_top(text: str, top_default: int) -> QAMatch | None:
    if (
        _TOP_HOT_RE.search(text) is not None
        or _TOP_RANK_RE.search(text) is not None
        or _TOP_NUM_RE.search(text) is not None
        or _TOP_PLAY_RE.search(text) is not None
    ):
        return QAMatch(intent="top", top_n=parse_top_n(text, top_default))
    return None


def _match_chart(text: str, chart_default: int) -> QAMatch | None:
    has_word = _CHART_WORD_RE.search(text) is not None
    has_rank = _CHART_RANK_RE.search(text) is not None
    has_rate = _CHART_RATE_RE.search(text) is not None
    if (has_word or has_rate) and has_rank:
        return QAMatch(intent="chart", top_n=parse_top_n(text, chart_default))
    if _CHART_CHART_RE.search(text) is not None and (has_word or has_rate):
        return QAMatch(intent="chart", top_n=parse_top_n(text, chart_default))
    return None


# 翻页: 必须整句匹配 ("下一页"/"上一页" 类)，避免误伤正常聊天
_PAGE_NEXT_RE = re.compile(r"^(?:翻|看|来)?\s*(?:下一页|下一頁|下页|下頁|next|下一张|下张)$", re.IGNORECASE)
_PAGE_PREV_RE = re.compile(r"^(?:翻|看|来)?\s*(?:上一页|上一頁|上页|上頁|prev|上一张|上张)$", re.IGNORECASE)


def match_page_turn(text: str) -> PageTurn | None:
    """识别翻页意图; 非翻页返回 None."""
    normalized = text.strip().lower().rstrip("。！？!?.～~")
    if _PAGE_NEXT_RE.match(normalized) is not None:
        return "next"
    if _PAGE_PREV_RE.match(normalized) is not None:
        return "prev"
    return None


def match_question(
    text: str,
    hours_default: int = 12,
    page_size: int = 20,
) -> QAMatch | None:
    """匹配玩家问法, 返回意图与槽位; 无关消息返回 None."""
    stripped = text.strip()
    if not stripped:
        return None
    # 越具体的意图越先匹配: 历史 > 排行 > 越级 > 分布 > 状态
    for matcher in (
        lambda s: _match_history(s, hours_default),
        lambda s: _match_top(s, page_size),
        lambda s: _match_chart(s, page_size),
        _match_rating,
        _match_status,
    ):
        matched = matcher(stripped)
        if matched is not None:
            return matched
    return None
