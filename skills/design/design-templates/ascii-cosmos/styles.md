# 风格预设库

每个预设给 8 个 `:root` CSS 变量 + 5 个 ASCII 层颜色 + hero 背景渐变。改其他地方需要相应连带改（图片滤镜、scrambler 字符颜色等）。

> **配色原则**：5 个 ASCII 层在背景上必须**同时可读 + 互相和谐**。同一冷暖、轻微变奏，不要把"对比 = 好看"。

---

## 1. 深空青（默认 · cosmic-cyan）

最克制的太空感，宝石蓝紫为底，青/粉/琥珀的发光层。适合本地优先 AI、笔记/写作、独立软件、CLI 工具。

```css
:root{
  --bg:#05060f;
  --fg:#e6e8ff;
  --dim:#7a7fa8;
  --accent:#8be9ff;     /* 青 */
  --accent2:#ff6ad5;    /* 粉 */
  --accent3:#c792ea;    /* 紫 */
  --line:#1a1d3a;
  --hl:#0d1024;
  --paper:#0a0c1f;
}
.hero{ background: radial-gradient(ellipse at 30% 20%, #1a0a2e 0%, #05060f 55%, #000 100%); }
#ascii-nebula  { color:#a87bd6; }   /* 星云 */
#ascii-stars   { color:#cfe6ff; }   /* 星点 */
#ascii-planet  { color:#8be9ff; }   /* 行星 */
#ascii-asteroids{ color:#f5b971; }  /* 小行星 */
#ascii-comets  { color:#ff8fd2; }   /* 彗星 */
```
图片滤镜：`hue-rotate(200deg) saturate(.9) contrast(1.1) brightness(.6)`

---

## 2. 暖色羊皮纸（letterpress-warm · 原墨思配色）

宋体凸印 + 米色背景，复古旧报纸感。适合中文写作工具、独立出版、设计工作室、小众杂志。

```css
:root{
  --bg:#F3E4D4;
  --fg:#1f1510;
  --dim:#8a7560;
  --accent:#660125;     /* 酒红 */
  --accent2:#a83344;
  --accent3:#7a4a1f;
  --line:#d8c4af;
  --hl:#ecd8ca;
  --paper:#ecd8ca;
}
.hero{ background: linear-gradient(180deg, #F3E4D4 0%, #e9d2b8 100%); }
#ascii-nebula  { color:#b88a6a; opacity:.5; mix-blend-mode:multiply; }
#ascii-stars   { color:#5a3a1e; opacity:.7; }
#ascii-planet  { color:#660125; }
#ascii-asteroids{ color:#7a4a1f; }
#ascii-comets  { color:#a83344; }
```
图片滤镜：`sepia(.3) contrast(1.05) saturate(.85) brightness(.95)`
注：暖色背景下要把 `mix-blend-mode: screen` 改成 `multiply`，让 ASCII 是"压在纸上"而不是"发光"。

---

## 3. 赛博紫（cyber-violet）

霓虹紫 + 电子粉，赛博朋克招牌色。适合 AI / Web3 / 游戏外设 / 电竞订阅。

```css
:root{
  --bg:#0a0118;
  --fg:#f0e6ff;
  --dim:#7e5cab;
  --accent:#ff00aa;     /* 霓虹品红 */
  --accent2:#00ffe0;    /* 青电流 */
  --accent3:#b14aff;    /* 紫 */
  --line:#2a0d4a;
  --hl:#150327;
  --paper:#10021f;
}
.hero{ background: radial-gradient(ellipse at 70% 30%, #4a0e6e 0%, #0a0118 60%, #000 100%); }
#ascii-nebula  { color:#b14aff; opacity:.55; }
#ascii-stars   { color:#e0d4ff; }
#ascii-planet  { color:#00ffe0; }
#ascii-asteroids{ color:#ff00aa; }
#ascii-comets  { color:#ffd400; }   /* 黄电流彗星 */
```
图片滤镜：`hue-rotate(280deg) saturate(1.4) contrast(1.1) brightness(.65)`

---

## 4. 终端绿（terminal-green）

黑底 phosphor 绿，复古 CRT 终端味。适合 CLI 工具、开发者订阅、安全产品、复古游戏。

