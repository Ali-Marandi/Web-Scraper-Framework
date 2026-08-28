---
name: ascii-cosmos
description: Generate a single-file product landing page with a layered ASCII cosmos hero (rotating ASCII planet, drifting irregular asteroids, comet trails, nebula gas clouds — each in its own harmonious color) plus full marketing sections (about / features grid / showcase / spec / pricing / CTA / footer). Takes a natural-language description of one product (any kind — a note app, a coffee subscription, a CLI tool, an indie hardware, a hosting service…) and outputs ONE working .html file with deep-space dark or warm-letterpress theme. Runs in BOTH Claude Code (writes to ~/Desktop) and GLM / online chat (outputs HTML inline). Trigger phrases: "做个宇宙风产品落地页", "生成 ASCII 产品官网", "ascii-cosmos-gen ...", "做个独立软件 / 独立硬件落地页", or when user drags this skill folder into chat asking for an atmospheric product landing page.
visibility: public
mode: template
carrier: web-page
scenario: marketing-landing
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个宇宙风产品落地页"
  - "生成 ASCII 产品官网"
  - "做个独立软件落地页"
  - "做个独立硬件落地页"
  - "ascii 落地页"
  - "ascii hero"
legacy_gen: true
---

# ascii-cosmos — ASCII 宇宙调性产品落地页生成器

## 作品长什么样

单文件 HTML 产品官网，hero 是动态分层 ASCII 宇宙：

- **星云气体云**（紫，柔和散点）
- **闪烁星点**（冷白，带 ★ ✦ 装饰）
- **旋转 ASCII 行星**（青，带 3 圈卫星轨道）
- **漂浮不规则小行星**（琥珀金，6 种带陨石坑的多行 ASCII 形状，自旋 + 缓慢漂移）
- **彗星拖尾**（粉，从屏幕掠过）

下面是常规 marketing 区块：关于 / 核心功能 6 卡片网格 / 界面预览 2 块 / 技术规格 / 订阅方案 3 档 / CTA / 页脚。所有强调字段都有"hover 时打乱-解码"的字符滚动动效（`.pt` 类）。

适合：独立软件、笔记/写作工具、本地优先 AI、CLI、独立硬件、订阅服务、SaaS、电子书、播客、任何"安静 / 克制 / 有手作味"的产品。

## 何时触发

用户说：
- "做个宇宙风产品落地页"
- "做个 ASCII 风格的产品官网"
- "生成一个像墨思那样的落地页 — 我的产品是 ..."
- "ascii-cosmos-gen ..."
- 把本 skill 文件夹拖进对话框并描述一个产品

提供：
- **产品名字 + 一句话定位**（必需）
- **核心卖点 / 功能清单**（推荐 — 给 6 张卡片用）
- **定价档位**（可选 — 没说就编 3 档：免费 / 专业 / 团队）
- **风格**（可选 — 深空青 / 暖色羊皮纸 / 赛博紫 / 终端绿 …，照抄 `styles.md` 预设名或自由描述。不写就用默认深空青）

如果用户**只给产品名一句话**：自己围绕这个产品把 6 个功能、3 档价、技术规格全部脑补出来。语气要克制、有手作味，不要 marketing 鸡血。

## 两种运行模式

### 模式 A · Claude Code / 本地（有文件系统）
- 输出位置：`~/Desktop/{slug}.html`（**单文件**，所有图片走 unsplash URL 或用户给的链接）
- slug 用产品英文名小写连字符
- 一句话报告：路径 + 用了什么风格 + 多少卡片

### 模式 B · GLM / 在线对话（无文件系统）
- 直接把完整 HTML 包在 ` ```html ` 代码块里输出
- 图片全部用 `https://images.unsplash.com/photo-XXX?...` 或 `https://picsum.photos/seed/{slug}-NN/W/H` 占位
- 不要尝试访问本地文件、不要建议命令行操作
- 末尾一行说明：保存为 .html 双击打开即可

判断：如果你**无法 Read 看到本地图片**或工作目录不是用户家目录 → 默认走 B。

## 工作步骤

### 1. 读模板
读取本 skill 同目录下的 `template.html`。这是完整骨架，包含：
- 全部 CSS（深空主题色 + 5 个 ASCII 层 + 卡片 / 价格 / 规格 / hero 网点字 …）
- 全部 JS（5 层 ASCII 渲染、信息区轨道、字符滚动、标签筛选、平滑滚动、实时时钟）
- 12 处 `<!-- SWAP-N -->` 注释标记需要替换的位置

