---
name: portfolio-detail
description: Generate a single-file Chinese atelier-style portfolio website (horizontal-row list + hover-reveal thumb interaction, art lishu typography "Alimama DaoLiTi" via CDN, light/dark theme, hash-routed detail pages). Takes a natural-language description of the studio (name, director, discipline, works) and outputs ONE working .html file. Runs in BOTH Claude Code (writes to ~/Desktop) and GLM / online chat (outputs HTML inline). Trigger phrases include "做个中式工作室作品集", "做个隶书作品集", "lishu-portfolio-gen ...", "做个白屋风格的作品集", or when user drags this skill folder into chat asking for an atelier-style site.
visibility: public
mode: template
carrier: web-page
scenario: portfolio
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个中式工作室作品集"
  - "做个隶书作品集"
  - "做个白屋风格的作品集"
  - "横排作品集"
  - "刀隶体作品集"
related_patterns: vr-canvas, digital-eguide
legacy_gen: true
---

# portfolio-detail — 中式工作室 / 隶书作品集（带二级详情页）

## 一句话特征
横排文字行 + hover 浮现右侧大图 + 阿里妈妈刀隶体艺术大字 + 黑白纯色 + light/dark + hash 路由详情页 + 列表/画册双视图。

## 与其他作品集 skill 的差别

| skill | 核心模式 | 适合谁 |
|---|---|---|
| `portfolio-gen` | 无限拖拽画布 + tile 平铺 | 摄影师 / 平面设计师挂样品 |
| `portfolio-museum-gen` | 英雄轮播 + 大卡 + 瀑布流 + 详情页（影像策展感） | 视频/影像/装置艺术家 |
| `industrial-archive-gen` | 黑框翻页封面 + 侧栏档案 + 北欧工业 | 实物产品 / 器物 / 硬件 |
| **`lishu-portfolio-gen`** | **横排文字行 + hover 显示右侧缩略图 + 隶书大字 + 中式克制** | **装帧 / 字体 / 工艺 / 中式工作室** |

如果用户的项目是「书 / 字体 / 展览 / 静物 / 中草药 / 茶 / 陶 / 木 / 纸 / 香」这一类需要克制典雅气质的——用这一份。

## 何时触发

用户说：
- "做个中式 / 东方 / 古典风格的作品集"
- "做个隶书风格的网站 / 工作室主页"
- "做个白屋风格的作品集" / "做个像 Gurgel D'Alfonso 那样的横排列表网站"
- "lishu-portfolio-gen ..."

并提供：
- **工作室描述**（必需）：名字、主理人、城市、学科、几件作品的标题与故事
- **作品图片**（可选）：URL / 上传 / 路径。没有也能跑（用 picsum 占位）

如果用户**完全没给作品标题** → 必须问一次至少有哪几件作品要展示。
如果用户**只给了标题**没给详情 → 自己写：每件作品都生成 1 句 lead + 3 段 prose + 6-8 行 specs + 3-6 张 picsum 图 + 几条 credits。语气与作品类型匹配（书 → 装帧 / 字 → 字体 / 物 → 静物 / 展 → 展览视觉）。

## 两种运行模式

### 模式 A · Claude Code / 本地（有文件系统）
- 用 `Bash` 列文件夹、`sips` 探每张图宽高
- 输出位置：`~/Desktop/{slug}-portfolio.html`（**单文件**，所有图片走 URL）
- 如果用户给了本地图片：拷到 `~/Desktop/{slug}-portfolio-images/` 并改 src 为相对路径

### 模式 B · GLM / 在线对话（无文件系统）
- 用户拖入 zip 解压后能看到 4 份文件
- **只输出一份完整 HTML 字符串**，包在 ` ```html ` 代码块里
- 用户上传图片但没给 URL → 全用 `https://picsum.photos/id/{id}/{w}/{h}` 占位（用已知存在的 ID）
- 不要尝试访问本地文件、不要建议命令行操作

判断：如果你**无法 Read 看到本地图片** → 默认走 B。

## 文件分工

