---
name: web-shader-extractor
description: |
  从网页中提取 WebGL/Canvas/Shader 视觉特效代码，反混淆后移植为独立原生 JS 项目。
  触发条件：用户提供网址并要求提取 shader、提取特效、提取动画效果、提取 canvas 效果、
  复刻某网站的视觉效果、"把这个网站的背景效果扒下来" 等。
---

# Web Shader Extractor

从网页提取 WebGL/Canvas/Shader 特效，反混淆并移植为独立项目。

核心原则：
- **先 1:1 复刻，确认正确后再考虑简化框架**
- **全程自主执行，不中断用户** — 提取是只读操作，安全性无风险。除 Phase 6 简化提议外，所有步骤自动完成，不询问用户确认。遇到问题自行判断最佳方案继续推进，只在需要用户做产品决策时才询问。

## Phase 0: 环境检查（首次自动执行）

在开始提取前，检查并自动安装所需依赖。**不要询问用户，直接安装**。

```bash
# 1. 检查 Node.js
node --version 2>/dev/null || {
  echo "Node.js not found, installing..."
  # macOS
  brew install node 2>/dev/null || {
    # fallback: 直接下载 LTS
    curl -fsSL https://nodejs.org/dist/v22.15.0/node-v22.15.0-darwin-arm64.tar.gz | tar xz -C /usr/local --strip-components=1
  }
}

# 2. Playwright 及浏览器（fetch-rendered-dom.mjs 内置自动安装，但这里预检可提前发现问题）
RUNNER_DIR="$HOME/.cache/playwright-runner"
if [ ! -d "$RUNNER_DIR/node_modules/playwright" ]; then
  echo "Installing Playwright (one-time setup)..."
  mkdir -p "$RUNNER_DIR"
  echo '{"type":"module"}' > "$RUNNER_DIR/package.json"
  npm install playwright --prefix "$RUNNER_DIR"
  npx --prefix "$RUNNER_DIR" playwright install chromium
  echo "Playwright + Chromium installed."
fi
```

如果安装过程中遇到权限或网络问题，尝试以下备选方案：
- npm 权限问题 → 使用 `--prefix` 安装到用户目录
- 网络问题（Chromium 下载慢）→ 设置 `PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright` 使用国内镜像
- 实在无法安装 Playwright → 降级为纯 curl 模式（跳过 DOM 渲染，仅分析静态 HTML + JS bundle），在 Phase 2 中标注可能缺失 canvas-info

## Phase 1: 获取源码

**并行执行**：Playwright 获取渲染后 DOM + curl 获取静态 HTML。

```bash
# Playwright（获取 canvas 引擎版本、组件树、运行时网络请求）
node ~/.claude/skills/web-shader-extractor/scripts/fetch-rendered-dom.mjs '<URL>'
# → /tmp/rendered/: dom.html, canvas-info.json, network.json, screenshot.png, console.log

# curl（获取原始 HTML，用于提取内嵌配置和密钥）
curl -s -L --compressed '<URL>' > /tmp/page.html
```

如果 Playwright 脚本失败（未安装/启动异常），先尝试自动修复（重新安装依赖），若仍失败则降级为纯 curl 模式继续工作，不要停下来询问用户。

从 network.json 和 HTML 交叉提取 JS URL，批量下载到 /tmp/。

### Phase 2: 技术栈识别

```
canvas-info.json 的 dataEngine 字段：
├─ "three.js rXXX" → Three.js（r170+ 可能是 TSL → references/tsl-extraction.md）
├─ "Babylon.js vX.X" → Babylon.js
├─ null → 进一步区分：
│   ├─ bundle 含 createShader/shaderSource → Raw WebGL / PixiJS
│   └─ bundle 含 getContext('2d') 且无 WebGL 调用 → 2D Canvas（→ references/porting-strategy.md § 2D Canvas）
└─ 无 canvas → CSS/SVG 动画

URL 或 HTML 特征匹配已知平台 → 直接跳转专用工作流（跳过通用 Phase 3-4）：
├─ unicorn.studio → references/unicorn-studio.md（Firestore REST API 直取配置+shader）
└─ shaders.com → references/shaders-com.md（Nuxt payload + XOR 解码 + TSL→GLSL 翻译）

扫描确认：bash scripts/scan-bundle.sh /tmp/*.js
→ 框架特征速查 references/tech-signatures.md
```

### Phase 3: 配置提取

```
1. 搜索公开 API → 直接获取配置（API 返回可能是编码的 → references/encoded-definitions.md）
2. 从 Nuxt payload / __NEXT_DATA__ / HTML 内嵌 JSON 提取
3. 从 JS bundle 提取默认值
→ 详见 references/config-extraction.md
```

### Phase 4: Shader 代码提取

用 **Agent** 分析 JS bundle（1MB+ 不适合主上下文）。
→ Agent prompt 模板和反混淆规则 `references/extraction-workflow.md`

### Phase 5: 移植

```
纯 2D 全屏 shader → 原生 WebGL2（零依赖）
3D / PBR / GPGPU → 保留原始框架（CDN importmap）
不确定 → 先用原始框架，Phase 6 再评估
→ 详见 references/porting-strategy.md
```

### Phase 6: 简化评估

移植完成后，自行验证效果（打开页面截图对比）。如果效果正确且存在简化空间，**向用户提议简化方案**，由用户决定是否执行。

### Phase 7: 提取报告（询问用户是否生成）

提取完成后，**询问用户**是否生成 `EXTRACTION-REPORT.md`（会消耗额外 token 回顾对话历史）。

报告内容结构：
```markdown
# 提取报告：{项目名}
**来源/作者/平台/时间**

## 目标效果（一句话描述）
## 提取思路与时间线（每个迭代的问题→修复）
## 场景结构（组件树/图层结构）
## 最终渲染管线（pass 列表）
## 关键资源文件
## 发现的关键经验（表格：经验/影响/沉淀位置）
## 剩余已知差异
## 技术栈（原始 vs 移植）
```

报告放在项目目录内（如 `ascii-glyph-dither/EXTRACTION-REPORT.md`）。

## Reference 索引

| 需要时 | 读取 |
|--------|------|
| 识别框架（Three.js/WebGL/PixiJS 特征） | `references/tech-signatures.md` |
| Agent 提取 prompt + 反混淆规则 | `references/extraction-workflow.md` |
| 获取配置参数（API/payload/内嵌） | `references/config-extraction.md` |
| Three.js TSL 节点 shader 重建 | `references/tsl-extraction.md` |
| 编码/加密配置解码 | `references/encoded-definitions.md` |
| onBeforeCompile GLSL 注入陷阱 | `references/shader-injection.md` |
| 移植框架选择 + 项目结构 | `references/porting-strategy.md` |
| **Unicorn Studio** 专用流程（curtains.js + Firestore） | `references/unicorn-studio.md` |
| **shaders.com** 专用流程（TSL + XOR 编码 + Y-flip 陷阱） | `references/shaders-com.md` |
