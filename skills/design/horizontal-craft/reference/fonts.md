# 字体选择与搭配 Chinese Font Selection

> 本文件是场景化中文字体选择、搭配与加载参考。不要在每个中文排版任务中默认读取；只有当字体会显著影响视觉方向，或需要命名字体 / 可加载字体测试时读取。

本文件按"选字体的实际顺序"组织：**一、选字体（决策线，从头读到尾选完）→ 二、加载执行（选完才需要）→ 三、原则自检（最后对照）**。
不要跳着读字体表；先在 § 一 按气质定位，再到 § 二 取加载方式。

## 一、选字体（决策线）

不要先浏览所有字体表，也不要为了“好看”直接挑一个刺激的字体名。先把用户意图归类，再按媒介、字体角色、加载可用性筛选，最后只进入匹配的字体库表。

### 1.1 用户意图 → 场景类别

| 用户意图 / 关键词 | 场景类别 | 进入字体库 |
|---|---|---|
| SaaS / Dashboard / 产品页 / 科技 / 商务 / 工业 / 硬朗 / 效率 | 现代 / 工业 / 科技 / 商务 | 表 A |
| 文学 / 古典 / 文化 / 新中式 / 感性 / 编辑 / 出版 / 杂志 | 文学 / 古典 / 优雅 / 感性 | 表 B |
| 古籍 / 文言 / 诗词 / 引文 / 对话 / 传统文化 / 楷书气质 | 古籍 / 文言 / 引文 / 对话文 | 表 C |
| 公文 / 党政机关 / 通知 / 制度文件 / 红头文件 | 公文 / 规范（大陆） | 表 D |
| 台湾公文 / 台湾教科书 / 繁体正式 / 楷書教育 | 公文 / 教科书（台湾） | 表 E |
| 学术 / 论文 / 白皮书 / 研究报告 / 严谨 / 可信 | 学术 / 严谨 / 出版 | 表 F |
| 小红书封面 / 海报 / 活动页 / 标语 / 主视觉 / 大字号 | 标题 / 海报 / 大字号 | 表 G |

如果一个需求同时命中多个类别，先按**产物主目的**选主类别：

- 产品/UI 可用性优先 → 表 A；
- 阅读与出版感优先 → 表 B / F；
- 固定图片封面冲击力优先 → 表 G；
- 正式规范优先 → 表 D / E。

### 1.2 字体筛选

进入字体库表后，不要直接选字体名。按下面 4 个条件筛掉不合适的字体。

| 筛选维度 | 判断问题 | 选择原则 |
|---|---|---|
| **交付媒介** | 是 Web/HTML、固定图片、长文、Dashboard，还是公文？ | Web 优先 `A:CDN` / `B:OSS切片`；固定图片可更强；长文和 Dashboard 优先可读；公文按规范。 |
| **字体角色** | 这套字体用于正文、标题、展示字、引文、数字，还是 UI 控件？ | 正文重可读；标题重气质；展示字只用于短标题/标语；UI 控件优先稳定屏幕字体。 |
| **加载可用性** | 字体是否真的能在 HTML 中加载？ | `A:CDN` 可直接用；`B:OSS切片` 用 `@font-face`；`C:仅参考` 不能直接写进 `font-family`。 |
| **内容密度** | 字数多、信息密，还是短标题/海报？ | 密内容用稳字体；短标题才允许强展示字体。 |

快速筛选规则：

- **Web / HTML 输出**：优先 `A:CDN` 或 `B:OSS切片`；`C:仅参考` 不要直接写进 `font-family`。
- **社媒图 / 海报 / 固定图片输出**：可以使用强展示字体，但仍需要可加载方案、用户提供字体文件，或明确它只是视觉气质参考。
- **长文 / 报告 / 公众号**：正文优先高可读字体；强展示字体最多用于标题、栏目名、引文或关键数字。
- **Dashboard / 表单 / 后台 / 工具页**：优先系统字体栈、思源黑、MiSans 等屏幕字体；不要用强展示字体做 UI 正文。
- **公文 / 正式材料**：优先用户或机构规范；不要用海报字体“增强设计感”。

### 1.3 字体库表

字体库表只放字体本身的信息：字体名、字重、用途提示、加载方式。OSS/CDN/OSS切片状态也在这里体现，不要在场景路由表里重复展开。

“加载”列含义：

- `A:CDN` = 公共 CDN 可达，`<link>` 直接引（见 § 6）。
- `B:OSS切片` = 当前已上传OSS切片，按 § 1.2/§ 1.4 写 `@font-face`。
- `C:仅参考` = 无公共加载方案，仅作气质参考；确定方向后改用本类同气质 A/B 字体，或由用户提供字体文件。
- `系统` = 系统字体（如 PingFang/macOS），无需加载但不跨平台保证。

以下字体库表只在场景命中后读取，不要跨场景扫表。

### 表 A：现代 / 工业 / 科技 / 商务

**关键词**：现代 · 工业 · 科技 · 商务 · 硬朗 · 效率 · 中性 · 极简 · UI · SaaS · Dashboard · 产品页

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 思源黑体 Source Han Sans | 7（ExtraLight–Heavy） | 屏幕通用首选，可正文可标题 | A:CDN |
| MiSans 小米兰亭 | 7（Thin–Heavy） | 屏幕、移动 UI、Dashboard；字怀稍开 | A:CDN |
| PingFang 苹方 | 6 | macOS/iOS 系统首选 | 系统 |
| HarmonyOS Sans | 9 | 鸿蒙生态；字重最丰富之一；有 OSS 切片可加载 | B:OSS |
| 阿里巴巴普惠体 | 5 | 商务、阿里系产品；有 OSS 切片可加载 | B:OSS |
| OPPO Sans | 5 | 移动端、ColorOS 生态；有 OSS 切片可加载 | B:OSS |
| BIZ UD Gothic | 2 | 日系气质；⚠ CJK 以 JIS 为主，简体部分字符 fallback | A:CDN |
| 方正兰亭黑（家族） | 6+ | 出版排版经典选择 | C:仅参考 |
| 汉仪旗黑 | 12 | 字重最丰富，商业项目 | C:仅参考 |
| 创客贴金刚体 | 1 | 强工业感标题；有 OSS 切片可加载 | B:OSS |
| 字体传奇特战体 | 1 | 极强工业/锐角，仅标题 | B:OSS切片 |
| 站酷酷黑 | 1 | 硬朗标题 | B:OSS切片 |
| 标小智无界黑 | 1 | 现代/无界感标题；有 OSS 切片可加载 | B:OSS |

**提示**：工业/科技不等于一律超黑粗体；信息密度高时强字体只用于主标题或关键数字。故障、特战类强烈改变气质，适合海报/发布页，不适合后台和长文。

### 表 B：文学 / 古典 / 优雅 / 感性

**关键词**：文学 · 古典 · 优雅 · 感性 · 文化 · 新中式 · 情绪 · 抒情 · 编辑 · 出版 · 杂志

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 思源宋体 Source Han Serif | 6 | 通用稳妥首选，可正文可标题 | A:CDN |
| BIZ UD Mincho | 2 | 现代明朝、易读性强；⚠ JIS 为主、简体部分字符 fallback | A:CDN |
| 方正书宋 | 多 | 经典书宋，温和 | C:仅参考 |
| 方正雅宋 / 准雅宋 | 多 | 现代宋代表 | C:仅参考 |
| 汉仪玄宋 | 5 | 偏现代，字面率小、留白多 | C:仅参考 |
| 汉仪书宋 | 多 | 经典书宋 | C:仅参考 |
| 霞鹜致宋 | 1 | 文化气质标题 | B:OSS切片 |
| 飞花宋体 / 一点明体 / 京华老宋体 | 1 | 文学气质标题；飞花宋体、一点明体有 OSS 切片，京华老宋体仅参考 | B:OSS切片 / C:仅参考 |
| 瀞之故障明朝 | 1 | 故障感文学标题 | C:仅参考 |
| 新愚公沧桑体 | 1 | 沧桑/感性文学标题；有 OSS 切片可加载 | B:OSS |
| ORADANO 明朝体 | 1 | 古典明朝感标题；有 OSS 切片可加载 | B:OSS |

**提示**：这类字体适合建立气韵，不适合密集 UI 和数据系统。文化感不能只靠字体——同时控制字距、行高、段落灰度。

### 表 C：古籍 / 文言 / 引文 / 对话文

**关键词**：古籍 · 文言 · 诗词 · 引文 · 对话 · 剧本 · 书卷 · 传统文化 · 楷书气质

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 霞鹜文楷 LXGW WenKai | 3 | 现代书卷感（清刻本风），古籍今译/文言/教科书 | A:CDN |
| 寒蝉正楷体 | 1 | 楷体引文 | B:OSS切片 |
| 演示春风楷 | 1 | 装饰性楷体标题 | B:OSS切片 |
| 初夏明朝体 / 源流明体 | 多字重 | 明朝体文学标题/引文 | B:OSS切片 |
| 润植家如印奏章楷 | 1 | 古意标题 | C:仅参考 |
| 梦源宋体 | 多 | 现代宋体替代 | C:仅参考 |
| 江西拙楷 | 1 | 拙朴楷体 | B:OSS切片 |
| 仓耳今楷 | 多 | 严谨可读楷体，教育/儿童 | C:仅参考 |
| Kaiti SC（macOS） | 1 | 系统楷，标题、引文 | 系统 |
| 方正楷体 GBK | 1 | 大陆常见楷，标题/引文 | C:仅参考 |

