# Unicorn Studio 提取工作流

Unicorn Studio (unicorn.studio) 是一个 no-code WebGL 设计工具，使用 curtains.js 作为渲染引擎，Firebase/Firestore 作为后端。

## 识别特征

- URL 模式: `unicorn.studio/remix/{remixId}` 或 `unicorn.studio/edit/{designId}`
- Meta tag: `<meta name="ai:technical-stack" content="Vue 3, curtains.js, Firebase, JavaScript SDK">`
- 嵌入 SDK: `unicornStudio-*.js`（~84KB embed 版本）
- 主应用 bundle: `index-*.js`（~2.1MB，含 shader 模板）

## 数据获取路径

### 路径 1: Firestore REST API（推荐，适用于 remix）

```bash
# Firebase 配置（从 unicorn.studio 前端 JS bundle 中提取，每次提取时动态获取）
# 获取方式：curl -s https://www.unicorn.studio/ | grep -oP 'apiKey:"[^"]+"' | head -1
API_KEY="<从网站 bundle 动态提取>"
PROJECT="unicorn-studio"

# Step 1: 获取 remix 元数据（含 versionId、designId、cre建者信息）
curl -s "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/(default)/documents/remixes/{REMIX_ID}?key=$API_KEY"

# Step 2: 获取版本数据（含所有图层定义、参数、纹理引用）
# versionId 从 Step 1 的 fields.versionId.stringValue 提取
curl -s "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/(default)/documents/versions/{VERSION_ID}?key=$API_KEY"
```

### 路径 2: GCS/CDN Embed 数据（适用于已发布的嵌入）

```bash
# 非 Pro 用户
curl -s "https://storage.googleapis.com/unicornstudio-production/embeds/{DESIGN_ID}"

# Pro 用户
curl -s "https://assets.unicorn.studio/embeds/{DESIGN_ID}"
```

Embed JSON 格式: `{ options: {...}, layers/history: [...], modules: [...] }`
包含 `compiledFragmentShaders[]` 和 `compiledVertexShaders[]`（已编译的 GLSL）。

### 路径 3: 从页面内嵌 JSON 提取

Unicorn Studio 嵌入使用 `data-us-project` 或 `data-us-project-src` HTML 属性，
SDK `init()` 会扫描这些属性并加载对应项目。

## 先判断数据形态

Unicorn Studio 至少有两种常见数据形态：

### 1. embed/export scene

- 一般是最终给 `addScene()` 的 scene JSON
- 往往已经带 `compiledFragmentShaders[]` / `compiledVertexShaders[]`
- 这种格式可以直接喂给 embed runtime

### 2. editor/version history

- 常见来源是 Firestore `versions/{id}` 的 `history`
- 这是编辑器原始层数据，**不能**直接喂给 `addScene()`

如果把 `history` 误当 embed scene，典型症状是：

- `Plane: No fragment shader provided, will use a default one`
- `Plane: No vertex shader provided, will use a default one`
- `No composite shader data for element`
- canvas 创建成功，但画面全黑或只剩默认层

## Firestore 集合结构

| Collection | 用途 | 关键字段 |
|---|---|---|
| `designs` | 设计元数据 | creatorId, name, versionId, hasEmbed |
| `versions` | 版本数据（核心） | history[], options |
| `remixes` | 可 remix 设计 | designId, versionId, creatorId, thumbnail |

## 版本数据结构

Firestore REST 返回格式用 `{stringValue, integerValue, arrayValue, mapValue, ...}` 包裹，需递归解析。

`history` 数组中每个元素是一个图层：

```
layerType: "effect" | "text" | "image" | "model" | "shape"
type:      效果类型 (gradient, noiseFill, sdf_shape, glyphDither, bloomFast, ...)
```

### 图层参数（常见）

- `pos`, `scale`, `speed`, `opacity`, `blendMode`
- `trackMouse`, `trackAxes`, `mouseMomentum`
- `parentLayer`: UUID 或 false（关联父元素）
- `breakpoints[]`: 响应式断点配置
- `states`: appear/scroll/hover/mousemove 动画
- `customFragmentShaders[]`, `customVertexShaders[]`（通常为空，用内置效果时）

## 正确初始化策略

如果拿到的是 Firestore `version/history`，优先模仿站点自己的初始化链路，不要硬套 embed API。

典型调用顺序：

1. `unpackageHistory()` 或 `unpackVersion()`
2. `createFontScript()`
3. `createCurtains()`
4. `handleItemPlanes()`
5. `fullRedraw()`

如果页面 bundle 里有专门的 Remix/Preview 组件，优先跟着它走，不要只看公开 UMD/SDK 文档。

### 资源本地化