```css
:root{
  --bg:#000800;
  --fg:#a8ffb0;
  --dim:#5fa05f;
  --accent:#00ff66;     /* phosphor 绿 */
  --accent2:#80ff80;
  --accent3:#ffaa44;
  --line:#0a3010;
  --hl:#001500;
  --paper:#001a05;
}
.hero{ background: radial-gradient(ellipse at center, #052010 0%, #000800 70%, #000 100%); }
#ascii-nebula  { color:#2a8a44; opacity:.45; }
#ascii-stars   { color:#a8ffb0; }
#ascii-planet  { color:#00ff66; }
#ascii-asteroids{ color:#ffaa44; }
#ascii-comets  { color:#80ffd4; }
```
图片滤镜：`grayscale(1) brightness(.6) sepia(1) hue-rotate(70deg) saturate(2)`
另外可在 `.hero::after` 加扫描线：`background: repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(0,255,102,.05) 3px, rgba(0,255,102,.05) 4px);`

---

## 5. 极光（aurora · 默认风格的冷淡变奏）

灰青冰蓝主色，加一抹粉绿，像北极极光。适合冥想 / 健康 / 旅行 / 北欧风产品。

```css
:root{
  --bg:#0c1420;
  --fg:#dceaf0;
  --dim:#6b8499;
  --accent:#7fe3c4;     /* 极光绿 */
  --accent2:#b8a4ff;    /* 淡紫 */
  --accent3:#ffb3c1;    /* 极光粉 */
  --line:#1a2638;
  --hl:#101a28;
  --paper:#0e1622;
}
.hero{ background: linear-gradient(160deg, #1a3548 0%, #0c1420 50%, #050810 100%); }
#ascii-nebula  { color:#b8a4ff; opacity:.5; }
#ascii-stars   { color:#dceaf0; }
#ascii-planet  { color:#7fe3c4; }
#ascii-asteroids{ color:#ffb3c1; }
#ascii-comets  { color:#88ddff; }
```
图片滤镜：`hue-rotate(180deg) saturate(.7) contrast(1.05) brightness(.7)`

---

## 6. 沙漠日落（desert-sunset · 暖色 ASCII 系）

橙红土 + 焦糖 + 杏色，沙丘黄昏感。适合咖啡 / 独立硬件 / 工艺品 / 食品订阅。

```css
:root{
  --bg:#1a0a05;
  --fg:#f5e6d0;
  --dim:#a8765a;
  --accent:#ff8b3d;     /* 烤橙 */
  --accent2:#d94545;    /* 焦红 */
  --accent3:#ffd47a;    /* 杏黄 */
  --line:#3a1a10;
  --hl:#1f0d06;
  --paper:#15080a;
}
.hero{ background: radial-gradient(ellipse at 50% 80%, #5a1f10 0%, #1a0a05 60%, #000 100%); }
#ascii-nebula  { color:#a8765a; opacity:.5; }
#ascii-stars   { color:#ffd47a; }
#ascii-planet  { color:#ff8b3d; }
#ascii-asteroids{ color:#d94545; }
#ascii-comets  { color:#ffe9c2; }
```
图片滤镜：`sepia(.5) saturate(1.3) contrast(1.1) brightness(.7) hue-rotate(-10deg)`

---

## 怎么自由设计

如果用户给的风格描述不在以上 6 种里，按这个流程：

1. **定主色调温度**：冷（蓝/紫/青）/ 暖（橙/红/黄）/ 中性（绿/灰）
2. **`--bg` 选最深值**（如 `#05060f`），`--fg` 选最浅值（如 `#e6e8ff`）
3. **`--accent` / `--accent2` / `--accent3`** 三色：拉开**色相**而非饱和度，它们在小区域出现，要"互相点亮"
4. **5 个 ASCII 层颜色** 排序原则：
   - `nebula` → 半透紫/灰，做底
   - `stars` → 高明度白/暖白，最亮
   - `planet` → 主 `--accent`
   - `asteroids` → 暖色对比（即使主调冷也加暖一抹）
   - `comets` → 第二高饱和，做"流过去"的视觉锚
5. **图片滤镜** 必须连带调，否则 unsplash 图会"颜色不进环境"

> 测试方法：把 5 个层颜色填进调色板生成器（Coolors / Realtime Colors），确认它们之间最低对比度 ≥ 2.0，最高色相差 ≥ 90°。
