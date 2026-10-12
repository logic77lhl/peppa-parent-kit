# 小猪佩奇 · 亲子共读内容工具包

> 把《小猪佩奇》剧集变成可打印的亲子阅读材料：**逐集内容 schema + 446 集剧情数据 + 质量校验器 + 打印渲染器**。

这个仓库不是「又一个模板生成器」。它解决的是一个具体问题：
**如何为 400+ 集内容保证「每一天真的不一样」，并且能被机器检查出来。**

---

## 为什么做这个

现成的做法通常是：写一个模板，按主题分类轮询填充。产出看起来很完整，
但翻开第 30 天和第 3 天会发现提问几乎一样——家长和孩子都会察觉。

这个工具包的做法是三件事：

1. **把「一集内容」拆成 13 个结构化字段**（剧情 / 时间轴 / 角色情绪 / 单词 / 金句 / 三层提问 / 玩法 / 提示 / 测验…），
   强制 LLM 产出「咬合本集」的内容，而不是通用句
2. **给每条内容标注来源**（TVMaze / TMDB / 字幕 / LLM），缺口可追溯、可回填
3. **写一个校验器，把「重复」变成可检测的失败**，而不是靠人眼翻 446 页

---

## 目录结构

```
peppa-parent-kit/
├── schema/
│   └── peppa_daily_content.schema.json   # JSON Schema (draft 2020-12)
├── data/
│   └── tvmaze_peppa_episodes.json        # 446 集英文剧情摘要（TVMaze 公开 API）
├── tools/
│   ├── content_check.py                  # 质量校验器：结构/数量/咬合/重复/难度
│   └── render_daily_cards.py             # 内容 JSON → A4 双栏打印版 PDF
├── samples/
│   └── content_gold.json                 # 黄金样例：3 集完整填写
└── docs/
    └── SCHEMA.md                         # 字段字典与填写指南
```

---

## 快速开始

```bash
git clone https://github.com/logic77lhl/peppa-parent-kit.git
cd peppa-parent-kit

# 校验内容文件（退出码 0 = 通过）
python tools/content_check.py samples/content_gold.json

# 渲染打印版（需要 edge + pymupdf）
python tools/render_daily_cards.py
```

---

## 核心：每日内容 Schema

一集内容的完整结构（13 个区块）：

| 区块 | 作用 | 关键约束 |
|---|---|---|
| `plot` | 中文剧情 + 来源标注 | 30-160 字，**只写发生了什么** |
| `core` | 核心道理 + 价值词 + 主情绪 | `lesson` ≤40 字 |
| `concepts` | 概念标签 | 1-4 个，2-4 字 |
| `beats` | 场景时间轴 | 3-6 拍，每拍带 stage 枚举 |
| `roles` | 角色与情绪路径 | 如 `无聊 → 兴奋 → 不甘 → 开心` |
| `words` | 今日单词 | 3-6 个，`example` 必须是本集原句 |
| `lines` | 跟读金句 | 1-3 句，带语法标签 |
| `ask` | 三层提问 | 2-4 条，须含「回忆」+ 发散类 |
| `play` | 玩一玩 | 须用家里现成东西，标时长 |
| `tips` | 家长提示 | 发音 / 文化 / 育儿 / 安全 |
| `quiz` | 小测验 | 2-3 选项，标答案下标 |
| `review` | 间隔复习 | 默认 `[1,3,7,21]` 天 |
| `quality` | 自检结果 | 由校验器回填 |

### 11 种日型（`day_type`）

```
新剧日   台词日   单词日   动手日   创作日
家庭日   复习日   主题周   里程碑日  反转日  无屏幕日
```

日型决定卡片的视觉重心——台词日放大金句，单词日放大词卡，动手日放大活动说明。
详见 [docs/SCHEMA.md](docs/SCHEMA.md)。

---

## 质量校验器

```bash
$ python tools/content_check.py samples/content_gold.json
=== content_gold.json ===
集数：3　错误：0　警告：0
  ✓ 全部通过
```

检查五类问题：

| 类别 | 检查内容 |
|---|---|
| **结构** | 必填缺失、类型错、枚举非法、`ep` 格式、`day` 重复 |
| **数量** | plot 字数区间、beats 3-6、words 3-6、ask 2-4、quiz 选项与答案越界 |
| **咬合** | 提问/玩法与本集内容的关键词重合度（含同义扩展，如 `水坑 ↔ 泥坑`） |
| **重复** | 30 天滑动窗口内提问≥2 条雷同、玩法雷同、金句重复 |
| **难度** | 标注与实际单词难度不符、复习日缺 review |

实测：合格样例 `0 错 0 警`；旧版模板化数据 `42 错 18 警`。

---

## 数据来源

| 数据 | 来源 | 覆盖度 |
|---|---|---|
| 剧集清单 | B站 12 季核实表（446 集，中英对照） | 100% |
| 剧情摘要 | [TVMaze](https://www.tvmaze.com/shows/4972/peppa-pig) 公开 API | S1–S5 完整；S6 后部分缺失 |
| 中文剧情/提问/玩法 | LLM 基于上述摘要生成 | — |

TVMaze 无需 API key。缺失部分（约 111 集）可由 TMDB 或字幕回填，
`plot.source` 字段已预留追溯能力。

### 关于季号

同一批剧集在不同市场被称为不同季号（TMDB 9 季 / 大陆 11 季 / B站 12 季）。
本仓库统一采用 **B站 12 季口径**，引用时请注明。

---

## 批量生成建议流程

1. 以 `data/tvmaze_peppa_episodes.json` 的 summary 作为 `plot.source_en`
2. LLM 逐集生成 `content`，**输入需包含前 30 天已用词与已用问题**（防重复的关键）
3. 合并为单个 JSON，跑 `tools/content_check.py`
4. 错误必须修，警告逐条判断
5. 先 `--limit 10` 验证质量，再放开全量

---

## 打印渲染

`tools/render_daily_cards.py` 把内容 JSON 渲染成 A4 双栏打印版。

几个踩过的坑（都已在代码中处理）：

- **Edge 打印默认 Letter 纸** → 必须显式 `@page { size: A4 portrait }`
- **判断溢出的完备判据**：打印整本后总页数 == 设计页数，任何一页溢出都会让总页数变多
- **单栏塞不下就改双栏**：A4 高度减半，比缩字号有效得多
- 图片色块需要 `-webkit-print-color-adjust: exact` 才能在 PDF 里保留

---

## 数据与内容的边界

这个工具包**不生成教学内容**，只做三件事：结构、排版、校验。

认知内容（提问、玩法、金句）的质量取决于喂给 LLM 的输入质量。
schema 的作用是把「质量」变成可检查的字段和规则——但填内容的人（或模型）仍然
需要对每一集负责。这是刻意的设计：工具不假装自己能替代理解。

---

## License

MIT

数据来源 TVMaze（CC BY）整理，仅供个人学习与家庭使用。
《小猪佩奇》版权属 Astley Baker Davies / eOne所有，本仓库不包含任何动画素材。