**提示**：楷、明、仿宋类适合营造文气，但不要默认用于长篇屏幕正文。对话文优先保证人名、冒号、引号和行距清楚。古籍/文言场景同时检查标点、断句、直排/横排和字距。

### 表 D：公文 / 规范（大陆）

**关键词**：公文 · 党政机关 · 通知 · 制度文件 · 正式规范 · 红头文件

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 方正小标宋简体 | 1 | 公文一级标题 | C:仅参考 |
| 仿宋 GB2312 | 1 | 公文正文（16pt） | C:仅参考 |
| 黑体（系统/方正） | 多 | 公文小标题（16pt） | 系统/C |
| 楷体 GB2312 | 1 | 公文签发说明（16pt） | C:仅参考 |

**提示**：公文场景不要自由发挥；优先遵守用户或机构提供的格式规范。公文字体方案不要迁移到普通网页、海报或产品 UI。

### 表 E：公文 / 教科书（台湾）

**关键词**：台湾公文 · 台湾教科书 · 繁体正式 · 楷書教育

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 中文采楷書 | 1 | 台湾公文/教材标准 | C:仅参考 |
| 华康楷体 | 多 | 台湾公文/教科书 | C:仅参考 |
| 文鼎楷体 | 多 | 同上 | C:仅参考 |
| 文鼎 PMingLiu 明朝体 | 1 | 繁体经典正文 | 系统 |

**提示**：台湾公文/教科书不要套用大陆公文的仿宋方案。双语材料注意中文楷书与西文（如 Times New Roman）的行高、基线和字号协调。

### 表 F：学术 / 严谨 / 出版

**关键词**：学术 · 严谨 · 论文 · 白皮书 · 研究报告 · 出版 · 正式 · 可信

**通用稳妥搭配**：思源宋体（正文）+ 思源黑体（标题），或 方正书宋 + 方正兰亭黑。

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 思源宋体 | 6 | 正文首选 | A:CDN |
| 思源黑体 | 7 | 标题首选 | A:CDN |
| 狮尾四季春 | 多字重 | 学术、严谨、出版标题；繁中/宋体气质 | B:OSS切片 |
| 思源赢宋 | 1 | 学术报告标题；有 OSS 切片可加载 | B:OSS |
| 朱雀仿宋 | 1 | 仿宋正文（特定语境） | B:OSS切片 |
| 字体圈欣意吉祥宋 | 1 | 严谨宋体 | B:OSS切片 |

**提示**：严谨场景优先可读性和可信度，不使用过强装饰字。仿宋适合公文/制度/正式文本气质，不要滥用于现代产品页正文。

### 表 G：标题 / 海报 / 大字号

**关键词**：标题 · 海报 · 封面 · 主视觉 · 标语 · 小红书封面 · 活动页 · 大字号 · 显眼

| 字体 | 字重数 | 用途/提示 | 加载 |
|---|---|---|---|
| 得意黑 Smiley Sans | 1 | 倾斜现代标题 | A:CDN |
| 钉钉进步体 | 1 | 现代品牌标题 | A:CDN / B:OSS切片 |
| 抖音美好体 DouyinSans | 1 | 抖音生态、活泼现代；有 OSS 切片可加载 | B:OSS |
| 阿里妈妈数黑体 | 1 | 营销标题、强冲击 | B:OSS切片 |
| 思源黑体 Heavy | 1 | 通用稳妥重标题 | A:CDN |
| 庞门正道标题体 | 1 | 标语、口号；有 OSS 切片可加载 | B:OSS |
| 文悦古典明朝 | 1 | 古风/复古标题 | C:仅参考 |
| 汉仪铸字尚黑 / 悦圆 | 多 | 现代品牌 | C:仅参考 |
| 优设标题黑 | 1 | 通用标题 | B:OSS切片 |
| 追光斗鱼体 / 一品启航体 / 快看世界体 | 1 | 强气质标题；一品启航体、快看世界体有 OSS 切片，追光斗鱼体仅参考 | B:OSS切片 / C:仅参考 |
| 字魂扁桃体 / 仓迹高德国妙黑 / Leefont 蒙黑体 | 1 | 装饰性标题；均有 OSS 切片 | B:OSS切片 |
| 淘宝买菜体 / 汤宪滨宋 / 荆南俊俊体 | 1 | 强气质标题；荆南俊俊体有 OSS 切片，淘宝买菜体/汤宪滨宋仅参考 | B:OSS切片 / C:仅参考 |

**提示**：标题/海报字体可以更强，但必须服务主题，不要只为"显眼"。小红书、海报、活动页可以用；B2B SaaS、后台、研究报告慎用。标题很长时优先处理断行和层级，再决定是否用强展示字体。

### 1.4 家族搭配范式（选完气质字体后，定正文+标题搭配）

### 范式 A：单家族，多字重（极简，推荐入门）
- 思源黑体 Light（正文）
- 思源黑体 Medium（小标题）
- 思源黑体 Bold（大标题）

### 范式 B：宋 + 黑 经典搭配
- 思源宋体 Regular（正文）
- 思源黑体 Medium（标题、图注、CTA 按钮）

### 范式 C：标题大字宋，正文黑（出版风）
- 方正准雅宋 Bold（大标题）
- 方正兰亭黑 Light（正文）

### 范式 D：同家族多字重 + 共同模数
- 方正兰亭准黑 GBK 12pt（小标题）
- 方正兰亭纤黑 GBK 9pt（正文）
- 方正细黑一 GBK 6pt（图注）
- 同模数（1.5pt）下三个字号通过家族字重协同

### 范式 E：宋 + 楷（古典 / 文学）
- 方正书宋 Regular 10.5pt（正文）
- 霞鹜文楷 Medium 14pt（标题、引文）
- 适合：古诗集、文学随笔、传统文化项目

### 范式 F：大陆公文专用方案
- 方正小标宋简体（标题候选）
- 仿宋 GB2312（16pt，正文候选）
- 黑体（16pt，层级/小标题候选）
- 楷体 GB2312（16pt，特定说明/签发类文本候选）
- 只用于大陆公文、通知、制度等正式文书，不迁移到普通网页/海报/UI。

### 范式 G：台湾公文 / 教科书专用方案
- 中文采楷書（中文正文/教材候选）
- Times New Roman（西文候选）
- 注意中文楷书与西文衬线的基线、行高和字号协调。

### 1.5 中英文混排

中英混排时，目标不是“谁排在 font-family 第一”，而是：
- 中文标点、破折号、省略号不能被西文字体接管；
- 英文单词、数字可以有更好的 Latin 字体表现；
- 行高、基线和视觉重量要协调。

| 中文字体 | 可搭配西文 | 备注 |
|---|---|---|
| 思源黑体 | Source Sans Pro / Inter | 技术、SaaS、报告 |
| PingFang | San Francisco | macOS / iOS 原生匹配 |
| MiSans | MiSans Latin | 同家族，行高匹配好 |
| HarmonyOS Sans | HarmonyOS Sans Latin | 同家族 |
| 思源宋体 | Source Serif Pro | 报告、编辑、出版感 |
| 方正书宋 | Times / Georgia | 经典宋 + 经典衬线 |
| 微软雅黑 | Segoe UI | Windows 环境 |
| 霞鹜文楷 | Crimson Pro | 文楷 + 现代衬线 |
| 方正仿宋 | EB Garamond / Crimson | 公文/古典感 |

#### 安全默认：中文字体在前

通用中文页面、H5、卡片和报告正文，默认用中文字体在前，保护中文标点：

```css
font-family: "PingFang SC", "HarmonyOS Sans SC", "Noto Sans CJK SC",
             "Microsoft YaHei UI", "Microsoft YaHei",
             system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
```

#### 需要 Latin 优先时，不要直接把 Inter 放到 body 第一位

如果把 `Inter`、`Helvetica` 放到 body 第一位，破折号、引号、省略号等共享码位字符可能被西文字体抢走，导致下沉、断开或视觉不一致。

更稳的做法：

```css
@font-face {
  font-family: "Inter Local";
  src: local("Inter");
  unicode-range: U+0000-007F;
}
body {
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.latin {
  font-family: "Inter Local", Inter, system-ui, sans-serif;
}
```

也可以只对英文标题、数字、代码、标签使用 Latin class，不要让它接管中文正文标点。

### 1.6 可变字体（Variable Font）

新一代字体支持轴向调节，适合屏幕：
- 思源黑体 Variable（GitHub）
- 鸿蒙 HarmonyOS Sans Variable
- **MiSans VF**（小米官网，权重轴）
- Inter Variable

CSS：
```css
font-family: "Source Han Sans VF";
font-variation-settings: "wght" 450;
```

变体字重让设计响应屏幕尺寸（小屏用粗，大屏用细）。

## 二、加载执行（选定字体后）

### 2.1 三种加载情境，分清楚再写

