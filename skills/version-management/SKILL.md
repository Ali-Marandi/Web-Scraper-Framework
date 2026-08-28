---
name: Version Management Skill
description: 独立通用 Skill：管理前端项目全生命周期。只要任务**可能**写出 .html/.jsx/.tsx/.vue 入口文件，就必须在写出第一个文件**之前**读取并遵循本 Skill（用于确定落盘路径与项目目录），而不是产出之后才补救；即使用户没有提到"项目"或"版本"也要使用。同时响应用户的版本相关操作（查看历史、恢复版本、切换项目等）。
---

# 版本管理

> **执行方式：** 版本管理**完全由本 Skill + `send_file` 实现**；前后端不维护 Git、不记版本流水。Agent 在云机项目目录执行 git 与文件操作。下文 git 均为完整可执行命令；后期封装为 tool 后替换指令段落，**决策逻辑与流程顺序不变**。

> **对用户沟通规则：** 版本管理的技术细节（git 命令、meta.json 更新、版本号计算等）是内部执行过程，禁止在对话中向用户展示或提及。用户只需看到：生成结果 + send_file 吐出的版本卡片。如需告知版本信息，只说"已保存为 V{n}"，不解释底层操作。

---

## ⚠️ 路径硬规则（最高优先级，写任何文件之前先执行本节）

**本 Skill 必须在写出第一个入口文件之前介入，而不是产出之后补救。** 任何入口文件（`.html` / `.jsx` / `.tsx` / `.vue`）第一次写入磁盘时，目标路径就必须位于 `我的项目/{项目名}/` 内。

### 基准路径

「我的项目」**固定位于工作区根目录**，与 `send_file` 的 `file_path` 写法 `/我的项目/{项目名}/...` 一一对应。执行任何 `mkdir` / `cd` / 写文件操作之前，必须先回到工作区根目录（或使用从根目录起算的完整路径）；**禁止**在未确认 `pwd` 的情况下使用相对路径 `我的项目/...`——这是「我的项目」文件夹长在错误位置的常见原因。

### 写文件前的固定顺序（不可调换）

```bash
# 1. 确定项目名（生成规则见 §1.2）
# 2. 回到工作区根目录，创建项目目录
cd {工作区根目录}
mkdir -p "我的项目/{项目名}/assets"
# 3. 进入项目目录，之后所有文件【直接】在此目录内创建
cd "我的项目/{项目名}"
# 4. 写入 index.html / prototype.html 等入口文件与代码文件
# 5. 再进入 §1 的 git / meta.json / send_file 流程
```

### 违例清单（以下任何一种都算流程错误，即使事后移动也算）

- 先把文件写到工作区根目录、`~/Desktop`、`/tmp` 或当前任意目录，再移动进项目目录
- 只在对话中贴代码块，不落盘
- 在项目目录之外执行写文件命令

### 写文件前自检（最后一道闸）

调用任何写文件命令之前，自问一句：**「我即将写入的目标路径，是否位于 `我的项目/{项目名}/` 之内？」** 答案不是 → 停止，先执行上面的固定顺序建目录，再写文件。

---


## 0. 与 Design Skill 的衔接（必读）

本 Skill 与 Design Skill **并列协作**（二者由同一个 Design Agent 同时承载）：Design Skill 负责设计产出，本 Skill 负责落盘与版本管理。本节描述二者在 HTML 交付场景下的协同过程。

> **触发不依赖 Design Skill。** 本 Skill 按文件类型触发：只要产出**或修改**入口文件（.html / .jsx / .tsx / .vue）就必须走本 Skill，与该任务是否经过 Design Skill 路由无关——包括未走任何设计流程、直接裸改已有 HTML 文字/颜色的情况（此时跳过 quality-gate，直接 资源校验 → git → meta.json → send_file）。

### 触发顺序（与 Design Skill 协同时）

```text
Design Skill 路由 → 场景 skill（portfolio / deck / prototype 等）
→ 【写文件前】按本 Skill 顶部「路径硬规则」先建 我的项目/{项目名}/
→ 产出 .html / .jsx / .tsx / .vue → 文件【直接写入】我的项目/{项目名}/（不是事后移动）
→ quality-gate.md 通过
→ 本 Skill（资源校验 → git → meta.json → send_file）
```

