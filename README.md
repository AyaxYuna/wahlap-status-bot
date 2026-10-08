# Wahlap 服务器实时状态

AstrBot 插件：查询展示华立（舞萌DX国服）服务器实时状态与全服数据。

数据源为免鉴权聚合接口 `https://maimai.imikufans.cn`（聚合转发 [isMaiDown by Chongxi](https://mai.chongxi.us)，文档见 `https://maimai.imikufans.cn/docs.php`），**无需注册、无需申请 Key**。v1.0 仅做查询展示。

> 注意：`top100 / ratinglist / chart145` 依赖上游页面抓取，上游改版时可能短暂返回 `Fetch failed`，此时插件会直接提示获取失败而非崩溃。

## 指令

| 指令 | 说明 |
|---|---|
| `/wlstatus` | 服务器实时状态（6 探针服务 + 延迟 + 上报统计 + 公告） |
| `/wlhistory [时间]` | 服务可用性历史（默认 12 小时；支持 `24` / `2d` / `30min` / `一个小时` / `今天`） |
| `/wltop [条数]` | 全服游玩次数排行（默认 20 条/页，`当前页码：1/5`，`下一页`/`/wlnextpage` 翻页） |
| `/wlrating` | 当前版本全服 Rating 分布（无参看全部分段；`/wlrating w0-w3` / `10000-13000` / `w15` 查区间） |
| `/wlchart [条数]` | 高难谱面越级排行（默认 20 条/页，同上翻页） |
| `/wlhelp` | 显示帮助 |

## 自然问法（无需斜杠，直接发就行）

意图识别见 `qa/prompt.py`，回复渲染见 `qa/response.py`：

- 状态：`舞萌服务器炸了吗` / `华立服务器怎么了` / `舞萌net怎么了` / `网咋样` / `机台灰网` … → `/wlstatus`
- 历史：`华立服务器最近{num}分钟/小时/天怎么样` / `今天舞萌服务器怎么样` … → `/wlhistory`（分钟向上取整，范围钳位 1~48 小时）
- 排行：`推荐乐曲排行榜` / `推荐乐曲top{topnum}` / `热门歌曲榜` … → `/wltop`（默认 20）
- 越级：`越级谱面排行榜` / `越级谱面top{topnum}` / `145排行` … → `/wlchart`（默认 30）
- 分布：`rating从w0到w3有多少人` / `w11到w5的rating有多少人` / `rating从10000到14000有多少人` / `rating分布` … → `/wlrating`
  w 记法是圈内黑话：`wD` = 1.D 万（w0=10000，w5=15000，w15=11500），上限 w99=19900；也认 `1.5w` / `1w5` / 纸面数字。

命中后会自动截断事件（不触发 LLM 二次回复）；`/` 开头消息与本插件自己的回复会自动跳过，避免自激循环。`145` 这类纯数字必须搭配排行词才会触发，`这首歌真炸了` 这类夸歌说法会被间隙词过滤。

每条查询回复末尾会附一条随机小贴士（`qa/tips.py`，共 197 条：105 舞萌 + 75 音击角色 + 17 乐曲空耳）。
Tip 可用 `tip_enabled` 开关；`tip_bias` 用 Walker 别名表法加权（偏好类 60%，其余两类各 20%，O(1) 采样），默认不设置即全池均匀。

## 配置

在 AstrBot WebUI 插件页可视化配置（见 `_conf_schema.json`）：`base_url / site_url / timeout / status_cache_ttl(20s) / history_cache_ttl(300s) / static_cache_ttl(6h) / page_size(20) / pager_expire_min(30) / history_default_hours / tip_enabled(true) / tip_bias(不设置)`。

## 使用条款

- 回复末尾均标注数据来源，使用/分发时请保留。
- 建议调用频率 30 秒/次，插件内已按接口类型做缓存（状态 20s、历史 5min、静态排行 6h）。
- 非官方数据，仅供参考，与华立科技及世嘉官方无任何关联。