| 字体类型 | 加载方式 | 示例 |
|---|---|---|
| **A. 公共 CDN 可达** | 直接 `<link>` 引 CDN（Google Fonts / jsDelivr 等自带子集化机制，浏览器自动按需下载） | 思源黑/宋、Noto SC、霞鹜文楷、得意黑、Source Sans 3 等 |
| **B. OSS 切片 / 自托管切片** | 用生成 CSS 的 `@font-face` 引 woff2 切片 + `unicode-range`；`ext` 兜底放最后 | 当前已上传 OSS 切片的展示字体、找不到公共 CDN 但有自托管切片的字体 |
| **C. 完全无加载方案** | 不要写进 `font-family`——仅用作气质参考 | § 2 候选清单中未标 `✓可加载`、且 § 6 无 CDN/无OSS切片的字体 |

### 2.2 B 类OSS切片：标准方案

当前 OSS 切片字体采用 **高频优先 CSS**：先加载高频汉字切片，再加载标点、拉丁，最后用扩展切片兜底。

参考 CSS 结构：

```text
@font-face common-hi  → 高频汉字，使用精确 unicode-range 列表
@font-face punct      → CJK 符号 + 通用标点 + 全角 ASCII
@font-face latin      → 基本拉丁 + 拉丁补充 + 常用标点
@font-face ext        → 兜底剩余字符，放最后
```

切片说明：

| 切片名 | 推荐写法 | 覆盖 |
|---|---|---|
| `common-hi` | 使用生成 CSS 里的精确高频汉字 `unicode-range`，不要简化成整段 `U+4E00-9FFF` | 高频/常用中文，优先用于标题、封面和常见正文测试 |
| `punct` | `U+3000-303F, U+2000-206F, U+FF00-FFEF` | CJK 符号标点、通用标点、全角 ASCII |
| `latin` | `U+0020-007E, U+00A0-00FF, U+2010-2027` | 基本拉丁、拉丁补充、常用标点 |
| `ext` | `U+0-10FFFF`，必须放在最后 | 兜底剩余字符，含低频汉字、生僻字和未覆盖字符 |

为什么 `common-hi` 不直接写 `U+4E00-9FFF`：

- `U+4E00-9FFF` 会让 common 切片承担整个 CJK 统一汉字区，失去“高频优先”的意义。
- 生成 CSS 里的 `common-hi` 已经把常用 2500 汉字压成精确范围，浏览器只在页面出现这些字时下载高频切片。
- 低频字交给最后的 `ext` 兜底，避免首屏强行加载过大的完整中文切片。

**当前OSS 切片链接**：直接使用 § 1.4 的已上传 URL，不再套 `{oss-host}` 占位。

**Paste-ready `@font-face` 模板**（从 § 1.4 复制某个字体/字重的 4 个 URL；`common-hi` 的 `unicode-range` 从对应生成 CSS 复制）：

```css
/* 高频汉字：不要简化为 U+4E00-9FFF；复制生成 CSS 里的精确范围 */
@font-face {
  font-family: "{字体显示名}";
  src: url("{common-hi-url}") format("woff2");
  unicode-range:
    /* paste generated common-hi unicode-range here */;
  font-display: swap;
}

/* CJK 符号 + 通用标点 + 全角 ASCII */
@font-face {
  font-family: "{字体显示名}";
  src: url("{punct-url}") format("woff2");
  unicode-range: U+3000-303F, U+2000-206F, U+FF00-FFEF;
  font-display: swap;
}

/* 基本拉丁 + 拉丁补充 + 常用标点 */
@font-face {
  font-family: "{字体显示名}";
  src: url("{latin-url}") format("woff2");
  unicode-range: U+0020-007E, U+00A0-00FF, U+2010-2027;
  font-display: swap;
}

/* 兜底：剩余字符。必须放最后 */
@font-face {
  font-family: "{字体显示名}";
  src: url("{ext-url}") format("woff2");
  unicode-range: U+0-10FFFF;
  font-display: swap;
}
```

使用注意：

- `common-hi`、`punct`、`latin`、`ext` 的顺序不要乱；`ext` 必须最后。
- 如果没有对应字体的生成 CSS，临时预览可以用 § 1.4 的 URL + 简化范围，但不能当成正式加载方案。
- 若用户只做短标题/社媒卡片，通常只会命中 `common-hi`、`punct`、少量 `latin`；长文和生僻字才会触发 `ext`。
- 生产环境仍需确认授权、缓存策略、CORS、文件体积和实际命中字符。

**机制说明**：浏览器根据页面实际字符与 `unicode-range` 匹配下载字体切片。高频汉字先命中 `common-hi`，标点命中 `punct`，英文/数字命中 `latin`，其余字符由最后的 `ext` 兜底。

### 2.3 当前已上传 OSS 字体切片 URL 表

本节是字体加载查表，放在 `fonts.md` 内，避免运行时再跳到第三个文件。

使用顺序：

1. 先按 § 2 完成“用户意图 → 场景类别 → 字体筛选”。
2. 如果选中 `B:OSS切片` 字体，再回到本节查对应 `font-family`、`font-weight` 和 4 个切片 URL。
3. 把 URL 填入 § 1.2 的 `@font-face` 模板。
4. 多字重家族必须写 `font-weight`，不要把所有切片都声明成 `normal`。
5. `common-hi` 的精确 `unicode-range` 仍应从对应生成 CSS 复制；没有生成 CSS 时只能临时测试。

不要从本节直接挑字体。本节只负责“已选字体如何加载”。

#### 字体家族概要

