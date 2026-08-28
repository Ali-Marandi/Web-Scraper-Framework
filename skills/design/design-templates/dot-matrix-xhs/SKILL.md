---
name: dot-matrix-xhs
description: Bayer 抖动黑白点阵的小红书封面 / 杂志感海报 / 独立刊物封面模板 — 黑底 + Canvas 真做 Bayer 8×8 有序抖动把任意图片转成纯黑白点阵 + 上下双向 vignette + 杂志栏目式四角文字（刊号 / 栏目 / wordmark / credit）+ Noto Sans JP Black 中文超大粗黑标题 2×2 网格 + 中心方括号期号。4 套版式骨架（单图封面 / 上图下字 / 系列三联 / 内页长文），容器查询 cqh 适配任意尺寸。触发：用户要"点阵感 / dither / 1-bit / 黑白颗粒 / 小红书封面 / Vol 期号海报 / 独立刊物 / 报纸印刷感"。NOT 多区块产品页，NOT 彩色海报。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: 点阵.html
source_priority: skill-first
triggers:
  - "做个点阵小红书封面"
  - "黑白颗粒封面"
  - "1-bit 海报"
  - "Vol 期号封面"
  - "独立刊物封面"
  - "报纸印刷感封面"
  - "dither 抖动"
related_patterns: social-card-editorial
---

# dot-matrix-xhs — Bayer 抖动黑白点阵封面

把任意一张照片实时做 Bayer 8×8 有序抖动，变成"报纸印刷点阵"，叠在杂志感四角文字 + 中文 2×2 大标题骨架上。**容器比例固定 1280×1644（小红书纵版封面）**，但用 container-query (cqh) 单位排版，缩到任何尺寸都不糊。

## 怎么用这份 skill

1. **看气质**：先 Read `点阵.html`（深夜篝火 / a fire at midnight 范例），重点看 Bayer dithering 的颗粒密度、暗角强度、四角栏目字的层级关系。**这一步只是为了"知道对的样子长什么样"。**
2. **挑骨架**：从下面 4 个版式骨架里选一个（单图封面 / 上图下字 / 系列三联 / 内页长文），**禁止整张 clone 深夜篝火**（同样的 2×2 + 中部方括号 + 底部 wordmark 一起出现就是撞脸）。
3. **抄积木**：Canvas Bayer 函数、容器查询排版、四角文字布局可以直接搬。
4. **过红线**：写完对照"必须 / 禁止"清单自检。

## 视觉 DNA — 这些不能丢

少了任意一条就不再是点阵杂志感：

1. **黑底 + Canvas 真做 Bayer 抖动**：底层一定是一张被 Bayer 8×8 抖动过的图，**不是 CSS noise，不是 SVG filter，不是预渲染好的 PNG，必须 Canvas 实时跑**。任何图（人物、风景、物件）经过 `adjustBrightness(-20~-30) + adjustLevels(60~80, 190~210) + bayerDither` 后才是对的。
2. **像素硬边渲染**：canvas 必须 `image-rendering:pixelated`，缩放时点阵保持硬边，不能因放大变模糊变灰。
3. **上下双向 vignette**：`linear-gradient(180deg, rgba(0,0,0,.55) 0%, transparent 18%, transparent 70%, rgba(0,0,0,.45) 100%)`，让顶部刊号和底部 wordmark 有底气；**不要四角 vignette**（圆形会立刻变成手机相机镜头味）。
4. **杂志栏目式四角**：左上=刊号 (`No 04 / 2026`)、右上=栏目英文+中文小字、左下=主 wordmark、右下=年份+credit。**至少填 3 角**，这是独立刊物的标识；少于 3 角就只是张图配字。
5. **超大粗黑中文标题**：`Noto Sans JP Black` + `PingFang SC` 兜底，`font-weight:900`，`line-height:1.1`，`letter-spacing:0`（中文密排不加字距）。**禁止细体 / 楷书 / 隶书 / 圆体**。
6. **白字带轻 text-shadow**：所有覆盖在点阵图上的文字都要 `text-shadow:0 0 .8cqh rgba(0,0,0,.85)`，让白字在浅色点阵区域也读得清。

## 必须 / 禁止（写完自检）

**必须**：
- [ ] Canvas 真做了 Bayer dithering（不是 CSS 滤镜、不是 SVG noise、不是预渲染图）
- [ ] 容器有固定 `aspect-ratio`（封面用 1280/1644，海报可自由）
- [ ] 容器加 `container-type:size`，排版单位用 `cqh` / `cqw`
- [ ] 四角至少 3 角有内容（刊号、栏目、wordmark、credit 选 3）
- [ ] 主标题字重 ≥ 800
- [ ] 中文 webfont 按"四件套"加载（preconnect + preload + print-onload + noscript）
- [ ] canvas 三行 `image-rendering:pixelated / -moz-crisp-edges / crisp-edges` 一个不能少