| 文件 | 角色 | 怎么用 |
|---|---|---|
| `reference.html` | **完整成品参考** — 白屋 BAIWU 6 件作品 | 看：list 项的措辞、prose 语气、specs 词汇、JSON 字段密度 |
| `template.html` | **空骨架** — 同样的 CSS/JS/路由系统，2 件示例 + 20 个 SWAP 标记 | 在它的基础上改，输出最终 HTML |
| `README.md` | 用户视角的使用说明 | 模型不用看 |
| `SKILL.md` | 给模型看的工作流（本文件） | **必读** |

**核心规则**：所有改动基于 `template.html`；从 `reference.html` 学**怎么写**（语气、字数、tag 用词），但不要复制具体内容。

## 工作步骤

### 1. 读两份 HTML
- 先读 `reference.html` 体会"完整后长什么样"（特别是 `works-data` JSON 的字段密度和 prose 语气）
- 再读 `template.html` 找 20 个 SWAP 位置

**不要改 JS / 不要改 CSS / 不要改详情页路由系统 / 不要改字体引入**。
SWAP 都在 HTML 文本和 JSON 数据里。

### 2. 解析用户输入抽信息

抽取：
- **ATELIER_NAME_ZH** — 工作室中文名（2-4 字最佳，例如「白屋」「素园」「墨记」「青庐」「拙轩」）
- **PINYIN** — 拼音（5-6 个英文字母，全大写：BAIWU / SUYUAN / MOJI）
- **CHAR** — Logo 用的单字（通常是工作室名首字：白 / 素 / 墨 / 青 / 拙）
- **CITY** — 城市
- **DIRECTOR_ZH / DIRECTOR_EN** — 主理人姓名 + 拼音
- **DISCIPLINE** — 3 个学科词（"装帧 · 字体 · 静物"）
- **TAGLINE** — 一句话定位（20-40 字，楷体气质）
- **YEAR_FOUNDED** — 成立年份（可用干支：乙未冬 / 甲辰春）

每件作品抽：
- **slug** — URL ID，小写英文连字符（`kong-shan-ji` / `wu-ming-shu`）
- **title_zh** — 中文标题（2-5 字最佳，越精炼越有调性）
- **title_en** — 英文副题（书名号风格：`An Anthology of Empty Mountains`）
- **year** — 年份或干支年（`甲辰 / 2024` / `2025` / `乙巳 / 2025`）
- **tag** — 顶部分类，方括号包，如 `[ 诗集 · 装帧设计 ]` / `[ 字体设计 · 中草药图谱 ]`
- **cover** — 详情页大图 URL
- **list 行 location** — `城市，年份 · 工艺/规格`（hover 时浮现）
- **meta** — 4 个键值对（详情页 4 列摘要）
- **lead** — 30-70 字开篇大字，可用 `<em>关键词</em>` 强调一处
- **prose** — 3-4 段散文，每段 80-150 字
- **specs** — 6-10 行规格表（开本/纸张/装订/字体/印量/印刷/工艺/定价等）
- **gallery** — 3-6 张图，layout 三选一：`g-wide` / `g-half` / `g-third`
- **credits** — 4-7 对职位/名字

如果用户只给一句话/没给故事 → **自己编**：根据作品标题和类型，写出符合作品调性的 lead 和 prose。语气参考 reference.html — 不要 marketing 语言，要有「博物馆 wall-text + 工作室札记」的感觉（克制、具体、缓慢、有手工痕迹）。

### 3. 列作品 + 探尺寸（仅模式 A）

```bash
ls -la "{works_path}"
sips -g pixelWidth -g pixelHeight "{works_path}/{file}" 2>/dev/null
```

得到每张图的 (filename, w, h, aspect)。优先选竖图作 list 缩略图（4:3 容器，竖图更上相）。

### 4. 替换 20 个 SWAP