| font_examples | css_family | font_weights | scene | count |
| --- | --- | --- | --- | --- |
| 寒蝉正楷体 | `"ChillKai"` | 400 | 古籍 / 文言 / 引文 / 对话文 | 1 |
| 演示春风楷 | `"Slide Chunfeng Kai"` | 400 | 古籍 / 文言 / 引文 / 对话文，楷体标题 | 1 |
| 江西拙楷 | `"Jiangxi ZhuoKai"` | 400 | 古籍 / 文言 / 拙朴楷体 | 1 |
| 朱雀仿宋 | `"Zhuque Fangsong"` | 400 | 学术 / 严谨 / 仿宋语境 | 1 |
| 思源赢宋 | `"CorpSrcWinSong Slim"` | 400 | 学术 / 严谨 / 出版标题 | 1 |
| 阿里巴巴普惠体 | `"Alibaba PuHuiTi 3.0"` | 400 | 现代 / 商务 / 阿里系 | https://fileup.chatglm.cn/chatglm-operation/AlibabaPuHuiTi-3-55-Regular/file/a0/a055f93b5d | https://fileup.chatglm.cn/chatglm-operation/AlibabaPuHuiTi-3-55-Regular/file/89/8988f0ce3a | https://fileup.chatglm.cn/chatglm-operation/AlibabaPuHuiTi-3-55-Regular/file/54/54bcd7c6b7 | https://fileup.chatglm.cn/chatglm-operation/AlibabaPuHuiTi-3-55-Regular/file/98/98f1a2b7c1 | upload batch 3 |
| 抖音美好体 DouyinSans | `"Douyin Sans"` | 400 | 标题 / 海报 / 活泼现代 | https://fileup.chatglm.cn/chatglm-operation/DouyinMeiHaoTi/file/30/30da93e844 | https://fileup.chatglm.cn/chatglm-operation/DouyinMeiHaoTi/file/3b/3b171d2f15 | https://fileup.chatglm.cn/chatglm-operation/DouyinMeiHaoTi/file/a3/a380b67b0f | https://fileup.chatglm.cn/chatglm-operation/DouyinMeiHaoTi/file/44/449109fb5c | upload batch 3 |
| HarmonyOS Sans SC (Thin) | `"HarmonyOS Sans SC"` | 100 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Thin/file/00/00540c8656 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Thin/file/d1/d1f7d77c1e | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Thin/file/df/df02b19609 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Thin/file/37/37c8413537 | upload batch 3 |
| HarmonyOS Sans SC (Light) | `"HarmonyOS Sans SC"` | 300 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Light/file/29/29bf93d0c0 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Light/file/20/20282efc71 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Light/file/8e/8edf18df66 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Light/file/3c/3c72b5376c | upload batch 3 |
| HarmonyOS Sans SC (Regular) | `"HarmonyOS Sans SC"` | 400 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Regular/file/01/01c1e63b4b | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Regular/file/60/600b67ec1f | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Regular/file/01/01a87f4cf2 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Regular/file/b8/b864f26ac4 | upload batch 3 |
| HarmonyOS Sans SC (Medium) | `"HarmonyOS Sans SC"` | 500 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Medium/file/3a/3a02b63f25 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Medium/file/7c/7c75e18d44 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Medium/file/31/3147c5bf0e | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Medium/file/c7/c70bc7fcd3 | upload batch 3 |
| HarmonyOS Sans SC (Bold) | `"HarmonyOS Sans SC"` | 700 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Bold/file/7c/7cae48675b | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Bold/file/40/40cfd77cc2 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Bold/file/3f/3f31fa480d | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Bold/file/26/26a9ef75a3 | upload batch 3 |
| HarmonyOS Sans SC (Black) | `"HarmonyOS Sans SC"` | 900 | 现代 / 工业 / 科技 / 鸿蒙生态 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Black/file/24/246d346cc6 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Black/file/70/70dad93690 | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Black/file/5f/5f6a76369a | https://fileup.chatglm.cn/chatglm-operation/HarmonyOS_Sans_SC_Black/file/2f/2f83a1c310 | upload batch 3 |
| OPPO Sans (Regular) | `"OPPO Sans"` | 400 | 现代 / 移动端 / ColorOS | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Regular/file/43/43f018edfb | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Regular/file/2d/2dfba362f9 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Regular/file/d0/d075041026 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Regular/file/a2/a2375f3414 | upload batch 3 |
| OPPO Sans (Medium) | `"OPPO Sans"` | 500 | 现代 / 移动端 / ColorOS | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Medium/file/a0/a0eba90561 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Medium/file/7b/7b241f2dad | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Medium/file/b5/b55f3cb429 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Medium/file/e3/e3bf64883a | upload batch 3 |
| OPPO Sans (Bold) | `"OPPO Sans"` | 700 | 现代 / 移动端 / ColorOS | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Bold/file/49/496c8f2d63 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Bold/file/c3/c332d5e576 | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Bold/file/bf/bfeea08fdc | https://fileup.chatglm.cn/chatglm-operation/OPPOSans-Bold/file/e3/e36dd64024 | upload batch 3 |
| 狮尾四季春 Black / 狮尾四季春 Bold / 狮尾四季春 ExtraLight | `"Swei Spring CJK TC"` | 200, 700, 900 | 学术 / 严谨 / 出版，繁中/宋体标题 | 3 |
| 字体圈欣意吉祥宋 | `"XinYi JiXiang Song"` | 400 | 学术 / 严谨 / 宋体标题 | 1 |
| 初夏明朝体 Bold / 初夏明朝体 ExtraLight / 初夏明朝体 Heavy … | `"Early Summer Serif"` | 200, 300, 400, 500, 600, 700, 900 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | 7 |
| 狮尾四季春糖 ExtraLight / 狮尾四季春糖 Light / 狮尾四季春糖 Medium … | `"Swei Spring Sugar CJK TC"` | 200, 300, 400, 500 | 文学 / 古典 / 优雅 / 感性，柔和宋体 | 4 |
| 源流明体 Bold / 源流明体 ExtraLight / 源流明体 Heavy … | `"GenRyuMin JP"` | 200, 300, 400, 500, 600, 700, 900 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | 7 |
| ORADANO 明朝体 | `"ORADANO Mincho"` | 400 | 文学 / 古典 / 感性标题 | 1 |
| 新愚公沧桑体 | `"XinYuGong CangSang Ti"` | 400 | 文学 / 古典 / 感性标题 | 1 |
| 霞鹜致宋 | `"LXGW ZhiSong"` | 400 | 文学 / 古典 / 感性标题 | 1 |
| 飞花宋体 | `"Feihua Song"` | 400 | 文学 / 古典 / 感性标题 | 1 |
| 一点明体 | `"I.Ming"` | 400 | 文学 / 古典 / 明朝体标题 | 1 |
| 润植家康熙字典美化体 | `"RunZhiJia KangXi"` | 400 | 文学 / 古籍 / 传统标题 | 1 |
| 润植家康熙字典美化体 清瘦款 | `"RunZhiJia KangXi Slim"` | 400 | 文学 / 古籍 / 传统标题 | 1 |
| 一品启航体 | `"YiPin QiHang Ti"` | 400 | 标题 / 海报 | 1 |
| 快看世界体 | `"Kuaikan Shijie Ti"` | 400 | 标题 / 海报 / 年轻内容 | 1 |
| Leefont 蒙黑体 | `"Leefont MengHei"` | 400 | 标题 / 海报 / 强气质标题 | 1 |
| 仓迹高德国妙黑 | `"Cangji Gaode Guomiao Hei"` | 400 | 标题 / 海报 / 强气质标题 | 1 |
| 荆南俊俊体 | `"JingNan JunJunTi"` | 400 | 标题 / 海报 / 强气质标题 | 1 |
| 庞门正道标题体 | `"PangMenZhengDao Title"` | 400 | 标题 / 海报 / 标语口号 | 1 |
| 钉钉进步体 | `"DingTalk JinBuTi"` | 400 | 标题 / 海报 / 现代品牌 | 1 |
| 阿里妈妈数黑体 | `"Alimama ShuHeiTi"` | 400 | 标题 / 海报 / 营销 / 产品发布 | 1 |
| 字魂扁桃体 | `"ZiHun BianTao Ti"` | 400 | 标题 / 海报 / 装饰标题 | 1 |
| 优设标题黑 | `"YouShe Title Black"` | 400 | 标题 / 海报 / 通用重标题 | 1 |
| 字体传奇特战体 | `"ZiTiChuanQi TeZhan Ti"` | 400 | 现代 / 工业 / 特战锐角标题 | 1 |
| Blix Bold / Blix ExtraLight / Blix Light … | `"Blix"` | 100, 200, 300, 400, 500, 600, 700 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | 7 |
| Blix Text | `"Blix Text"` | 400 | 现代 / 工业 / 科技 / 商务，多字重正文/标题测试 | 1 |
| 乡立方黑体 | `"XiangLiFang HeiTi"` | 400 | 现代 / 工业 / 科技标题 | 1 |
| 创客贴金刚体 | `"Chuangkit KingKong"` | 400 | 现代 / 工业 / 科技标题 | 1 |
| 德拉黑体 | `"Dela Gothic One"` | 400 | 现代 / 工业 / 科技标题 | 1 |
| 标小智无界黑 | `"BiaoXiaoZhi WuJie Hei"` | 400 | 现代 / 工业 / 科技标题 | 1 |
| 站酷酷黑体 | `"ZCOOL KuHei"` | 400 | 现代 / 工业 / 科技标题 | 1 |
| Plix 普利士 Bold / Plix 普利士 ExtraLight / Plix 普利士 Light … | `"Plix"` | 100, 200, 300, 400, 500, 600, 700 | 现代 / 工业 / 科技，多字重标题/产品发布 | 7 |
| Plix 普利士 Text | `"Plix Text"` | 400 | 现代 / 工业 / 科技，多字重正文/标题测试 | 1 |
| 联盟起艺卢帅正锐黑体 | `"Lushuai Zhengrui Hei"` | 400 | 现代 / 工业 / 锐利标题 | 1 |

#### URL 查表

