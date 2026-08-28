# Three.js TSL 识别与重建

Three.js r170+ 的 TSL (Three Shading Language) 用 JS 函数调用链组合 shader 节点图，运行时编译为 GLSL。

## 识别信号

1. Bundle 有大量 `uniform`/`shader` 但几乎没有 `precision`/`gl_FragColor`
2. canvas `data-engine` 显示 r170+
3. 存在 `.mul()`/`.add()`/`.toVar()`/`.assign()` 链式调用

## TSL → GLSL 映射

| TSL | GLSL |
|-----|------|
| `screenUV` | `gl_FragCoord.xy / resolution` |
| `viewportSize` | `uniform vec2 resolution` |
| `float()`/`vec2()`/`vec3()`/`vec4()` | 同名（但 TSL 中是 JS 函数） |
| `.mul()`/`.add()`/`.sub()`/`.div()` | `*`/`+`/`-`/`/` |
| `sin()`/`cos()`/`mix()`/`smoothstep()` | 同名 |
| `clamp()`/`abs()`/`fract()`/`floor()` | 同名 |
| `pow()`/`exp()`/`sqrt()`/`dot()`/`length()` | 同名 |
| `Fn()` | shader 函数包裹器（内联到 GLSL） |
| `uniform()` | `uniform <type> name` |
| `convertToTexture()` | RTT（多 pass 渲染） |
| `.sample(uv)` | `texture(sampler, uv)` |
| `.toVar()`/`.assign()` | 声明/赋值可变变量 |
| `.oneMinus()` | `1.0 - x` |

## 重建步骤

1. **定位**：搜索组件名附近的 `fragmentNode` 属性
2. **映射表**：从 bundle 顶部 import 语句推断 minified → TSL 函数名
   ```javascript
   import { A as screenUV, W as sin, ... } from "three-module"
   ```
3. **翻译**：链式调用 → GLSL 表达式
   ```javascript
   // TSL: screenUV.x.sub(center.x).mul(aspect)
   // GLSL: (uv.x - center.x) * aspect
   ```
4. **RTT**：`convertToTexture(childNode)` → 独立 pass 渲染到 FBO，主 shader 中 `texture()` 采样