- image/font/texture 尽量下载到本地
- `history` 里的 `src`、`fontCSS.src` 要改成本地路径
- 某些对象字段可能是数字 key 的 map，落地前要规整成数组

### 效果类型特有参数

| 效果 | 关键参数 |
|---|---|
| gradient | fill[], stops[], gradientType, gradientAngle, wrap |
| noiseFill | noiseType, turbulence, color1, color2, colorPhase, chroma, direction |
| sdf_shape | shape(0-22), refraction, extrude, smoothing, axis, animationDirection, lightPosition |
| glyphDither | characters, glyphSet, scale, gamma, monochrome, texture(sprite atlas) |
| bloomFast | amount, intensity, exposure, tint |

## Shader 代码提取

**关键发现**: Embed SDK（~84KB）不含 GLSL shader 代码。Shader 模板在主应用 bundle（~2.1MB）中，经 7 步编译管线处理后存入 embed JSON。

### Shader 在 App Bundle 中的位置

Shader 模板是字符串字面量，通过变量名标识：

```
效果名           → 变量名
glyphDither     → X$ (fragment)
noiseFill       → WY (fragment)
sdf_shape       → XY (fragment)
gradient        → eX (fragment)
bloomFast       → Hj (fragment)
通用顶点         → ye (vertex)
梯度顶点         → ko (vertex)
合成片段         → Uz (composite fragment)
合成顶点         → Nz (composite vertex)
```

注意：变量名会随构建版本变化，需搜索关键特征定位。

### 模板变量

Shader 模板中含 `${variable}` 占位符，编译时替换：

| 变量 | 内容 |
|---|---|
| `${fe}` | mask 相关 uniform 声明 |
| `${Vt}` | 图层混合辅助函数 (applyLayerMix, applyLayerMixAlpha, applyLayerMixClip) |
| `${gt}` | PCG hash / 随机数函数 (pcg2d, randFibo) |
| `${ht}` | 混合模式函数 (17 种模式: Normal, Add, Multiply, Screen, Overlay, ...) |
| `${pe("var")}` | mask 应用 + fragColor 输出 |
| `${wf}` | BCC noise derivatives (OpenSimplex2S) |
| `${Aa}` | Perlin noise 函数 |
| `${yr}` | deband 抖动函数 |
| `${cm}` | 渐变颜色/停止点 uniform 声明 |
| `${xz}` | 高斯权重函数 (bloom blur) |

### 编译管线

```
1. Fz(): 替换 uniform 值为常量
2. Dz(): 处理渐变颜色数量（switch case 裁剪）
3. Mz(): 求值常量 switch（死代码消除）
4. Rz(): 处理 #ifelseopen/#ifelseclose 块（条件编译）
5. Iz(): 移除未使用函数
6. Cz(): 移除未使用 uniform 声明
7. Bp(): 去注释、规范化空白
```

## 渲染管线（核心，移植时必须正确还原）

```
curtains.js WebGL2 渲染器
├─ 每个效果图层 = 一个 Plane + 独立 FBO
├─ 图层按 renderOrder 线性链式渲染，每个 plane 读前一个 FBO 为 uTexture
├─ Element（shape/text/image）+ 子效果形成 render group：
│   1. Element 自身 plane 先渲染 → FBO_elem
│   2. 子效果按 effects 数组顺序依次渲染 → FBO_child1, FBO_child2, ...
│   3. Composite plane 最后渲染：alpha-blend 子效果输出到背景场景
├─ 独立后处理效果 (parentLayer=false) 处理全局场景
└─ 最后一个 plane 直接输出到 canvas（无 FBO）
```

### Element + 子效果的 FBO 链（关键）

```
以 shape group (sdf + noise) 为例：

FBO_before ─────────────────────────────────────────┐
                                                     │
Shape 自身 plane → FBO_shape (渲染基础几何)            │
    ↓                                                 │
Child noiseFill → FBO_noise (uBgTexture = FBO_shape)  │
    ↓                                                 │
Child sdf_shape → FBO_sdf (uTexture = FBO_noise)      │
    ↓ (showBg=0: 形状外 = vec4(0) 透明)              │
    ↓                                                 │
Composite plane → FBO_result                          │
    uTexture = FBO_sdf (最后一个子效果输出)             │
    uBgTexture = FBO_before (element 之前的场景) ←─────┘
    output = alpha_blend(fg, bg) = fg + bg * (1 - fg.a)
```

### 子效果关联机制

```js
// Element 的 effects 数组 → 子效果的 parentLayer UUID 列表
shape.effects = ["e270a7cd-...", "fb591190-..."]

// 每个子效果引用父 element 的 UUID
noiseFill.parentLayer = "e270a7cd-..."   // effects[0]
sdf_shape.parentLayer = "fb591190-..."   // effects[1]

// embed SDK 中查找子效果：
getChildEffectItems() {
    return this.effects.map(uuid =>
        state.layers.find(l => l.parentLayer === uuid)
    ).filter(Boolean)
}
```