| font | css_family | font_weight | scene | common_hi | latin | punct | ext | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORADANO 明朝体 | `"ORADANO Mincho"` | 400 | 文学 / 古典 / 感性标题 | `https://fileup.chatglm.cn/chatglm-operation/OradanoGSRR/file/cf/cfca08647b` | `https://fileup.chatglm.cn/chatglm-operation/OradanoGSRR/file/96/9669e6fafc` | `https://fileup.chatglm.cn/chatglm-operation/OradanoGSRR/file/2e/2e080147a0` | `https://fileup.chatglm.cn/chatglm-operation/OradanoGSRR/file/77/7785a5869e` | previous fonts.md |
| 一品启航体 | `"YiPin QiHang Ti"` | 400 | 标题 / 海报 | `https://fileup.chatglm.cn/chatglm-operation/一品启航体/file/76/76e29dad38` | `https://fileup.chatglm.cn/chatglm-operation/一品启航体/file/55/55e3ca4732` | `https://fileup.chatglm.cn/chatglm-operation/一品启航体/file/be/be931f15f9` | `https://fileup.chatglm.cn/chatglm-operation/一品启航体/file/7f/7f1a985296` | previous fonts.md |
| 一点明体 | `"I.Ming"` | 400 | 文学 / 古典 / 明朝体标题 | `https://fileup.chatglm.cn/chatglm-operation/I.Ming-7.00/file/07/07ffdc1adc` | `https://fileup.chatglm.cn/chatglm-operation/I.Ming-7.00/file/f1/f1d05f12d2` | `https://fileup.chatglm.cn/chatglm-operation/I.Ming-7.00/file/0a/0a40bb960b` | `https://fileup.chatglm.cn/chatglm-operation/I.Ming-7.00/file/8a/8a0b4c63be` | previous fonts.md |
| 乡立方黑体 | `"XiangLiFang HeiTi"` | 400 | 现代 / 工业 / 科技标题 | `https://fileup.chatglm.cn/chatglm-operation/乡立方黑体/file/56/56aba77493` | `https://fileup.chatglm.cn/chatglm-operation/乡立方黑体/file/5a/5ab39ea07b` | `https://fileup.chatglm.cn/chatglm-operation/乡立方黑体/file/0c/0cff80e0d0` | `https://fileup.chatglm.cn/chatglm-operation/乡立方黑体/file/91/91c932c78e` | previous fonts.md |
| 字体传奇特战体 | `"ZiTiChuanQi TeZhan Ti"` | 400 | 现代 / 工业 / 特战锐角标题 | `https://fileup.chatglm.cn/chatglm-operation/字体传奇特战体/file/de/de9cb81c4c` | `https://fileup.chatglm.cn/chatglm-operation/字体传奇特战体/file/36/36f5e042e9` | `https://fileup.chatglm.cn/chatglm-operation/字体传奇特战体/file/65/651d795fc4` | `https://fileup.chatglm.cn/chatglm-operation/字体传奇特战体/file/11/11548cd4b7` | previous fonts.md |
| 字体圈欣意吉祥宋 | `"XinYi JiXiang Song"` | 400 | 学术 / 严谨 / 宋体标题 | `https://fileup.chatglm.cn/chatglm-operation/字体圈欣意吉祥宋/file/c9/c9dddef6e8` | `https://fileup.chatglm.cn/chatglm-operation/字体圈欣意吉祥宋/file/af/aff9039041` | `https://fileup.chatglm.cn/chatglm-operation/字体圈欣意吉祥宋/file/31/313d305e30` | `https://fileup.chatglm.cn/chatglm-operation/字体圈欣意吉祥宋/file/34/3486a908c2` | previous fonts.md |
| 字魂扁桃体 | `"ZiHun BianTao Ti"` | 400 | 标题 / 海报 / 装饰标题 | `https://fileup.chatglm.cn/chatglm-operation/字魂扁桃体/file/19/194181e6cb` | `https://fileup.chatglm.cn/chatglm-operation/字魂扁桃体/file/88/88cd111dd2` | `https://fileup.chatglm.cn/chatglm-operation/字魂扁桃体/file/01/01ccc9e7e1` | `https://fileup.chatglm.cn/chatglm-operation/字魂扁桃体/file/ca/caa5025441` | previous fonts.md |
| 寒蝉正楷体 | `"ChillKai"` | 400 | 古籍 / 文言 / 引文 / 对话文 | `https://fileup.chatglm.cn/chatglm-operation/ChillKai/file/eb/ebda4b10a4` | `https://fileup.chatglm.cn/chatglm-operation/ChillKai/file/44/440fb6ae60` | `https://fileup.chatglm.cn/chatglm-operation/ChillKai/file/9d/9dea0f4c28` | `https://fileup.chatglm.cn/chatglm-operation/ChillKai/file/c2/c2ee5f953f` | previous fonts.md |
| 庞门正道标题体 | `"PangMenZhengDao Title"` | 400 | 标题 / 海报 / 标语口号 | `https://fileup.chatglm.cn/chatglm-operation/PangMenZhengDaoBiaoTiTiMianFeiBan-2/file/5d/5d64a9bdcb` | `https://fileup.chatglm.cn/chatglm-operation/PangMenZhengDaoBiaoTiTiMianFeiBan-2/file/de/de6cbf790e` | `https://fileup.chatglm.cn/chatglm-operation/PangMenZhengDaoBiaoTiTiMianFeiBan-2/file/c4/c4600cb505` | `https://fileup.chatglm.cn/chatglm-operation/PangMenZhengDaoBiaoTiTiMianFeiBan-2/file/0b/0b92972246` | previous fonts.md |
| 德拉黑体 | `"Dela Gothic One"` | 400 | 现代 / 工业 / 科技标题 | `https://fileup.chatglm.cn/chatglm-operation/DelaGothicOne-Regular/file/18/1806c3702f` | `https://fileup.chatglm.cn/chatglm-operation/DelaGothicOne-Regular/file/79/79e72e7dc7` | `https://fileup.chatglm.cn/chatglm-operation/DelaGothicOne-Regular/file/01/011df6fd58` | `https://fileup.chatglm.cn/chatglm-operation/DelaGothicOne-Regular/file/e9/e9bc1db661` | previous fonts.md |
| 快看世界体 | `"Kuaikan Shijie Ti"` | 400 | 标题 / 海报 / 年轻内容 | `https://fileup.chatglm.cn/chatglm-operation/kuaikanshijieti/file/34/34f1113cd5` | `https://fileup.chatglm.cn/chatglm-operation/kuaikanshijieti/file/87/87aebfd38a` | `https://fileup.chatglm.cn/chatglm-operation/kuaikanshijieti/file/ed/ed4819ef67` | `https://fileup.chatglm.cn/chatglm-operation/kuaikanshijieti/file/19/190ff5cb5e` | previous fonts.md |
| 思源赢宋 | `"CorpSrcWinSong Slim"` | 400 | 学术 / 严谨 / 出版标题 | `https://fileup.chatglm.cn/chatglm-operation/CorpSrcWinSong-slim/file/2e/2e88d410e7` | `https://fileup.chatglm.cn/chatglm-operation/CorpSrcWinSong-slim/file/70/701fb6cf26` | `https://fileup.chatglm.cn/chatglm-operation/CorpSrcWinSong-slim/file/01/01d5854ec6` | `https://fileup.chatglm.cn/chatglm-operation/CorpSrcWinSong-slim/file/06/065e0e26bb` | previous fonts.md |
| 新愚公沧桑体 | `"XinYuGong CangSang Ti"` | 400 | 文学 / 古典 / 感性标题 | `https://fileup.chatglm.cn/chatglm-operation/新愚公沧桑体/file/4c/4cbdf91141` | `https://fileup.chatglm.cn/chatglm-operation/新愚公沧桑体/file/1b/1b9de889cf` | `https://fileup.chatglm.cn/chatglm-operation/新愚公沧桑体/file/d6/d67a6cf51b` | `https://fileup.chatglm.cn/chatglm-operation/新愚公沧桑体/file/df/dffb5f4b32` | previous fonts.md |
| 朱雀仿宋 | `"Zhuque Fangsong"` | 400 | 学术 / 严谨 / 仿宋语境 | `https://fileup.chatglm.cn/chatglm-operation/朱雀仿宋/file/73/739649f27b` | `https://fileup.chatglm.cn/chatglm-operation/朱雀仿宋/file/8b/8b0607dcf5` | `https://fileup.chatglm.cn/chatglm-operation/朱雀仿宋/file/f9/f9508b25a5` | `https://fileup.chatglm.cn/chatglm-operation/朱雀仿宋/file/34/349ba93dfa` | previous fonts.md |
| 江西拙楷 | `"Jiangxi ZhuoKai"` | 400 | 古籍 / 文言 / 拙朴楷体 | `https://fileup.chatglm.cn/chatglm-operation/江西拙楷2.0/file/30/30489bcd64` | `https://fileup.chatglm.cn/chatglm-operation/江西拙楷2.0/file/a5/a5576e755f` | `https://fileup.chatglm.cn/chatglm-operation/江西拙楷2.0/file/42/42ca2970b1` | `https://fileup.chatglm.cn/chatglm-operation/江西拙楷2.0/file/dd/ddbe3161a0` | previous fonts.md |
| 润植家康熙字典美化体 | `"RunZhiJia KangXi"` | 400 | 文学 / 古籍 / 传统标题 | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体/file/fe/fe7aa424c4` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体/file/ee/ee8b8f834b` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体/file/5b/5bdb2beb2a` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体/file/60/60b82d3143` | previous fonts.md |
| 润植家康熙字典美化体 清瘦款 | `"RunZhiJia KangXi Slim"` | 400 | 文学 / 古籍 / 传统标题 | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体-清瘦款/file/20/2099cd5e83` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体-清瘦款/file/5c/5cfb8dbdf6` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体-清瘦款/file/39/3964fcafc8` | `https://fileup.chatglm.cn/chatglm-operation/润植家康熙字典美化体-清瘦款/file/e6/e6c2d94792` | previous fonts.md |
| 站酷酷黑体 | `"ZCOOL KuHei"` | 400 | 现代 / 工业 / 科技标题 | `https://fileup.chatglm.cn/chatglm-operation/站酷酷黑体/file/ea/eadd08db72` | `https://fileup.chatglm.cn/chatglm-operation/站酷酷黑体/file/13/13dd379397` | `https://fileup.chatglm.cn/chatglm-operation/站酷酷黑体/file/4b/4bde15434e` | `https://fileup.chatglm.cn/chatglm-operation/站酷酷黑体/file/80/80b5c54b0d` | previous fonts.md |
| 联盟起艺卢帅正锐黑体 | `"Lushuai Zhengrui Hei"` | 400 | 现代 / 工业 / 锐利标题 | `https://fileup.chatglm.cn/chatglm-operation/联盟起艺卢帅正锐黑体/file/4f/4f37900ffc` | `https://fileup.chatglm.cn/chatglm-operation/联盟起艺卢帅正锐黑体/file/98/9840da1aeb` | `https://fileup.chatglm.cn/chatglm-operation/联盟起艺卢帅正锐黑体/file/70/70a1db7c91` | `https://fileup.chatglm.cn/chatglm-operation/联盟起艺卢帅正锐黑体/file/c2/c2af99b3fc` | previous fonts.md |
| 荆南俊俊体 | `"JingNan JunJunTi"` | 400 | 标题 / 海报 / 强气质标题 | `https://fileup.chatglm.cn/chatglm-operation/JingNanJunJunTi-JinNanJunJunTi-Bold-2/file/cb/cbb8549ae0` | `https://fileup.chatglm.cn/chatglm-operation/JingNanJunJunTi-JinNanJunJunTi-Bold-2/file/ab/abd1273106` | `https://fileup.chatglm.cn/chatglm-operation/JingNanJunJunTi-JinNanJunJunTi-Bold-2/file/f1/f13c84fb94` | `https://fileup.chatglm.cn/chatglm-operation/JingNanJunJunTi-JinNanJunJunTi-Bold-2/file/44/44a4205932` | previous fonts.md |
| 钉钉进步体 | `"DingTalk JinBuTi"` | 400 | 标题 / 海报 / 现代品牌 | `https://fileup.chatglm.cn/chatglm-operation/DingTalkJinBuTi-Regular/file/f7/f76dac6937` | `https://fileup.chatglm.cn/chatglm-operation/DingTalkJinBuTi-Regular/file/56/565cc41a96` | `https://fileup.chatglm.cn/chatglm-operation/DingTalkJinBuTi-Regular/file/ef/ef81576a19` | `https://fileup.chatglm.cn/chatglm-operation/DingTalkJinBuTi-Regular/file/84/84e1509a2c` | previous fonts.md |
| 阿里妈妈数黑体 | `"Alimama ShuHeiTi"` | 400 | 标题 / 海报 / 营销 / 产品发布 | `https://fileup.chatglm.cn/chatglm-operation/AlimamaShuHeiTi-Bold/file/cb/cbfb7e4458` | `https://fileup.chatglm.cn/chatglm-operation/AlimamaShuHeiTi-Bold/file/61/61711255c2` | `https://fileup.chatglm.cn/chatglm-operation/AlimamaShuHeiTi-Bold/file/9b/9b1d007c76` | `https://fileup.chatglm.cn/chatglm-operation/AlimamaShuHeiTi-Bold/file/c5/c51379dac8` | previous fonts.md |
| 飞花宋体 | `"Feihua Song"` | 400 | 文学 / 古典 / 感性标题 | `https://fileup.chatglm.cn/chatglm-operation/飞花宋体/file/f0/f0e72eccf3` | `https://fileup.chatglm.cn/chatglm-operation/飞花宋体/file/5b/5b11746893` | `https://fileup.chatglm.cn/chatglm-operation/飞花宋体/file/d2/d21c0e3479` | `https://fileup.chatglm.cn/chatglm-operation/飞花宋体/file/ea/ea8ab8cd6f` | previous fonts.md |
| Blix Bold | `"Blix"` | 700 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Bold/file/26/262abdf55d` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Bold/file/04/041fe34200` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Bold/file/a2/a249ce7687` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Bold/file/ae/aec610d95c` | fonts_upload_result2.csv |
| Blix ExtraLight | `"Blix"` | 200 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-ExtraLight/file/21/2193185438` | `https://fileup.chatglm.cn/chatglm-operation/Blix-ExtraLight/file/45/45edc00a9b` | `https://fileup.chatglm.cn/chatglm-operation/Blix-ExtraLight/file/9c/9cfecb9691` | `https://fileup.chatglm.cn/chatglm-operation/Blix-ExtraLight/file/ff/ffe53dfa43` | fonts_upload_result2.csv |
| Blix Light | `"Blix"` | 300 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Light/file/3f/3f0d54a8cb` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Light/file/f0/f04181a3ef` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Light/file/35/35033b633c` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Light/file/56/563ddfdb03` | fonts_upload_result2.csv |
| Blix Medium | `"Blix"` | 500 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Medium/file/2d/2de1e9a8ba` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Medium/file/b1/b1309f5393` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Medium/file/b7/b73c9a408a` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Medium/file/38/38887b9641` | fonts_upload_result2.csv |
| Blix Regular | `"Blix"` | 400 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Regular/file/5c/5cba7280ac` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Regular/file/26/26225968c9` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Regular/file/07/074ef94072` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Regular/file/29/299afaba9c` | fonts_upload_result2.csv |
| Blix SemiBold | `"Blix"` | 600 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-SemiBold/file/5e/5efb6f641f` | `https://fileup.chatglm.cn/chatglm-operation/Blix-SemiBold/file/dc/dc8a790bd9` | `https://fileup.chatglm.cn/chatglm-operation/Blix-SemiBold/file/2c/2c84409bd6` | `https://fileup.chatglm.cn/chatglm-operation/Blix-SemiBold/file/88/8851c60de7` | fonts_upload_result2.csv |
| Blix Text | `"Blix Text"` | 400 | 现代 / 工业 / 科技 / 商务，多字重正文/标题测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Text/file/0e/0e4aa0cd41` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Text/file/4a/4a4b2170ed` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Text/file/cd/cd0c4f3f0e` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Text/file/ed/ed3abc7940` | fonts_upload_result2.csv |
| Blix Thin | `"Blix"` | 100 | 现代 / 工业 / 科技 / 商务，多字重标题/界面测试 | `https://fileup.chatglm.cn/chatglm-operation/Blix-Thin/file/c5/c576803cdd` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Thin/file/66/665334cd4c` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Thin/file/ba/bad1b25e87` | `https://fileup.chatglm.cn/chatglm-operation/Blix-Thin/file/83/833afaf19e` | fonts_upload_result2.csv |
| 初夏明朝体 Bold | `"Early Summer Serif"` | 700 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Bold/file/9e/9e7a93c0d4` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Bold/file/ad/adfab8bd66` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Bold/file/1d/1d690160e4` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Bold/file/24/241fb12f1b` | fonts_upload_result2.csv |
| 初夏明朝体 ExtraLight | `"Early Summer Serif"` | 200 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-ExtraLight/file/cb/cb9f3dbb30` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-ExtraLight/file/11/1126df09ff` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-ExtraLight/file/a1/a15fd9a2be` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-ExtraLight/file/df/dfc81e40b7` | fonts_upload_result2.csv |
| 初夏明朝体 Heavy | `"Early Summer Serif"` | 900 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Heavy/file/bc/bcbd45c849` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Heavy/file/5a/5a7f10c952` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Heavy/file/2a/2a4268ce41` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Heavy/file/28/28f748319f` | fonts_upload_result2.csv |
| 初夏明朝体 Light | `"Early Summer Serif"` | 300 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Light/file/6d/6d80ac384b` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Light/file/81/81278898c7` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Light/file/19/19c59b5e10` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Light/file/f2/f254f3ee53` | fonts_upload_result2.csv |
| 初夏明朝体 Medium | `"Early Summer Serif"` | 500 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Medium/file/2d/2dd6de2b01` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Medium/file/60/60ada71088` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Medium/file/82/822f64e64e` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Medium/file/73/7335b8f693` | fonts_upload_result2.csv |
| 初夏明朝体 Regular | `"Early Summer Serif"` | 400 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Regular/file/ff/ff27654498` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Regular/file/36/36d455145e` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Regular/file/cf/cf9bea1ab5` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-Regular/file/90/9088bd3069` | fonts_upload_result2.csv |
| 初夏明朝体 SemiBold | `"Early Summer Serif"` | 600 | 文学 / 古典 / 优雅 / 感性，明朝体标题/短文 | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-SemiBold/file/63/6378c94799` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-SemiBold/file/8e/8eb81f0cd1` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-SemiBold/file/20/20aca09499` | `https://fileup.chatglm.cn/chatglm-operation/EarlySummerSerif-SemiBold/file/a1/a12ddfa661` | fonts_upload_result2.csv |
| 源流明体 Bold | `"GenRyuMin JP"` | 700 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Bold-2/file/c4/c4fca8acfc` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Bold-2/file/fd/fd97bd3c57` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Bold-2/file/ac/acb00d888a` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Bold-2/file/30/303e02361e` | fonts_upload_result2.csv |
| 源流明体 ExtraLight | `"GenRyuMin JP"` | 200 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-ExtraLight-3/file/8d/8d28bc4d1a` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-ExtraLight-3/file/58/586b40f864` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-ExtraLight-3/file/35/357938f213` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-ExtraLight-3/file/9c/9ca7d004e4` | fonts_upload_result2.csv |
| 源流明体 Heavy | `"GenRyuMin JP"` | 900 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Heavy-4/file/42/42ee49d982` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Heavy-4/file/5b/5bade94110` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Heavy-4/file/e4/e4a56d24bb` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Heavy-4/file/57/573abe53c5` | fonts_upload_result2.csv |
| 源流明体 Light | `"GenRyuMin JP"` | 300 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Light-5/file/7b/7b804e9f2e` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Light-5/file/a3/a3a78821ad` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Light-5/file/32/32bce1ed1e` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Light-5/file/b2/b22d1d9ad0` | fonts_upload_result2.csv |
| 源流明体 Medium | `"GenRyuMin JP"` | 500 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Medium-6/file/00/00d40483a8` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Medium-6/file/9e/9e7ed7bb98` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Medium-6/file/de/de1074fa56` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Medium-6/file/32/32863e2ca5` | fonts_upload_result2.csv |
| 源流明体 Regular | `"GenRyuMin JP"` | 400 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Regular-7/file/06/0615f8acbd` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Regular-7/file/11/11f8f60de4` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Regular-7/file/ee/ee6452c6e8` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-Regular-7/file/6c/6c84952724` | fonts_upload_result2.csv |
| 源流明体 SemiBold | `"GenRyuMin JP"` | 600 | 文学 / 古典 / 引文 / 明朝体；日系/传统气质 | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-SemiBold-8/file/fa/faa4062b63` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-SemiBold-8/file/c8/c8ad6ba144` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-SemiBold-8/file/2a/2a2430a174` | `https://fileup.chatglm.cn/chatglm-operation/GenRyuMinJP-SemiBold-8/file/86/862003923c` | fonts_upload_result2.csv |
| Leefont 蒙黑体 | `"Leefont MengHei"` | 400 | 标题 / 海报 / 强气质标题 | `https://fileup.chatglm.cn/chatglm-operation/Leefont蒙黑体/file/44/44fa456e39` | `https://fileup.chatglm.cn/chatglm-operation/Leefont蒙黑体/file/43/43d9dac7ed` | `https://fileup.chatglm.cn/chatglm-operation/Leefont蒙黑体/file/86/86d7fc1b56` | `https://fileup.chatglm.cn/chatglm-operation/Leefont蒙黑体/file/f1/f1bccaa444` | fonts_upload_result2.csv |
| Plix 普利士 Bold | `"Plix"` | 700 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Bold/file/20/20ab9b228b` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Bold/file/ff/ff5ad6c35c` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Bold/file/7f/7f266e9ab8` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Bold/file/72/72ea6eba65` | fonts_upload_result2.csv |
| Plix 普利士 ExtraLight | `"Plix"` | 200 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-ExtraLight/file/44/44ea3ad18c` | `https://fileup.chatglm.cn/chatglm-operation/Plix-ExtraLight/file/de/de382861e8` | `https://fileup.chatglm.cn/chatglm-operation/Plix-ExtraLight/file/4f/4f33b32eab` | `https://fileup.chatglm.cn/chatglm-operation/Plix-ExtraLight/file/25/253ac4035a` | fonts_upload_result2.csv |
| Plix 普利士 Light | `"Plix"` | 300 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Light/file/0a/0a41f59145` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Light/file/56/56ca45cd72` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Light/file/9e/9e0d314ed6` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Light/file/32/32fc493bde` | fonts_upload_result2.csv |
| Plix 普利士 Medium | `"Plix"` | 500 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Medium/file/99/99735c84dd` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Medium/file/f2/f2062f9763` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Medium/file/08/084584f23a` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Medium/file/3e/3e7d5e1613` | fonts_upload_result2.csv |
| Plix 普利士 Regular | `"Plix"` | 400 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Regular/file/30/30e51f7096` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Regular/file/bd/bd02f2a6aa` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Regular/file/4a/4a12aff53e` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Regular/file/36/36e4af189f` | fonts_upload_result2.csv |
| Plix 普利士 SemiBold | `"Plix"` | 600 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-SemiBold/file/53/534febe072` | `https://fileup.chatglm.cn/chatglm-operation/Plix-SemiBold/file/95/95c63a7834` | `https://fileup.chatglm.cn/chatglm-operation/Plix-SemiBold/file/9c/9c42ed77cb` | `https://fileup.chatglm.cn/chatglm-operation/Plix-SemiBold/file/70/706b68a842` | fonts_upload_result2.csv |
| Plix 普利士 Text | `"Plix Text"` | 400 | 现代 / 工业 / 科技，多字重正文/标题测试 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Text/file/f5/f5cae38ed5` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Text/file/be/bebc157f30` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Text/file/bc/bc36d5dc10` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Text/file/f1/f1a08dd5ab` | fonts_upload_result2.csv |
| Plix 普利士 Thin | `"Plix"` | 100 | 现代 / 工业 / 科技，多字重标题/产品发布 | `https://fileup.chatglm.cn/chatglm-operation/Plix-Thin/file/f5/f5b452a7e5` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Thin/file/27/27d434dbf5` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Thin/file/88/887ee1fc9c` | `https://fileup.chatglm.cn/chatglm-operation/Plix-Thin/file/b6/b6c12b4ab2` | fonts_upload_result2.csv |
| 演示春风楷 | `"Slide Chunfeng Kai"` | 400 | 古籍 / 文言 / 引文 / 对话文，楷体标题 | `https://fileup.chatglm.cn/chatglm-operation/Slidechunfeng-Regular/file/e7/e7a2a98669` | `https://fileup.chatglm.cn/chatglm-operation/Slidechunfeng-Regular/file/7e/7e76141d49` | `https://fileup.chatglm.cn/chatglm-operation/Slidechunfeng-Regular/file/95/95292e23a0` | `https://fileup.chatglm.cn/chatglm-operation/Slidechunfeng-Regular/file/c5/c5aaf20d76` | fonts_upload_result2.csv |
| 狮尾四季春 Black | `"Swei Spring CJK TC"` | 900 | 学术 / 严谨 / 出版，繁中/宋体标题 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Black/file/74/745f6a117b` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Black/file/b5/b59271fb3a` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Black/file/c0/c0798484ce` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Black/file/2e/2ec18b32e7` | fonts_upload_result2.csv |
| 狮尾四季春 Bold | `"Swei Spring CJK TC"` | 700 | 学术 / 严谨 / 出版，繁中/宋体标题 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Bold/file/2c/2c1e22d582` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Bold/file/f8/f81c815d41` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Bold/file/8f/8fbc87b012` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-Bold/file/46/46bdb3bcac` | fonts_upload_result2.csv |
| 狮尾四季春 ExtraLight | `"Swei Spring CJK TC"` | 200 | 学术 / 严谨 / 出版，繁中/宋体标题 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-ExtraLight/file/ea/eae48f5558` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-ExtraLight/file/34/342b7933b1` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-ExtraLight/file/3f/3f04f2cef8` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringCJKtc-ExtraLight/file/c9/c97f798620` | fonts_upload_result2.csv |
| 狮尾四季春糖 ExtraLight | `"Swei Spring Sugar CJK TC"` | 200 | 文学 / 古典 / 优雅 / 感性，柔和宋体 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-ExtraLight/file/9e/9e740cfb8a` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-ExtraLight/file/7f/7ff7baed53` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-ExtraLight/file/e7/e72980f785` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-ExtraLight/file/2e/2e43afce54` | fonts_upload_result2.csv |
| 狮尾四季春糖 Light | `"Swei Spring Sugar CJK TC"` | 300 | 文学 / 古典 / 优雅 / 感性，柔和宋体 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Light/file/fb/fb2ea95fbd` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Light/file/48/480090eeb1` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Light/file/37/37aa2e72a7` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Light/file/4e/4ef78056ed` | fonts_upload_result2.csv |
| 狮尾四季春糖 Medium | `"Swei Spring Sugar CJK TC"` | 500 | 文学 / 古典 / 优雅 / 感性，柔和宋体 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Medium/file/ff/ffc7d6cc4e` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Medium/file/c7/c7e930b33f` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Medium/file/4d/4d33bd4f85` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Medium/file/09/09c3f1e9ac` | fonts_upload_result2.csv |
| 狮尾四季春糖 Regular | `"Swei Spring Sugar CJK TC"` | 400 | 文学 / 古典 / 优雅 / 感性，柔和宋体 | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Regular/file/9b/9b45083ab4` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Regular/file/d1/d121306867` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Regular/file/00/002363c227` | `https://fileup.chatglm.cn/chatglm-operation/SweiSpringSugarCJKtc-Regular/file/a6/a6a6836ee9` | fonts_upload_result2.csv |
| 霞鹜致宋 | `"LXGW ZhiSong"` | 400 | 文学 / 古典 / 感性标题 | `https://fileup.chatglm.cn/chatglm-operation/xiawuzhisong/file/e3/e3ef8f1238` | `https://fileup.chatglm.cn/chatglm-operation/xiawuzhisong/file/c3/c3ffb778a6` | `https://fileup.chatglm.cn/chatglm-operation/xiawuzhisong/file/a9/a99e73508a` | `https://fileup.chatglm.cn/chatglm-operation/xiawuzhisong/file/94/94ba9251ce` | fonts_upload_result2.csv |
| 仓迹高德国妙黑 | `"Cangji Gaode Guomiao Hei"` | 400 | 标题 / 海报 / 强气质标题 | `https://fileup.chatglm.cn/chatglm-operation/仓迹高德国妙黑/file/54/546b95a0d0` | `https://fileup.chatglm.cn/chatglm-operation/仓迹高德国妙黑/file/7f/7f2986f888` | `https://fileup.chatglm.cn/chatglm-operation/仓迹高德国妙黑/file/74/748bbd6371` | `https://fileup.chatglm.cn/chatglm-operation/仓迹高德国妙黑/file/3f/3f52c4766f` | fonts_upload_result2.csv |
| 优设标题黑 | `"YouShe Title Black"` | 400 | 标题 / 海报 / 通用重标题 | `https://fileup.chatglm.cn/chatglm-operation/优设标题黑/file/24/24ecaa8f59` | `https://fileup.chatglm.cn/chatglm-operation/优设标题黑/file/93/930ab5a2bf` | `https://fileup.chatglm.cn/chatglm-operation/优设标题黑/file/87/8794e267e0` | `https://fileup.chatglm.cn/chatglm-operation/优设标题黑/file/90/90eab1b431` | fonts_upload_result2.csv |
| 创客贴金刚体 | `"Chuangkit KingKong"` | 400 | 现代 / 工业 / 科技标题 | `https://fileup.chatglm.cn/chatglm-operation/创客贴金刚体/file/95/95d2df8fbd` | `https://fileup.chatglm.cn/chatglm-operation/创客贴金刚体/file/fd/fd1829b5f1` | `https://fileup.chatglm.cn/chatglm-operation/创客贴金刚体/file/0f/0f474674d1` | `https://fileup.chatglm.cn/chatglm-operation/创客贴金刚体/file/1e/1ed6b8865c` | fonts_upload_result2.csv |
| 标小智无界黑 | `"BiaoXiaoZhi WuJie Hei"` | 400 | 现代 / 工业 / 科技标题 | `https://fileup.chatglm.cn/chatglm-operation/标小智无界黑/file/3c/3c8fed3f61` | `https://fileup.chatglm.cn/chatglm-operation/标小智无界黑/file/17/173c9801ef` | `https://fileup.chatglm.cn/chatglm-operation/标小智无界黑/file/7b/7b7b634392` | `https://fileup.chatglm.cn/chatglm-operation/标小智无界黑/file/14/1419fd9c1b` | fonts_upload_result2.csv |

