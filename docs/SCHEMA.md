# 每日亲子内容 Schema 字段字典 v1.0.0

> 配套文件：`peppa_daily_content.schema.json`（机器可校验）、`peppa_content_check.py`（质量校验）、`peppa_content_gold.json`（黄金样例）

## 设计原则

| 原则 | 说明 |
|---|---|
| **数据与渲染分离** | JSON 只管内容，不含任何排版信息；渲染层另行实现，可换版式不重生成内容 |
| **必填项最小化** | `required` 只保留「缺了就没法用」的字段，其余可选，保证批量生成时可渐进补全 |
| **来源可追溯** | 每个剧情都带 `source`，TVMaze / TMDB / 字幕 / LLM 四选一，便于缺口回填与人工复核 |
| **质量自评** | 每集带 `quality` 块，由校验器回填；批量生成后可快速筛出返工项 |
| **长度上限内嵌** | 所有面向家长的文本都设 `maxLength`，避免又变回「大段说明」 |

## 顶层结构

```
version          schema 版本（semver，破坏性改动升 major）
meta             整本元信息
  title, total_days, start_date, generator
  source          { episode_list, plot_source, confidence }
  calibration     { difficulty_curve, day_types, avoid_repeat_window }  ← 复现批量生成参数
episodes[]       剧集数组
```

## Episode 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|:--:|---|
| `ep` | `season-episode` | ✅ | 如 `1-01`、`9-40`。跨平台季号不同时以本表口径为准 |
| `day` | int ≥1 | ✅ | 第几天，须连续不重复 |
| `date` | date | | 由 `day` + `meta.start_date` 推导，可不存 |
| `title.zh` | string | ✅ | 中文剧名，取自核实表 |
| `title.en` | string | ✅ | 英文剧名 |
| `title.zh_alt` | string[] | | 同义译名，用于检索 |
| `day_type` | enum | ✅ | 见下表，决定卡片强调哪个区块 |
| `difficulty` | enum | ✅ | 简单 / 中等 / 挑战 |
| `airdate` | date? | | 首播日期，可用于「季节联动」排序 |
| `tags.season_context` | string | | 如 `二胎`、`看牙`、`圣诞节` |
| `tags.life_scenario` | string | | 对应育儿场景，如 `分离焦虑`、`输不起` |
| `content` | object | ✅ | 见下 |
| `quality` | object | | 自检结果 |

### day_type 取值

| 值 | 玩法侧重 | 卡片强调 |
|---|---|---|
| 新剧日 | 正常观看 + 剧情理解 | 剧情 |
| 台词日 | 金句跟读 + 角色扮演 | 金句 |
| 单词日 | 词卡 + 单词狩猎 | 单词 |
| 动手日 | 户外 / 家务活动 | 玩法 |
| 创作日 | 涂色 / 手工 / 改编 | 玩法 |
| 家庭日 | 全家桌游、比赛 | 玩法 |
| 复习日 | 重看 + 打卡盖章 + 复习排期 | review |
| 主题周 | 连看同主题 5 集 | 视当日而定 |
| 里程碑日 | 每 50 集庆典 | 特殊版式 |
| 反转日 | 孩子当老师、家长故意答错 | 问答 |
| 无屏幕日 | 只听音频猜剧情 | 听力 |

## content 字段

| 字段 | 必填 | 约束 | 说明 |
|---|:--:|---|---|
| `plot` | ✅ | | 见下 |
| `core` | ✅ | | 见下 |
| `concepts` | | 1-4 个 | 概念标签，2-4 字：`天气` `安全规则` `家庭互动` |
| `beats` | ✅ | 3-6 拍 | 场景时间轴 |
| `roles` | | ≤5 个 | 角色与情绪 |
| `words` | ✅ | 3-6 个 | 今日单词 |
| `lines` | ✅ | 1-3 句 | 跟读金句 |
| `ask` | ✅ | 2-4 条 | 三层提问 |
| `play` | ✅ | | 玩一玩 |
| `tips` | | ≤4 条 | 家长提示 |
| `quiz` | | ≤4 题 | 小测验 |
| `review` | | | 间隔复习排期 |

### plot

| 字段 | 必填 | 约束 |
|---|:--:|---|
| `summary` | ✅ | 30-160 字，2-3 句。**只写发生了什么，不写评价** |
| `source` | ✅ | `tvmaze` / `tmdb` / `bilibili_subtitle` / `llm` |
| `source_en` | | 英文原始摘要 |
| `confidence` | | high / medium / low，低于 medium 建议人工复核 |

