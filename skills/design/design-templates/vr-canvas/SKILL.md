---
name: vr-canvas
description: Generate a single-file VR-style portfolio website — works are tiled on the inside of a 3D cylinder/sphere (concave wraparound, like an immersive headset), with mouse-controlled head tilt, long-press to drag and browse the infinite canvas, click to open work detail. Includes overlays for About / CV / Contact / Filter. Takes a natural-language description of the studio and works (images + brief copy); outputs ONE working .html file. Runs in BOTH Claude Code (writes to ~/Desktop) and GLM / online chat (outputs HTML inline). Trigger phrases: "做个 VR 作品集", "做个无限画布作品集", "做个穹顶包裹的作品集", "vr-canvas-gen ...", or when user drags this skill folder into chat asking for a wraparound/immersive portfolio site.
visibility: public
mode: template
carrier: web-page
scenario: portfolio
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个 VR 作品集"
  - "做个无限画布作品集"
  - "做个穹顶包裹的作品集"
  - "弧幕作品集"
  - "包裹感作品集"
related_patterns: portfolio-detail, digital-eguide
legacy_gen: true
---

# vr-canvas — VR 弧幕作品集生成器

## 何时触发
用户说「做个 VR 作品集」/「做个穹顶 / 弧幕 / 包裹感的作品集」/「做个无限画布作品集」/「vr-canvas-gen ...」，并提供了：
- **作品文件**（图片，文件夹路径或多个文件路径）— GLM 模式可以是描述
- **自然语言描述**（工作室介绍 + 每件作品的故事 — 散文也行，不必结构化）

## 输入解析
从用户消息抽取：
- **works_path**（A 模式必填）：作品文件夹路径或一组文件路径
- **bio_text**（必填）：工作室自我介绍 + 各项目背景。可能含：工作室名、城市、领域、成立年份、团队、客户类型、各作品的故事
- **风格变体**（可选）：默认深色「材料/工作室」氛围；用户说「亮色 / 杂志感 / 赛博 / 极简」时调 `:root` 配色

如果用户只说「做个 VR 作品集」但没给作品 → **必须问一次**作品和工作室名字。
给了作品但没写描述 → **不追问**，从文件名/视觉内容推断标题和分类。

## 运行环境（两种模式）

### A. Claude Code / 本地（有文件系统）
- 用 `Bash` 列文件、`sips` 探尺寸、`cp` 拷贝图片
- 输出到 `~/Desktop/{slug}-vr-canvas/index.html` + `images/`
- 图片用相对路径 `images/work-NN.jpg`
- 模板自带 `images/p-01-color-macro.jpg ... p-18-magazine.jpg` 共 18 张设计向真实摄影（≈2.2MB），用户没传图片时直接 open template.html 就能看到完整 VR 球面效果

### B. GLM / 在线对话（无文件系统）
- 你**只输出一份完整的 HTML 字符串**（包在 ```html 代码块里）
- 用户上传图片但没给 URL → 用 `https://picsum.photos/seed/{描述-序号}/1080/1080` 做占位
- 用户给了 URL → 直接 `<img src="https://...">`
- 不要尝试访问本地文件、不要建议命令行操作（除了「把这段保存成 index.html」）

判断：**不能用 Read 看到本地图片** → 默认走 B。

## 文件分工

| 文件 | 角色 | 怎么用 |
|---|---|---|
| `reference.html` | **完整成品**（虚白工作室 20 件作品 + 完整 about/cv/contact/filter 文案）| 看：tile 文案语气、tag 词汇、desc 长度、about/cv 信息密度、整体氛围 |
| `template.html` | **空骨架**（同样的 CSS/JS，2 件示例 + 全部 SWAP 标注）| 在它的基础上改，输出最终 HTML |

**核心规则**：所有改动基于 `template.html`；从 `reference.html` 学**怎么写得像**，但不要复制它的具体内容（虚白、京都驻地、青木茶寮 …… 这些都是别人的）。

## 工作步骤

### 1. 读两份 HTML
- 先读 `template.html`，定位 SWAP 标记（共 12 处）
- 再扫一眼 `reference.html`，体会作品文案、about/cv 的密度与节奏

**不要改 JS、不要改 .work / .frame / .sphere / .viewport / .overlay 的 CSS、不要改任何 #sphere / #viewport / .splash 的逻辑**。