### 2.4 备查：CDN / 系统字体加载方式

> 关键规则：在 `font-family` 里写了命名字体，就必须同时加载它（用 `<link>` 引 CDN，或用 `@font-face` 自托管）。
> 只写名字不加载 = 没用，浏览器会 fallback 成默认字体。拿不准就优先 A 类有公共 CDN 的字体。

#### 中文字体

| 字体 | 类型 | 加载方式 |
|---|---|---|
| 思源黑体 Source Han Sans SC | 黑 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-source-han-sans-sc-vf/font.css`；也可走自托管切片 → 见 § 1 |
| 思源宋体 Source Han Serif SC | 宋 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-source-han-serif-sc-vf/font.css`；也可走自托管切片 → 见 § 1 |
| Noto Sans SC | 黑 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-source-han-sans-sc-vf/font.css`（国内 jsDelivr，思源黑同源；原 Google：`Noto+Sans+SC`） |
| Noto Serif SC | 宋 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-source-han-serif-sc-vf/font.css`（国内 jsDelivr，思源宋同源；原 Google：`Noto+Serif+SC`） |
| 霞鹜文楷 LXGW WenKai | 楷 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-lxgw-wen-kai-screen-r/font.css`（国内 jsDelivr；原 Google：`fonts.googleapis.com/css2?family=LXGW+WenKai`） |
| 得意黑 Smiley Sans | 标题/黑 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-smiley-sans-oblique-regular/font.css` |
| 钉钉进步体 | 标题/黑 | A：`https://cdn.jsdelivr.net/npm/cn-fontsource-ding-talk-jin-bu-ti-regular/font.css`；B：OSS 切片 → 见 § 1.4 |
| BIZ UDGothic / UDMincho | 黑/宋（日文为主，简体部分字符会 fallback） | A：`https://fonts.googleapis.com/css2?family=BIZ+UDGothic`（或 `BIZ+UDMincho`）（Google CDN，国内加载可能慢；日文为主的边缘字体，按需使用） |
| MiSans | 黑 | A：`https://cdn.jsdelivr.net/npm/misans@4.1.0/lib/Normal/MiSans-Regular.min.css`（按字重换 Medium/Bold） |
| HarmonyOS Sans | 黑 | B:OSS；切片见 § 2.3（Thin–Black 全字重）|
| 阿里巴巴普惠体 | 黑 | B:OSS；切片见 § 2.3 |
| OPPO Sans | 黑 | B:OSS；切片见 § 2.3（Regular/Medium/Bold）|
| 抖音美好体 DouyinSans | 标题/黑 | B:OSS；切片见 § 2.3 |
| 阿里妈妈数黑体 | 标题/黑 | B：OSS 切片 → 见 § 1.4 |
| 其他已上传测试字体 | 标题/宋/楷/仿宋 | 见 § 1.4；仅用于标题、封面、海报、社媒卡片或特定测试，不默认用于正文 |

