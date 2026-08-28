---
name: industrial-archive
description: Generate a single-file industrial-archive product landing page (Nordic museum aesthetic, hash-routed detail pages). Takes a natural-language description of one or more "exhibit-style" products (objects, tools, hardware, watches, kitchenware, lighting, audio, instruments, anything with a designed/forged/restrained quality); outputs ONE working .html file. Visitors see a black-framed cover that flips between exhibits, sidebar index, side meta column (material/origin/year/dimension), and click any exhibit → full detail page (giant italic title, spec table, hero image, lead + 3 prose paragraphs, gallery, prev/next). Runs in BOTH Claude Code (writes to ~/Desktop) and GLM / online chat (outputs HTML inline). Trigger: "做个工业风产品落地页", "做克制之物风格的展品页", "industrial-archive-gen ...", or when user drags this skill folder into chat asking for a product page in the Nordic-industrial archive style.
visibility: public
mode: template
carrier: web-page
scenario: brand-landing
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个工业风产品落地页"
  - "做克制之物风格的展品页"
  - "北欧博物馆藏品风"
  - "industrial archive"
  - "策展感产品页"
related_patterns: portfolio-detail
legacy_gen: true
---

# industrial-archive — 工业风展品 / 产品落地页生成器

把"一段自然语言描述"变成一份单文件 HTML，效果是**北欧工业典藏 / 博物馆策展感**的产品落地页：

- 黑色画框中的产品大图，左右点击翻转切换
- 左侧带索引指示条的展品目录
- 右侧 4 个 meta 块（材料 / 产地 / 年代 / 尺寸）
- 顶栏跑马灯
- 点击画框或底部 CTA → 进入展品详情页（巨大斜体标题、规格表、主图、开篇大字 + 3 段散文、6 图画廊、上一件/下一件）
- 进入页有引言 splash

## 何时触发

用户说"做个工业风的产品落地页 / 克制之物风格的展品 / industrial-archive-gen ..."，并提供：
- **产品描述**（必需）：一段散文，描述 1—N 件展品的名字、年代、产地、材料、来历
- **图片 URL**（可选）：每件展品至少 1 张主图、最好 3—6 张细节图。没有也能跑（用 picsum 占位灰图）
- **风格**（可选）：默认是冷调钢蓝灰，可换成 styles.md 里的预设

如果用户**完全没给展品名/故事** → 必须问一次至少有哪几件展品要展示，以及大致是什么品类（容器 / 灯具 / 椅具 / 仪器 / 工具 / ...）。

如果用户**只给了名字**没给故事 → 自己编：每件展品都生成 1 句 lead + 3 段 prose + 4-6 行 spec。语气参考 `reference.html`：**博物馆 wall-text** 感 — 克制、具体、缓慢，不要 marketing 语言。

## 两种运行模式

### 模式 A · Claude Code / 本地（有文件系统）
- 输出：`~/Desktop/{slug}-archive.html`（**单文件**，所有图走 URL）
- 如果用户给了本地图，建议告知用户改用 URL 或自己拷到同目录后写相对路径

### 模式 B · GLM / 在线对话（无文件系统）
- **直接给一份完整 HTML 字符串**，包在 ` ```html ` 代码块里
- 用户没给图 URL → 全用 `https://picsum.photos/seed/{slug}-{nn}/{w}/{h}?grayscale` 占位
- 不要尝试访问本地文件

判断：如果你**无法 Read 看到本地图片** → 默认走 B。

## 文件分工

| 文件 | 角色 | 怎么用 |
|---|---|---|
| `reference.html` | **完整成品参考** — "克制之物" 4 件北欧工业藏品 | 看：lead 怎么写、prose 语气、spec 用词、tagline 格式、maker 命名 |
| `template.html` | **空骨架** — 同样的 CSS/JS/路由，2 件示例 + 17 个 SWAP 标记 | 在它的基础上改，输出最终 HTML |
| `styles.md` | 风格预设库 | 用户指定风格时查这份 |
| `README.md` | 用户视角的使用说明 | 模型不用看 |
| `SKILL.md` | 给模型看的工作流（本文件） | **必读** |

