# -*- coding: utf-8 -*-
"""渲染超深度样张：每日亲子学习单 daily_deep.html / .pdf
数据：daily_content_deep.json
新增区块：场景时间轴 beats / 角色情绪 roles / 例句 words.ex / 家长提示 tips / 小测验 quiz
"""
import json, io, sys, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("daily_content_deep.json", encoding="utf-8") as f:
    data = json.load(f)

START = datetime.date(2026, 9, 21)
WD = ["一", "二", "三", "四", "五", "六", "日"]
DAY_TYPES = ["📺 新剧日", "🗣 台词日", "🔤 单词日", "✋ 动手日", "🎨 创作日", "👨‍👩‍👧 家庭日", "🔁 复习日"]

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

cards = []
for e in data["episodes"]:
    d = START + datetime.timedelta(days=e["day"] - 1)
    wd, dti = WD[d.weekday()], d.weekday()

    beats = "".join(
        '<li class="beat"><span class="bt">{t}</span><span class="bd">{d}</span>'
        '<span class="be">{en}</span></li>'.format(t=esc(b["t"]), d=esc(b["d"]), en=esc(b["en"]))
        for b in e["beats"])

    roles = "".join(
        '<tr><td class="who">{who}</td><td class="mood">{mood}</td><td class="learn">{learn}</td></tr>'.format(
            who=esc(r["who"]), mood=esc(r["mood"]), learn=esc(r["learn"]))
        for r in e["roles"])

    words = "".join(
        '<div class="word L{lv}"><div class="w1"><span class="w-en">{en}</span><span class="w-ipa">{ipa}</span>'
        '<span class="w-lv">L{lv}</span></div><span class="w-zh">{zh}</span>'
        '<span class="w-ex">{ex}</span></div>'.format(
            en=esc(w["en"]), ipa=esc(w["ipa"]), zh=esc(w["zh"]), lv=w["level"], ex=esc(w["ex"]))
        for w in e["words"])

    lines = "".join(
        '<div class="line"><p class="le">{en}</p><p class="lz">{zh}</p>'
        '<p class="lw">💡 {why}</p></div>'.format(en=esc(l["en"]), zh=esc(l["zh"]), why=esc(l["why"]))
        for l in e["lines"])

    tips = "".join(
        '<div class="tip"><span class="th">{h}</span><p>{b}</p></div>'.format(h=esc(t["h"]), b=esc(t["b"]))
        for t in e["tips"])

    ask = "".join(
        '<div class="ask a-{i}"><span class="atag">{t}</span><span class="aq">{q}</span></div>'.format(
            i=i, t=esc(a["type"]), q=esc(a["q"]))
        for i, a in enumerate(e["ask"]))

    mats = "".join('<span class="mat">{}</span>'.format(esc(m)) for m in e["materials"])

    quiz = "".join(
        '<div class="qitem"><span class="qn">Q{}</span><span class="qq">{}</span>'
        '<span class="qopts">{}</span></div>'.format(
            i + 1, esc(q["q"]), "　".join("□ " + esc(o) for o in q["opt"]))
        for i, q in enumerate(e["quiz"]))

    cards.append("""
<section class="card dt{dti}">
  <header>
    <div class="date">第 {day} 天 · {date} 星期{wd}</div>
    <div class="dtype">{dty}</div>
  </header>

  <h1><span class="epno">{ep}</span>{zh} <span class="en">{en}</span></h1>
  <div class="chips">{concepts}</div>

  <div class="cols">
  <div class="col">

  <section class="blk plot">
    <h2>剧情</h2><p>{plot}</p>
  </section>

  <section class="blk core"><h2>核心</h2><p>{core}</p></section>

  <section class="blk beats">
    <h2>场景时间轴</h2>
    <ol class="timeline">{beats}</ol>
  </section>

  <section class="blk roles">
    <h2>角色与情绪</h2>
    <table class="rtable"><tr><th>角色</th><th>情绪变化</th><th>这集学到</th></tr>{roles}</table>
  </section>

  <section class="blk play">
    <h2>玩一玩</h2><p>{play}</p>
    <div class="mats"><b>需要准备：</b>{mats}</div>
  </section>

  </div>
  <div class="col">

  <section class="blk words">
    <h2>今日单词</h2>{words}
  </section>

  <section class="blk lines"><h2>跟读金句</h2>{lines}</section>

  <section class="blk askbox"><h2>问一问</h2>{ask}</section>

  <section class="blk tips"><h2>家长提示</h2>{tips}</section>

  <section class="blk quiz"><h2>小测验（让孩子连线或打钩）</h2>{quiz}</section>

  </div>
  </div>

  <footer>
    <span class="chk">☐ {checkin}</span>
    <span class="stamp">今日打卡 ⬜</span>
  </footer>
</section>""".format(
        dti=dti, day=e["day"], date=d.isoformat(), wd=wd, dty=DAY_TYPES[dti],
        ep=esc(e["ep"]), zh=esc(e["zh"]), en=esc(e["en"]),
        concepts="".join('<span class="chip">{}</span>'.format(esc(c)) for c in e["concepts"]),
        plot=esc(e["plot"]), core=esc(e["core"]), beats=beats, roles=roles,
        words=words, lines=lines, ask=ask, play=esc(e["play"]), mats=mats,
        tips=tips, quiz=quiz, checkin=esc(e["checkin"])))

