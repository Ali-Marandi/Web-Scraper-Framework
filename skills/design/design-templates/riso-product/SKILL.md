---
name: riso-product
description: Risograph 印刷质感的产品页 / 品牌页 / 落地页模板 — 奶油纸底 + 半调点纸纹 + 两到三色叠印 + 隷書 / 毛笔体大标题带错位色阴影 + Neobrutalism 硬阴影按钮卡片。7 套配色预设（粉+蓝 / 薄荷+珊瑚 / 柠檬+紫电 / 橄榄+玫瑰 / 暗夜荧光 / 天蓝+芥末 / 赤陶+鸭蓝）× 4 套版式骨架（单页长滚动 landing / home+单详情页 / 杂志独立刊物 / 海报式单屏）。触发：用户要"印刷感 / riso 风 / 复古丝网 / 奶油纸感 / 中式杂志感"的品牌官网、产品 landing、限量发售页、独立刊物页。当用户只说"做个产品页"且无明确风格时不要用它。
visibility: public
mode: template
carrier: web-page
scenario: brand-landing
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个 riso 风产品页"
  - "印刷感品牌页"
  - "奶油纸 landing"
  - "复古丝网产品页"
  - "中式杂志感品牌页"
  - "限量发售页"
  - "独立刊物页"
related_patterns: saas-landing
---

# riso-product — riso 印刷质感页面

把 risograph 油印机的"两到三色叠印 + 半调点 + 奶油纸"翻译成网页。骨架来自 NOIRLAB 声学家居品牌的设计原型（见 `reference.html`），但**这份 skill 给的是气质和积木，不是模板**。

## 怎么用这份 skill

1. **看气质**：先 Read `reference.html`，理解颜色叠加方式、阴影方向、字体层级、半调点疏密。**这一步只是为了"知道对的样子长什么样"。**
2. **挑配色**：从下面 7 套预设里选一套（或按用户描述自由调），**不要默认用 reference 的粉+蓝**。
3. **挑骨架**：从下面 4 个版式原型里选一个（或混搭）；**禁止整页 clone reference 的 home + 4 详情页 + 故事页结构**。
4. **抄积木**：CSS 片段（halftone、paper、neobrutalism shadow、riso shade、错位标题阴影）可以直接拿用。
5. **过红线**：写完对照"必须 / 禁止"清单自检。

## 视觉 DNA — 这些不能丢

少了任意一条，就不再是 riso：

1. **奶油纸底**：背景不能是纯白也不能是冷灰，必须带温暖的米黄/燕麦/亚麻色（明度 88–94，饱和度 8–18）
2. **半调点叠印**：全局 `body::after` 用 `radial-gradient(circle at 1px 1px, ...)` 5–8px 网格、`mix-blend-mode: multiply`、opacity 30–55%。色块大区域上再叠一层不同色的更大颗粒（8–12px）
3. **两到三色叠印 hero**：hero / 大色块用 2-3 个 `radial-gradient` ellipse 不同位置不同色（粉 + 蓝 + 黄 是经典三色组合，但可以全替），`mix-blend-mode: multiply`，让色彩在交叠处自然产生第三色
4. **隷書/毛笔体大标题** + **错位色阴影**：`text-shadow: 4px 4px 0 var(--accent-a), 8px 8px 0 var(--accent-b)`，模拟丝网印刷套印错位的物理瑕疵
5. **Neobrutalism 硬阴影**：按钮/卡片用 `box-shadow: Npx Npx 0 var(--ink)`（N=4–8），hover 偏移到 0，元素位移 `translate(Npx, Npx)`，2px solid 实色边框

## 必须 / 禁止（写完自检）

**必须**：
- [ ] 至少 1 处文字带错位色阴影
- [ ] 全局有可见但不糊的半调点纸纹
- [ ] 至少 1 个 hero / 大色块用了 2 色以上 radial gradient multiply 叠加
- [ ] 按钮/卡片至少有 1 套是硬阴影 + hover 偏移
- [ ] 标题字体是隷書/毛笔体或楷书（参考 `--hanli` 字体栈），**不是 PingFang / Source Han Sans**
- [ ] 颜色饱和但不刺，paper 底色降低任何强色的塑料感