**核心规则**：所有改动基于 `template.html`；从 `reference.html` 学**怎么写**（语气、字数、词汇），但不要复制具体内容。

## 关键差别 — reference 用 SVG，template 用 `<img>`

- `reference.html` 的 4 件展品是**手绘 SVG**（铸铁壶 / 轴承灯 / 桦木椅 / 测距仪），那是定制内容
- `template.html` 已经把 SVG 系统替换成 `<img src="cover URL">`，用户给 URL 就用 URL，没给就用 picsum
- 你不需要写 SVG。如果用户特别要求"画出来"，再考虑写一个 SVG 函数塞进 `coverHTML()`

## 工作步骤

### 1. 读两份 HTML
- 先读 `reference.html` 体会"完整后长什么样"，特别是 `exhibits-data` JSON 的字段密度和 prose 语气（克制、具体、有时代背景）
- 再读 `template.html` 找 17 个 SWAP 标记（搜 `SWAP-`）

**不要改 JS / 不要改 CSS / 不要改详情页路由系统**。
SWAP 都在 HTML 文本和 JSON 数据里。

### 2. 解析用户输入抽信息

#### 全站层级（17 个 SWAP 中的 1-15、17）
- **COLLECTION_TITLE / COLLECTION_SUB** — 系列大标题 + 副标。如"克制之物 / 北欧工业典藏 1948—1988"。SWAP-1
- **INTRO_VOLUME_TAG** — 进入页顶部的 tag，如"北欧工业典藏 · Vol.01"。SWAP-2
- **INTRO_TITLE_HTML** — splash 页大标题，2-4 字 + 中间一个 `<span class="accent">·</span>` 分隔符。如 `克制<span class="accent">·</span>之物`。SWAP-3
- **INTRO_TITLE_EN** — splash 页英文副标，全大写 + em-dash，如 `Restrained Objects — A Nordic Industrial Archive 1948 — 1988`。SWAP-4
- **INTRO_QUOTE** — 一句策展引言，60—100 字，散文感。SWAP-5
- **INTRO_ATTRIBUTION** — 引言出处，如`— 策展前言 / Curatorial Note`。SWAP-6
- **HEAD_GLYPH** — 左上 logo 字符。1-2 个 serif 字符，建议带特殊感的字母如 `Æ` `Ø` `沉` `匠` `ʘ`。SWAP-7
- **HEAD_GLYPH_SUB** — logo 下一行说明，如`克制之物 / 编号 N°01—04`。SWAP-8
- **HEAD_CENTER_CN / HEAD_CENTER_EN** — 顶部中央两行小字。SWAP-9, 10
- **HEAD_RIGHT_TOP / HEAD_RIGHT_BOTTOM** — 顶右两行：日期/城市 + 坐标/编号。SWAP-11, 12
- **CURATOR_NAME / CURATOR_EMAIL** — 策展方名称 + 邮箱。SWAP-13, 14
- **CRUMB_ROOT / CRUMB_VOLUME** — 详情页面包屑两个固定项。SWAP-15
- **TICKER_TAIL** — 跑马灯尾巴的总标语。SWAP-17