| SWAP | 位置 | 内容 |
|---|---|---|
| 1 | `<title>` | `{ATELIER_NAME} {PINYIN} — {DIRECTOR}作品集 / Studio` |
| 2 | meta description | 一句网站简介 |
| 3 | curtain 单字 | 工作室名首字（如「白」） |
| 4 | logo SVG 内单字 | 同 SWAP-3 |
| 5 | logo SVG 内拼音 | `{PINYIN}` 大写 |
| 6 | 主导航 li | 通常 3 项：作品 / 关于 / 联系 |
| 7 | brand-block 中文名 | `{ATELIER_NAME}` 拆字加空格（如 `白&nbsp;&nbsp;屋`） |
| 8 | brand-block 英文 | `{PINYIN} Studio · {CITY}` |
| 9 | tagline | 楷体一句话定位，20-40 字，可用 `<br>` 换行 |
| 10 | **list 项 N 件** | 每件 `<a class="item" href="#work/{slug}">` 包含 num/project-name/en-name/location/photo-thumb |
| 11 | **gallery 项 N 件** | 同样的 N 件作品，更紧凑的网格 — slug 必须和 list 一致 |
| 12 | 关于标题 | `关&nbsp;于&nbsp;{name}<span class="en">About</span>` |
| 13 | 关于段落 | 1-3 段楷体（成立背景 / 主理人 / 设计观），每段 60-120 字 |
| 14 | 关于事实表 | 4-6 项 li (Founded/Location/Discipline/Director/Hours) |
| 15 | 联系标题 | `来&nbsp;信<span class="en">Get in Touch</span>` |
| 16 | 联系段落 | 1-2 段邀请来信 + 回信周期承诺 |
| 17 | 联系事实表 | 4-6 项 (E-mail/Phone/Address/Instagram/公众号) |
| 18 | rotating credit | `Site by {WHO}`（通常是工作室名） |
| 19 | footer 三块 | © / ICP / 社交链接 |
| 20 | **works-data JSON** | **N 件作品的完整详情数据（关键！）** |

### 5. 写 works-data JSON（最关键的一步）

每件作品都要在 JSON 数组里有一条，**slug 必须和 list/gallery 卡片 href 里的 `#work/SLUG` 完全一致**。

JSON 字段：
```json
{
  "slug": "kong-shan-ji",
  "title_zh": "空山集",
  "title_en": "An Anthology of Empty Mountains",
  "year": "甲辰 / 2024",
  "tag": "[ 诗集 · 装帧设计 ]",
  "cover": "https://picsum.photos/id/143/1800/1100",
  "meta": [
    {"label": "Type / 类型", "value": "诗集装帧"},
    {"label": "Year / 年份", "value": "2024"},
    {"label": "Edition / 印量", "value": "首印 320 本"},
    {"label": "Format / 开本", "value": "130 × 195 毫米"}
  ],
  "lead": "三十六首关于山的诗。我们想做一本——读者翻开后，先听见<em>风声</em>，再读见字的书。",
  "prose": [
    "段落一：诗稿来源 / 设计语境。80—150 字。",
    "段落二：制作中的关键决定 — 字体、纸张、装订选择。",
    "段落三：最后呈现 / 留给读者的感受。"
  ],
  "specs": [
    ["开本 / Format", "130 × 195 毫米"],
    ["页数 / Pages", "144 页"],
    ["纸张 / Paper", "本色棉纸 90gsm"],
    ["装订 / Binding", "线装四目"],
    ["字体 / Typeface", "老宋（标题）· 楷体（正文）"],
    ["印刷 / Printing", "单色凸印"],
    ["印量 / Edition", "首印 320 本"],
    ["定价 / Price", "¥ 388"]
  ],
  "gallery": [
    {"src": "...", "layout": "g-wide", "caption": "封面"},
    {"src": "...", "layout": "g-half"},
    {"src": "...", "layout": "g-half"},
    {"src": "...", "layout": "g-third"},
    {"src": "...", "layout": "g-third"},
    {"src": "...", "layout": "g-third"}
  ],
  "credits": [
    ["设计 / Design", "周墨白"],
    ["手工装订 / Binding", "陈漱石（杭州·订书坊）"]
  ]
}
```