**禁止**：
- [ ] 不要把 reference.html 的 `<section>` 结构整段抄（公告条 → header → hero → USP 四列 → feature → cat-grid → material → process → gallery → counters → testi → faq → news → footer + 4 个详情页 + 1 个故事页）
- [ ] 不要默认粉 #FF3F8E + 蓝 #2240FF — 那就是 NOIRLAB 的指纹
- [ ] 不要黑金 / 玻璃拟态 / 深空渐变 / emoji / 3D 塑料贴纸
- [ ] 不要给图片上一层重的灰色 overlay（半调点要轻、油墨要透）
- [ ] 半调点不要做成同色同尺寸，会显得是 CSS noise；至少两层不同颗粒不同色
- [ ] 不要照抄 NOIRLAB 品牌名 / 林见安 / 同济 / 28dB 这些 NOIRLAB 专属文案

## 七套配色预设（任选一套，禁止默认）

每套都满足"低饱和奶油底 + 两强色 + 一辅色（可选)"的结构。复制到 `:root`。

```css
/* 1. 热粉 + 联邦蓝（NOIRLAB 原作 — 慎用，会撞脸）*/
--paper:#F1EBDA; --ink:#1B1A18;  --a:#FF3F8E; --b:#2240FF; --c:#FFD23A;

/* 2. 薄荷 + 珊瑚 — 清新、女性向、护肤/茶饮/订阅盒 */
--paper:#EFEEE5; --ink:#1F2A28;  --a:#FF6B5A; --b:#2BB7A1; --c:#FFC857;

/* 3. 柠檬 + 紫电 — 高冲击、潮流、运动鞋/电子/年轻品牌 */
--paper:#F4EFE4; --ink:#16151A;  --a:#F4E04D; --b:#6A2EE8; --c:#FF4D8D;

/* 4. 橄榄 + 玫瑰 — 沉稳、内敛、茶/酒/家居/独立刊物 */
--paper:#EFE9D8; --ink:#1E1C18;  --a:#C24A6C; --b:#5C6E2C; --c:#D9A24A;

/* 5. 暗夜 + 荧光 — 深色底 riso，反向操作 */
--paper:#1B1A18; --ink:#F1EBDA;  --a:#FF3F8E; --b:#4DE0C7; --c:#FFD23A;
/* 注意：深底时半调点要用浅色、screen 混合 */

/* 6. 天蓝 + 芥末 — 户外、咖啡、慢生活、文具 */
--paper:#EDE8D8; --ink:#1B1B1B;  --a:#3D89C7; --b:#D6A92E; --c:#E0625E;

/* 7. 赤陶 + 鸭蓝 — 工艺/手作/陶艺/民艺 */
--paper:#F0E7D5; --ink:#1F1A16;  --a:#C25538; --b:#2F6B7D; --c:#E4B83B;
```

替换原则：把 reference.html 里 `var(--pink)` 换成你选的 `var(--a)`，`var(--blue)` 换成 `var(--b)`，`var(--yellow)` 换成 `var(--c)`。**整套统一替换**，不要某处粉某处红。

## 四套版式骨架（任选一套，不要再做"home + 4 详情页 + 故事页"组合）

每套都自带 riso 视觉，但**结构截然不同**，让产物不撞脸。

### 骨架 A — 单页长滚动 landing
```
[announce marquee] → [hero w/ 错位标题] → [3 列 USP] → [产品概览 grid 3-6 卡]
→ [大单品 spotlight w/ 半身图 + 规格表] → [创始人引言段 + 数字 counter]
→ [社区/真实评论 3 卡] → [FAQ 5–7 条手风琴] → [订阅条] → [footer]
```
**没有详情页**。所有产品/详情都在同一页折叠展开。适合 1–4 个 SKU 的窄品牌。

### 骨架 B — 双页：home + 单详情页（无 hash 路由）
```
home: [hero 全屏图+错位标题] → [4 卡产品 grid] → [品牌故事 2 列长文] → [footer]
detail: 独立 detail.html → [大 hero 图 + 价格胶囊] → [左长文 + 右 sticky 规格表]
        → [3 张细节图 dgallery] → [其他系列 3 卡] → [返回 home]
```
适合 1 个主推产品 + 一些次要 SKU 的品牌（比如 1 款香水 + 3 个配件）。

### 骨架 C — 杂志/独立刊物布局
```
[封面页：单大字 + riso 噪点全屏 + 期号/日期 mono]
[目录 contents：左竖排序号，右每篇标题+作者+栏目]
[内页：左右栏不对称，长文 6:4 / 引文 7:3 / 大图 1:1 / 图文混排]
[书脊页脚：mono 小字 章节名 + 页码]
```
适合品牌内容站 / brand magazine / 文化品牌 / 出版相关项目。可以没有任何 CTA 按钮。