**JS / CSS 不要改**（除了主题色变量与字体可以按 styles 改）。

### 2. 读风格预设
看 `styles.md`：5 种预设。如果用户的风格描述匹配某个名字，照那份的 CSS 变量替换 `:root`。否则按用户描述自己设计 6 个变量（`--bg / --fg / --dim / --accent / --accent2 / --accent3 / --line / --paper`）+ 5 个 ASCII 层颜色（`#ascii-nebula / -stars / -planet / -asteroids / -comets`）。

> 配色铁律：5 个 ASCII 层颜色必须**互相和谐 + 都能在背景上读出来**。深色背景 → 高饱和发光色；浅色背景 → 中低明度有重量的色。

### 3. 解析用户输入抽信息

抽：
- **PRODUCT_EN** — 英文 logo 名，全大写 ASCII 字（用于 hero 大字 ASCII title）
- **PRODUCT_CN** — 1-2 个中文字（hero 副标题大字，会渲染为网点字）
- **TAGLINE** — 一句话副标语（30-50 字）
- **VERSION / TYPE / PLATFORM** — 3 个 meta 标签
- **ABOUT_PARAGRAPH** — 80-150 字关于段落，3-5 个 `<span class="pt">` 强调短语
- **3 HIGHLIGHT** — 3 个 cell（标题 + 一句话描述）
- **6 FEATURES** — 6 张卡片：图片 URL + ASCII overlay（5-6 行小图） + 标题 + 副标题 + 1-2 个标签 + 分类（ai/write/graph/sync 任选或自定义）
- **2 SHOWCASE** — 2 段界面介绍（截图 URL + mini-ascii 装饰 + 标题带 `<em>` 强调 + 2 段 60-100 字描述）
- **10 SPEC ROWS** — 10 行键值对（版本 / 平台 / 引擎 / 数据格式 / 同步协议 …）
- **3 PRICING** — 3 档（名字 / 价格数字 / 价格单位 / 描述 / 5-6 条特性 / CTA 按钮文案）。**中间一档加 `featured` 类**
- **CTA_BIG** — 大字号 CTA 文案（带 `<em>` 强调）+ 副文案 + 3 个按钮 + 6-7 个平台标签

### 4. 替换 12 处 SWAP

| SWAP | 位置 | 内容 |
|---|---|---|
| 1 | `<title>` | `{PRODUCT_CN}{PRODUCT_EN} — {TAGLINE}` |
| 2 | header logo + 5 项 nav | logo 文字 + 导航锚点（默认：功能 / 界面 / 规格 / 订阅 / 关于） |
| 3 | hero ASCII title | `PRODUCT_EN` 的 ANSI Shadow 风 ASCII（用 https://patorjk.com/software/taag 风格，5 行高） |
| 4 | hero 中文大字 + tagline + 3 meta | `PRODUCT_CN` + `TAGLINE` + 3 个 meta span |
| 5 | intro 段落 + 3 cells | `ABOUT_PARAGRAPH`（含 `<span class="pt">` 强调）+ 3 个 `<div class="cell">` |
| 6 | 6 张 features 卡片 | 每张：`data-cat` + `<img src>` + ASCII overlay + 标题 + small + tags |
| 7 | 4 个 filter tag | 分类 chip（all + 你定的 3-4 个分类，匹配卡片的 data-cat） |
| 8 | 2 块 showcase | 每块：截图 + mini-ascii + h3（含 em） + 2 段 p（含 pt 强调） |
| 9 | 10 行 spec table | 每行：`<b>` 字段名 + `<span class="pt">` 值 |
| 10 | 3 档 pricing | name / num / desc / ul li / btn |
| 11 | info 区 CTA | info-big 大字（含 em）+ hero-sub 副文案 + 3 个按钮 + platforms |
| 12 | footer | 版权 + 一句署名 |

**强制保留**（不能动）：
- 全部 `<script>` 块（5 层 ASCII 渲染 / 信息区轨道 / scramble / 标签筛选 / 平滑滚动 / 时钟）
- `.pt` 类的字符滚动机制（要在用户文案里手动撒 `<span class="pt" data-text="...">...</span>`）
- 5 个 ascii-layer 的 `<pre id="ascii-...">` 节点
- `<pre id="info-ascii">` 节点
- 6 张卡片的 data-cat 和筛选逻辑
- featured 价格档的样式

