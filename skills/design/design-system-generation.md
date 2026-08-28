---
name: Design System Generation Skill
description: Import, extract, normalize, or persist a reusable DESIGN.md from an existing design system, HTML artifact, screenshot, template, style reference, or generated interface.
---

# Design System Generation Skill

把视觉规则变成一份可复用的 `DESIGN.md`。普通首版页面生成**不需要**这个 skill；仅当用户要导入、提取、规范化、持久化或复用一套设计语言时用。核心理念（借鉴 DESIGN.md 方法）：用自然语言描述视觉系统、有精确值就保留、并解释每个设计选择**为什么**存在而不只是长什么样。产出经 `skills/design/design-system-reference.md` 供未来生成复用。

## 三种模式

- **Import（导入）**：用户给了现成 `DESIGN.md`/设计规范，要变成可复用参考。行为：读取、保留用户自有规则、检查缺失段、仅在有用时规范化结构、**不要按模型自己的品味重写**、保留精确值、必要时标出歧义。（如"这是我的 DESIGN.md 后面按这个来"、"检查这份有没有缺失"）
- **Extraction（提取）**：从 HTML/截图/模板/页面/CSS/style skill/品牌参考提取设计规则。行为：检视来源、提取可见值与模式、区分精确值与推断值、**既描述表面风格也描述底层意图**、不机械照抄每条 CSS、不臆造没有的细节、分离可复用规则与一次性细节。（如"从这个 HTML 提炼 DESIGN.md"、"把截图总结成设计系统"）
- **Persistence（持久化）**：把当前已认可的产物风格沉淀成未来可复用的系统。行为：检视当前产物、从已认可设计提取稳定规则、识别哪些该重复哪些是一次性、**别把页面特有细节变成通用规则**。（如"把当前页面风格沉淀成 DESIGN.md"、"后面页面都沿用这版"）

多模式同时适用时，以用户明确请求为准。

## 不要用这个 skill 当

只生成单个首版页面、只用现有设计系统而不改它、只做局部编辑、只改确定性参数（色/间距/圆角/密度）、或普通的设计参考查找（那用 `design-system-reference.md`）。

---

## Workflow

### 1. 判断模式
分类为 Import / Extraction / Persistence；多个适用时以用户明确请求为准。

---

### 2. 提取设计意图（不只描述外观）

解释设计为什么用每个模式，而不只是它长什么样。

弱：`蓝色按钮、圆角卡片。`
好：`蓝色专用于主操作与进度状态，给界面一条清晰路径；圆角软化了原本偏技术感的布局，让密集信息更易接近。`

应说清：每个视觉选择传达什么、哪些是结构性哪些是装饰性、如何扩展到未来页面、哪些元素是风格的核心、哪些不该被滥用。

### 3. 分离稳定规则与一次性选择

好的设计系统不盲目保留每个细节。把决策分为：**核心规则**（未来都重复）、**可选母题**（有用但非处处必需）、**一次性细节**（只属于当前产物）、**应避免**（不该重复）。

例：
```text
核心规则：项目年份/角色/状态用紧凑等宽元数据标签。
可选母题：项目多时，列表用 hover 预览图。
一次性细节：超大动画项目编号只属于首页 hero。
应避免：别给无关内容页加随机系统标签。
```

### 4. 产出或更新 DESIGN.md

用户给了现成 `DESIGN.md` → 更新/规范化而非整体替换；从产物提取 → 产出新的；持久化当前设计 → 产出供 `design-system-reference.md` 复用的。简洁但足以指导未来生成，别搞庞大的 design bible。

---

# DESIGN.md 结构

默认用下面 9 段结构。每段写**实用规则 + 为什么**（不只是值），有精确值就保留、推断的标注清楚。

**1. Visual Theme & Atmosphere** — 整体气质：情绪、精致度、密度、视觉温度、个性、受众、头 2 秒的感受。**用一个具体参照物锚定主题，而非一串形容词**——"现代/干净/高级/可信"什么都没指定，模型只会做出落在这些词中心的平庸结果；形容词描述一个「区域」，一个具体参照（某类实物/场景/年代，如"1970 年代某老牌大学的研究生讲义"）描述一个「点」，一句话带出配色/字体/留白/有无装饰，还自带「它不是什么」。若一定要用形容词，定义它在本系统里的具体含义。