### uTime 时间基准（关键陷阱）

Embed SDK 中 `uTime` **不是秒数**，而是逐帧累加：
```js
// setEffectPlaneUniforms() 中：
t.uniforms.time.value += speed * 60 / this.fps;
```

在 60fps 下：`uTime += speed` 每帧。1 秒后 `uTime = speed × 60`。

| 效果层 | speed | 1 秒后 uTime |
|--------|-------|-------------|
| noiseFill | 0.25 | 15 |
| sdf_shape | 0.5 | 30 |
| gradient | 0.25 | 15 |

**移植时必须乘以 `speed × 60`**，否则动画慢 15-60 倍：
```js
// 正确：
uni1f(prog, 'uTime', elapsedSeconds * speed * 60);
// 错误：
uni1f(prog, 'uTime', elapsedSeconds);
```

### showBg 参数的关键作用

- `showBg=0`：光线未命中几何体时输出 `vec4(0)` **透明**（不是黑色！）
- `showBg=1`：光线未命中时采样 `uTexture/uBgTexture`（显示背景内容）

**移植时 showBg=0 是最常见的陷阱**：如果错误地输出 `vec4(0,0,0,1)` 不透明黑色，
composite alpha blend 会被覆盖而不是透过下方图层。必须确保 alpha=0。

## 移植策略

1. **纯 2D 后处理效果** (glyphDither, bloomFast): 原生 WebGL2 全屏四边形
2. **生成式效果** (noiseFill, gradient): 原生 WebGL2
3. **3D SDF** (sdf_shape): 原生 WebGL2 raymarching
4. **复杂场景** (多图层合成): 需要 multi-pass FBO 管线
5. **文字图层**: Canvas 2D 渲染文字 → 作为纹理上传 WebGL

## Playwright 验证

Playwright 默认 headless 环境可能没有可用 WebGL。出现下面症状时，先怀疑环境，不要立刻怀疑提取逻辑：

- `Renderer: WebGL context could not be created`
- `0 canvas(es) found`
- `Error creating Curtains instance`
- 截图纯黑

这时改用 `swiftshader` 再验证：

```bash
--use-angle=swiftshader
--use-gl=angle
--enable-unsafe-swiftshader
--ignore-gpu-blocklist
```

建议验证顺序：

1. 看 console 是 shader/runtime 错误，还是 WebGL context 创建失败
2. 看 DOM 里是否真的生成了 `canvas`
3. 用 `swiftshader` 截图
4. 和原站缩略图或首屏截图做构图对比

### Glyph Atlas 生成

原始 glyph atlas 是 base64 PNG（存在跨浏览器兼容问题）。
推荐用 Canvas 2D 动态生成：

```js
function createGlyphAtlas(chars, size = 40) {
  const canvas = document.createElement('canvas');
  canvas.width = size * chars.length;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${size * 0.8}px monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let i = 0; i < chars.length; i++) {
    ctx.fillText(chars[i], size * i + size / 2, size / 2);
  }
  return canvas; // → gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas)
}
```

## Cloud Functions 端点

所有位于 `https://us-central1-unicorn-studio.cloudfunctions.net/`：
- `publishEmbedTest` — 发布/更新 embed（需认证）
- `getUserIdByUsername` — 用户名→userId
- `handleVideos/handleModels/handleImages` — 资源处理
- `generateImprovedMSDF` — MSDF 文字渲染
- `generateDepthMap` — 深度图生成
- `copyRemixAssets` — remix 资源复制

## 示例：完整提取流程

```bash
# 1. 从 URL 提取 remix ID
REMIX_ID="QZxhNFb1X1OaUqaJLT9S"

# 2. 获取 remix 元数据
curl -s "https://firestore.googleapis.com/v1/projects/unicorn-studio/databases/(default)/documents/remixes/$REMIX_ID?key=$API_KEY" > remix.json

# 3. 提取 versionId
VERSION_ID=$(python3 -c "import json; print(json.load(open('remix.json'))['fields']['versionId']['stringValue'])")

# 4. 获取版本数据
curl -s "https://firestore.googleapis.com/v1/projects/unicorn-studio/databases/(default)/documents/versions/$VERSION_ID?key=$API_KEY" > version.json

# 5. 解析版本数据中的图层和参数 → 用 Python/Node 递归解析 Firestore REST 格式

# 6. 从 app bundle 提取对应效果类型的 shader 模板
curl -s "https://www.unicorn.studio/assets/index-*.js" > app-bundle.js
# 搜索效果类型名定位 shader 代码

# 7. 组合参数 + shader 模板 → 构建独立 WebGL2 项目
```