### 5. 写 ASCII 大字标题（SWAP-3）

用 ANSI Shadow / ANSI Regular 字体的 5 行 ASCII 文字。每个字母用 ╗╔═║║║╝╚═╝ 这种线条字符。例如 INKWEAVE 是：
```
██╗███╗   ██╗██╗  ██╗██╗    ██╗███████╗ █████╗ ██╗   ██╗███████╗
██║████╗  ██║██║ ██╔╝██║    ██║██╔════╝██╔══██╗██║   ██║██╔════╝
██║██╔██╗ ██║█████╔╝ ██║ █╗ ██║█████╗  ███████║██║   ██║█████╗
██║██║╚██╗██║██╔═██╗ ██║███╗██║██╔══╝  ██╔══██║╚██╗ ██╔╝██╔══╝
██║██║ ╚██╗██║██║  ██╗╚███╔███╔╝███████╗██║  ██║ ╚████╔╝ ███████╗
╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝
```

**如果产品英文名超过 8 字母** → 缩到 8 字母内的简称（如 `INTERSTELLAR` → `STELLAR`），或者用更窄的 ANSI 字体（更细的 `▌▐█`）。

**如果你不确定字模长什么样** → 至少给个看得过去的 5 行 ASCII，不要留空。

### 6. 写卡片 ASCII overlay（SWAP-6 内嵌）

每张卡片右下盖一段 4-5 行的小 ASCII 装饰，对应这张卡片的功能。例如：
- "智能续写" → `╭─────╮ │ ... │ ╰──→──╯`
- "知识图谱" → `●─●─● │\\ │/│ ●─●`
- "搜索" → `┌─────┐ │ ⌕ 找到 │ │  3 处 │ └─────┘`
- "同步" → `▣ ⇄ ▢ ╲ ╱ ⇅ ╱ ╲ ▤ ⇄ ▥`
- "时间线" → `←─◆─◆─◆─→ ░░▒▒▓▓██`

不要超过 5 行，不要超过 14 字符宽。

### 7. 撒 `<span class="pt" data-text="...">` 强调

模板里所有需要"hover 时字符乱码再解码"的强调短语都用：
```html
<span class="pt" data-text="原文">原文</span>
```
- intro 段落里撒 3-5 处
- showcase p 里每段撒 1-2 处
- spec 每行的值都包一层 `<span class="pt">`
- pricing btn 文字也加 `pt`
- 标题里的色字用 `<span class="em">...</span>`（不是 `pt`）

### 8. 风格变体（可选）
如果用户指定了风格，照 `styles.md` 改：
- `:root` 8 个变量
- `.hero` background 渐变
- 5 个 `#ascii-{layer}` 颜色
- 图片滤镜（深色用 `hue-rotate(200deg) brightness(.7)`，暖色用 `sepia(.3) saturate(.85)`）

> **没有指定风格时**：根据产品的"调性词"自动选色 — 见下面「调性 → 配色映射」。

### 8.5 替换 ASCII 场景 motif（推荐！）

模板的 hero 默认是宇宙（行星 + 小行星 + 彗星 + 星云）。**这个 motif 应该跟着产品调性换** — 一个咖啡订阅不该飘小行星，一个森林漫步 app 不该有彗星。

改法**只改一个对象**：找到 `<script>` 里的 `// SWAP-13 · ASCII 场景资产` 标记，整体替换里面的 `SCENE = { ... }`。其它 JS 不要动。

`SCENE` 11 个键各自的角色：

| 键 | 默认（宇宙） | 角色 / 视觉职责 |
|---|---|---|
| `floaters` | 6 个不规则小行星 ASCII 形状（多行数组） | 屏幕里漂浮 + 自旋的"主物体" |
| `centerShade` | `" .,:;-~+*=%#@█"` | 中央旋转球体的明暗梯度（暗→亮 14 字符） |
| `diffuseChars` | `"·∙∶⋮⋯░▒"` | 弥漫底层的"气体云"密度梯度（淡→浓） |
| `sparkRare` | `"★"` | 稀有大亮点 (4% 概率) |
| `sparkBright` | `"✦"` | 中频亮点 (15%) |
| `sparkDim` | `".∙"` | 普通暗点 |
| `streakHead` | `"☄"` | 飞掠物的"头"（最亮的一格） |
| `streakTailNear/Mid/Far/End` | `"*","∙","·","."` | 拖尾从近到远 4 段渐隐 |
| `centerSats` | `"◉◎○"` | 围绕中央球体的 3 颗"卫星"，由内向外 |
| `orbitDots` | `".∙•"` | 3 圈轨道线的点字符，由内向外 |