**禁止**经 Design Skill 的产出在 quality gate 未通过时 commit 或 `send_file`。
**禁止** Design Skill 在未经本 Skill 完成的情况下，将 HTML 网页项目视为已交付（仅贴代码块、不落盘、不写 `我的项目/` 均不算交付）。

### Design Skill 负责 / 本 Skill 负责

| 维度 | Design Skill | 本 Skill |
|------|--------------|----------|
| 场景、风格、版式、文案语言 | ✅ | — |
| quality-gate、Design Compliance 注释 | ✅ | — |
| 项目目录、assets 落盘、git 版本 | — | ✅ |
| `meta.json`、`send_file` 版本卡片 | — | ✅ |
| 对用户表述 | 设计结果说明 | 仅「已保存为 V{n}」 |

### commit 摘要建议

`git commit -m` 与 `meta.json` 的 `summary` 可带上场景，便于用户识别，例如：

- `V2: 首页 hero 改版（portfolio）`
- `V3: 基于 V1：换国际主义风格（landing-page）`

### 读取入口

Design 侧的衔接说明见：`SKILL.md` § Version Management Handoff。落盘、git、`meta.json`、`send_file` 等机制以本 Skill 为准（design 仅移交、不重复定义）。

---

## 0.1 预览现状（已知限制，维持线上）

| 现象 | 原因 | 当前处理 |
|------|------|----------|
| 多文件 HTML 项目（多页面，含多个html）无法跳转 | 预览走 OSS 链接，本次只处理了 HTML 和图片资源，但整包暂未上传 OSS，其他 html 引用的仍为相对路径无法被前端加载 | **暂不处理**，维持线上 |
| 部分场景点击历史版本预览可能仍看到最新版 | 预览时现扫工作区路径再生成 OSS，未按 tag 隔离 | **暂不处理**，维持线上 |
| 带 `.js``.css``assets/` (图片)的单文件 HTML 一般可预览 | 后端将 HTML 内资源相对路径替换为 OSS 链接 | 正常 |

**Agent 须知：** 上述限制不影响版本提交与 `send_file` 吐出；勿因预览失败而改为内联全部资源或强行单文件化。

---

## 1. 项目创建

### 1.1 判断规则

产出物包含以下类型的前端文件：`.html`、`.jsx`、`.tsx`、`.vue` → **必须**创建/更新项目并走版本流程（与当时走的是哪个调用方 Skill 无关）。
产出物是 image、doc、ppt、JSON、design spec、纯文本等 → 普通文件，不创建项目。

**常见误判（禁止）：** 因路由到某个调用方场景就认为「只贴代码块」或「写 Desktop 即可」；凡写出入口 HTML/前端文件即按项目交付。

### 1.2 路径强制检查（关键规则）

**所有 web_project 文件必须保存到 `我的项目/{项目名}/` 下。禁止保存到 workspace root、Desktop、临时目录或仅贴代码块。**

首选做法是**预防**而非补救：按文件顶部「⚠️ 路径硬规则」，在写出第一个文件之前就建好项目目录并直接写入。以下检查是 commit / `send_file` 前的**最后门禁**：

1. **写入前**：按顶部硬规则先建目录、直接写入正确位置
2. **commit / send_file 前**：执行下方门禁脚本；发现散落文件 → **必须先 `mv` 进项目目录**，重新校验通过后才能继续
3. **项目名生成规则**：根据用户意图、内容主题自动生成语义化中文或英文项目名（如 `北京旅游网站`、`企业客户管理后台`）

```bash
# 提交前路径门禁（在工作区根目录执行）
cd {工作区根目录}

# (a) 项目目录内必须存在至少一个入口文件（不限定 index.html，prototype.html 等同样有效）
ls "我的项目/{项目名}/"*.html "我的项目/{项目名}/"*.jsx \
   "我的项目/{项目名}/"*.tsx "我的项目/{项目名}/"*.vue 2>/dev/null | grep -q . \
  || { echo "ERROR: 我的项目/{项目名}/ 内没有入口文件，禁止 commit / send_file"; }

# (b) 工作区根目录及其他位置不得散落入口文件
find . -maxdepth 2 -not -path "./我的项目/*" \
  \( -name '*.html' -o -name '*.jsx' -o -name '*.tsx' -o -name '*.vue' \) \
  | while read -r f; do
      echo "STRAY: $f → 必须执行 mv \"$f\" \"我的项目/{项目名}/\" 后重新校验"
    done
```

