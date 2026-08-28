# Shader 代码提取：Agent Prompt 与反混淆

## Agent 深度提取 Prompt 模板

启动 Agent（subagent_type: general-purpose）分析 bundle：

```
分析文件 /tmp/main.js（约 X MB 的 minified JS bundle），提取所有与视觉特效相关的代码。

需要提取的内容：

1. **GLSL Shader 源码**：搜索包含 "precision", "uniform", "void main",
   "gl_FragColor", "gl_Position" 的字符串。提取完整的 vertex/fragment shader。

2. **渲染相关 JS 类**：canvas/renderer 创建、粒子/几何体管理、
   requestAnimationFrame 动画循环、鼠标交互代码。

3. **符号映射表**：minified 变量名 → 原始含义
   （THREE.Vector2, THREE.Color, THREE.Scene 等）

4. **配置和参数**：默认颜色、尺寸、密度等可调参数

将所有提取的代码保存到 /tmp/extracted-effects.txt，按功能分段标注。
```

**关键**：Agent 能看到完整文件，主上下文放不下 1MB+ 的 bundle。

## 识别 Minified 符号

通过构造参数和方法调用推断：

```javascript
new ??(40, w/h, 0.1, 1000)       → PerspectiveCamera(fov, aspect, near, far)
new ??(-1, 1, 1, -1, 0, 1)      → OrthographicCamera
new ??({canvas, antialias, ...}) → WebGLRenderer
new ??(2, 2)                     → PlaneGeometry(w, h)
new ??(data, w, h, fmt, type)    → DataTexture
new ??(w, h, {minFilter, ...})   → WebGLRenderTarget

??.setRenderTarget()  → renderer
??.getElapsedTime()   → clock
??.setAttribute()     → bufferGeometry
```

## 框架脱壳（React / Vue 等 → Vanilla JS）

Canvas 效果常被 React/Vue 等框架包装。脱壳思路：

1. **找副作用入口**：`useEffect`/`onMounted` 中的 Canvas 初始化代码就是核心逻辑
2. **收集 cleanup**：所有销毁操作（`removeEventListener`、`cancelAnimationFrame`、`observer.disconnect()`）汇总为 `destroy()` 函数
3. **丢弃响应式包装**：Canvas 状态（粒子位置、帧计数等）只在 RAF 内读写，直接用 `let` 变量，不需要 `useState`/`ref` 等响应式容器

原生 API（`IntersectionObserver`、`ResizeObserver`、`matchMedia` 等）不受框架影响，原样保留。

## 反混淆规则

1. **类名**：根据构造参数和方法调用推断
2. **变量名**：根据用途命名（`ringPos`, `particleScale`, `simMaterial`）
3. **Shader 变量**：uniform/varying 名通常未被 minify（`uTime`, `vPosition`）
4. **保留原始 GLSL**：shader 代码通常是完整字符串，直接提取
5. **字符串注入**：`${someVar.noise}` 表示噪声库被注入到 shader 中