### 骨架 D — 海报式单屏（fold-only）
```
首屏一整页占满：
  上：announce + brand
  中：超大错位标题（屏幕 60% 高度）+ 一句话副标
  下：单个 CTA + 一个细节图缩略（可点开 lightbox）
不需要滚动。适合 waitlist / drop / 限量发售 / event。
```

## 可直接抄的 CSS 积木

### 全局纸纹 + 半调点（必备）
```css
body{
  background: var(--paper);
  color: var(--ink);
  position: relative;
}
/* 颗粒噪点（纸纤维感）*/
body::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:9000;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .12 0 0 0 0 .10 0 0 0 0 .08 0 0 0 .35 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  opacity:.45; mix-blend-mode:multiply;
}
/* 半调网点 */
body::after{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:8990;
  background-image: radial-gradient(circle at 1px 1px, rgba(27,26,24,.08) 1px, transparent 1.4px);
  background-size: 5px 5px;
  mix-blend-mode: multiply; opacity:.55;
}
```

### 错位色标题阴影
```css
.headline-riso{
  font-family: var(--hanli);  /* 见下方字体栈 */
  text-shadow: 4px 4px 0 var(--a), 8px 8px 0 var(--b);
  letter-spacing: .04em;
}
/* 反白版本：暗底 */
.headline-riso--invert{
  color: var(--paper);
  text-shadow: 3px 3px 0 var(--a), 6px 6px 0 var(--c);
}
```

### 隷書/毛笔字体栈（中文标题专用）
```css
:root{
  --hanli: "白舟隷書教漢", "HakushuReisho", "Yuji Mai", "Yuji Boku",
           "ZCOOL XiaoWei", "STLiti", "华文隶书", "LiSu", "SimLi", Georgia, serif;
}
/* 若要 CDN 兜底 */
/* <link href="https://fonts.googleapis.com/css2?family=Yuji+Mai&family=ZCOOL+XiaoWei&display=swap" rel="stylesheet"> */
/* 用 local() 检测系统装的白舟隷書 */
@font-face{
  font-family:"HakushuReisho"; font-display:swap;
  src: local("HOT-ReishoR-K"), local("Hakushu Reisho R"), local("白舟隷書教漢");
}
```
**禁止**用 PingFang / Source Han Sans / Microsoft YaHei 做标题——会立刻没有 riso 味。正文可以用 Inter / 系统 sans。

### riso 三色叠印（大色块/hero 用）
```css
.riso-shade{
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 55% 65% at 18% 25%, rgba(255,63,142,.55) 0%, transparent 60%),
    radial-gradient(ellipse 50% 55% at 82% 75%, rgba(34,64,255,.50) 0%, transparent 60%),
    radial-gradient(ellipse 30% 35% at 65% 18%, rgba(255,210,58,.40) 0%, transparent 70%);
  mix-blend-mode: multiply;
}
```
**关键**：3 个 ellipse 必须**位置错开**（左上 / 右下 / 中右）才有套印错位感。三色都对齐中心 = 失败。

### Neobrutalism 按钮
```css
.btn-riso{
  display:inline-flex; align-items:center; gap:14px;
  padding:16px 28px; font-weight:600; letter-spacing:.05em;
  border:2px solid var(--ink); border-radius:999px;
  background: var(--ink); color: var(--paper);
  box-shadow: 5px 5px 0 var(--a);
  transition: all .25s cubic-bezier(.2,.8,.2,1);
}
.btn-riso:hover{
  background: var(--a); color: var(--paper);
  box-shadow: 0 0 0 var(--a);
  transform: translate(5px, 5px);
}
```
4 种变体：`--ink`（实心黑底）/ `--paper`（白底蓝阴影）/ `--ghost`（透明 + ink 边框）/ `--accent`（强色底）。**hover 偏移到 0 + translate** 是这套阴影的关键，hover 是阴影"消失"而不是"加深"。

### Neobrutalism 卡片
```css
.card-riso{
  border: 2px solid var(--ink);
  box-shadow: 6px 6px 0 var(--ink);
  background: var(--paper-2);
  transition: transform .3s, box-shadow .3s;
}
.card-riso:hover{
  transform: translate(-3px, -3px);
  box-shadow: 9px 9px 0 var(--a);  /* 阴影变彩色 + 加深 */
}
```