任一项报 ERROR / STRAY → **禁止** commit 与 `send_file`，先纠正路径再重跑门禁。

### 1.3 文件结构规则

**核心原则：项目目录自包含，所有文件（代码 + 资源 + export 产物）都进 Git 追踪。**

- **单文件 vs 多文件：** 不强制单文件（内联 JS/CSS），也不鼓励一律多文件。根据项目复杂度自行判断：
  - 简单落地页、H5、单页展示 → 可单文件 `index.html`
  - 需复用样式/脚本、组件较多 → 可多文件（如 `index.html` + `style.css` + `main.js`）
- **用户上传落点：** `upload/`；项目内资源唯一目录：`我的项目/{项目名}/assets/`
- 代码中通过**相对路径**引用：`assets/{文件名}`，禁止引用 `upload/` 路径（预览时由后端将相对路径替换为 OSS 链接，Agent 无需手写 OSS 地址）
- 资源使用语义化英文命名（如 `hero-banner.png`），避免中文和空格
- `assets/` **进入 Git 追踪**——每个版本的快照包含当时的全部资源，恢复历史版本时代码和资源一起回退，确保任意历史版本可完整预览

#### 资源的处理（upload → assets，必做）

**禁止** HTML 写 `assets/xxx` 而磁盘无对应文件（常见裂图原因：只写了路径，未从 `upload/` 复制）。

1. 在 `upload/` 找源文件（消息附件路径、`find upload`、`ls -lt upload` 最近上传）
2. `mkdir -p 我的项目/{项目名}/assets`
3. `cp upload/{源} 我的项目/{项目名}/assets/{名}`——`{名}` 与 HTML 中 `assets/{名}` **完全一致**（HTML 已写好则按引用名复制重命名）
4. 再写/改 HTML 引用；多张图逐步 cp
5. **提交前校验**（有 MISSING 不得 commit / send_file）：

```bash
cd 我的项目/{项目名}
grep -ohE 'assets/[a-zA-Z0-9_.-]+' index.html 2>/dev/null | sort -u | while read -r ref; do
  [ -f "$ref" ] || echo "MISSING: $ref"
done
```

6. 无 MISSING 后按 §3 创建版本并 `send_file`

#### 资源来源（三种，落盘规则相同）

| 来源 | 典型顺序 | Agent 动作 | 是否新版本 |
|------|----------|------------|------------|
| **用户上传** | 先 HTML 后传图 / 先传图后 HTML | 从 `upload/` `cp` 到 `assets/`，引用与文件名一致；后传图时按现有 HTML 引用名命名 | 只 cp、未改代码 → ❌；改了 HTML 引用 → ✅ |
| **Agent 搜图** | 用户要配图、Agent 联网找图 | 下载到 `assets/{名}`（禁止仅写外链 URL）；再写/改 HTML 引用 | ✅ |
| **Agent 生图** | 用户要配图、Agent 生成图片 | 写入 `assets/{名}`（禁止只写 `assets/xxx` 不落盘）；再写 HTML | ✅ |

**共用：** 凡 HTML 含 `assets/` 引用，提交前必做上述校验；无文件则补落盘或改引用，禁止带 MISSING commit。
**先有 HTML 无图：** 可用占位文案/样式，但**不要**写不存在的 `assets/xxx`；用户传图或 Agent 补图后再写真实引用并 cp。

#### 跨版本保留用户图片（重要）

用户已上传并引用在 `assets/` 中的图片，在后续**自然语言 / 评论 / 参数编辑器**编辑产生新版本时：

- 用户**未**要求去掉该模块、**未**要求换图 → **必须保留**原有 `assets/` 文件及 HTML 中的 `assets/...` 引用，勿删除、勿改路径、勿要求用户重传
- 仅改样式、文案、布局等 → 只改代码文件，不动 `assets/`（除非用户明确要求替换资源）
- `git add .` 会自动将未改动的 `assets/` 文件纳入新版本快照（Git 自动复用未变文件，不重复存储），无需手动处理

#### 小样文件保留规则

