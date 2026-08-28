# shaders.com 提取工作流

shaders.com 是一个 shader 设计工具，使用 Nuxt.js + Three.js r183 TSL + Supabase。

## 识别特征

- URL: `shaders.com/collection/{slug}/{presetId}` 或 `shaders.com/preset/{id}`
- Canvas: `data-renderer="shaders"` + `data-engine="three.js r183"`
- Nuxt.js (`_nuxt/` 路径)
- Clerk 认证
- Supabase 存储 (`data.shaders.com/storage/v1/`)

## 关键架构差异

与 Unicorn Studio 完全不同：
- **不使用 GLSL** — 使用 Three.js TSL (Three Shader Language) 节点系统
- **87 种组件类型** — 每种有自己的 TSL `fragmentNode` 函数
- **定义数据是 XOR + base64 编码的**
- **组件可嵌套** — 树形结构（Glass 的 children 是其内部效果）

## 数据获取

### API 端点

```bash
# 集合变体（含编码定义）— 公开，无需认证
curl -s "https://shaders.com/api/collections/{slug}/{variantId}"

# 预览 API（含编码定义 + 水印注入）
curl -s "https://shaders.com/api/preview/preset/{presetId}"

# Nuxt payload（只含元数据，不含 shader 定义）
curl -s "https://shaders.com/collection/{slug}/{id}/_payload.json"
```

### 定义解码

定义使用 XOR + base64 编码，有两套密钥：

1. **网站 API**（`/api/collections/`）：
   - 混淆密钥: `a5e7244ad0973f07e10285bfa75ddbe4`（来自 Nuxt runtime config）
   - 组件/属性名用短代码（`C52`=Plasma, `p06`=angle, 等）
   - 解码: `JSON.parse(XOR(base64decode(encoded), keyBytes))`
   - 然后需要 code→name 映射表还原可读名称

2. **预览 API**（`/api/preview/`）：
   - 密钥: `shaders-preview-key`
   - 使用人类可读属性名（无需映射）
   - 注意：会注入水印 `ImageTexture` 组件

### 代码映射表

87 种组件按字母排序编号 `C00-C86`，233 种属性按字母排序编号 `p00-p232`。
映射表可从 JS bundle 中提取。

## 已知陷阱

### Y 轴翻转（反复出现！）

**SDF 纹理和 UV 坐标系统性 Y 翻转** — 已在多次提取中确认：

shaders.com 的 SDF 二进制（`.bin`）使用**图像坐标系**（Y=0 在顶部），
而 WebGL 纹理坐标 Y=0 在底部。直接加载会导致形状上下翻转。

```glsl
// 错误：直接用 shapeUV 采样
float sdf = texture(tSDF, shapeUV).r;

// 正确：翻转 Y
vec2 sdfUV = vec2(shapeUV.x, 1.0 - shapeUV.y);
float sdf = texture(tSDF, sdfUV).r;

// 注意：梯度的 Y 分量也需要取反
float dSdy = -(texture(tSDF, sdfUV - vec2(0, eps)).r - sdf) / eps;
```

同样，组件定义中的 `center.y` 使用 DOM 坐标（Y=0 在顶部），
在 Glass shader 中需要翻转：`center.y = 1.0 - center.y`。

### SDF 二进制格式

- 格式：512×512 Float32 单通道（1,048,576 bytes = 512² × 4）
- 值域：有符号距离，负值=内部，正值=外部（如 [-0.065, 0.486]）
- **不需要重映射**（不要做 `*2-1`），直接使用原始值
- 需要 `OES_texture_float_linear` 扩展做线性过滤
- WebGL2 加载：`gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32F, 512, 512, 0, gl.RED, gl.FLOAT, data)`

## 组件类型速查

| 类别 | 组件 | 复杂度 |
|------|------|--------|
| 纹理 | Plasma, Godrays, SimplexNoise, LinearGradient, RadialGradient | 中 |
| 形状 | Glass, Blob, Circle, Ring, Star, RoundedRect, Polygon | 高（Glass 最复杂） |
| 畸变 | WaveDistortion, ChromaticAberration, Liquify, Twirl, Bulge | 低-中 |
| 风格化 | FilmGrain, Halftone, Ascii, Dither, Glow, Bloom | 低-中 |
| 后处理 | Blur, ProgressiveBlur, BrightnessContrast, HueShift | 低 |