#### 每件展品的字段（SWAP-16，最关键）
```json
{
  "slug": "iron-kettle",
  "num": "N°01",
  "title": "铸铁壶",
  "en": "IRON KETTLE",
  "year": "1958",
  "place": "丹麦 · 哥本哈根",
  "maker": "Carl Hansen Værksted / 卡尔·汉森工坊",
  "material": "灰口铸铁 · 山毛榉木柄<br/>黑釉烧结涂层",
  "origin": "丹麦 · 哥本哈根<br/>Carl Hansen Værksted",
  "dim": "高 18 cm · 容 1.2 L<br/>底径 14 cm",
  "tagline": "FORGED ESSENTIAL / 锻造的必需品",
  "lead": "一只为<em>沉默与水的低温</em>而设计的容器——壶身的厚度，是为了让热停留得久一点，而不是更快地变热。",
  "spec": [
    ["编号", "1958 · K-04"],
    ["材料", "灰口铸铁 + 山毛榉"],
    ["工艺", "砂模铸造 / 黑釉烧结"],
    ["重量", "1.86 kg"],
    ["产量", "限量 240 件 · 现存 31"]
  ],
  "prose": [
    "段一 80—160 字。来源/语境/年份/工坊背景。",
    "段二 80—160 字。工艺/手工细节/关键决定。",
    "段三 80—160 字。今天的状态/影响/仍在用的事实。"
  ],
  "cover": "https://example.com/kettle-cover.jpg 或 picsum URL",
  "gallery": [
    {"src": "...", "layout": "f-3", "caption": "壶身正立面"},
    {"src": "...", "layout": "f-2", "caption": "山毛榉木柄"},
    {"src": "...", "layout": "f-2", "caption": "壶嘴细部"},
    {"src": "...", "layout": "f-2", "caption": "底部砂模印"},
    {"src": "...", "layout": "f-4", "caption": "工坊蓝图"},
    {"src": "...", "layout": "f-6", "caption": "陈列剖面"}
  ]
}
```

### 3. 替换 SWAP

把 `template.html` 里 17 个 `{{...}}` 占位符全部换成你抽出来的内容。
**注意**：`{{INTRO_TITLE_HTML}}` 是 HTML 不是纯文本，里面要带 `<span class="accent">·</span>`。

### 4. 写 exhibits-data JSON（最关键的一步）

把 `<script id="exhibits-data" type="application/json">` 里那 2 个示例对象**整个替换**成 N 个真展品对象。

#### 件数建议
- 最少 1 件（单品落地页也行 — JS 已处理 N=1 时不自动轮播）
- 最佳 3—6 件
- 超过 8 件展品索引会拥挤，建议拆分

#### 标题字数建议
- `title` 中文 2-4 字最好看（"铸铁壶"、"轴承灯"、"测距仪"）。如果产品名长，用副标，如 `"title": "测距仪"`、`tagline: "MARITIME RANGEFINDER / 海事测距仪"`
- `en` 全大写英文，2 词为佳

#### tagline 格式
固定：`英文短语 + 空格/空格 + 中文短语`，例：
- `FORGED ESSENTIAL / 锻造的必需品`
- `PIVOT & LIGHT / 旋转与光`
- `FOUR LEGS, NO MORE / 四只脚，仅此而已`
- `MEASURED HORIZON / 被丈量的地平线`

#### lead 写法
30—80 字。**必须在某一两个关键词上加 `<em>...</em>`**——CSS 会给这些字下面加一根钢蓝色细线。
反例：`这是一只很好的水壶。` ← 没有 em，没有具体细节
正例：`一只为<em>沉默与水的低温</em>而设计的容器——壶身的厚度，是为了让热停留得久一点。`

#### prose 写法
3 段，每段 80—160 字。语气：**博物馆 wall-text** — 克制、具体、有时代背景，不要 marketing 语言。
- 段一：来源 / 语境（产地、年份、工坊、那个时代）
- 段二：工艺 / 决定（关键设计、工艺细节、为什么要这么做）
- 段三：呈现 / 影响（今天的现存数量、是否仍在用、对后来的影响）

#### spec 写法
4-6 行，每行一个键值对。
- 第一行通常是 `["编号", "{年份} · {型号}"]`
- 最后一行通常是产量/现存：`["产量", "限量 240 件 · 现存 31"]`（JS 会把最后一行的值显示在详情页的"现存 / EXTANT"块）

#### gallery layout 必须四选一
- `f-3` — 横图，16:10，占 1/2 宽（占 6 列中的 3 列）
- `f-2` — 竖图，4:5，占 1/3 宽
- `f-4` — 横图，16:9，占 2/3 宽
- `f-6` — 全宽，21:8