**禁止**：
- [ ] 不要照抄"2×2 中文字阵列 + 中心方括号 + 底部 wordmark"完整组合 — 那是深夜篝火的指纹
- [ ] 不要用 SVG noise / `filter: contrast` / `background-image: radial-gradient(...dot)` 模拟点阵 — 一眼假
- [ ] 不要让点阵保留灰阶（Bayer 输出必须是纯黑 0 或纯白 255 二值，不允许中间值）
- [ ] 不要给图加饱和色调（黄昏滤镜、青蓝调、奶油色）— 这套审美就是 1-bit 纯黑白
- [ ] 不要圆角 — 框架、按钮、卡片全是直角
- [ ] 不要 emoji / 3D 贴纸 / 渐变色 / 玻璃拟态 / 阴影漂浮
- [ ] 标题不要 PingFang Regular / Source Han Sans Light — 必须 Heavy / Black 字重
- [ ] 不要照搬"深/夜/篝/火 + VOL IV / 2026 + 夜火 wordmark + 小红书号 955873829" — 那是范例的指纹

## 四套版式骨架（任选一套，不要再做"深夜篝火"组合）

每套都自带点阵 + 四角文字 DNA，但**结构截然不同**，让产物不撞脸。

### 骨架 A — 单图封面（深夜篝火原型，可参考但慎用）
```
[底层]  Bayer 点阵全屏图 + 上下 vignette
[四角]  左上刊号 / 右上栏目+中文 / 左下 wordmark / 右下 credit
[上中]  hr 分割线 + 2×2 中文超大标题 + 英文斜体副标
[正中]  方括号期号或主题词
```
适合：单张视觉强烈的照片做封面（人物特写、风景、静物）。1280×1644。

### 骨架 B — 上图下字
```
[上 60%]  Bayer 点阵图 + 顶部刊号 + 栏目
[下 40%]  纯黑区，左侧大标题（横排单行或两行），右侧引文 + 出处
[底栏]    细线 + wordmark + 期号
```
适合：长标题或要放副文、引文、署名（不强求 2×2 网格的项目）。1280×1644 或 1080×1350。

### 骨架 C — 系列三联封面
```
[整张分 3 列]  每列一张独立 Bayer 点阵图（人物特写 / 物件 / 环境）
              每列底部各有自己的小标题 + 编号 01 / 02 / 03
[顶栏]        统一刊号 + 栏目
[底栏]        统一 wordmark + 总集名
```
适合：系列报道、人物组照、产品组合、旅行游记封面。横版 1644×1280 或纵版 1280×1644。

### 骨架 D — 内页 / 长文版心
```
[顶栏]   刊号 + 栏目 + hr
[左栏]   sticky 大标题 + 引文（占 40% 宽）
[右栏]   长正文（多段 p + 行内引用），插 1-2 张 Bayer 小图
[底栏]   页码 + wordmark
```
适合：刊物内文页、长 essay、采访稿（不只是封面，还有阅读内容）。1280×1800+ 或 A4 比例。

## 可直接抄的代码积木

### Bayer 8×8 抖动（核心，不能简化）
```js
function bayerDither(ctx, W, H){
  const d = ctx.getImageData(0,0,W,H), px = d.data;
  const m = [
    [ 0,32, 8,40, 2,34,10,42],[48,16,56,24,50,18,58,26],
    [12,44, 4,36,14,46, 6,38],[60,28,52,20,62,30,54,22],
    [ 3,35,11,43, 1,33, 9,41],[51,19,59,27,49,17,57,25],
    [15,47, 7,39,13,45, 5,37],[63,31,55,23,61,29,53,21]
  ];
  for (let y=0; y<H; y++) for (let x=0; x<W; x++){
    const i=(y*W+x)*4;
    const luma = (0.299*px[i] + 0.587*px[i+1] + 0.114*px[i+2]) / 255;
    const t = (m[y%8][x%8] + 0.5) / 64;
    const v = luma > t ? 255 : 0;
    px[i]=px[i+1]=px[i+2]=v; px[i+3]=255;
  }
  ctx.putImageData(d,0,0);
}
```
**关键**：8×8 矩阵不要换 4×4（颗粒过粗）、不要换 Floyd-Steinberg（变成误差扩散的另一种味道，颗粒会"流"）。点阵密度 = canvas 内部分辨率：W=600 H=771 是封面默认，要更细就开到 900×1158，要更糙就 400×514。

