# 框架识别特征

## Three.js

**未混淆**：`THREE.`, `WebGLRenderer`, `ShaderMaterial`, `BufferGeometry`

**混淆后**（通过构造参数推断）：

| 调用模式 | 原始类 |
|---------|--------|
| `new X({canvas, antialias, alpha})` | `WebGLRenderer` |
| `new X(fov, aspect, near, far)` — 4 数字 | `PerspectiveCamera` |
| `new X(-1, 1, 1, -1, 0, 1)` — 6 参数 | `OrthographicCamera` |
| `new X(w, h, {wrapS, minFilter})` | `WebGLRenderTarget` |
| `new X(data, w, h, format, type)` — Float32Array | `DataTexture` |
| `new X(2, 2)` 作为几何体 | `PlaneGeometry` |
| `new X({uniforms, vertexShader, fragmentShader})` | `ShaderMaterial` |
| `X.getElapsedTime()` | `Clock` |

**常量**：`ClampToEdgeWrapping`, `NearestFilter`, `RGBAFormat`, `FloatType`, `DoubleSide`

## 2D Canvas

`dataEngine: null` 时，用 `getContext('2d')` 有无 + `createShader`/`shaderSource` 有无区分：
- 有 `getContext('2d')`，无 WebGL 调用 → 纯 2D Canvas
- 有 WebGL 调用 → Raw WebGL / PixiJS

## Raw WebGL

```javascript
gl.createShader / gl.shaderSource / gl.compileShader / gl.createProgram
gl.bindBuffer / gl.bindFramebuffer / gl.drawArrays
```

## PixiJS

`PIXI.Application`, `PIXI.Filter`, `new PIXI.Filter(vertSrc, fragSrc, uniforms)`

## Babylon.js

`BABYLON.Engine`, `BABYLON.ShaderMaterial`, `BABYLON.Effect.ShadersStore`

## GPGPU 模式

两个 `WebGLRenderTarget`（ping-pong）+ `OrthographicCamera(-1,1,1,-1,0,1)` + `PlaneGeometry(2,2)` + `DataTexture` 初始位置 + `setRenderTarget` 循环

## 常见噪声

| 函数 | 类型 |
|------|------|
| `snoise` | Simplex noise (Ashima) |
| `cnoise` | Classic Perlin |
| `cellular` | Worley/Voronoi |
| `fbm` | Fractal Brownian Motion |