#### Motif 库（按产品类型选）

| 产品类型 | floaters 主体 | centerShade | diffuseChars | sparks | streakHead/tail | centerSats | 视觉故事 |
|---|---|---|---|---|---|---|---|
| **咖啡 / 茶 / 饮品** | 咖啡豆 / 茶叶 形状 | `" .'-=+oO0@#"` | `"·~,'\""` (蒸汽) | `★ ✧ . ∙` | `"☕"` 头 + `"*∙·."` 拖尾 | `"●◐○"` (三种烘焙) | 一杯咖啡 + 飘豆 + 蒸汽 + 偶尔一颗豆掉过 |
| **森林 / 自然 / 户外** | 树叶 / 松果 形状 | `" .,;:!|tT#"` (年轮) | `"~^,'\""` (雾) | `"⁂"` 萤火 + `"·"` 露珠 | `"𓅯"` 鸟 + `"~~~~"` 飞行轨迹 | `"❀✿✾"` (花) | 一棵树 + 落叶 + 雾 + 萤火虫 + 偶尔飞鸟 |
| **音乐 / 播客 / 音频** | 音符 / 唱片碎片 | `" .─=≡▪▫■□"` | `"·∶⋮⁞"` (噪点) | `"♪♫"` + `"·"` | `"♬"` 头 + `"~∼≈"` 波 | `"◉◎○"` (黑胶圈) | 一张唱片 + 飘音符 + 频谱噪点 + 节拍 |
| **代码 / CLI / 开发者** | `{}` `[]` `()` `<>` 包裹的小 ASCII 块 | `" 01[](){}<>#"` | `"·.,:|"` | `"★ ✦ . _"` | `"_"` 光标 + `"   "` (闪现型) | `"◉⊞⊟"` 模块 | 一个调用图 + 飞过的 commit + 闪烁光标 + 矩阵雨 |
| **手作 / 工艺 / 极物** | 锤 / 刨花 / 钉 / 锈点 | `" .·°*+x#X@"` | `"·:.,"` (尘) | `"✦ ▪ ▫"` | `"→"` 头 + `"-—"` 切线 | `"◉○⊙"` (齿轮) | 一个工作台 + 飘刨花 + 木屑 + 偶尔一记 |
| **冥想 / 健康 / 慢生活** | 涟漪 / 圆 / 波浪 形状 | `" ··∘○●"` | `"~∼≈"` (呼吸波) | `". ∙ °"` | `"◌"` 头 + `"·· ··"` 散点 | `"◯◌○"` (空圆) | 一个呼吸圆 + 涟漪 + 暖色尘埃 + 缓慢 |
| **极客硬件 / 电子** | 芯片 / 电路块 (`├┤├ ┐└┘`) | `" .·•◊◆■"` | `"⋅¨"` (电气噪) | `"⚡"` 偶现 + `"·"` | `"►"` 头 + `"==="` 数据流 | `"⊙⊚⊛"` (LED) | PCB + 漂浮电容 + 数据流飞过 |
| **写作 / 笔记 / 思考** | `"…"` `"——"` `"§"` 标点形状 | `" .,;:!?¶§"` | `"··¨"` | `". ∶ ⋮"` | `"✒"` 头 + `"~~~"` 笔迹 | `"◉◯●"` (墨点) | 一支笔 + 飘标点 + 笔迹划过 + 思绪点 |
| **意式 / 复古 / 80s** | 像素方块 / 撞色几何 | `" .░▒▓█"` | `"·:|"` | `"◆ ◇ ▰"` | `"◉"` 头 + `"━━"` 实线 | `"■□▣"` | 一个 CRT + 像素粒子 + 扫描线 |
| **海洋 / 旅行 / 远方** | 鱼 / 帆 / 船 / 浪 | `" .~≈≋"` 水波 | `"~∼≈≋"` (波纹) | `"·°"` (气泡) | `"⛵"` 头 + `"~~~"` 尾流 | `"◐◑◯"` (月相) | 一艘船 + 浪 + 气泡 + 海鸟划过 |

#### 怎么写 floaters 形状

每个形状是 3-4 行的多行 ASCII，宽 8-12 字符。一定要：
- 形状轮廓闭合（比如树叶 `,/^\,` `(   )` `'\_/'` ）
- 多个变体不要长得一模一样，至少 3-6 个不同的
- 单字符宽度，不要用全角
- 留 1 格 padding 让旋转抖动好看