### core

| 字段 | 必填 | 约束 |
|---|:--:|---|
| `lesson` | ✅ | ≤40 字，一句话核心道理。**不要写成「这集告诉我们…」** |
| `keywords` | ✅ | 2-4 个价值词：分享 / 坚持 / 道歉 / 耐心 |
| `emotion` | | 快乐 难过 生气 害怕 骄傲 感动 平静 紧张 失落 |

### beat（场景时间轴）

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `stage` | ✅ | 开场 / 铺垫 / 转折 / 小冲突 / 高潮 / 解决 / 结尾 |
| `desc` | ✅ | ≤40 字，这一拍发生了什么 |
| `en` | | 对应英文原句，无则留空 |
| `graphic` | | 插画关键词，指向 `kid_motifs` 中的图元 |

### role

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `who` | ✅ | 佩奇 / 乔治 / 猪妈妈 / 猪爸爸 / 苏西 / 其他角色 |
| `emotion_path` | ✅ | 情绪变化用箭头：`无聊 → 兴奋 → 不甘 → 开心` |
| `learned` | ✅ | ≤30 字，这集里学到了什么 |
| `say` | | 代表性台词 |

### word

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `en` | ✅ | 英文单词 |
| `ipa` | ✅ | 音标，带斜杠 |
| `zh` | ✅ | 中文释义 |
| `level` | ✅ | 1-3 整数，1 最易 |
| `pos` | | n / v / adj / adv / num / phrase |
| `example` | | **必须是本集原句** |
| `graphic` | | 对应图元 key |
| `is_new` | | 是否首次出现，复习排期用 |

### line（跟读金句）

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `en` | ✅ | 英文台词 |
| `zh` | ✅ | 中文对照 |
| `why` | | ≤50 字，**为什么值得学**（句型/语法点/文化点） |
| `grammar` | | 语法标签：`must + 动词原形` / `不规则过去式` |
| `repeat` | | 是否适合反复跟读 |

### ask（三层提问）

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `type` | ✅ | 回忆 / 联系生活 / 想象 / 情绪 / 判断 / 预测 |
| `q` | ✅ | ≤40 字，**必须咬合本集剧情** |
| `expect` | | 参考回答要点，给不确定的家长兜底 |
| `zh` | | 是否需中文作答 |

**结构要求**（校验器会警告）：至少 1 条「回忆」，且至少 1 条发散类（想象/判断/预测）。

### play

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `activity` | ✅ | ≤80 字，**必须用家里现成东西** |
| `duration_min` | | 1-20 整数 |
| `materials` | | 需要准备的材料 |
| `indoor` | | 是否适合室内/雨天 |
| `lang_en` | | 活动中要说的英文句型 |

### tip / quiz / review

| 字段 | 说明 |
|---|---|
| `tip.kind` | 发音 / 文化 / 育儿 / 安全；`tip.text` ≤60 字 |
| `quiz.q` | ≤30 字；`options` 2-3 项；`answer` 为正确项下标；`kind` 词汇/剧情/常识/判断 |
| `review.review_days` | 复习相对天数，默认 `[1,3,7,21]` |
| `review.recall_prompt` | 复习时的提示问题 |
| `review.links_to` | 关联往期集号，形成复习网络 |

## 校验器检查的五类问题

```
python peppa_content_check.py content.json
```

| 类别 | 检查内容 |
|---|---|
| **结构** | 必填缺失、类型错、枚举非法、`ep` 格式、`day` 重复 |
| **数量** | plot 字数区间、beats 3-6、words 3-6、ask 2-4、lines 1-3、quiz 选项数与答案下标 |
| **咬合** | 提问/玩法与本集内容的关键词重合度（含同义扩展，如「水坑↔泥坑」） |
| **重复** | 30 天滑动窗口内，提问≥2 条雷同、玩法雷同、金句重复 |
| **难度** | 标注「简单」但单词平均难度过高、「挑战」却过于简单、复习日缺 review |

退出码：`0` 全部通过；`1` 存在错误。

## 批量生成时的建议流程

1. 用 `tvmaze_peppa_episodes.json` 的 summary 作为 `plot.source_en`
2. LLM 逐集生成 `content`，输入 = 标题 + summary + 当日 `day_type`/`difficulty` + **前 30 天已用词与问题**
3. 输出合并为单个 JSON
4. 跑 `peppa_content_check.py`，错误必须修，警告逐条判断
5. 用 `--limit` 先跑 10 集验证质量，再放开全量