# 移植策略

## 框架选择

```
纯 2D Canvas（getContext('2d')，无 WebGL）？
├─ YES → Vanilla JS（零依赖，见下方 § 2D Canvas）
└─ NO  → 纯 2D 全屏 shader / 后处理？
         ├─ YES → 原生 WebGL2（零依赖）
         └─ NO  → 涉及 3D / PBR / GPGPU / onBeforeCompile？
                  ├─ YES → 保留原始框架（CDN importmap）
                  └─ 不确定 → 先用原始框架，Phase 6 再评估
```

## 原生 WebGL 项目结构

```
<name>/
├── index.html        # <canvas>
├── js/
│   ├── main.js       # WebGL2 初始化 + 多 pass 渲染循环
│   └── shaders/      # .glsl.js（export const fragmentShader）
└── README.md
```

- `canvas.getContext('webgl2')` + `#version 300 es`（`in`/`out`、`texture()`）
- 多 pass 用 framebuffer + texture attachment
- `requestAnimationFrame` 驱动

## Three.js 项目结构

```
<name>/
├── index.html        # importmap CDN
├── js/
│   ├── main.js       # 场景/相机/渲染器 + RTT 管线
│   └── shaders/      # .glsl.js
└── README.md
```

- `RawShaderMaterial` + `glslVersion: THREE.GLSL3`
- `WebGLRenderTarget` 做多 pass
- CDN importmap，零安装

CDN 模板：
```html
<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.183.0/build/three.module.js" } }
</script>
```

验证：`curl -sI '<url>' | head -3`

## 多层合成场景移植要点

从 Unicorn Studio / curtains.js 等 no-code 工具提取的场景通常有复杂的 FBO 链。以下是常见陷阱和正确做法：

### 1. 理解 parentLayer 与 effects 的父子关系

在 Unicorn Studio 中：
- **Element 层**（shape/text/image）的 `effects[]` 数组存储子效果的 UUID
- **Effect 层**的 `parentLayer` 字段指向父元素的 UUID
- 子效果按 effects 数组顺序依次渲染，每个 pass 读取前一个 pass 的 FBO

移植时必须还原这个链式 FBO 结构，不能简单合并成一个 pass。

### 2. showBg=0 的透明背景

`showBg=0` 意味着 shader 在未命中几何体的区域输出 `vec4(0)`（完全透明）。
这不是"黑色"，而是**透明**，后续合成时会显示下方图层。

```glsl
// 正确：showBg=0 → 透明
if (hit < 0.5) { fragColor = vec4(0.0); return; }

// 错误：输出黑色（会覆盖下方图层）
if (hit < 0.5) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
```

移植时必须用 alpha composite pass（`fg + bg * (1 - fg.a)`）将结果叠加到下方图层。

### 3. 文字/图片元素的合成方式

Element 层（text/image）需要用 Canvas 2D 渲染后作为纹理上传 WebGL。
**合成方式决定了视觉效果**：

```glsl
// 错误：alpha-over 覆盖（丢失背景纹理）
fragColor = mix(bg, vec4(txt.rgb, 1.0), txt.a);

// 错误：additive（饱和为白色，丢失色彩变化）
fragColor = vec4(bg.rgb + txt.rgb * txt.a, 1.0);

// 正确：亮度放大（保留背景噪声的色彩纹理变化）
fragColor = vec4(bg.rgb * mix(1.0, amplifyFactor, txt.a), 1.0);
```

**原理**：原始场景中文字元素叠加在噪声层上，经过 glyph dither 后，
字符颜色取自该位置的像素色。如果文字区域是平坦单色，ASCII 字符就是单色的。
用亮度放大方式，噪声的色相比例完整保留（紫:青:暗 按相同系数放大），
glyph dither 后的字符就带有噪声纹理的色彩变化。

### 4. 重复效果实例

同一种效果（如 noiseFill）可能在场景中出现多次：一次作为背景独立层，
一次作为 shape group 的子效果。参数可能相同但在管线中位置不同，
子效果的输出会被后续效果（如 SDF 折射）处理，产生不同的视觉。

### 5. Glyph Atlas 兼容性

base64 内嵌的 PNG glyph atlas 在某些浏览器/WebGL 环境中 `texImage2D` 会报
`INVALID_VALUE: bad image data`。推荐用 Canvas 2D 动态生成。

### 6. 颜色空间一致性（最常见的视觉偏差来源）

Three.js / shaders.com 等工具全程在 **linear 空间** 工作。移植到原生 WebGL 时：

```
错误做法（每个 pass 独立 gamma）：
  Pass1: 输出 pow(linear, 1/2.2)    ← sRGB
  Pass2: 读入 sRGB + 计算高光(linear) + 输出 pow(result, 1/2.2)  ← 混乱！

正确做法（全程 linear，最终一次 gamma）：
  Pass1~N: 全部输出 linear 值
  Final:   pow(linear, 1/2.2)        ← 唯一一次 sRGB 编码
```

hex 颜色定义 → `pow(srgb, 2.2)` 转 linear → 全程 linear 计算 → 最终 `pow(linear, 1/2.2)` 输出。

### 7. 参数精确对齐原则

**绝对禁止手动调参来"补偿"视觉差异**。所有公式乘数必须与原始代码完全一致。
如果效果不对，应排查颜色空间、噪声实现、时间基准等根因，而不是改乘数。
手动调参在当前配置下可能看起来更好，但会在其他参数组合下崩溃。

## 2D Canvas

每个效果一个文件，导出 `create<Name>Effect(container)` → `{ destroy }`。多效果用 `main.js` 管理切换。

### 性能要求

- `IntersectionObserver` + `visibilitychange` — 不可见时停止 RAF
- DPR 上限 `Math.min(devicePixelRatio, 2)`
- 后处理用离屏 Canvas 缓存，静态内容仅 resize 时重建
- 大量粒子数据用 `Float32Array`

## 通用规范

- ES Module（`import`/`export`）
- minified 变量名替换为有意义名称
- README 含效果说明、技术原理、可调参数

## Phase 6：简化评估

**触发**：移植完成后自行验证效果正确。**提议而非自动执行** — 这是全流程唯一需要用户决策的步骤。

```
只用了 RawShaderMaterial + WebGLRenderTarget + fullscreen quad？
├─ → 可简化为原生 WebGL2（减少 ~600KB）
用到 PBR / onBeforeCompile / 3D 场景？
├─ → 不简化
不确定？
└─ → 不提议
```
