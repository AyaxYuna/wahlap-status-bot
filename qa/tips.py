"""游玩小贴士: 每条回复末尾随机附一条.

共 100 条: 75 条舞萌相关 + 25 条音击角色相关.
语料来源: SEGA 官网玩法说明、萌娘百科、玩家社区黑话与 B 站攻略.
"""

from __future__ import annotations

import random

MAIMAI_TIPS: list[str] = [
    # 第一条固定
    "上机游玩时不要大力拍打或滑动哟～",
    # 基础操作
    "TAP既可以拍按键，也可以直接摸屏幕",
    "滑星只能在屏幕上滑，按键可滑不动它",
    "打滑星先点一下星星头再滑动，别直接蹭",
    "滑星判定区比看起来大，活用它偷吃步吧",
    "同时出现的圆圈会变黄，记得一起按下去",
    "HOLD要按到尾巴结束，提前松手会断连击",
    "围着屏幕的8个键都会用到，先热热手腕吧",
    "想冲DX分数，就多啃BREAK多的谱",
    "选曲时按8号键可以直接降一档难度",
    "判定总对不上？去设置里调JUDGMENT TIMING",
    "单人只占机台一边，把另一边让给拼机的朋友",
    "等不及倒计时？按5号键直接跳过",
    "拼机时两人都Full Combo，就能点亮Full Sync",
    "想要Full Sync DX？先和搭子一起打出All Perfect",
    # 成绩与段位
    "FC就是全连，一个Miss都不能有",
    "FC+要求不断连，且只有Perfect和Great判定",
    "AP要求全曲没有Great以下判定",
    "SSS要100%以上，SSS+要100.5%以上",
    "理论值是101%，先定个100.5%的小目标吧",
    "DX Rating就是大家说的底分/底力",
    "总Rating由新版本B15和旧版本B35共50首构成",
    "10000分是紫，12000变铜，13000变银",
    "14000金，14500白金，15000出虹！",
    "16000是虹极，w99？那是给外星人准备的",
    "卡在15000上不去？去啃14+谱面吧",
    "紫色谱面是MASTER，红色EXPERT过了就试试",
    "Re:MASTER不是每首歌都有，遇到请珍惜",
    "推分遇到瓶颈？换首慢歌找找手感",
    "拼机难度不同？低难度那侧更容易拿同步标记",
    # 服务器与账号
    "国服查分要绑微信，去舞萌DX公众号找「我的记录」",
    "上机先扫码登录，别一路当游客",
    "变游客了？多半是机台断网了",
    "二维码刷不出来，可以去公众号NET碰碰运气",
    "频繁狂点NET可能会进小黑屋冷静一下",
    "开机卡logo不动？先检查机厅网络",
    "人多时自觉排队，别让后面罚站太久",
    "打歌前先查查服务器状态，灰网就改天再战",
    "本插件的状态数据来自isMaiDown的机台探针",
    "出勤前看看群里有没有人喊老冯起飞",
    "群里喊「绿网了」，一般就是服务器恢复了",
    "服务器炸了别慌，先问我一句「网咋样」",
    "水鱼查分器可以备份你的成绩",
    "成绩导入需要一点动手能力，备好教程",
    # 文化与版本
    "框体像滚筒洗衣机？SEGA官方都玩过这个梗",
    "有人叫它乌萌，说的也是舞萌DX",
    "国服2019年起由华立代理运营",
    "以前的旧框玩不到新曲，追版本要去新框",
    "国服大约一年更新一个大版本",
    "全服Rating分布的标题里，写着当前国服版本",
    "中二和音击是亲姐妹，联动曲经常串门",
    "华立每年都会办WEC电竞比赛",
    "找机厅可以用玩家维护的全国音游地图",
    "没机厅？平板手台也能先练起来",
    "对着墙打的前辈也是真实存在的",
    "东方曲和V家曲都是配信常客",
    "想和大家玩一样的歌？去看看全服游玩Top100",
    # 收集与系统
    "段位认定要一口气打完4首歌",
    "段位认定有血条，空了就直接寄了",
    "还有随机段位，手气不好别怪我",
    "旅伴地图推完了吗？里面藏着解锁曲",
    "称号和姓名框是收集党的命",
    "本周课题曲记得打，有额外奖励拿",
    "集章卡进度可以在NET上查",
    "昵称里可以加平假名和片假名",
    "昵称改一次要等10次游玩",
    "新手教程可以跳过，但建议打完",
    "觉得机厅太吵？试试插上耳机",
    "别在机厅大喊大叫，当心当场社死",
    "maimai是2012年出生的老前辈了",
    "舞萌这个译名，被称为最信达雅的翻译之一",
    "一万分才算入门？别听大佬们凡尔赛",
    "七千底分的大佬也是从绿谱练起的",
    "绿色是BASIC，黄色是ADVANCED，新手从绿谱起步",
    "出勤记得带水，体力谱很耗人",
    "Oshama Scramble!是t+pazolite写的，看板娘是しゃま",
    "しゃま表面是牛奶公司社长，背地里是见习魔法使",
    "しゃま卖的牛奶，据说加了特别的魔法",
    "しゃま以前说话带にゃん口癖，后来改了",
    "米璐库也是FiNALE出身的老搭档了",
    "PANDORA PARADOXXX是削除写的，曾是maimai第一个15级",
    "潘多拉魔盒要集徽章，最少准备7个币",
    "潘多拉Re:MAS曾被KOP决赛ban过",
    "从魔盒进潘多拉有15秒专属演出",
    "潘多拉还有后日谈AFTER PANDORA",
    "宴会场CYCLES是从头滑到尾的滑星宴",
    "有人上下反转打QZKago拿AP，你呢",
    "KOP新曲GIGANTØMAKHIA了解一下",
    "系ぎて和Λzure Vixen都是5th KOP的歌",
    "宙天是t+pazolite写的6th KOP新曲",
    "AMAZING MIGHTYYYY!!!!是14+吃分好选择",
    "封焔の135秒，体力谱刷分香",
    "旅伴满级9999，还能超觉醒重练",
    "旅伴到特定等级会觉醒，9999级满6星",
    "每个版本都有无尽区域，刷距离用它",
    "日服有机台打印的DX Pass卡，加成15天",
    "国服不能在NET加对手，上机才能加",
    "绝版集章卡能在舞里程商店买到",
    "判定显示也能换皮肤，去NET里调",
    "国服也收录了YOASOBI的アイドル",
    "KING of Performai是官方全国大赛",
    "セツナトリップ这种老歌，常年混迹段位曲",
    "Grip & Break down也是段位常客",
    "唱和シャルル都进过初段，你也行",
    "しゃま在DX PLUS当回了搭档",
]