### 预处理：压暗 + 拉对比（让 Bayer 出黑白分明的点阵）
```js
function adjustBrightness(ctx, W, H, delta){
  const d = ctx.getImageData(0,0,W,H), px = d.data;
  for (let i=0; i<px.length; i+=4)
    for (let c=0; c<3; c++){ let v=px[i+c]+delta; px[i+c]=v<0?0:v>255?255:v; }
  ctx.putImageData(d,0,0);
}
function adjustLevels(ctx, W, H, lo, hi){
  const d = ctx.getImageData(0,0,W,H), px = d.data, scale = 255 / (hi - lo);
  for (let i=0; i<px.length; i+=4)
    for (let c=0; c<3; c++){ let v=(px[i+c]-lo)*scale; px[i+c]=v<0?0:v>255?255:v; }
  ctx.putImageData(d,0,0);
}
```
**调用顺序固定**：`drawImage → adjustBrightness(-25) → adjustLevels(70, 195) → bayerDither`。**不要先 dither 再调对比** — dither 已是二值化，之后调对比无效。

### Canvas 元素配置
```html
<canvas class="bg" id="bg" width="600" height="771"></canvas>
<img class="src" id="src" src="YOUR_IMG_URL" crossorigin="anonymous" alt="">
```
```css
canvas.bg{
  position:absolute; inset:0;
  width:100%; height:100%;
  image-rendering:pixelated;
  image-rendering:-moz-crisp-edges;
  image-rendering:crisp-edges;
  z-index:0; display:block;
}
img.src{ display:none }
```
源图 `<img>` 只用来给 canvas drawImage，不直接显示。`crossorigin="anonymous"` 必须 — 否则 getImageData 跨域报错。

### 完整 Canvas 处理流程
```js
(async function(){
  if (document.fonts && document.fonts.ready){ try { await document.fonts.ready; } catch(e){} }
  const img = document.getElementById('src');
  const canvas = document.getElementById('bg');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;

  const ready = (img.complete && img.naturalWidth > 0)
    ? Promise.resolve()
    : new Promise((res, rej) => { img.onload = res; img.onerror = rej; });
  try { await ready; } catch(e){ console.warn('img failed', e); return; }

  const ratio = Math.max(W / img.naturalWidth, H / img.naturalHeight);
  const dw = img.naturalWidth * ratio, dh = img.naturalHeight * ratio;
  ctx.drawImage(img, (W - dw) / 2, (H - dh) / 2, dw, dh);

  adjustBrightness(ctx, W, H, -25);
  adjustLevels(ctx, W, H, 70, 195);
  bayerDither(ctx, W, H);
})();
```

### 容器查询排版（适配任意尺寸不糊）
```css
.frame{
  position:relative;
  height:min(94vh, 1644px);
  aspect-ratio: 1280 / 1644;
  container-type:size;
  background:#000; color:#fff;
  overflow:hidden;
}
.title{ font-size:12cqh; }
.credit{ font-size:.85cqh; letter-spacing:.28em; }
```
**为什么 cqh 不用 vh**：vh 跟视口走，容器尺寸变了文字不跟。cqh 跟 `.frame` 容器走，封面缩到一半也保持版式比例。

### 上下双向 vignette
```css
.vignette{
  position:absolute; inset:0; z-index:1; pointer-events:none;
  background: linear-gradient(180deg,
    rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 18%,
    rgba(0,0,0,0) 70%, rgba(0,0,0,.45) 100%);
}
```
顶部更重一些（.55 vs .45），因为刊号比 credit 字号小、需要更多对比保护。

### 四角栏目布局
```css
.layer{
  position:absolute; inset:0; z-index:2;
  padding:3.6cqh 4.4cqh;
  display:flex; flex-direction:column;
  pointer-events:none;
}
.layer *{ text-shadow:0 0 .8cqh rgba(0,0,0,.85) }
.top{
  display:flex; justify-content:space-between; align-items:center;
  font-size:.95cqh; letter-spacing:.32em; text-transform:uppercase; font-weight:500;
}
.bottom{
  margin-top:auto;
  display:flex; justify-content:space-between; align-items:flex-end;
}
```
`margin-top:auto` 让 footer 一定贴底，无论中间内容多少。

### 中文 2×2 标题（仅骨架 A）
```html
<div class="title-grid">
  <div class="col"><span class="sm">深</span><span class="sm">篝</span></div>
  <div class="col"><span class="lg">夜</span><span class="lg">火</span></div>
</div>
```
```css
.title-grid{
  display:inline-flex; align-items:flex-start; gap:0;
  font-family:'Noto Sans JP','PingFang SC','Heiti SC',sans-serif;
  font-weight:900; line-height:1.1; letter-spacing:0;
}
.title-grid .col{ display:flex; flex-direction:column }
.title-grid .sm, .title-grid .lg{ font-size:12cqh }
```
**约束**：必须 4 个汉字，按词组拆成两列（深/篝 一列、夜/火 一列），不是按阅读顺序。3 字、5 字、6 字不用这个骨架。