若正式构建前存在小样阶段（模型先生成一个包含多个编号设计方向的 HTML 供用户选择），小样 HTML 必须移入 `我的项目/{项目名}/` 下保存，命名为 `style-samples.html`；用户不满意要求重新出方向时，后续轮次递增命名为 `style-samples-2.html`、`style-samples-3.html`，禁止覆盖已有小样文件。所有小样文件禁止命名为 `index.html` 或其他入口文件名。小样通过 `send_file` 吐出供用户预览和选择。`style-samples*.html` 已在 `.gitignore` 中通配排除，不进 Git 版本历史、不计入项目版本号。禁止在小样文件落盘到项目目录之前删除小样源文件/源文件夹。

### 1.4 创建流程

首次为用户产出入口文件时（**第 1–3 步必须发生在写出任何代码文件之前**，见顶部「⚠️ 路径硬规则」）：

1. 根据用户意图生成项目名称
2. 回到工作区根目录；若「我的项目」不存在：`mkdir -p 我的项目/`
3. 创建项目目录与 assets：`mkdir -p 我的项目/{项目名}/assets`，然后 `cd` 进入，**所有文件直接在此目录内写出**
4. 用户图先从 `upload/` cp 到 `assets/`，再写 HTML；禁止只写 `assets/` 路径不落盘
5. Git 初始化与首次提交：

```bash
cd 我的项目/{项目名}
git init
echo -e "meta.json\nstyle-samples*.html" > .gitignore
git add .
git commit -m "V1: {一句话摘要}"
git tag v1
# ↑ 以上必须全部执行完，然后创建 meta.json，最后调用 send_file 吐出 V1
```

6. 创建 `meta.json`（结构见 §5）
7. 调用 `send_file` 吐出该版本（见 §3.4），`title` = 项目名称（如 `北京旅游网站`）

### 1.5 项目目录结构

```
upload/                  ← 用户上传落点（不进项目 Git）

我的项目/
└── {项目名}/
    ├── .git/
    ├── .gitignore       ← 排除 meta.json 和 style-samples*.html
    ├── meta.json        ← 版本元数据（不进 Git）
    ├── style-samples*.html ← 设计方向小样，含多个编号方向供用户选择（不进 Git，可选，可多轮）
    ├── index.html       ← 主入口（进 Git，路径因项目而异）
    ├── ...              ← 其他代码文件（进 Git）
    ├── assets/          ← 资源文件（进 Git，随版本快照一起追踪）
    └── export/          ← export 导出产物（进 Git，固定图片类项目用）
```

---

## 2. 多项目管理

### 2.1 识别当前项目

按优先级判断：

1. 用户自然语言中明确提到的项目名
2. 前端传入的当前 tab 对应项目（仅用于识别项目，不决定编辑哪个版本）
3. 本 session 中最近操作的项目
4. 均无法判断 → 扫描 `我的项目/` 子目录，读各项目 `meta.json`，列出项目并追问

### 2.2 切换项目

读取目标项目 `meta.json`，告知用户：「已切换到项目：{项目名}，当前版本 V{n}」

### 2.3 非项目任务

非入口文件产出的任务不触发任何项目或版本操作。

---

## 3. 版本管理

### 3.1 编辑入口与版本确定

| 编辑入口 | 项目 | 版本 |
|---------|------|------|
| 评论功能（预览区选中元素写指令） | MD 指令含项目名 | MD 指令含版本号（预览中的版本） |
| 参数编辑器（预览区编辑按钮） | MD 指令含项目名 | MD 指令含版本号（预览中的版本） |
| 自然语言（对话框输入） | 见下方规则 | 见下方规则 |
| 对话流卡片「基于该版本编辑」 | 卡片对应项目 | 卡片对应版本（走 §4 合并流程） |

**自然语言默认：编辑最新项目的最新版本。**

确定项目：按 §2 优先级（用户指名 > 前端上下文 > 最近操作 > 追问）。

确定版本：

| 场景 | 处理方式 |
|------|----------|
| 用户明确指定版本（如「基于 V2 改标题」、或输入框预填「基于「{项目名}」V2版本进行编辑」） | 按指定版本 → §4 合并流程 |
| 用户指定项目未指定版本 | 该项目的最新版本 |
| 其他情况 | 默认最新项目的最新版本 |