ONGEKI_TIPS: list[str] = [
    "星咲あかり(CV赤尾ひかる)，总喊着和你一起加油",
    "藤沢柚子7月11日生日，和maimai初代是同一天",
    "あかり的代表曲是Perfect Shining!!",
    "藤沢柚子(CV久保田梨沙)随身带着糖果包，见者有份",
    "柚子的登场台词是「じゃっじゃ～ん！柚子、登場～！」",
    "三角葵(CV春野杏)，「お手柔らかにお願いね」",
    "あかり/柚子/葵三人组叫ASTERISM，人称ponkotsu三人组",
    "ASTERISM的代表曲是Starring Stars",
    "高瀬梨緒(CV久保ユリカ)，和μ's的小泉花陽同一个声优",
    "梨緒的口头禅是「アタシが高瀬梨緒よ！」",
    "結城莉玖(CV朝日奈丸佳)，口癖是がおー",
    "梨緒/莉玖/椿的⊿TRiEDGE，组合曲是本能的 Survivor",
    "藍原椿(CV橋本ちなみ)，总问你要不要她陪",
    "椿的タテマエと本心の大乱闘，在舞萌和中二也能玩到",
    "早乙女彩華(CV中島唯)，「おーっす、彩華だよ♪」",
    "桜井春菜(CV近藤玲奈)，初见面就要和你握手",
    "九條楓(CV佳村はるか)，是学生会副会长",
    "柏木咲姫(CV石見舞菜香)，还给GGST的布莉姬配过音",
    "STARTLINER是kz(livetune)写的音击主题曲",
    "三角葵7月16日生日",
    "逢坂茜(CV大空直美)是R.B.P.成员",
    "珠洲島有栖(CV長縄まりあ)也是R.B.P.成员",
    "HEADLINER是全员合唱纪念曲",
    "R.B.P.是茜/楓/有栖三人组",
    "Grievous Lady是Arcaea联动来的",
    "主线第4章叫負のオンゲキ",
    "每月任务攒牌子去奖牌店换bonus曲",
    "在日本，单曲排名可以在音击NET上查，手台用户可以通过三方NET服务查分",
    "星星票能给卡牌突破等级上限",
    "每周1次5连必出SR以上",
    "推し角色最多能注册30个",
    "No Limit RED Force是あかり/椿/彩華/咲姫/美亜五人曲",
    "角色歌CD里附赠游戏能用的SR卡",
    "咲姫在Re:ステージ里也有登场",
    "玩家们被称为オンゲキシューターズ",
    "版本从無印一路走到了Re:Fresh Act.2...",
    "スン(マイル)フラワー是あかり和千夏的二重唱",
    "音击角色们生活的校园是奏坂学园，主角是高二的三人组",
    "落ちこぼれ三人组也有大梦想",
    "校内大赛叫奏坂festa，攒エール才能参赛",
    "第1章标题就叫Let's Shoot ONGEKI",
    "音击无印2018年7月26日稼动，和あかり同一天生日",
    "前半打音击猫，后半打BOSS",
    "BOSS没打倒只能拿DRAW，WIN才是真通关",
    "这游戏有KADOKAWA参与制作",
    "音游加弹幕射击，摇杆躲子弹才是本体",
    "音击，可按键，可摇动，音乐沉浸，开始闪耀四方",
    "音击，是SEGA创造的一个 神 音乐游戏",
    "TAP只看颜色不看位置，左右手随便换",
    "黄色铃铛全回收叫FULL BELL",
    "赤紫橙子弹伤害分别是18/36/54%",
    "卡组强度不够，理论值也救不了你",
    "火水木三属性相克，组卡要看相性",
    "一局100円保底两首，印卡另算",
    "想用自机角色？去CARD MAKER印卡",
    "LUNATIC谱面？那是另一个游戏",
    "音击至今没有国际版，想玩只能去日本（手台我不叙述了）",
    "あかり的声优是听声选中的，当时连人设都没有",
    "梨緒自称超絶最強，还单方面把あかり当对手",
    "莉玖5月5日生日，玩吉他的假小子",
    "椿12月31日生日，不擅表达还有点S",
    "美亜是咲姫的亲妹妹，猫系可爱女生",
    "咲姫3月3日生日，优等生背地里玩cos",
    "小星11月23日生日，重度怕麻烦游戏宅",
    "彩華2月14日生日，恋爱话题苦手却爱当相談役",
    "春菜6月12日生日，沉迷做点心还有点天然",
    "桜井春菜，我的妈妈",
    "千夏8月22日生日，好奇心旺盛根本坐不住",
    "つむぎ10月27日生日，最讨厌被当成小孩",
    "有栖9月6日生日，整天穿玩偶装的神秘少女，江江~",
    "茜4月1日生日，目标世界征服的赤き天災",
    "楓10月1日生日，惹怒她很可怕还是机械白痴",
    "7EVENDAYS<-->HOLIDAYS是学年差最大的组合",
    "bitter flavor是春菜和彩華的双人组",
    "マーチングポケッツ是中学生三人组",
    "美亜曾作为谜之角色带boss曲先行登场",
    "柚子是慢悠悠的乐天派",
    "あかり是努力家，团队气氛制造机",
]

