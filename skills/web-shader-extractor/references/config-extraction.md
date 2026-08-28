# 配置参数提取

配置值必须从源站提取，不猜测。（猜错实例：颜色差 60x、图案完全不同）

## 来源（按优先级）

### 1. 公开 REST API

```bash
# 在 JS bundle 中搜索 API 端点
grep -oE 'api/(presets|shaders|collections)[^"]*' /tmp/*.js
# 直接调用
curl -s -L --compressed 'https://example.com/api/collections/slug/uuid'
```

API 返回可能是编码的 → 见 `encoded-definitions.md`

### 2. Nuxt.js Payload

```bash
grep -oE '_payload\.json[^"]*' /tmp/page.html          # payload URL
grep -oE 'public:\{[^}]*\}' /tmp/page.html             # runtime config（可能含密钥）
```

### 3. Next.js

```bash
# App Router (RSC)
grep -oE '"(scene|glass|postProcessing)":\{' /tmp/page.html
# Pages Router
grep -o '<script id="__NEXT_DATA__"[^>]*>[^<]*' /tmp/page.html | sed 's/.*>//'
```

### 4. 内联 JSON / window 全局变量

```bash
grep -oE 'window\.__CONFIG__\s*=\s*\{[^;]+' /tmp/page.html
```

### 5. JS Bundle 默认值（最后手段）

```bash
grep -oE '(config|options|settings)\s*=\s*\{' /tmp/entry-chunk.js
```

## 验证

- 颜色范围：0-1 还是 0-255？
- resolution：像素值还是比例系数？
- 布尔值：`false` 是否跳过整个渲染 pass？
