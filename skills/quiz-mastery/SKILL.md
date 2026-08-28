---
name: quiz-mastery
description: 出题、测验、复习、掌握度追踪工具。**用户说"复习"、"巩固"、"回顾"任一关键词时优先触发本 skill**。当用户的请求与"题目/复习"相关时触发：把学习资料/PDF/材料转成题目练习（"给这个 PDF 出几道题"）、导入题目文件做练习（"我有一份题目文件，帮我做"）、复习已学内容（"复习一下昨天的"、"巩固一下"、"回顾下昨天"、"用艾宾浩斯帮我安排"）、遗忘曲线追踪、掌握度评分。**🔴 强制规则**：每次出题/导入题目成功后，**首轮展示题目前必须问一句**"要不要生成网页练习页？"，用户说要 → 调用 quiz-html skill。**不处理**：长期学习项目的进度管理、计划制定（→ study-buddy）。
---

# 测验大师 (Quiz Mastery)

## 两大核心能力

### 能力一：从学习资料出题
1. 用户提供学习资料（.md / .txt / .docx / .pdf / .ppt / .pptx）
2. 调用 `generate_from_material.py` 获取知识点提取 prompt
3. 将 prompt 发给 LLM，得到知识点 JSON
4. 调用 `service.save_knowledge_points()` 保存知识点
5. 调用 `run_quiz.py` 生成出题 prompt
6. 将 prompt 发给 LLM，得到题目 JSON
7. **⭐ 询问用户是否生成网页练习页**（见下方"网页练习联动"章节）
   - 用户说要 → 调用 `quiz-html` skill 生成 HTML 并打开
   - 用户说不用 → 走原流程
8. 逐题展示给用户，收集答案
9. 调用 `submit_answers.py` 提交评分

### 能力二：从题目文件练习
1. 用户提供题目文件（.md / .txt / .docx / .pdf / .ppt / .pptx）
2. 调用 `import_quiz.py` 获取题目解析 prompt
3. 将 prompt 发给 LLM，得到标准化题目 JSON
4. 调用 `service.import_questions()` 导入题目并创建 session
5. **⭐ 询问用户是否生成网页练习页**（见下方"网页练习联动"章节）
   - 用户说要 → 调用 `quiz-html` skill 生成 HTML 并打开
   - 用户说不用 → 走原流程
6. 逐题展示给用户，收集答案
7. 调用 `submit_answers.py` 提交评分

## 何时使用（触发条件）

1. **用户主动要求**："出几道题"、"测试一下"、"来个小测"、"练习题"、"考考我"
2. **用户说"复习"、"巩固"、"回顾"**：直接触发
3. **基于已有题目文件练习**：用户上传题目文件后触发

> ⚠️ **不处理 study-buddy 的"即时练习"**——那条链路由 study-buddy 走外部 `exam_take`，不调本 skill。

## 没历史数据时的兜底

当用户说"复习"但 `data/user_progress/` 是空的（新用户/没答过题）：
- **不要硬启动复习流程**——没数据可复习
- 主动告诉用户："还没有可复习的历史数据，要不要先用一份学习资料出题练一下？"
- 引导用户走"能力一：从学习资料出题"

## 难度系统

| 级别 | 含义 | 说明 |
|------|------|------|
| L1 | 识记 | 基础记忆和理解，考察概念辨认和基本事实 |
| L2 | 理解 | 深层理解，考察概念区分、原理解释和简单应用 |
| L3 | 应用 | 综合运用，考察实际场景应用、分析和问题解决 |

- **首次出题**：强制从 L1 开始
- **答对当前难度**：升一级（最高 L3）
- **答错当前难度**：降一级（最低 L1）

## 题型分配规则

| 级别 | 选择题 | 判断题 | 填空题 | 简答题 |
|------|--------|--------|--------|--------|
| L1 | 70% | 30% | - | - |
| L2 | 50% | 20% | 30% | - |
| L3 | 40% | 20% | 20% | 20% |

## 出题数量

- **默认每次出 3 道题**（一次对话展示 3 题，用户一次性回答后统一评分）
- 每轮最多 **15 题**（用户可要求调整数量）
- 简答题尽量少出，不自动评分（标记为 `needs_review`，由外部 LLM/人工评判）

## 薄弱知识点追踪

- **标记为薄弱**：累计错误次数 ≥ 3
- **不解除**：薄弱知识点只增不减，作为历史档案保留
- 内部数据保存在 `data/user_progress/`（错误次数、艾宾浩斯阶段等）
- **同步到 USER.md 第 3 节"薄弱知识点"**（由本 skill 直接写入，来源=`quiz-mastery`）：
  | 知识点 | 错误次数 | 来源 | 备注 |
  - 已有该知识点 → 更新错误次数
  - 未在表中 → 新增一行

## 遗忘曲线复习机制

基于艾宾浩斯遗忘曲线，按 **1天 → 2天 → 4天 → 7天 → 15天** 间隔安排复习：
- 答对：review_stage +1（推进到下一个间隔）
- 答错：review_stage 重置为 0（从头开始）
- 复习推荐包含：即将遗忘的知识点 + 最近 3 天薄弱知识点