MUSIC_TIPS: list[str] = [
    "啊🤪～啊🤪～啊咦😬啊咦😬啊→啊↑啊↓😨啊😰～嗯💥哎哎🤗哎哦哎嗯😋～哦哎🥳爱爱爱爱爱😍 ——《TECHNOPOLIS 2085》",
    "stop in my mind.(stop playing maimai.) ——《Climax》",
    "Make some noise! ——《Climax》",
    "光鲜亮丽~光鲜光鲜亮丽~鸡丝拉拉拉拉拉面~ ——《INFiNiTE ENERZY -Overdoze-》",
    "冬の窓辺に~冬の窓辺に~冬の窓辺に~花花花一輪~ ——《花と、雪と、ドラムンベース。》",
    "Result! Fantastic Clear! Rank SS! Ahahahaha... ——《QZKago Requiem》",
    "Let's 牛乳 Dance! ——《Oshama Scramble》",
    "啊——！我没有拿外卖！——《Tempestissimo》",
    "湖南辣子谁放油，看着放，别放多麻辣烧饼都来要 ——《YURUSHITE》",
    "Let's f**king go! ——《Retribution》",
    "你别想收了这首歌！——《Retribution》",
    "巴拉巴巴巴~巴巴拉巴拉巴巴巴~ ——《コスモポップファンクラブ》",
    "天苍苍，野茫茫，风吹草低见牛羊！争渡，争渡，惊起一滩鸥鹭！——《PANDORA PARADOXXX》",
    "我 有 抑 郁 症 ——《PANDORA PARADOXXX》",
    "我 治 好 了 抑 郁 症 ——《系ぎて》",
    "我 治 好 了 抑 郁 症 ——《AFTER PANDORA》",
    "压力巨大！压力爆炸！压力压力！巨大压力！——《Xaleid◆scopiX》",
    "我去，是吴奇隆！——《Apollo》",
    "小鸡裹麻袋~啊~小鸡裹麻袋... ——《超主人公》",
    "三倍~ice cream! ——《Second Heaven》",
    "I don't give a f**k... ——《DESTRUCTION 3,2,1》",
    "玛德 蓝原椿推 ——《Ai C》",
    "达咩达咩~达咩哟~ ——《ばかみたい》",
]