**2. Color Palette & Roles** — 按**角色**而非清单记录颜色，说明每个用在哪、哪些不该滥用，强调克制 accent，没可见值不臆造、推断的标注：
```md
### Core Palette
- Background `#F7F3EA` — 暖调编辑感底色，页面背景。
- Text Primary `#171717` — 高对比正文与标题。
- Text Muted `#73706A` — 元数据、说明、次要细节。
- Accent `#D94F30` — 仅用于主 CTA、激活态、每区块一处高亮。
- Border `rgba(23,23,23,0.14)` — 不靠重盒子的细微结构。
```

**3. Typography Rules** — 字族 + **语义层级体系**（多数系统 9–15 级，用 headline/display/body/label/caption 等语义命名，每类可再分 small/medium/large），各级字号/字重/行高、层级跨度（克制：标题约 1.9× 正文而非 5×）、中-拉-数字混排。

**4. Layout & Elevation（布局与层级）** — 网格/版心、间距节奏、留白策略、内容区结构、对齐逻辑（结构而非装饰）。**并说清"层级/深度怎么表达"**：用阴影就定义阴影规则；扁平设计要说清替代方案（边框 / 色彩对比 / 色调分层，如背景用浅色、主内容用纯白卡）——层级如何传达是核心决策，不能漏。

**5. Component & Shape（组件与形状）** — **形状语言**：整体的形状性格（锐利 / 柔和）与统一的圆角策略（如所有交互元素统一 4px，"克制的现代感"）。**组件形态**：关键组件（卡片/按钮/标签/输入框等）的圆角、边框、阴影、内距规则，**尤其覆盖状态变体**（primary/secondary、hover/pressed/active、空/错误/禁用）——状态覆盖是设计系统的关键，不只画默认态。

**6. Interaction & Motion** — 动效性格、入场/hover/过渡惯例、始终带 reduced-motion，区分核心交互与一次性效果。

**7. Responsive Behavior** — 断点、移动端如何重排、触控友好、各视口可读性。

**8. Do's and Don'ts** — 写具体规则。**注意：又长又啰嗦的 Don'ts 往往说明主题描述太模糊（足够具体的参照会自带大部分负向约束）；一个具体参照 + 一份刻意的 Do/Don't 才是最佳组合。**
```text
Do：作品为主要佐证；保持强层级；元数据标签克制一致；限制 accent 数量；用一个难忘的结构/交互主意；有精确值就复用。
Don't：假评价/假指标/假 logo；通用区块填空；照抄品牌素材/专有 UI；无目的的装饰渐变/emoji；每个区块一样响；可发布产物里有死链/失效点击；把一次性 hero 效果当通用规则。
```

**9. Agent Prompt Guide** — 写给未来 agent 的、直接可操作的生成指令：
```md
在本系统里生成新页面时：从作品优先结构开始；角色/年份/类别用紧凑元数据标签；accent 保留给主操作与激活态；尽早展示真实作品、别先放长 bio；用一个大胆结构动作、其余区块安静；除非用户要简单版避免通用卡片网格；保留响应式与触控友好。
```

---


## Lightweight Tokens

If useful, include a compact token section.

Use only when values are available or can be responsibly inferred.

Example:

```json
{
  "color": {
    "background": "#F7F3EA",
    "surface": "#FFFFFF",
    "textPrimary": "#171717",
    "textMuted": "#73706A",
    "accent": "#D94F30",
    "border": "rgba(23, 23, 23, 0.14)"
  },
  "radius": {
    "sm": "6px",
    "md": "12px",
    "lg": "24px"
  },
  "spacing": {
    "base": "8px",
    "section": "96px"
  },
  "typography": {
    "bodySize": "16px",
    "bodyLineHeight": "1.5",
    "labelSize": "11px"
  }
}
```

Do not include fake precision. If values are inferred, state that they are inferred.

---

## 各模式补充（避免项）

三模式的核心行为已在前面「三种模式」给出。各自要避免：
- **Extraction**：别把原始 CSS 倒进 DESIGN.md、别臆造没有的值、别把一次性细节当系统规则、别漏掉响应式/交互。
- **Persistence**：别过拟合当前页、别把占位内容当设计规则、别把临时实验固化成永久系统、别忽略用户已认可的风格决定。
- **Import**：输出可以是更新版/规范化版/缺口分析+建议/兼容性说明；不删用户规则除非冲突或重复。

## Quality Rules

一份好的 `DESIGN.md`：可复用、具体、扎根源材料、简洁够用、分清核心vs可选、IP安全、对未来生成有用。**避免**：通用设计套话、空泛的 premium/modern/clean 措辞、有理论无可操作规则、照抄专有品牌系统、把单个产物细节当通用规则、臆造源材料不支持的 token。

## IP and Brand Safety

源是公开品牌灵感时：不把输出当官方系统、不照抄 logo/素材/精确页面结构/专有 UI、只描述高层视觉特质、产出导向原创的可复用规则。源是用户自有时：明确提供则视为权威、保留精确值、不完整处标注假设。

## Chinese Typography Reference

产物含大量中文/CJK、中文编辑排版、公众号、小红书、中文 deck、中文 UI 标签或印刷风 HTML 时，用 `horizontal-craft/chinese-typography.md`；把印刷方法转为 HTML 结构：版心、网格、留白、标题组、图版、边注、章节节奏与标点。

## Quality Gate

交付前应用 `quality-gate.md`；本场景可加更严的检查，但不得削弱共享门禁。

## Handoff

生成/导入/规范化/更新后的 `DESIGN.md` 经 `skills/design/design-system-reference.md` 供未来设计复用，应是可复用参考而非一次性总结。有用时记下：源产物/模板/截图、所选 style skill/品牌灵感、日期版本、假设、缺失信息。
