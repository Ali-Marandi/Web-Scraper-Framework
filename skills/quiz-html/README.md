# quiz-html · 网页题库生成器

把题目数组 → 一个可独立打开的 HTML 练习网页。

## ✨ 功能一览

- 📂 **双重筛选**：分类（学科/子模块） + 学习状态（已掌握/未做/错题）
- 🎯 **4 种题型**：选择 / 判断 / 填空 / 简答
- 🤖 **智能答题**：选 ≠ 提交，可反复改；答错给一次重试机会
- ⌨️ **键盘快捷键**：A/B/C/D · Enter · ← → · Space
- 📝 **模拟考模式**：选题量 + 限时 + 一次性提交 + 成绩页
- 🧠 **记忆口诀**：题目带 `memory_tip` 字段会高亮显示
- 🌓 **主题切换**：明 / 暗双主题，localStorage 记忆
- 💾 **进度持久化**：浏览器记住每题状态，关掉再开还在
- 📱 **移动端适配**：手机也能用

## 🚀 快速上手

```bash
# 1. 准备题目 JSON 文件（数组）
cat > /tmp/q.json << 'EOF'
[
  {"type":"single_choice","prompt":"1+1=?","options":["A. 1","B. 2","C. 3"],"answer":"B",
   "explanation":"基础运算","category":"数学 / 加减法","level":1}
]
EOF

# 2. 生成 HTML
python3 scripts/build_quiz_html.py /tmp/q.json --title "数学练习" --open
```

## 📁 目录结构

```
quiz-html/
├── SKILL.md                  # skill 描述（给 agent 用）
├── README.md                 # 本文件（给人看）
├── skill.yaml                # skill 元数据
├── scripts/
│   └── build_quiz_html.py    # 注入脚本
├── templates/
│   └── quiz_template.html    # HTML 模板（含 {{占位符}}）
└── examples/
    └── demo.html             # 示例：已注入的可直接打开的 demo
```

## 🔗 与 quiz-mastery 联动

本 skill 不直接出题，专门负责"题目 → 网页"这一步。
出题/导入请用 `quiz-mastery`。完整链路：

```
quiz-mastery 出题
       ↓
   题目 JSON
       ↓
  询问用户："要做成网页吗？"
       ↓ 用户说要
   quiz-html  ← 你在这里
       ↓
  生成 .html
       ↓
 浏览器打开 → 用户开始练
```

## 📝 题目字段

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `type` | ✅ | string | `single_choice` / `true_false` / `fill_blank` / `short_answer` |
| `prompt` | ✅ | string | 题干 |
| `options` | 选择题 | array | `["A. xxx", "B. yyy", ...]` |
| `answer` | ✅ | string | 标准答案 |
| `explanation` | 推荐 | string | 解析（支持 `**粗体**` `*斜体*` `\` 代码 \``） |
| `knowledge_point` | 推荐 | string | 知识点名（侧边栏分组用） |
| `category` | 推荐 | string | 分类路径，建议格式 `"学科 / 子模块"` |
| `level` | 可选 | int | 难度 1-3 |
| `memory_tip` | 可选 | string | 记忆口诀，会用橙色卡片高亮 |

## ⌨️ 用户使用快捷键

| 按键 | 作用 |
|---|---|
| `A` `B` `C` `D` | 选选项 |
| `T` `F` | 判断题 |
| `Enter` | 提交 |
| `←` `→` | 上一题 / 下一题 |
| `Space` | 查看答案 |
| `Ctrl/⌘+Enter` | 模拟考一键交卷 |

## 🛠️ 命令行参数

```
python3 build_quiz_html.py <questions.json> [options]

  --output, -o    输出 HTML 路径（默认：题目同目录）
  --title         页面标题
  --subtitle      副标题（默认自动生成）
  --id            题库 ID（用于 localStorage 隔离）
  --open          生成后用浏览器打开
```

## 🔍 退出码

| 码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 参数错误 / 文件不存在 / 模板缺失 |
| 2 | JSON 解析失败 / 数据格式不合法 |

## 📌 边界

| 任务 | 用谁 |
|---|---|
| 出题 / 评分 / 掌握度追踪 | `quiz-mastery` |
| 长期学习计划 | `study-buddy` |
| **把题目做成网页让用户在浏览器练** | **`quiz-html` (本 skill)** |