#### 拉丁/西文字体（中英混排时给 Latin 部分；比系统默认更有性格）

> 这些都不是系统字体，必须加载。**不要默认用 Inter**（AI 烂大街，见 `anti-ai-slop.md`）——优先下面这些。

| 字体 | 风格 | Web 加载 |
|---|---|---|
| Source Sans 3 | 无衬线，中性专业（思源黑的拉丁同源感） | `https://cdn.jsdelivr.net/npm/@fontsource/source-sans-3/index.css`（国内 jsDelivr） |
| Source Serif 4 | 衬线，编辑/出版感（配思源宋） | `https://cdn.jsdelivr.net/npm/@fontsource/source-serif-4/index.css`（国内 jsDelivr） |
| Crimson Pro | 衬线，文学/优雅 | `https://cdn.jsdelivr.net/npm/@fontsource/crimson-pro/index.css`（国内 jsDelivr） |
| EB Garamond | 衬线，古典/书卷 | `https://cdn.jsdelivr.net/npm/@fontsource/eb-garamond/index.css`（国内 jsDelivr） |

### 2.5 组装 font-family 栈（选字和落 CSS 之间的最后一步，最容易出错）

选完字体后，写 `font-family` 时最常见的错误是**漏掉 CJK 字体那一环**——比如选了「Inter 英文 + 系统中文」，却写成
`font-family: 'Inter', system-ui, sans-serif`，中文直接跳到 system-ui，渲染不可控。

