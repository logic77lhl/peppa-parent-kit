[中文](README.md) | **English**

# Peppa Parent Kit

> Turn *Peppa Pig* episodes into printable parent–child reading material: **a per-episode content schema + plot data for 446 episodes + a quality checker + a print renderer**.

This is not "yet another template generator". It solves one specific problem:
**how do you make 400+ days genuinely different from each other, and prove it with a machine?**

---

## Why

The usual approach is: write a template, rotate it by topic. The output looks complete, but open day 30 and day 3 side by side and the questions are nearly identical. Parents and children notice.

This kit does three things instead:

1. **Split one episode into 13 structured fields** (plot / timeline / character emotions / vocabulary / key lines / three-tier questions / activity / tips / quiz …), forcing the model to produce content that interlocks with *this* episode rather than generic filler.
2. **Tag the source of every piece** (TVMaze / TMDB / subtitles / LLM), so gaps are traceable and backfillable.
3. **Ship a checker that turns "repetition" into a detectable failure**, instead of asking a human to read 446 pages.

---

## Layout

```
peppa-parent-kit/
├── schema/
│   └── peppa_daily_content.schema.json   # JSON Schema (draft 2020-12)
├── data/
│   └── tvmaze_peppa_episodes.json        # 446 English plot summaries (TVMaze public API)
├── tools/
│   ├── content_check.py                  # quality checker: structure / counts / interlock / repetition / difficulty
│   └── render_daily_cards.py             # content JSON → A4 two-column printable PDF
├── samples/
│   └── content_gold.json                 # gold sample: 3 episodes fully filled
└── docs/
    └── SCHEMA.md                         # field dictionary and authoring guide
```

---

## Quick start

```bash
git clone https://github.com/logic77lhl/peppa-parent-kit.git
cd peppa-parent-kit

# validate a content file (exit code 0 = pass)
python tools/content_check.py samples/content_gold.json

# render the printable version (needs Edge + pymupdf)
python tools/render_daily_cards.py
```

---

## The daily content schema

13 blocks per episode:

| Block | Purpose | Key constraint |
|---|---|---|
| `plot` | Chinese plot + source tag | 30–160 characters, **only what happened** |
| `core` | core lesson + value word + main emotion | `lesson` ≤ 40 characters |
| `concepts` | concept tags | 1–4, each 2–4 characters |
| `beats` | scene timeline | 3–6 beats, each with a stage enum |
| `roles` | characters and their emotional path | e.g. `bored → excited → frustrated → happy` |
| `words` | today's vocabulary | 3–6, each `example` must be a line from this episode |
| `lines` | read-aloud key lines | 1–3, with grammar tags |
| `ask` | three-tier questions | 2–4, must include a recall question and an open one |
| `play` | activity | uses things already at home, with a duration |
| `tips` | parent notes | pronunciation / culture / parenting / safety |
| `quiz` | quick quiz | 2–3 options, records the answer index |
| `review` | spaced review | default `[1,3,7,21]` days |
| `quality` | self-check results | filled in by the checker |

### 11 day types (`day_type`)

```
new episode · dialogue · vocabulary · hands-on · making · family · review · theme week · milestone · twist · screen-free
```

The day type decides the visual emphasis of the card — dialogue days blow up the key line, vocabulary days blow up the word card, hands-on days blow up the activity. Details in [docs/SCHEMA.md](docs/SCHEMA.md).

---

## The quality checker

```bash
$ python tools/content_check.py samples/content_gold.json
=== content_gold.json ===
episodes: 3   errors: 0   warnings: 0
  ✓ all clear
```

Five categories:

| Category | Checks |
|---|---|
| **Structure** | missing required fields, wrong types, invalid enums, `ep` format, duplicate `day` |
| **Counts** | plot length range, 3–6 beats, 3–6 words, 2–4 questions, quiz option/answer bounds |
| **Interlock** | keyword overlap between questions/activities and this episode's content (with synonyms, e.g. puddle ↔ mud puddle) |
| **Repetition** | within a 30-day sliding window: ≥2 near-duplicate questions, duplicate activities, repeated key lines |
| **Difficulty** | vocabulary level mismatch, missing review on review days |

Measured: the gold sample gets **0 errors, 0 warnings**; older template-generated data got **42 errors, 18 warnings**.

---

## Data sources

| Data | Source | Coverage |
|---|---|---|
| Episode list | Bilibili 12-season verified table (446 episodes, Chinese + English) | 100% |
| Plot summaries | [TVMaze](https://www.tvmaze.com/shows/4972/peppa-pig) public API | complete for S1–S5; partial after S6 |
| Chinese plot / questions / activities | LLM, grounded on those summaries | — |

TVMaze needs no API key. The missing part (~111 episodes) can be backfilled from TMDB or subtitles; `plot.source` already carries the provenance.

### About season numbering

The same episodes ship as different season numbers in different markets (TMDB 9, mainland China 11, Bilibili 12). This repo uses the **Bilibili 12-season numbering**; cite it when referencing.

---

## Suggested batch workflow

1. Use `data/tvmaze_peppa_episodes.json` summaries as `plot.source_en`.
2. Generate `content` episode by episode — **the prompt must include the words and questions used in the previous 30 days**. This is what prevents repetition.
3. Merge into one JSON and run `tools/content_check.py`.
4. Fix every error; judge warnings one by one.
5. Validate with `--limit 10`, then run the full batch.

---

## Print rendering

`tools/render_daily_cards.py` turns content JSON into an A4 two-column printable PDF.

Traps already handled in code:

- **Edge prints Letter by default** → `@page { size: A4 portrait }` must be explicit.
- **The complete overflow test**: total pages after printing must equal designed pages; any single overflowing page increases the total.
- **When one column doesn't fit, go two columns** — halving the A4 height works far better than shrinking type.
- Image blocks need `-webkit-print-color-adjust: exact` to survive the PDF.

---

## Where the tool stops

This kit **does not generate the teaching content**. It only does structure, layout, and checking.

The quality of the cognitive content (questions, activities, key lines) depends on what you feed the model. The schema turns "quality" into checkable fields and rules — but whoever fills it in (human or model) is still responsible for each episode. That's deliberate: the tool doesn't pretend to replace understanding.

---

## License

MIT.

Episode data is organised from TVMaze (CC BY) and is for personal study and family use. *Peppa Pig* is © Astley Baker Davies / eOne; this repo contains no animation assets.