不追问。所有版本均可恢复；误编非预期版本可通过恢复回退。

#### 评论编辑与参数编辑的处理规则

用户在预览区（包括历史版本预览）使用评论编辑或参数编辑后，前端生成 MD 指令发送给 Agent。MD 指令中包含**项目名**和**版本号**，Agent 按以下规则处理：

1. 从 MD 指令中解析项目名 → 定位 `我的项目/{项目名}/`
2. 从 MD 指令中解析版本号 → 得到 `V{n}`
3. 读取该项目 `meta.json` 的 `latest_version`，判断版本关系：
   - **指定版本 = 最新版本** → 直接在当前工作区编辑 → 按 §3.3 创建新版本
   - **指定版本 ≠ 最新版本（历史版本）** → **必须**按 §4.4 合并流程执行（先 `git checkout v{n} -- .` 恢复到指定版本，再执行编辑，最后一次性 commit 为新版本）。**禁止跳过恢复步骤**，无论 Agent 认为当前版本与目标版本差异多小，都必须严格恢复后再改。
4. 按锚点在项目目录内所有 HTML 文件中搜索匹配，定位目标元素并执行修改
5. 完成后按 §3.3 / §4.4 的 git 指令创建版本 + 更新 `meta.json` + `send_file`

> **MD 模板由前端维护。** 本 Skill 不定义具体 MD 格式；只要包含项目名、版本号、锚点、修改内容即可被 Agent 解析。

### 3.2 创建版本的时机

| 触发场景 | 是否生成新版本 | 说明 |
|--------|-------------|------|
| 首次生成 | ✅ V1 | 项目创建 |
| 自然语言编辑 | ✅ | 版本号递增 |
| 评论功能编辑 | ✅ | 版本号递增 |
| 参数编辑器保存 | ✅ | 改文本、样式参数、替换图片均视为新版本 |
| 版本恢复 | ✅ | 见 §4 |
| 基于历史版本编辑 | ✅ | §4 合并，产生一个版本 |
| 用户仅上传资源、无代码变更 | ❌ | 只写 `assets/`，不 commit |
| 用户上传资源且 Agent 更新了代码引用 | ✅ | 须 commit + `send_file` |
| 在同项目下新增入口文件（如新增 `light.html`） | ✅ | 新文件与现有文件一起提交为新版本 |
| 小样阶段产出 `style-samples*.html` | ❌ | 不进 Git、不计版本号，仅 `send_file` 吐出供用户选择 |

### 3.3 创建版本的 Git 指令

修改完成后，在项目目录执行：

```bash
cd 我的项目/{项目名}
LATEST_TAG=$(git tag --sort=-v:refname | head -n 1)
NEXT_NUM=$((${LATEST_TAG#v} + 1))
NEXT_TAG="v${NEXT_NUM}"
git add .
git commit -m "V${NEXT_NUM}: {一句话摘要}"
git tag $NEXT_TAG
# ↑ 以上必须全部执行完，然后更新 meta.json，最后调用 send_file 吐出新版本
```

### 3.4 对话流输出（send_file）

每生成一个新版本，必须调用 `send_file`。

#### 3.4.1 默认规则：单入口文件项目

| 参数 | 值 |
|------|-----|
| `ext` | 固定填 `web_project` |
| `title` | 项目名称，如 `北京旅游网站`；**不要**包含版本号（前端用 `version` 字段拼接）；绝对不能是具体文件的名称（如 index、main 等） |
| `file_path` | 项目主入口文件完整路径，如 `/我的项目/北京旅游网站/index.html` |
| `project_name` | 与 `meta.json` 中 `project_name` 一致 |
| `version` | 本次版本号，如 `V3` |

调用示例：
```json
{"title": "北京旅游网站", "ext": "web_project", "file_path": "/我的项目/北京旅游网站/index.html", "project_name": "北京旅游网站", "version": "V3"}
```

#### 3.4.2 多入口文件项目（新增规则）

当项目包含**多个独立入口 HTML 文件**时（例如 `index.html` + `light.html`，或多个页面）：

1. **所有入口文件必须在同一 commit 中提交**（`git add .` 自然包含全部）
2. **send_file 策略：**
   - 若只有一个**主入口**（其他为辅助），默认只吐主入口
   - 若调用方 Skill 有显式要求吐出多个文件（如 prototype 双文件），按调用方要求执行
   - 禁止遗漏：所有 HTML 文件都必须被 git 追踪