**JSON 易错 ⚠️**：
- 中文 prose 里要用引号 → 必须用全角的 `「...」` 或 `"..."`（U+201C / U+201D），**不能**用 ASCII `"`（会破 JSON）
- 不要在 JSON 字符串里写真换行；要换段落就在 prose 数组里多写一项
- `<em>词</em>` 在 lead 里**直接写 HTML 标签**——渲染时按 innerHTML 出
- gallery `layout` 必须三选一：`g-wide`（占满）/ `g-half`（占一半）/ `g-third`（占 1/3）

### 6. 图片源选择
- **picsum 占位**：用 `id/X` 形式而非 `seed/X`（更稳定）。已知好用的 ID：0, 20, 40, 51, 64, 76, 88, 91, 96, 119, 121, 130, 143, 145, 158, 164, 165, 175, 177, 180, 187, 195, 200
- 同一作品的 cover / gallery 用相邻的几个 ID，能制造一致的色调
- 不要用 `?grayscale` 参数（用户希望图片是彩色的）

### 7. 中文工作室命名灵感（如果用户没给）
若用户让你"自己起一个" → 选 2 字 + 古朴：
- 物名类：白屋 / 素园 / 墨记 / 青庐 / 拙轩 / 听雨 / 一勺 / 半亩
- 字行类：素白 / 子衿 / 砚池 / 半山 / 寻常 / 浮云
- 避免 "工作室 / 设计 / Studio" 这种功能词，让名字本身就是诗

### 8. 视频支持
如果作品 cover 是 .mp4 / .webm / .mov，详情页会自动用 `<video autoplay muted loop>` 替代 `<img>`。模型只要在 cover URL 里给视频路径就行。

### 9. 报告

**模式 A**：一句话报告。
> 已生成 ~/Desktop/baiwu-portfolio.html — 6 件作品，hover 行查看缩略图，点击进入详情页。Light/Dark 在左下，列表/画册在顶部居中。

**模式 B**：直接给完整 HTML 代码块 + 一行说明。
> 把上面这段保存成 `index.html` 双击打开。鼠标移到任意作品名上看右侧浮现的缩略图，点击跳详情页。要换图把 picsum URL 换成你的图片地址。

## 强制保留（不能改）

- **字体引入**：`@font-face` 加载阿里妈妈刀隶体的 woff2 url（不要换字体源）
- **CSS 变量系统**：light/dark 双主题
- **全部 JS**：theme toggle、view mode toggle、hover-row 交互、rotating credit、详情页 hash 路由 `applyRoute()`、`renderDetail()`
- **`<script id="works-data">`** 节点必须保留
- **`<main id="detail-root">`** 必须保留（详情页挂载点）
- **`body[data-view="home/detail"]` 和 `body[data-mode="list/gallery"]`** 状态系统
- **#logo / #main-menu / .theme-toggle / #project-view / #svp-credit** 五个固定定位元素

## 易错速查

- **slug 不匹配**：list 项 `#work/kong-shan-ji` ↔ gallery 项 `#work/kong-shan-ji` ↔ JSON `"slug": "kong-shan-ji"` —— 三处必须完全一致
- **JSON 引号**：中文内容里的引号一定用全角「」或 `"..."`，不是 ASCII `"`
- **gallery 太多**：每件作品最多 6 张图，超了排版会乱
- **prose 过长**：每段 80-150 字，超过 200 字阅读体验下降
- **list / gallery 不同步**：必须包含同样的作品集（一一对应）
- **picsum seed**：用 `id/X` 不要用 `seed/X`，避免随机 ID 命中已删除的图
- **作品 < 3 件**：可以，最少 2 件就能跑
- **作品 > 8 件**：建议分两批，太多 list 行会让页面变长
- **首字下沉**：详情页的 `.detail__prose p:first-of-type::first-letter` 用刀隶体 — 第一段必须是中文开头（不要以 `<em>` 或英文开头）
- **删了 picsum 的彩色**：图片应保持彩色，不要在 CSS 加 `filter: grayscale()`
