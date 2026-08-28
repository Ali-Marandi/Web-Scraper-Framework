# onBeforeCompile 注入 GLSL 的陷阱

## 场景

使用 `MeshPhysicalMaterial` 的 `transmission` 功能但需要增强效果时（如 drei 的 MeshTransmissionMaterial），
通过 `material.onBeforeCompile` 注入自定义 GLSL 代码。

## 常见陷阱

### 1. 函数签名版本差异

Three.js 不同版本的内置函数签名不同：

```glsl
// r166 及之前
vec4 getIBLVolumeRefraction(n, v, roughness, diffuseColor, specularColor, specularF90,
  pos, modelMatrix, viewMatrix, projectionMatrix, ior, thickness,
  attenuationColor, attenuationDistance)

// r167+ 新增 dispersion 参数
vec4 getIBLVolumeRefraction(n, v, roughness, diffuseColor, specularColor, specularF90,
  pos, modelMatrix, viewMatrix, projectionMatrix, dispersion, ior, thickness,
  attenuationColor, attenuationDistance)
```

**必须检查目标版本的实际签名**：
```bash
curl -s "https://cdn.jsdelivr.net/npm/three@0.167.0/src/renderers/shaders/ShaderChunk/transmission_pars_fragment.glsl.js" \
  | tr '\n' ' ' | grep -oE 'vec4 getIBLVolumeRefraction\([^)]+\)'
```

### 2. GLSL 不允许嵌套函数定义

```glsl
// 错误！GLSL 不支持函数内定义函数
void main() {
  float myRand(vec2 co) { return fract(sin(...)); }  // 编译失败
}

// 正确：函数必须在全局作用域
float myRand(vec2 co) { return fract(sin(...)); }
void main() {
  float r = myRand(uv);
}
```

### 3. 条件编译宏保护

某些变量只在特定宏下可用：
- `vWorldPosition` → 需要 `USE_TRANSMISSION` 启用
- `vTransmissionMapUv` → 需要 `USE_TRANSMISSIONMAP` 启用
- `roughnessFactor` → 在 `lights_physical_fragment` 之后可用

```glsl
// 在替换 #include <transmission_fragment> 时
// 原始代码自带 #ifdef USE_TRANSMISSION，替换代码也必须包含
#ifdef USE_TRANSMISSION
  // ... 你的代码
#endif
```

### 4. 变量名冲突

注入的全局函数/变量可能与 Three.js 内部冲突：
- 避免使用 `hash`, `random`, `noise` 等通用名
- 自定义函数加前缀：`snoise` → OK，`random` → 可能冲突
- uniform 名称加前缀 `u`：`uDistortion`, `uNoiseTime`

## 推荐模式

### 安全注入：修改 normal 而不替换整个 chunk

```javascript
material.onBeforeCompile = (shader) => {
  shader.uniforms.uDistortion = { value: 0 };
  shader.uniforms.uNoiseTime = { value: 0 };

  // 在 fragment shader 最前面加 uniform 声明 + 工具函数
  shader.fragmentShader = `
    uniform float uDistortion;
    uniform float uNoiseTime;
    ${noiseGLSL}
  ` + shader.fragmentShader;

  // 在 transmission_fragment 之前插入法线扰动
  shader.fragmentShader = shader.fragmentShader.replace(
    '#include <transmission_fragment>',
    `
    #ifdef USE_TRANSMISSION
    {
      // 扰动 normal 影响折射方向
      if (uDistortion > 0.0) {
        normal = normalize(normal + uDistortion * vec3(
          snoiseFractal(vWorldPosition * 0.08 + vec3(uNoiseTime)),
          snoiseFractal(vWorldPosition.zxy * 0.08 - vec3(uNoiseTime)),
          snoiseFractal(vWorldPosition.yxz * 0.08)
        ));
      }
    }
    #endif
    #include <transmission_fragment>
    `
  );
};
```

### 完整替换：需要随机多采样 + 色差时

当需要 MeshTransmissionMaterial 的颗粒感（随机采样噪声）和色差效果时，
必须完整替换 `#include <transmission_fragment>`。关键点：

1. 保留 `#ifdef USE_TRANSMISSION` / `#endif` 包裹
2. 保留 transmissionMap 和 thicknessMap 的 `#ifdef` 块
3. 使用正确版本的 `getIBLVolumeRefraction` 签名
4. 自己处理色差时，传 `dispersion = 0.0`，用不同 IOR 采样 R/G/B
5. 低采样数（6）+ 每像素随机偏移 → 产生可见的胶片颗粒感

## 视觉效果来源速查

| 效果 | 来源 | 实现方式 |
|------|------|----------|
| 玻璃折射 | MeshPhysicalMaterial `transmission` | Three.js 内置 |
| 色差 (chromatic aberration) | 不同 IOR 采样 R/G/B | 替换 transmission_fragment |
| 胶片颗粒感 | 低采样数 + 每像素随机方向 | 替换 transmission_fragment |
| 有机扭曲 | simplex noise 扰动法线/折射方向 | onBeforeCompile 注入 |
| 颜色偏移 | `dispersion` 属性 (r167+) | MeshPhysicalMaterial 内置 |