### 2.（仅 A 模式）列作品 + 探尺寸
```bash
ls -la "{works_path}"
sips -g pixelWidth -g pixelHeight "{works_path}/{file}" 2>/dev/null
```

每件作品按文件名 + 视觉判断 (Read 看代表性几张) → (title, brand, year, tags, desc)。

### 3. 解析 bio_text 抽信息

**工作室级**（每个值都至少有默认 fallback）：
- **STUDIO_NAME_CN / STUDIO_NAME_EN**（如「虚白 / Xubai」「明川 / Mingchuan」）
- **STUDIO_TYPE**（如「设计工作室」「影像工作室」「建筑事务所」「独立设计师」）
- **TAGLINE**（两行：长句 + 短结论，参考 `虚白是一家以材料与场景为方法的中文设计工作室，致力于在品牌、视觉与空间之间寻找静止的位置`）
- **LOCATION_PRIMARY / SECONDARY**（如「中国 · 上海」「日本 · 京都」；只有一个城市就把第二行去掉）
- **TIMEZONE_PRIMARY / SECONDARY**（如「北京时间 UTC+8」、第二个城市的 JST/EST 等）
- **YEAR_FOUNDED**（如 2017）
- **CTA_TEXT**（默认「我们来聊聊吧。」，可改成「Let's Talk」「联系合作」等）
- **TAB_LABELS**（默认 `作品 / 关于 / 履历`，可改）
- **CAPABILITIES**（4—5 项能力，写进 about overlay）
- **TEAM**（3—5 名成员，写进 about overlay；个人作品集就只写自己一行）
- **CV_YEARS**（按年份分组的项目时间线）
- **AWARDS**（3—8 条展览/奖项）
- **CONTACT_EMAILS**（new project / press / hiring 三类邮箱）
- **OFFICE_ADDRESSES**（1—2 个办公室地址）
- **SOCIAL**（IG / 微信 / Twitter / Behance 等）
- **FILTER_CATEGORIES / YEARS**（用于 filter overlay 的复选框，自动从 WORKS 派生）

**每件作品**：
- **id**（'01'—'NN' 字符串两位）
- **brand**（客户名或「个人项目」「独立创作」）
- **title**（4—12 字简洁标题）
- **year**（YYYY 数字）
- **tags**（数组，1—3 个英文一词，如 Identity / Editorial / Web / Installation / Poster / Sound / Motion / Print / Type / Packaging / Exhibition / Light）
- **img**（封面图，1080×1080 正方形）
- **hero**（详情页头图，1600×1000 横版）
- **g1, g2**（详情页两张配图，800×600）
- **desc**（一句话 ~20—50 字，会显示在二级详情页副标题）
- **long**（详情页正文，2—3 段，每段 60—120 字）
- **spec**（4 行键值对：`[['Client','xxx'],['Year','xxx'],['Scope','xxx'],['Duration / Pages / Edition','xxx']]`）

如果 bio_text 只有零散描述没有具体故事 → **编**简短叙述呼应整体氛围，但**不要瞎编客户名**（写 'Personal' / '独立创作' / `工作室自发`）。

### 4. WORKS 数量
- 至少 **8 件**（屏幕上才不空），少于 8 件就重复填充：让 `workFor()` 自动用 mod 循环就行
- 上限 **30 件**（再多没必要，球面会重复）
- 推荐 **15—25 件**

### 5. 替换 12 个 SWAP

