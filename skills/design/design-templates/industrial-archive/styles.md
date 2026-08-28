# 风格预设 — 改 `:root` 那 8 个 CSS 变量就能切换

每个预设都是 8 行 CSS。换风格时把 `template.html` 里 `:root` 块的对应行替换即可。
不要去动字体（除非用户明确要求换字体），保持工业 / 博物馆质感。

---

## 1. default — 冷调钢蓝（默认 / "克制之物"原版）

```css
:root{
  --bg:        #e6e9ee;
  --bg-soft:   #f1f3f6;
  --paper:     #c9cfd6;
  --ink:       #0c0f14;
  --ink-soft:  #535963;
  --line:      #aab0b8;
  --line-soft: #c4c9d0;
  --steel:     #3a4a5a;
}
```
适合：北欧工业、机械藏品、灰色金属、仪器、铸铁器物
触发词：克制 / 北欧 / 工业 / 钢铁 / 灰

---

## 2. warm-leather — 暖棕复古

```css
:root{
  --bg:        #ece4d6;
  --bg-soft:   #f4eee2;
  --paper:     #d8cdb8;
  --ink:       #1c160e;
  --ink-soft:  #6e5e44;
  --line:      #b6a787;
  --line-soft: #cdc1a5;
  --steel:     #8a5a2e;   /* 棕铜 */
}
```
适合：皮革、木作、烟斗、相机、老钟表、复古家具
触发词：暖 / 复古 / 棕 / 皮革 / 怀旧 / 老件

---

## 3. night-iron — 暗夜铁

```css
:root{
  --bg:        #14161a;
  --bg-soft:   #1c1f24;
  --paper:     #2a2e35;
  --ink:       #e8eaee;     /* 反色：底深字浅 */
  --ink-soft:  #9aa0a8;
  --line:      #3a3f46;
  --line-soft: #2a2e34;
  --steel:     #c9a35a;   /* 暗金 */
}
```
适合：高端音响、机械键盘、烟火、暗色系产品、灯具
触发词：暗 / 深色 / 夜 / 暗金 / 黑色

注：用此预设时还要把 body `background-image` 的两个 radial 颜色调整为更深，建议：
```css
body{
  background-image:
    radial-gradient(at 20% 22%, rgba(58,74,90,0.18) 0px, transparent 50%),
    radial-gradient(at 78% 80%, rgba(201,163,90,0.05) 0px, transparent 55%);
}
```

---

## 4. paper-press — 纸张印刷

```css
:root{
  --bg:        #f3eee2;
  --bg-soft:   #faf5e8;
  --paper:     #e2d9c1;
  --ink:       #181410;
  --ink-soft:  #5a4f3e;
  --line:      #b9ac8e;
  --line-soft: #cec3a6;
  --steel:     #9a3324;   /* 铅红 */
}
```
适合：书籍、文具、印刷品、手作笔记、新闻类
触发词：纸 / 印刷 / report / 文具 / 报刊 / 出版

---

## 5. navy-blueprint — 海军蓝图

```css
:root{
  --bg:        #1f2a3a;
  --bg-soft:   #263244;
  --paper:     #324154;
  --ink:       #f4f6fa;
  --ink-soft:  #aab6c8;
  --line:      #4a5568;
  --line-soft: #2e3a4d;
  --steel:     #ffffff;     /* 白线条 */
}
```
适合：海事仪器、航空、导航、舰船零件、深色仪表
触发词：海军 / 蓝图 / blueprint / 航海 / 舰

注：建议同时把跑马灯 `.ticker` 的背景改 `var(--bg-soft)`、文字改 `var(--ink)`，否则浅底深字看不清。

---

## 6. ceramic-clay — 陶土黏土

```css
:root{
  --bg:        #e7d8c4;
  --bg-soft:   #f1e6d5;
  --paper:     #d3bfa3;
  --ink:       #2a1c12;
  --ink-soft:  #6b4f38;
  --line:      #b39472;
  --line-soft: #c8ad8c;
  --steel:     #5e3a1f;   /* 炉火棕 */
}
```
适合：陶器、瓷、土耳其器物、东亚老物件、有泥土感的工艺品
触发词：陶 / 瓷 / 土 / 窑 / 泥 / 黏土

---

## 7. mint-laboratory — 实验室薄荷

```css
:root{
  --bg:        #e8efea;
  --bg-soft:   #f1f5f2;
  --paper:     #c8d4ce;
  --ink:       #102018;
  --ink-soft:  #4f655a;
  --line:      #99ada3;
  --line-soft: #b9c7bf;
  --steel:     #2a6e5a;   /* 苔藓绿 */
}
```
适合：医疗器械、玻璃容器、实验室仪器、植物类、中性医疗
触发词：实验 / 医疗 / 玻璃 / 苔藓 / 绿

---

## 怎么挑

如果用户没说风格，根据品类自动挑：

| 品类 | 默认风格 |
|---|---|
| 铸铁、钢、机械、北欧器物 | default |
| 木作、皮革、复古、相机 | warm-leather |
| 音响、灯具、深色高端 | night-iron |
| 文具、纸品、书 | paper-press |
| 海事、航空、导航 | navy-blueprint |
| 陶瓷、东亚器物 | ceramic-clay |
| 实验仪器、医疗、玻璃 | mint-laboratory |
| 不确定 | default（最安全） |