### 图片半调叠加（不糊掉图）
```css
.img-riso{
  position: relative; overflow: hidden;
  border: 2px solid var(--ink); box-shadow: 5px 5px 0 var(--a);
}
.img-riso > img,
.img-riso > .img{
  width:100%; height:100%; object-fit: cover;
  filter: contrast(1.05) saturate(.9);  /* 略降饱和，靠近油墨色 */
}
.img-riso::after{
  content:""; position:absolute; inset:0; pointer-events:none;
  background-image: radial-gradient(circle at 1px 1px, rgba(34,64,255,.18) 1px, transparent 1.4px);
  background-size: 5px 5px;
  mix-blend-mode: multiply;
}
```
**核心**：半调点叠在图之上但只用 18% 不透明度，图本身保持清晰；图加 `filter: contrast(1.05) saturate(.9)` 把数字感拉回油墨感。

### 跑马灯公告条（可选）
```css
.announce{
  background: var(--a); color: var(--paper);
  border-bottom: 2px solid var(--ink); text-shadow: 1.5px 1.5px 0 var(--b);
  height:40px; display:flex; align-items:center; overflow:hidden;
}
.announce__track{ display:flex; gap:64px; white-space:nowrap; animation: marquee 38s linear infinite; }
@keyframes marquee{ from{transform:translateX(0)} to{transform:translateX(-50%)} }
```

## 中文 webfont 加载（必做）

谷歌的 Yuji Mai / ZCOOL XiaoWei 是中文 + 日文 webfont，文件大。按"四件套"加载：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" fetchpriority="high"
  href="https://fonts.googleapis.com/css2?family=Yuji+Mai&family=ZCOOL+XiaoWei&display=swap">
<link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Yuji+Mai&family=ZCOOL+XiaoWei&display=swap"
  media="print" onload="this.media='all'">
<noscript><link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Yuji+Mai&family=ZCOOL+XiaoWei&display=swap"></noscript>
```
然后 `font-display: swap` + 系统隶书兜底（已写在 `--hanli` 里）。

## 反模式速查（看到这些就回头改）

| 症状 | 错在哪 | 修正 |
|---|---|---|
| 标题用 PingFang 加粗 | 没用毛笔/隷書字体 | 换 `var(--hanli)` |
| 标题没阴影 / 阴影是黑色 | 没做错位色阴影 | `text-shadow:4px 4px 0 var(--a),8px 8px 0 var(--b)` |
| 背景是 #FFFFFF / 冷灰 | paper 底色不对 | 换温暖奶油色 #F1EBDA / #EFE9D8 |
| 半调点要么没有要么糊一片 | opacity 错、颗粒太大或太密 | 5–8px 网格，opacity 30–55% |
| 图片灰蒙蒙看不清 | 加了重 overlay | 只叠半调点 18% + `filter: contrast(1.05) saturate(.9)` |
| 按钮 hover 阴影变大 | 方向反了 | hover 阴影应该缩到 0 + 元素 translate |
| 全用 NOIRLAB 粉+蓝 | 撞脸 | 换七套预设之一 |
| 写了 4 个 hash 路由详情页 | 整页 clone 了 reference 结构 | 用骨架 A/B/C/D 之一 |

## 关于 reference.html

放在 skill 同目录，**所有图片已 base64 内联**（用 CSS `:root` 变量 `--img-01..06` 去重）—— 单文件 ~2.6MB，直接双击就能打开看完整效果。**只看气质，不要照抄结构**。如果你只是想知道"对的样子大概长啥样"，看它；如果你想知道"我这个新项目该怎么搭"，看上面的骨架 A/B/C/D 和积木。

## 输入信息核对

让用户给齐这些再动手：
1. 品牌名 + 一句话定位
2. 1–6 个产品 / 1 个主推 / 单事件（影响选骨架）
3. 配色偏好（用预设名 or 描述）
4. 图片：用户给 or 用 picsum 占位
5. 风格描述里有没有"撞脸 NOIRLAB"的禁区（用户要"低调克制" → 别用骨架 A 全屏跑马灯）

## 输出要求

- 单文件 HTML（可选 hash 路由，骨架 A/D 不要，B/C 可选）
- 移动端响应式（≥1024 / 900 / 520 三档断点至少做两档）
- 中文 webfont 按上面四件套加载
- 不写注释解释 CSS 是什么，CSS 自己会说话
