# -*- coding: utf-8 -*-
"""peppa_content_check.py —— 每日内容质量校验器

用法:
    python peppa_content_check.py daily_content.json [more.json ...]

校验五类问题:
  1. 结构   —— 必填字段缺失、类型错、枚举值非法
  2. 数量   —— 单词/问题/时间轴拍数是否达下限
  3. 咬合   —— 提问/玩法/金句是否真的提到本集的东西（关键词重合度）
  4. 重复   —— 30 天滑动窗口内，问题/玩法/金句是否与往期雷同
  5. 难度   —— 是否与 day_type + difficulty 档位相符
"""
import json, io, re, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DAY_TYPE_SET = {"新剧日", "台词日", "单词日", "动手日", "创作日", "家庭日", "复习日",
                "主题周", "里程碑日", "反转日", "无屏幕日"}
ASK_TYPE_SET = {"回忆", "联系生活", "想象", "情绪", "判断", "预测"}
STAGE_SET = {"开场", "铺垫", "转折", "小冲突", "高潮", "解决", "结尾"}
TIP_KIND_SET = {"发音", "文化", "育儿", "安全"}
PLOT_SOURCE_SET = {"tvmaze", "tmdb", "bilibili_subtitle", "llm"}

STOP = set("的了是在有和就都而及与也很不你我他她它们个这那什么怎么样的吗吧啊要会能对从把被给让给".split())


def norm(s):
    """归一化文本用于比较：去标点、转小写、去停用词"""
    s = str(s).lower()
    s = re.sub(r"[，。！？、；：\"'（）()\[\]…—·,.!?;:]", "", s)
    return "".join(ch for ch in s if ch not in STOP)


def tokens(s):
    """抽取中文 2-gram + 单字 + 英文单词，用于咬合度计算。
    同时注入同义词组，缓解「水坑 vs 泥坑」这类字面不重合的误报。"""
    n = norm(s)
    zh = set(n[i:i + 2] for i in range(len(n) - 1)) if len(n) > 1 else set()
    zh |= set(n)                       # 单字也算
    en = set(re.findall(r"[a-z]{3,}", str(s).lower()))
    return zh | en


SYN = [
    ("水坑", "泥坑"), ("坑", "泥"), ("雨衣", "雨"), ("鞋", "靴"),
    ("难过", "伤心"), ("开心", "高兴"), ("玩具", "恐龙"), ("找", "寻"),
]
def syn_expand(tk):
    """把命中的同义对另一侧也加入，扩大咬合命中范围"""
    extra = set()
    for a, b in SYN:
        if a in tk or b in tk:
            extra |= {a, b}
    return tk | extra