CSS = """
@page{size:A4 portrait;margin:6mm}
*{box-sizing:border-box;margin:0}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#efe7da;padding:10px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.card{width:190mm;min-height:272mm;margin:0 auto 8mm;background:#fffdf8;border-radius:5mm;
  padding:8mm 9mm 7mm;box-shadow:0 2px 9px rgba(0,0,0,.16);page-break-after:always;
  display:flex;flex-direction:column;gap:2.6mm}
.card header{display:flex;justify-content:space-between;align-items:center}
.date{font-size:9pt;color:#8a7a63}
.dtype{font-size:10pt;font-weight:bold;color:#fff;background:#e8843c;padding:1mm 3mm;border-radius:4mm}
.dt1 .dtype{background:#4c9f70}.dt2 .dtype{background:#4a90d9}.dt3 .dtype{background:#c9564c}
.dt4 .dtype{background:#8e6cb8}.dt5 .dtype{background:#d98c3f}.dt6 .dtype{background:#4c9f70}
h1{font-size:14pt;color:#4a3728;line-height:1.25}
.epno{font-size:9.5pt;color:#b09a7c;margin-right:2mm}
h1 .en{font-size:10pt;color:#9a8570;font-weight:normal;margin-left:2mm}
.chips{display:flex;gap:1.4mm;flex-wrap:wrap;margin-top:-1mm}
.chip{font-size:7.5pt;background:#f3e8d7;color:#7a6248;padding:.6mm 2mm;border-radius:3mm}
.blk h2{font-size:9.5pt;color:#c9564c;margin-bottom:.8mm;border-left:2.2mm solid #e8843c;padding-left:1.6mm}
.blk p{font-size:10.5pt;line-height:1.5;color:#4a3728}
.plot p{font-size:11pt}
.core{background:#eff6f0;border-radius:2.2mm;padding:1.4mm 2.2mm}
.core h2{color:#4c9f70;border-color:#4c9f70}
.core p{font-size:9pt;font-weight:bold;color:#3d7a52}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:5mm;align-items:start}
.col{display:flex;flex-direction:column;gap:2.4mm;min-width:0}
.timeline{list-style:none}
.beat{display:grid;grid-template-columns:12mm 1fr;gap:.6mm 1.6mm;padding:.7mm 0;border-bottom:1px dashed #eee2cf}
.bt{font-size:8pt;font-weight:bold;color:#e8843c}
.bd{font-size:9.5pt;color:#4a3728;line-height:1.32}
.be{grid-column:2;font-size:8.8pt;color:#7c6a55;font-style:italic}
.rtable{width:100%;border-collapse:collapse;font-size:9pt}
.rtable th{background:#f3e8d7;color:#7a6248;font-size:7.5pt;text-align:left;padding:.7mm 1.4mm}
.rtable td{border-bottom:1px dashed #eee2cf;padding:.8mm 1.4mm;color:#4a3728;line-height:1.32}
.rtable .who{font-weight:bold;color:#b0682f;white-space:nowrap}
.rtable .mood{color:#7c6a55}
.word{display:flex;flex-wrap:wrap;align-items:baseline;gap:1.4mm;padding:.6mm 0;border-bottom:1px dashed #eee2cf}
.w1{display:flex;align-items:baseline;gap:1.4mm;min-width:50mm}
.w-en{font-weight:bold;color:#4a90d9;font-size:10pt}
.w-ipa{color:#9a8570;font-size:7.5pt}
.w-lv{font-size:6.5pt;color:#b09a7c;border:1px solid #e3d5bf;border-radius:1.4mm;padding:0 1mm}
.w-zh{font-size:9.5pt;color:#4a3728;min-width:28mm}
.w-ex{font-size:9pt;color:#4c9f70;font-style:italic;flex:1}
.lines .line{background:#f0f5f0;border-radius:2.2mm;padding:1.3mm 2mm;margin-bottom:.8mm}
.le{font-size:10pt!important;font-weight:bold;color:#2f6b45}
.lz{font-size:9.5pt!important;color:#556;margin-top:.3mm}
.lw{font-size:8.3pt!important;color:#a08050;margin-top:.4mm}
.askbox .ask{display:flex;gap:1.6mm;align-items:baseline;padding:.6mm 0}
.atag{flex:0 0 auto;font-size:7pt;color:#fff;background:#4a90d9;border-radius:1.8mm;padding:.3mm 1.6mm}
.a1 .atag{background:#4c9f70}.a2 .atag{background:#8e6cb8}
.aq{font-size:10.2pt;color:#4a3728;line-height:1.38}
.play{background:#fdf3e3;border-radius:2.2mm;padding:1.4mm 2.2mm}
.play h2{color:#b0682f;border-color:#e8a34c}
.mats{margin-top:1.2mm;font-size:8.8pt;color:#8a7a63}
.mats b{color:#b0682f;font-weight:bold}
.mat{display:inline-block;background:#fff;border:1px solid #ecd9bd;border-radius:2mm;padding:.2mm 1.6mm;margin:0 1mm .6mm 0}
.tip{display:flex;gap:1.6mm;align-items:baseline;padding:.5mm 0}
.th{flex:0 0 auto;font-size:7.5pt;font-weight:bold;color:#fff;background:#8e6cb8;border-radius:2mm;padding:.3mm 1.6mm}
.tip p{font-size:9.5pt;line-height:1.38}
.qitem{display:flex;align-items:baseline;gap:1.4mm;padding:.7mm 0;font-size:9.5pt;line-height:1.38}
.qn{font-size:7pt;font-weight:bold;color:#fff;background:#e8843c;border-radius:50%;padding:.2mm 1.2mm;flex:0 0 auto}
.qq{color:#4a3728;font-weight:bold;flex:0 0 auto}
.qopts{color:#7c6a55;font-size:9pt}
footer{margin-top:auto;display:flex;justify-content:space-between;align-items:center;
  padding-top:1.4mm;border-top:2px dashed #e8d9c0}
.chk{font-size:9pt;color:#7a6248}
.stamp{font-size:9.5pt;color:#c9564c;font-weight:bold}
@media print{body{background:#fff;padding:0}.card{box-shadow:none;margin:0 auto;border-radius:0;min-height:auto;width:auto;padding:0;gap:2.4mm}}
"""

html = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>小猪佩奇 · 每日亲子学习单（超深度样张）</title><style>%s</style></head>
<body>%s</body></html>""" % (CSS, "".join(cards))

with open("daily_deep.html", "w", encoding="utf-8") as f:
    f.write(html)
print("written daily_deep.html,", len(html), "bytes,", len(cards), "cards")