**硬规则：任何含中文的页面，`font-family` 里必须显式出现一个 CJK 字体名。Latin 字体后面绝不能直接接 `system-ui`。**

按"中英是否用不同字体"分两种，直接照模板填：

```css
/* 情形 A：中英用同一字体 / 不特别指定英文字体 → CJK 字体在最前 */
font-family: '{CJK字体}', system-ui, sans-serif;
/* 例： */
font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;

/* 情形 B：中英用不同字体（指定了 Latin display 字体）→ Latin 在前，但 CJK 必须紧跟 */
font-family: '{Latin字体}', '{CJK字体}', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
/* 例： */
font-family: 'Inter', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
```

**反例（不要这样写）**：
```css
font-family: 'Inter', system-ui, sans-serif;   /* ✗ 中文 fallback 到 system-ui，不可控 */
font-family: 'Helvetica', 'PingFang SC';        /* ✗ 英文在前会抢走中文标点(破折号/引号下沉) */
```

**和"中文排英文前"铁律的关系**（两种策略，别混）：
- **情形 A（同字体）**：CJK 在前——这就是"中文排英文前"，避免英文字体抢走中文标点字形。
- **情形 B（分字体）**：Latin 在前但 CJK 必须紧跟——靠浏览器按字符 fallback，Latin 字体只渲染它有的拉丁字符，中文落到紧跟的 CJK 字体。这种情形若担心标点被 Latin 抢走，用 `unicode-range` 把 Latin 限定在拉丁码位：

```css
@font-face {
  font-family: "Inter Latin";
  src: local("Inter");
  unicode-range: U+0000-024F;   /* 只渲染拉丁，标点/中文留给 CJK */
}
body { font-family: "Inter Latin", "Noto Sans SC", "PingFang SC", system-ui, sans-serif; }
```

标点下沉/破折号问题详见 `punctuation.md` 破折号专题。

## 三、原则自检（选完字体后对照检查）

### 3.1 字面率（Face Ratio）选择结论

- **字面率约 95%**（思源黑、Noto Sans CJK、HarmonyOS Sans、MiSans、阿里普惠体等）：屏幕首选——大字面率在小字号下仍清晰。
- **字面率约 85%**（思源宋、霞鹜文楷、传统宋/楷）：印刷、长文阅读、文学/古籍气质首选——视觉松弛、易长时间阅读。
- **不要混搭悬殊字面率的字体**（如 95% 黑体 + 85% 宋体）做同等级标题/正文，视觉重量会断。

### 3.2 通用搭配原则

- 一个项目 ≤ 2 个字体家族；优先一家族多字重，靠粗细和字号拉层级。
- 同一设计最多 1 个强展示字体；正文回到高可读字体。
- 标题/海报字体强但必须服务主题，不要只为"显眼"。
- 候选清单的顺序不是优先级；按内容气质、可读性、媒介选择。

### 3.3 绝对避免

正文/严肃内容禁用：
- ❌ 华文彩云、华文琥珀、华文行楷
- ❌ 任何带阴影/3D/塑料质感的"特效字体"
- ❌ 装饰性毛笔字体（如造字工房悦圆系列做正文）
- ❌ 游戏字体（暗黑、星际等）做长文
- ❌ 楷体做现代长文正文（**儿童读物 / 教育例外**）—— 楷体笔画细易疲劳
- ❌ 仿宋体做大段现代正文（**公文例外**）—— 同上
- ⚠️ 中易宋体、中易仿宋、旧版微软雅黑：破折号/省略号可能断开或下沉，Web 与长文场景需测试
- ⚠️ 华文黑体、部分兰亭黑版本：标点可能不居中；如用于出版/品牌项目需实测

标题/海报谨慎用：
- ⚠️ 卡通字体用于商务
- ⚠️ 书法字体用于科技
- ⚠️ 衬线字体（宋体）用于运动/动感主题