3. **禁止**对项目目录调用 `ext=directory` 吐文件夹

示例（`index.html` 为主入口，`light.html` 为新增变体）：
```bash
# 同一次 commit 包含两个文件
git add index.html light.html assets/
git commit -m "V4: 新增 light 主题变体"
git tag v4
```

send_file 只吐主入口：
```json
{"title": "北京旅游网站", "ext": "web_project", "file_path": "/我的项目/北京旅游网站/index.html", "project_name": "北京旅游网站", "version": "V4"}
```

#### 3.4.3 Prototype 双文件交付（稳定规则）

当调用方 Skill 为 `prototype.md` 且该版本包含双交付文件（可交互原型 + 流程文档）时：

1. **版本纳入范围（必做）**
   本次版本必须同时纳入并提交两个 HTML 文件（通常为 `prototype.html` 与 `flow.html`），禁止只提交其中一个。
2. **对话流输出（必做）**
   对同一版本号调用 `send_file` **两次**，分别吐出两个单文件：
   - 第一次：`prototype.html`
   - 第二次：`flow.html`
3. **卡片命名建议**
   在 `title` 中标注文件角色，便于用户区分（title 不含版本号）：
   - `{项目名}-prototype`
   - `{项目名}-flow`
4. **禁止项**
   - 禁止将 `prototype.html + flow.html` 打包为目录一次性吐出
   - 禁止只吐其中一个文件并声称已完成 prototype 双交付

示例（同一版本 V4，连续两次）：
```json
{"title":"企业客户管理后台-prototype","ext":"web_project","file_path":"/我的项目/企业客户管理后台/prototype.html","project_name":"企业客户管理后台","version":"V4"}
{"title":"企业客户管理后台-flow","ext":"web_project","file_path":"/我的项目/企业客户管理后台/flow.html","project_name":"企业客户管理后台","version":"V4"}
```

#### 3.4.4 固定图片导出项目（小红书卡片等，新增规则）

对于 `fixed-image` 输出目标的场景（如小红书卡片、封面图、长图），典型流程为：

1. **先生成 HTML**（设计阶段产物）→ 按常规保存到 `我的项目/{项目名}/`
2. **后执行 export** 导出图片 → 导出产物保存到 `我的项目/{项目名}/export/`
3. **版本管理：** HTML 和 `export/` 都进 Git 追踪，同一次 commit
4. **send_file 策略（必做）：**
   - **第一次：** 吐出 HTML 文件（`ext: web_project`）
   - **第二次：** 吐出 export 产物
     - 若导出为单张图片：`ext: 具体扩展名`（如 `png`、`jpg`），`file_path: /我的项目/{项目名}/export/xxx.png`
     - 若导出为文件夹（多张图）：`ext: directory`，`file_path: /我的项目/{项目名}/export/`

**关键规则：**
- HTML 和 export 产物**必须在同一个项目目录下**
- 两者**必须在同一个版本（commit）中**
- 禁止 export 产物散落在项目目录外

示例（小红书长图项目，V2）：
```bash
# 项目目录结构
cd 我的项目/小红书旅行攻略
git add .
git commit -m "V2: 优化封面配色与排版"
git tag v2
```

send_file 调用（连续两次）：
```json
{"title":"小红书旅行攻略","ext":"web_project","file_path":"/我的项目/小红书旅行攻略/index.html","project_name":"小红书旅行攻略","version":"V2"}
{"title":"小红书旅行攻略-export","ext":"directory","file_path":"/我的项目/小红书旅行攻略/export/"}
```

### 3.5 对话流卡片与「基于该版本编辑」

- **历史版本与最新版本**在预览区顶部展示一致（具体 UI 由前端实现）；Agent 不区分两套预览协议
- 对话流中**每个**由 `send_file` 产生的版本卡片均带「基于该版本编辑」按钮（前端实现）
- 用户点击后，输入框预填：**「基于「{项目名称}」V{n}版本进行编辑」**（例：`基于「北京旅游网站」V2版本进行编辑`；版本号用大写 `V` + 数字，与 `send_file.version` 一致）
- Agent 收到该句式 → 按 §4 **合并流程**处理（文案中 `V{n}` 转为 `TARGET_TAG=v{n}`）
- **最新版与历史版卡片**均展示该按钮；预览区顶栏样式一致（由前端实现，Agent 无额外动作）