## 渲染管线

```
Three.js r183 TSL 渲染器
├─ 优先尝试 WebGPU，降级到 WebGL
├─ 正交相机 + 单个全屏四边形
├─ 组件树从底到顶合成
├─ 有 children 的组件用 RTT (render-to-texture) 捕获子内容
├─ blend mode 用自定义混合函数
└─ Glass 组件最复杂：SDF 评估 → 梯度法线 → 折射 → 色差 → 模糊 → 着色 → 高光 → 菲涅尔 → 合成
```

## 移植策略

1. **TSL 不能直接复制** — 需要翻译为 GLSL
2. **从 JS bundle 提取 TSL `fragmentNode`** → 反混淆 → 翻译为 GLSL
3. **组件树 → multi-pass FBO 管线**
4. **SDF 纹理需要 Y-flip**（见上方陷阱）
5. **Glass 组件参数多**（20+），需要精确匹配每个值

## 颜色空间处理（关键）

shaders.com 的 Three.js 渲染器全程在 **linear 空间** 工作：
- 组件定义中的 hex 颜色（如 `#2c2c42`）是 **sRGB** 值
- TSL 的 `color()` 函数自动将 sRGB→linear
- 所有中间 FBO 均存储 linear 值
- 最终由渲染器做 linear→sRGB 输出编码

移植时：
```glsl
// 1. 颜色定义时：sRGB hex → linear
vec3 colorA = pow(vec3(0.173, 0.173, 0.259), vec3(2.2));  // #2c2c42

// 2. 中间 pass：全部在 linear 空间计算，不做 gamma
// 3. 最终输出 pass（仅一次）：linear → sRGB
fragColor = vec4(pow(color.rgb, vec3(1.0/2.2)), color.a);
```

**常见错误**：在中间 pass 做 gamma 校正，导致后续 pass 在错误空间累加高光/菲涅尔。

## 参数精确对齐原则

**绝对禁止手动调参**。所有参数必须严格匹配 TSL 翻译中的公式和乘数：

```
TSL 原始乘数                → GLSL 必须使用的值
aberration * 0.06           → 不能改为 0.12
fresnelSoftness * 0.06      → 不能改为 0.12
fresnel (0.17)              → 不能改为 0.4
SDF gradient eps = 0.01     → 不能改为 0.005
```

如果视觉效果不匹配，应检查：
1. 颜色空间是否正确（sRGB/linear 混乱是最常见原因）
2. 噪声函数实现差异（Perlin 实现 vs `mx_noise_float`）
3. 时间基准是否正确
4. FBO 管线顺序是否与组件树匹配

**不要**通过修改乘数来"补偿"视觉差异 — 这会在其他参数配置下崩溃。

## TSL 时间约定

`timerLocal(speed)` = 每秒递增 `speed` 单位。移植时：`uTime = seconds * speed`。

然后 shader 内部再乘自己的系数：

| 组件 | speed 参数 | shader 内部乘数 | 实际速率/秒 |
|------|-----------|----------------|------------|
| Plasma | 2 | × 0.125 | 0.25 |
| Godrays | 0.7 | × 0.2 | 0.14 |
| WaveDistortion | 0.8 | × 0.5 | 0.4 |
| FilmGrain | — | 无时间（静态） | 0 |

## TSL→GLSL 标识符映射（SPCVwBqR.js）

常用映射（随构建版本变化，需动态提取）：

| 本地名 | TSL 函数 | GLSL |
|--------|---------|------|
| C / z | vec4() | vec4 |
| x / D | vec2() | vec2 |
| q / N | vec3() | vec3 |
| P / J | resolution | u_resolution |
| A / $ | uv | vUv |
| se / Oe | sin() | sin() |
| W / I | cos() | cos() |
| ne | mix() | mix() |
| D | smoothstep() | smoothstep() |
| fe | clamp() | clamp() |
| ar | mx_noise_float() | perlinNoise3D() |
| dr / Gt | timerLocal() | u_time × speed |
| Me / wt | rtt() | FBO pass |
| Ce | renderOutput() | fragColor |