**节奏建议**：1 张 f-3 + 3 张 f-2 + 1 张 f-4 + 1 张 f-6 = 6 张，刚好两行半。

#### 图片 URL
模式 A 用户给 URL → 用 URL；
模式 B 没给 → 用 picsum：`https://picsum.photos/seed/{slug}-{编号}/{w}/{h}?grayscale`
- cover 推荐 `1600/1000`
- f-3 推荐 `900/600`
- f-2 推荐 `600/750`
- f-4 推荐 `1200/675`
- f-6 推荐 `1600/610`
- 加 `?grayscale` 让占位图也保持工业灰调

### 5. 风格变体（可选）
如果用户指定风格，照 `styles.md` 改 `:root` 那 8 个 CSS 变量。默认是冷调钢蓝灰，最贴合"克制之物"原版。

### 6. 报告

**模式 A**：一句话报告。
> 已生成 `~/Desktop/{slug}-archive.html` — N 件展品，默认冷调钢蓝。双击打开，点击画框或底部 CTA 进入详情页。要换图把 cover/gallery 里的 picsum URL 换成你的图片地址。

**模式 B**：直接给完整 HTML 代码块 + 一行说明。
> 把上面这段保存成 `index.html` 双击打开。点画框看详情，键盘 ← → 切换展品。要换图把所有 picsum URL 换成你的图片地址。

## 强制保留（不能改）

- 全部 JS：translate / flip 翻转、`coverHTML()` 函数、`renderSidebar()`、`applyMeta()`、`renderDetail()`、键盘 / 自动轮播 / cursor
- 全部 CSS（除非走风格变体改 `:root`）
- `<script id="exhibits-data" type="application/json">` 节点必须保留
- `<div id="proj-list" class="proj-list">` 节点必须保留（但**不要**手写 li，让 `renderSidebar()` 生成）
- `<div id="cover-stage">` 内的 flipper 双面结构
- `<main class="stage">` 9 宫格

## JSON 易错速查

- **中文引号**：prose / lead 里如果要打"引号"，必须用全角 `"..."` (U+201C / U+201D)，**不能**用 ASCII `"`（会破 JSON）
- **真换行**：JSON 字符串里不要写真换行（直接按回车），也不要写 `\n`。要分段就用多个 prose 数组项；要换行就用 `<br/>`
- **`<em>` 标签**：在 lead 里**直接写 HTML 标签** `<em>...</em>`——会按 innerHTML 渲染，CSS 会给它加钢蓝下划线
- **slug 唯一**：每件展品的 slug 必须唯一，且小写英文连字符（`iron-kettle` 不是 `IronKettle` 也不是 `iron_kettle`）
- **gallery layout 拼写**：必须是 `f-3` `f-2` `f-4` `f-6` 之一，写错就不显示
- **picsum seed 唯一**：每张图给一个唯一 seed，否则不同图位会变成同一张
- **num 格式**：`N°01` 这个 N 加 ° 是必须的（°是 U+00B0），别打成 `No.01` 或 `N01`
- **maker 必须有"/"**：`"英文工坊名 / 中文工坊名"`，JS 会按 `/` 切左半边显示在右下角

## 字数 / 件数边界

- title ≤ 4 字，超过用 tagline 容纳更长副题
- lead ≤ 80 字（一行半）
- prose 每段 80—160 字（150 是甜区）
- spec 4-6 行
- gallery 3-6 图（少于 3 太空，多于 6 排版乱）
- 总展品数 1—8 件（最佳 3—6）
- ticker 不用手填件数 — JS 会自动遍历 DATA 拼

## 风格触发词速查

用户说→你照哪个风格：
- 没说 / "克制" / "北欧" / "工业" → 默认冷调钢蓝（已是 template 默认）
- "暖" / "复古" / "棕调" / "皮革" → styles.md `warm-leather`
- "暗" / "深色" / "夜色" → styles.md `night-iron`
- "纸张" / "印刷" / "report" → styles.md `paper-press`
- "纯色" / "海军蓝" → styles.md `navy-blueprint`