> **说明：** 不提供单独的「版本列表」能力；用户通过对话流历史卡片或自然语言指定版本即可。

---

## 4. 版本恢复

### 4.1 恢复范围

恢复是**整个项目目录状态的恢复**（代码文件 + `assets/` 资源 + `export/` 产物）。`git checkout` 还原目标版本的完整工作树，确保恢复后的版本可完整预览。

### 4.2 恢复入口

没有独立的前端「恢复」按钮。恢复通过以下方式触发：

| 入口 | 说明 |
|------|------|
| 自然语言「恢复到 V2」 | Agent 直接执行 §4.3 标准恢复 |
| 自然语言「基于 V2 改风格」 | Agent 执行 §4.4 合并流程（恢复 + 编辑 = 一个版本） |
| 对话流卡片「基于该版本编辑」按钮 | 输入框预填「基于「{项目名}」V{n}版本进行编辑」→ 用户发送 → Agent 按 §4.4 合并流程处理 |
| 评论 / 参数编辑（历史版本预览中） | MD 指令含历史版本号 → Agent 按 §4.4 合并流程处理 |

### 4.3 标准恢复（仅恢复，不附带编辑）

恢复 = checkout + 提交新版本 + send_file，三步缺一不可。仅执行 checkout 不算恢复完成。
执行指令：

```bash
cd 我的项目/{项目名}
TARGET_TAG="v{用户指定的版本号}"
LATEST_TAG=$(git tag --sort=-v:refname | head -n 1)
NEXT_NUM=$((${LATEST_TAG#v} + 1))
NEXT_TAG="v${NEXT_NUM}"
git checkout $TARGET_TAG -- .
git add .
git commit -m "V${NEXT_NUM}: 恢复至 V{目标版本号}"
git tag $NEXT_TAG
# ↑ 以上必须全部执行完，然后更新 meta.json，最后调用 send_file 吐出新版本
```

**恢复后状态理解：** 以工作区文件（代码 + `assets/` + `export/`）+ `meta.json` 为准；不依赖后端版本服务或历史对话回放。

恢复后 Agent 向用户确认：
- 当前项目名和新版本号
- 包含哪些文件/页面
- 相比恢复前的差异（如"不包含美食推荐板块，该功能在 V3 中添加"）
- 调用 `send_file` 吐出新版本主入口（参数同 §3.4）。

版本编号始终递增（V4 恢复到 V2 → 产生 V5）。原有版本保留。

### 4.4 恢复 + 编辑合并流程（只产生一个版本）

适用：用户指定基于历史版本编辑（含「基于「{项目名称}」V{n}版本进行编辑」）。

**版本号规则：** 无论基于哪个历史版本编辑，新版本号**必须**是当前最新版本 +1 的纯数字递增（如当前 V8 → 新版本 V9）。**禁止**使用带后缀的版本号（如 `V4-light`、`V4-dark`、`V2-new` 等），禁止以基准版本号为前缀命名。**禁止**覆盖、移动或删除已有版本的 tag——已有版本永远保留，新版本只能追加。

执行指令：
```bash
cd 我的项目/{项目名}
TARGET_TAG="v{目标版本号}"
git checkout $TARGET_TAG -- .
# ↓ 在此基础上执行用户请求的编辑（修改文件内容），不做中间 commit
LATEST_TAG=$(git tag --sort=-v:refname | head -n 1)
NEXT_NUM=$((${LATEST_TAG#v} + 1))
NEXT_TAG="v${NEXT_NUM}"
git add .
git commit -m "V${NEXT_NUM}: 基于 V{目标版本号}：{编辑内容摘要}"
git tag $NEXT_TAG
# ↑ 以上必须全部执行完，然后更新 meta.json，最后调用 send_file 吐出新版本
```

---

## 5. meta.json 结构

每个项目一份，记录项目整体状态。通过 `.gitignore` 排除，不进入版本历史。