## 脚本调用方式

### 1. 从学习资料提取知识点

```bash
python3 scripts/generate_from_material.py <file_path> <document_id>
```

输出知识点提取 prompt（JSON），将 prompts.system_prompt 和 prompts.user_prompt 发给 LLM。

### 2. 从题目文件导入题目

```bash
python3 scripts/import_quiz.py <file_path> <document_id> <user_id>
```

输出题目解析 prompt（JSON），将 prompts.system_prompt 和 prompts.user_prompt 发给 LLM。

### 3. 生成测验

```bash
python3 scripts/run_quiz.py <user_id> <document_id>
```

根据已保存的知识点和用户当前掌握度自动决定难度，输出出题 prompt（JSON）。

### 4. 提交答案

```bash
python3 scripts/submit_answers.py <user_id> <document_id> <session_id> '<answers_json>'
```

参数说明：
- `answers_json`：JSON 格式的答案字典，如 `{"q_001": "A", "q_002": "True"}`

返回评分结果：score、total、accuracy、逐题 results。

## 出题流程（面向 study-buddy 的调用说明）

1. 确定知识点来源（学习资料 or 已有题目文件）
2. 执行对应的提取/导入流程
3. 调用 `run_quiz.py` 生成出题 prompt
4. **每次展示 3 道题给用户**（一次性展示，编号清晰，不要逐题出），用户一次性回答后再统一评分
5. 收集用户回答（用户可以一次性回复 3 道题的答案）
6. 调用 `submit_answers.py` 提交评分
7. 将评分结果返回给 study-buddy，由其写入 memory 文件

⚠️ **本 skill 仅写入 USER.md 第 3 节"薄弱知识点"**（来源=`quiz-mastery`）；不写其他分区，也不写 `memory/`。其他持久化由 study-buddy 统一负责。

## 数据目录结构

```
skills/quiz-mastery/data/
├── knowledge_points/     ← 知识点定义（按 document_id）
├── sessions/             ← 测验会话记录
└── user_progress/        ← 用户掌握度数据（含薄弱标记、遗忘曲线）
```

## ⭐ 网页练习联动（与 quiz-html 协作）

每次拿到题目 JSON 之后（"能力一"步骤 7、"能力二"步骤 5），都要**主动问用户一句**：

> "题目准备好啦～ 要不要我把它们生成一个网页练习页？你可以在浏览器里慢慢做，错题会自动记下来，还能切换主题、模拟考试 🎯"

### 用户回应判定

| 用户说 | 判定 | 行动 |
|---|---|---|
| "要 / 好 / 嗯 / 来一个 / 生成 / 网页 / 浏览器" | ✅ 要 | 调用 `quiz-html` |
| "不用 / 不要 / 算了 / 直接做 / 这里做" | ❌ 不要 | 走原对话流程 |
| 没回应 / 不明确 | 默认 ❌ 不要 | 直接走原流程，不强推 |

### 调用 quiz-html 的具体步骤

```python
import json, subprocess, tempfile
from pathlib import Path

# 1. 把已经拿到的题目 JSON 写到临时文件
tmp_dir = Path(tempfile.mkdtemp(prefix="quiz_"))
qjson = tmp_dir / "questions.json"
qjson.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")

# 2. 决定输出路径（推荐放 ~/Desktop）
output = Path.home() / "Desktop" / f"quiz_{title_slug}.html"

# 3. 调脚本
result = subprocess.run([
    "python3",
    str(Path.home() / "Desktop/studybuddy_4.0/skills/quiz-html/scripts/build_quiz_html.py"),
    str(qjson),
    "--title", page_title,        # 如 "📚 物理 · 电学练习"
    "--output", str(output),
    "--open",                     # 生成后自动用浏览器打开
], capture_output=True, text=True)

info = json.loads(result.stdout)  # {"success": true, "output_path": "...", ...}
```

### 题目字段补全建议

调用前，最好给每道题补上以下字段（如果出题时没生成）：
- `category`：**一级分类，短词**（建议 2-6 字），用于网页顶部分类筛选 chip。
  - ✅ 推荐：`物理` / `数学` / `法律` / `历史` / `编程` / `通用`
  - ❌ 避免：`通用类 / 1.中华人民共和国证券法（1998年12月29日…）` 这种长串、含日期/编号/斜杠的写法
  - 如果非要分两级，用 `/` 分隔且二级也要短：`物理 / 电学`
- `knowledge_point`：知识点名（侧边栏分组用，可与 quiz-mastery 的 KP title 一致，不要带层级前缀）
- `memory_tip`：记忆口诀（可选，K12 学生很需要）

这样网页的分类筛选、侧栏分组、记忆卡片才能发挥作用。

### 边界

| 任务 | 用谁 |
|---|---|
| 出题、提取题目 | 本 skill (quiz-mastery) |
| 评分、掌握度追踪 | 本 skill (quiz-mastery) |
| **题目 → 网页练习页** | **quiz-html** |

调完 quiz-html 之后，**仍然要走 quiz-mastery 的评分流程**——网页里的答题状态是给用户自查用的，正式的 mastery 数据要靠 `submit_answers.py` 写入。两者并行不冲突。