**树叶示例**：
```js
floaters: [
  [" ,-^-, ",
   "|     |",
   " '---' "],
  ["  /\\\\  ",
   " /  \\\\ ",
   " \\__/ "],
  ["  *_*  ",
   " /...\\\\ ",
   " '___' "]
]
```

**音符示例**：
```js
floaters: [
  ["  ♪    ",
   " /|    ",
   "♪ |____♪"],
  ["    ♫  ",
   "    /\\\\ ",
   "♪__/  \\\\"],
  ["  ♩    ",
   "  |    ",
   "  o    "]
]
```

**写完检查**：把 SCENE 直接贴进控制台，跑一下 `JSON.stringify(SCENE)` 不报错就 OK。

#### 自由发挥的判定

如果用户的产品**不在上表 10 类**里 → 自己设计 motif，遵守原则：
1. **floaters** 选 3-6 个跟产品有具象关联的小图形（"它会让人想到这个产品"）
2. **centerShade** 14 字符明暗梯度，暗的字符（` .,`）开头，亮的（`@#█`）结尾，中间渐变
3. **diffuseChars** 5-8 个"半透明"字符（点 / 顿点 / 小方块 / 波浪），表现氛围底层
4. **streak** 整套要"前重后轻"渐隐
5. **sat / orbitDots** 各 3 个，表现轻重三级

> 一句话原则：**让人不戴眼镜、3 米外瞄一眼，能猜出这是个什么产品的网站。**

### 9. 调性 → 配色映射（用户没指定风格时按这个选）

| 用户描述里的关键词 | 推荐预设 | 主色 |
|---|---|---|
| 安静 / 克制 / 思考 / 写作 / 笔记 / 本地优先 | **深空青**（默认） | `#8be9ff` 青 |
| 温暖 / 手作 / 中式 / 文艺 / 慢 / 茶 / 复古 | **暖色羊皮纸** | `#660125` 酒红 |
| 高能 / 未来 / AI / Web3 / 游戏 / 极客 | **赛博紫** | `#ff00aa` 霓虹品红 |
| CLI / 终端 / 安全 / 复古 80s / phosphor | **终端绿** | `#00ff66` |
| 自然 / 健康 / 冥想 / 旅行 / 北欧 | **极光** | `#7fe3c4` 极光绿 |
| 咖啡 / 烘焙 / 工艺 / 食品 / 沙漠 / 大地 | **沙漠日落** | `#ff8b3d` 烤橙 |
| 海洋 / 远方 / 蓝色 / 冷静 / 数据 | 自由设计 | `#4fc3f7` 海洋蓝 |
| 黑金 / 奢侈 / 精确 / 钟表 / 高端硬件 | 自由设计 | `#d4af37` 香槟金 + 黑底 |

判定流程：
1. **用户明确说了风格名** → 照 `styles.md` 改
2. **用户没说，但产品有明显调性** → 按上表选最贴的预设
3. **完全开放** → 默认深空青

### 10. 报告

**模式 A**：一句话。
> 已生成 ~/Desktop/{slug}.html — {产品名}产品落地页，6 个功能卡片 + 3 档价格，深空青风格。双击打开。

**模式 B**：完整 HTML 代码块 + 一行说明。
> 保存为 `{slug}.html` 双击打开。要换图就把图片 URL 换成你自己的。要改 ASCII 主标题去顶部的 `<pre class="ascii-title lg">` 替换字模。

## 易错速查

- **5 个 ASCII 层颜色互相打架**：测试一下深色背景下 5 色都要清晰可读。粉太亮、紫太暗都会塌
- **ASCII 大字模板对不上**：5 行 ANSI Shadow 字符高度必须严格 5-6 行，不要 3 行
- **`<pre>` 里换行用真换行**，不要 `\n` 字符串字面量
- **卡片 data-cat 和 filter 不匹配** → 筛选失效。一致性检查
- **pricing 中间档忘加 `featured`** → 视觉重心丢
- **JSON / 对象里中文引号**：ASCII overlay 里如果用引号一律用全角 `""`
- **删了 `<pre id="ascii-comets">` 之类的层** → JS 报错。5 层节点必须全部保留
- **没给图片 URL** → 用 unsplash 的横图（`?auto=format&fit=crop&w=900&q=70`）或 picsum