def check_file(path, verbose=True):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    errs, warns = [], []
    eps = data.get("episodes", [])
    if not eps:
        print(f"[FAIL] {path}: episodes 为空")
        return 1

    seen_days = set()
    hist = []      # 滑动窗口 [(asks, play, lines)]
    WINDOW = 30

    for e in eps:
        ep = e.get("ep", "??")
        day = e.get("day")
        c = e.get("content", {})

        # ---------- 1. 结构 ----------
        for f in ("ep", "day", "title", "day_type", "difficulty", "content"):
            if f not in e:
                errs.append(f"{ep}: 缺字段 {f}")
        if not re.match(r"^\d+-\d{2}$", str(ep)):
            errs.append(f"{ep}: ep 格式应为 season-episode")
        if day in seen_days:
            errs.append(f"{ep}: day={day} 重复")
        seen_days.add(day)

        if e.get("day_type") not in DAY_TYPE_SET:
            errs.append(f"{ep}: day_type 非法 '{e.get('day_type')}'")
        if e.get("difficulty") not in {"简单", "中等", "挑战"}:
            errs.append(f"{ep}: difficulty 非法")

        t = e.get("title", {})
        if not t.get("zh") or not t.get("en"):
            errs.append(f"{ep}: title 需含 zh 与 en")

        # ---------- 2. 数量 ----------
        plot = c.get("plot", {})
        if not plot.get("summary"):
            errs.append(f"{ep}: plot.summary 缺失")
        else:
            L = len(plot["summary"])
            if L > 160:
                warns.append(f"{ep}: plot.summary {L} 字，超出建议上限 160")
            if L < 30:
                warns.append(f"{ep}: plot.summary 仅 {L} 字，可能过短")
        if plot.get("source") not in PLOT_SOURCE_SET:
            warns.append(f"{ep}: plot.source 未标注或非法")

        core = c.get("core", {})
        if not core.get("lesson"):
            errs.append(f"{ep}: core.lesson 缺失")
        if not (2 <= len(core.get("keywords", [])) <= 4):
            warns.append(f"{ep}: core.keywords 应为 2-4 个")

        beats = c.get("beats", [])
        if not (3 <= len(beats) <= 6):
            errs.append(f"{ep}: beats 应为 3-6 拍，实际 {len(beats)}")
        for i, b in enumerate(beats):
            if b.get("stage") not in STAGE_SET:
                errs.append(f"{ep}: beats[{i}].stage 非法 '{b.get('stage')}'")
            if not b.get("desc"):
                errs.append(f"{ep}: beats[{i}].desc 缺失")

        words = c.get("words", [])
        if not (3 <= len(words) <= 6):
            errs.append(f"{ep}: words 应为 3-6 个，实际 {len(words)}")
        for i, w in enumerate(words):
            for f in ("en", "ipa", "zh", "level"):
                if f not in w:
                    errs.append(f"{ep}: words[{i}] 缺 {f}")
            lv = w.get("level")
            if lv is not None and not (isinstance(lv, int) and 1 <= lv <= 3):
                errs.append(f"{ep}: words[{i}].level 应为 1-3 整数")
        # 同集内单词去重
        ens = [w.get("en", "").lower() for w in words]
        if len(ens) != len(set(ens)):
            warns.append(f"{ep}: words 内部有重复单词")

        lines = c.get("lines", [])
        if not (1 <= len(lines) <= 3):
            errs.append(f"{ep}: lines 应为 1-3 句")
        for i, l in enumerate(lines):
            if not l.get("en") or not l.get("zh"):
                errs.append(f"{ep}: lines[{i}] 缺 en 或 zh")

        asks = c.get("ask", [])
        if not (2 <= len(asks) <= 4):
            errs.append(f"{ep}: ask 应为 2-4 条，实际 {len(asks)}")
        for i, a in enumerate(asks):
            if a.get("type") not in ASK_TYPE_SET:
                errs.append(f"{ep}: ask[{i}].type 非法 '{a.get('type')}'")
            if not a.get("q"):
                errs.append(f"{ep}: ask[{i}].q 缺失")
        # 三层结构：至少覆盖 回忆 + 一种发散
        atypes = {a.get("type") for a in asks}
        if "回忆" not in atypes:
            warns.append(f"{ep}: ask 缺少「回忆」类问题")
        if not atypes & {"想象", "判断", "预测"}:
            warns.append(f"{ep}: ask 缺少发散类（想象/判断/预测）")

        play = c.get("play", {})
        if not play.get("activity"):
            errs.append(f"{ep}: play.activity 缺失")
        if not isinstance(play.get("duration_min"), int):
            warns.append(f"{ep}: play.duration_min 未标注或非整数")

        for i, tp in enumerate(c.get("tips", [])):
            if tp.get("kind") not in TIP_KIND_SET:
                warns.append(f"{ep}: tips[{i}].kind 非法 '{tp.get('kind')}'")

        for i, q in enumerate(c.get("quiz", [])):
            opts = q.get("options", [])
            if len(opts) < 2:
                errs.append(f"{ep}: quiz[{i}] 选项不足")
            ans = q.get("answer")
            if ans is None:
                warns.append(f"{ep}: quiz[{i}] 未给 answer")
            elif not isinstance(ans, int) or not (0 <= ans < len(opts)):
                errs.append(f"{ep}: quiz[{i}].answer 越界")

        # ---------- 3. 咬合度：提问/玩法/金句是否提到本集 ----------
        ep_tok = syn_expand(tokens(t.get("zh", "") + " " + t.get("en", "") + " " +
                        plot.get("summary", "") + " " +
                        " ".join(b.get("desc", "") for b in beats)))
        for i, a in enumerate(asks):
            overlap = syn_expand(tokens(a.get("q", ""))) & ep_tok
            if len(overlap) == 0:
                warns.append(f"{ep}: ask[{i}] 与本集内容无明显咬合")
        play_ov = syn_expand(tokens(play.get("activity", ""))) & ep_tok
        if len(play_ov) == 0:
            warns.append(f"{ep}: play 未提及本集任何要素，可能过于泛用")

        # ---------- 4. 重复检测（30 天窗口）----------
        cur_asks = [norm(a.get("q", "")) for a in asks]
        cur_play = norm(play.get("activity", ""))
        cur_lines = [norm(l.get("en", "")) for l in lines]
        dup_hit = []

        for j, (pa_list, ppl, pl_list) in enumerate(hist):
            overlap = 0
            for ca in cur_asks:
                if not ca:
                    continue
                for pa in pa_list:
                    if pa and (pa == ca or pa in ca or ca in pa):
                        overlap += 1
                        break
            if overlap >= 2:
                dup_hit.append("提问与 %d 天前雷同" % (day - (len(hist) - j)))
            if ppl and cur_play and (ppl == cur_play or ppl in cur_play or cur_play in ppl):
                dup_hit.append("玩法与 %d 天前雷同" % (day - (len(hist) - j)))
            for pl in pl_list:
                if pl and pl in cur_lines:
                    dup_hit.append("金句与 %d 天前重复" % (day - (len(hist) - j)))
                    break
        if dup_hit:
            warns.append(f"{ep}: " + "；".join(dup_hit[:3]))

        hist.append((cur_asks, cur_play, cur_lines))
        if len(hist) > WINDOW:
            hist.pop(0)

        # ---------- 5. 难度一致性 ----------
        lvl = e.get("difficulty")
        avg_word_lv = sum(w.get("level", 2) for w in words) / max(len(words), 1)
        if lvl == "简单" and avg_word_lv > 2.4:
            warns.append(f"{ep}: 标为「简单」但平均单词难度 %.1f 偏高" % avg_word_lv)
        if lvl == "挑战" and avg_word_lv < 1.6:
            warns.append(f"{ep}: 标为「挑战」但单词过于简单")
        if e.get("day_type") == "复习日" and not c.get("review"):
            warns.append(f"{ep}: 复习日缺少 review 排期")

    # ---------- 汇总 ----------
    tag = path.split("\\")[-1].split("/")[-1]
    print(f"=== {tag} ===")
    print(f"集数：{len(eps)}　错误：{len(errs)}　警告：{len(warns)}")
    if errs:
        print("\n[错误]")
        for x in errs[:40]:
            print("  ✗", x)
        if len(errs) > 40:
            print(f"  ... 另有 {len(errs)-40} 条")
    if warns and verbose:
        print("\n[警告]")
        for x in warns[:30]:
            print("  !", x)
        if len(warns) > 30:
            print(f"  ... 另有 {len(warns)-30} 条")
    if not errs and not warns:
        print("  ✓ 全部通过")
    return len(errs)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    total = sum(check_file(p) for p in sys.argv[1:])
    sys.exit(1 if total else 0)