### 方括号期号装饰
```css
.brackets{
  position:relative; padding:1cqh 2.6cqh;
  font-weight:500; font-size:1.1cqh; letter-spacing:.36em;
  text-transform:uppercase;
}
.brackets::before, .brackets::after{
  content:''; position:absolute;
  width:1.3cqh; height:1.3cqh; border:1px solid #fff;
}
.brackets::before{ top:0; left:0; border-right:none; border-bottom:none }
.brackets::after{ bottom:0; right:0; border-left:none; border-top:none }
```
左上 + 右下两个 L 角，模拟相机取景框 / 印刷裁切标记。

## 中文 webfont 加载（必做）

`Noto Sans JP` Heavy 是大字重日文体（带中文汉字 fallback），文件大；中文优先本地 PingFang/Heiti。按"四件套"：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" fetchpriority="high"
  href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+JP:wght@900&display=swap">
<link rel="stylesheet" media="print" onload="this.media='all'"
  href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+JP:wght@900&display=swap">
<noscript><link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+JP:wght@900&display=swap"></noscript>
```
字体栈一定带 `'PingFang SC','Heiti SC'` 兜底；英文小字用 Inter（italic 给副标用）。

## 输入信息核对

让用户给齐再动手：
1. **一张底图**（必需）— URL 或本地路径。人脸 / 风景 / 静物都可，但**明暗对比要强**，灰蒙蒙的图 dither 后糊一片；建议先在图编软件里看一眼，能分清主体与背景就行
2. **刊号 + 栏目**（必需）— `No 04 / 2026` + 栏目英文 (CAMPING / TRAVEL / FOOD…) + 中文小字 2-4 字
3. **标题**（必需）— 骨架 A 是 4 字 + 英文斜体副标；骨架 B/C/D 自由长度
4. **wordmark + credit**（必需）— 主品牌大字 2-4 字 + 年份 / 小红书号 / 作者名 / 出处
5. **比例**（可选）— 默认 1280/1644，可指定 1080/1350、1644/1280、1×1
6. **dither 颗粒密度**（可选）— "细 / 中 / 粗" 对应 canvas 内部宽度 900 / 600 / 400

## 反模式速查（看到这些就回头改）

| 症状 | 错在哪 | 修正 |
|---|---|---|
| 点阵糊一片，看不出原图 | 没做 adjustLevels 拉对比 | 加 `adjustLevels(70, 195)`，没有就不出点阵感 |
| 点阵全黑或全白 | brightness/levels 调过头 | brightness ∈ [-30, -10]，levels lo<80 hi>180 |
| 字飘在图上读不清 | 没加 text-shadow / 没 vignette | `text-shadow:0 0 .8cqh rgba(0,0,0,.85)` + 上下渐变 |
| 缩放后点阵变模糊 | 漏了 `image-rendering:pixelated` | canvas 三行 image-rendering 全加 |
| 字号缩放后不跟容器 | 用了 vh 而不是 cqh | 容器加 `container-type:size`，所有字号用 cqh |
| 标题字太细看起来软 | 用了 PingFang Regular / Light | 换 Noto Sans JP 900 + PingFang Heavy 兜底 |
| 中文标题字距大像招牌 | 加了 letter-spacing | 中文密排 `letter-spacing:0` |
| 四角文字只填 1-2 角 | 杂志感塌成"图配字" | 至少填 3 角（刊号 / 栏目 / wordmark / credit 选 3） |
| 用了 emoji / 圆角 / 彩色 | 违反 1-bit 黑白审美 | 删掉，回到纯黑白 + 直角 |
| 点阵看着像 CSS noise | 没真做 Canvas Bayer | 必须 Canvas 跑 `bayerDither`，不能 SVG/CSS 模拟 |
| 整张和深夜篝火一模一样 | 没选其他骨架 | 强制走 B/C/D 之一 |

## 关于 点阵.html

放在 skill 同目录，是「深夜篝火 · a fire at midnight」的完整范例（骨架 A 实现）。**只看 Bayer 调用顺序、cqh 排版结构、四角层级关系**，不要把"深/夜/篝/火 + VOL IV / 2026 + 夜火 wordmark + 小红书号 955873829"原文搬到新项目里 — 那是范例的指纹。

## 输出要求

- 单文件 HTML（HTML + CSS + Canvas 处理 JS）
- 容器查询 + 固定 `aspect-ratio`，缩放不糊
- 中文 webfont 四件套加载
- canvas 三行 `image-rendering` 全加
- 不写注释解释 Bayer 是什么 — 调用顺序对就行