```json
{
  "project_name": "北京旅游网站",
  "latest_version": "v3",
  "is_published": false,
  "published_version": null,
  "domain": null,
  "versions": [
    {
      "id": "v1",
      "timestamp": "2026-05-01T14:30:00+08:00",
      "based_on": null,
      "summary": "首页 + 景点列表"
    },
    {
      "id": "v2",
      "timestamp": "2026-05-05T10:30:00+08:00",
      "based_on": null,
      "summary": "风格变更为国际主义"
    },
    {
      "id": "v3",
      "timestamp": "2026-05-06T14:30:00+08:00",
      "based_on": "v1",
      "summary": "基于 V1：重新设计页面布局"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| project_name | string | 项目名称，Agent 自动生成，用户可修改 |
| latest_version | string | 当前最新版本号（如 "v5"） |
| is_published / published_version / domain | 一期默认 false / null |
| versions[].id | string | 版本号（如 "v1"） |
| versions[].timestamp | string | 创建时间（ISO 8601 带时区） |
| versions[].based_on | string \| null | 仅在恢复或基于历史版本编辑时有值，指向基准版本号；普通编辑时为 null |
| versions[].summary | string | Agent 自动生成的一句话变更摘要 |

---

## 6. 操作速查

| 用户行为 | 执行动作 |
|--------|--------|
| 「做一个 XX 网站」 | **先建** `我的项目/{项目名}/` → 在目录内生成文件 → §1 创建（git init + V1）→ `send_file` |
| 「做一个产品原型（prototype）」 | **先建**项目目录 → 在目录内生成 `prototype.html` + `flow.html` → 同版 commit（两文件都进 Git）→ 按 §3.4.3 连续两次 `send_file` |
| 「把标题改大一点」（无特殊上下文） | 编辑最新项目最新版 → §3.3 创建版本指令 → `send_file` |
| 「在现有项目下加 light 主题」 | 生成 `light.html` → 与现有文件同 commit → `send_file` 吐主入口 |
| 「基于 V2 改标题」 / 预填「基于「{项目名}」V2版本进行编辑」 | §4 合并流程 → `send_file` |
| 评论 / 参数编辑 | 解析 MD 指令中的项目名+版本号 → 按 §3.1 处理规则判断走 §3.3 或 §4.4 → `send_file` |
| 用户上传图（`upload/`） | `cp` → `assets/` → 对齐 HTML → §1 校验 → 改代码则 §3.3 |
| 先有 HTML 后传图 | 按 HTML 引用名 `cp`；未改代码不 commit，改引用则新版本 |
| Agent 搜图/生图填站 | 下载或写入 `assets/` → 写引用 → §1 校验 → §3.3 |
| 用户仅上传、无代码变更 | 只写 `assets/`，不 commit |
| 样式修改且未要求换图/删模块 | 改代码，**保留 assets 引用和文件** → §3.3 → `send_file` |
| 「恢复到 V2」 | §4 标准恢复（代码 + assets 一起回退）→ `send_file` |
| 点击卡片「基于该版本编辑」 | 用户发送预填文案 → §4 合并 → `send_file` |
| 自然语言说"发布"/"下线" | 引导用户使用前端发布按钮（一期暂不实现） |
| 「帮我写一份方案」 | 不触发版本管理 |
| 指代不明 | 扫描 `我的项目/` → 追问 |
| 小红书卡片 / 封面图 | 生成 HTML → 保存到项目 → export 到 `export/` → 同 commit → HTML `send_file` + export `send_file` |
| 小样阶段（「先出几个方向」） | 生成 `style-samples.html` → 保存到 `我的项目/{项目名}/` → `send_file` 吐出 → 等用户选方向 → 不 commit、不计版本号 |

---

## 7. 附录：预览与路径（Agent 参考）

- **工作区内：** HTML 使用 `assets/xxx.png` 等相对路径；多文件项目内 `link` / `script` 使用相对路径引用同目录或子目录代码文件
- **用户预览时：** 后端在云机解析绝对路径并替换为 OSS 链接；Agent **不要**在源码中写 OSS URL
- **Git 追踪范围：** 代码文件 + `assets/` 资源 + `export/` 产物均进 Git；`meta.json` 和 `style-samples*.html` 被 `.gitignore` 排除
- **已知限制：** 多文件项目的 JS/CSS 预览、历史版本预览与最新不一致——见 §0.1，本期不修复