| SWAP | 位置 | 内容 |
|---|---|---|
| 1 | `<title>` | `{STUDIO_NAME_CN} — {STUDIO_TYPE} · Index {YEAR}` |
| 2 | `.brand-block`（顶栏左 logo + 文字）| 自定义 SVG logo 或换图标 + 「声音 [关闭]」可改可保留 |
| 3 | `.tagline`（顶栏中部两行字）| `{TAGLINE}` 长句 + `<br>` + 短结论 |
| 4 | `.col-meta`（顶栏右上 location）| 1—2 个 `<div class="row"><span class="loc-dot live"></span>{LOCATION}</div>` |
| 5 | `.col-times`（顶栏右上时区）| `北京时间 UTC+8` / `<div id="time1">` 留空让 JS 填 / 第二行 `<div id="time2">` 也留空 |
| 6 | `.cta` 按钮 | `{CTA_TEXT}` |
| 7 | `.bottombar .tabs` | 三个 `<button class="tab">` 文字（默认 `作品 / 关于 / 履历`） |
| 8 | `#overlay-about` | 完整 about 内容：eyebrow + 标题 + 正文 + 能力领域 + 团队成员 |
| 9 | `#overlay-cv` | 按年份分组的项目时间线 + 展览/奖项 |
| 10 | `#overlay-contact` | 邮箱 / 地址 / 社交 / 招聘 6 个 contact-cell |
| 11 | `#overlay-filter` | 类别 / 年份 / 客户类型三组 checkbox（按你最终的 WORKS 派生） |
| 12 | `const WORKS = [...]` | 完整 WORKS 数组 |

### 6. 风格变体（可选）

默认配色（深色「材料 / 工作室」氛围）：
```css
--bg: #0d0c0b;
--ink: #f0e9df;
--ink-soft: #8a8278;
--accent: #c89a5a;
```

如果用户说：
- **亮色 / 杂志感** → bg `#f4f1ec`、ink `#1a1714`、accent `#8a4a1a`
- **极简白** → bg `#ffffff`、ink `#0a0a0a`、accent `#666666`
- **赛博紫** → bg `#0a0612`、ink `#e8d8ff`、accent `#9b6dff`
- **暖棕复古** → bg `#1f1610`、ink `#e8d4b6`、accent `#c8895a`

只改 `:root` 四个变量；不改 layout / JS。

### 7. 写出文件 / 输出 HTML

**模式 A（Claude Code）**：
```
~/Desktop/{slug}-vr-canvas/
├── index.html
└── images/
    ├── work-01.jpg ... work-NN.jpg
    └── (hero / g1 / g2 同名 -hero / -g1 / -g2)
```
slug 用工作室名拼音连字符（xubai / mingchuan / li-ming）。

**模式 B（GLM）**：
直接在回答里输出一份完整的 HTML，包在 ```html 代码块里。所有 `<img src>` 用 picsum 占位或用户给的 URL。

回答末尾说一句：
> 把上面这段保存成 `index.html` 双击打开。要换图，把 WORKS 数组里的 `img / hero / g1 / g2` 换成你的图片地址。

### 8. 报告

**模式 A**：一句话报告路径 + 件数 + 风格。
> 已生成 ~/Desktop/xubai-vr-canvas/index.html — 18 件作品，深色「材料」配色。双击打开，鼠标在屏幕里走会有 VR 头部转动感，长按拖拽翻阅其他作品，点击查看详情。

**模式 B**：直接给 HTML 代码块 + 一行使用说明。

## 强制保留（绝对不能改）

- 全部 JS（球面投影 / 拖拽惯性 / 滚轮缩放 / hash 路由 / splash / time tick / mouse tilt）
- `.work / .frame / .cell-head / .cell-foot / .num / .brand / .proj` 的 CSS
- `.viewport / .sphere` 的 CSS 和 DOM 结构
- `SPHERE_R = 1700 / STEP_DEG = 11 / ROW_HALF = 6`（这些是球面投影的核心参数；要更强 VR 感才改 R）
- `.overlay / .overlay-close / .info-pane / .info-section` 的结构（only 改文字，不改 class）
- `mix-blend-mode: difference` 在 topbar 上（这是设计语言核心）

## 易错速查

- **图片**：必须 1080×1080 正方形作为 `img`（球面 cell 是正方形）；详情页 hero 用 1600×1000 横版
- **WORKS 数量太少**：至少 8 件；不够就在 bio 里编几个「独立创作 / 实验项目」
- **不要**给所有作品写超长 long（300 字+）— 留白节奏比信息密度重要
- **不要**改 `font-family: "Noto Serif SC"` 之类的中文衬线字体（这是工作室质感的来源）
- **about / cv / contact 三个 overlay 都必须有**：用户即使没给信息，也要根据 bio 编出合理内容；不要留空 overlay
- **filter overlay 的 checkbox** 是装饰性的（没接 JS），但要根据实际 WORKS 派生类别和年份
- **个人作品集**（不是工作室）：team 写一个人就行；office addresses 改成「自由独立 · 工作地点 城市」