TIPS: list[str] = MAIMAI_TIPS + ONGEKI_TIPS + MUSIC_TIPS

# 类别池 (与 TIPS 顺序对应)
POOLS: tuple[list[str], list[str], list[str]] = (MAIMAI_TIPS, ONGEKI_TIPS, MUSIC_TIPS)

# 偏好权重: 偏好类:其余 = 3:1:1 (即 60% / 20% / 20%)
BIAS_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "舞萌类优先": (3.0, 1.0, 1.0),
    "音击类优先": (1.0, 3.0, 1.0),
    "乐曲空耳类优先": (1.0, 1.0, 3.0),
}


def _build_alias(weights: tuple[float, ...]) -> tuple[list[float], list[int]]:
    """Vose 别名表构建 (O(n)): 返回 (每格自留概率, 别名下标).

    思想: 把 n 个权重切分装进 n 个容量为 1/n 的格子, 每格至多两种权重.
    """
    n = len(weights)
    total = sum(weights)
    scaled = [w * n / total for w in weights]
    prob = [0.0] * n
    alias = list(range(n))
    small = [i for i, s in enumerate(scaled) if s < 1.0]
    large = [i for i, s in enumerate(scaled) if s >= 1.0]
    while small and large:
        small_idx = small.pop()
        large_idx = large.pop()
        prob[small_idx] = scaled[small_idx]
        alias[small_idx] = large_idx
        scaled[large_idx] = scaled[large_idx] - (1.0 - scaled[small_idx])
        if scaled[large_idx] < 1.0:
            small.append(large_idx)
        else:
            large.append(large_idx)
    for i in small + large:
        prob[i] = 1.0
    return prob, alias


_ALIAS_TABLES: dict[str, tuple[list[float], list[int]]] = {
    mode: _build_alias(weights) for mode, weights in BIAS_WEIGHTS.items()
}


def _alias_sample(mode: str) -> int:
    """O(1) 采样: 掷骰子选格, 再抛硬币决定取本格还是别名格."""
    prob, alias = _ALIAS_TABLES[mode]
    n = len(prob)
    col = int(random.random() * n)
    if col >= n:  # random() < 1 恒成立, 纯防御
        col = n - 1
    if random.random() < prob[col]:
        return col
    return alias[col]


def get_tip(bias: str = "不设置") -> str:
    """取一条小贴士; bias 为偏好模式, 未知/不设置时全池均匀抽取."""
    if bias not in _ALIAS_TABLES:
        return random.choice(TIPS)
    pool = POOLS[_alias_sample(bias)]
    return random.choice(pool)


def resolve_tip(enabled: bool, bias: str = "不设置") -> str:
    """按开关与偏好解析: 关闭返回空串 (调用方不显示 Tip 行)."""
    if not enabled:
        return ""
    return get_tip(bias)
