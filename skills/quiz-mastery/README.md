# Quiz Mastery Skill

OpenClaw agent 的独立出题/复习/掌握度追踪引擎。

## Features

- **从学习资料出题**：把 PDF / Word / Markdown 等学习材料转成分级测验（L1/L2/L3）
- **从题目文件导入练习**：解析已有题目文件，标准化后让用户答题
- **答案评分**：自动评分 + 逐题反馈
- **掌握度追踪**：跨三级难度记录用户进度
- **薄弱知识点**：累计错误次数 ≥ 3 → 标为薄弱（**只增不减**，作为历史档案）
- **遗忘曲线复习**：基于艾宾浩斯（1/2/4/7/15 天）安排复习

## Architecture

```
quiz-mastery/
├── SKILL.md                          # Skill metadata (LLM 读)
├── README.md                         # 本文件（人读）
├── skill.yaml                        # Skill 配置
├── scripts/
│   ├── generate_from_material.py     # 从学习资料提取知识点
│   ├── import_quiz.py                # 从题目文件导入题目
│   ├── run_quiz.py                   # 生成测验 prompt
│   └── submit_answers.py             # 提交答案 + 评分
├── src/quiz_mastery/                 # 核心引擎
└── data/
    ├── knowledge_points/             # 文档知识点定义
    ├── user_progress/                # 用户掌握度数据（含薄弱标记、艾宾浩斯阶段）
    └── sessions/                     # 测验会话记录
```

## Quick Start

### 1. 从学习资料提取知识点

```bash
python3 scripts/generate_from_material.py <file_path> <document_id>
```

输出知识点提取 prompt（JSON）。把 `prompts.system_prompt` 和 `prompts.user_prompt` 发给 LLM，得到知识点列表后调 `service.save_knowledge_points()` 保存。

### 2. 从题目文件导入

```bash
python3 scripts/import_quiz.py <file_path> <document_id> <user_id>
```

输出题目解析 prompt（JSON）。把 prompt 发给 LLM 得到标准化题目，调 `service.import_questions()` 导入。

### 3. 生成测验

```bash
python3 scripts/run_quiz.py <user_id> <document_id>
```

按用户当前掌握度自动决定难度，输出出题 prompt（JSON）。

### 4. 提交答案

```bash
python3 scripts/submit_answers.py <user_id> <document_id> <session_id> '<answers_json>'
```

返回：`score`、`total`、`accuracy`、逐题 `results`。

## 数据集成（与 OpenClaw agent 的关系）

本 skill **不写 `memory/`**，仅写 USER.md 第 3 节"薄弱知识点"。所有持久化由调用方 agent 统一负责，详见 SKILL.md。

| 数据 | 谁写 | 写到哪 |
|------|------|--------|
| 知识点定义、答题战绩、艾宾浩斯阶段 | 本 skill | `data/` 目录 |
| 薄弱知识点（错误次数 ≥ 3） | 本 skill | USER.md 第 3 节（来源=`quiz-mastery`） |
| 学习项目状态、DAY 排期 | study-buddy（上游 agent） | USER.md 第 2 节 |

## 难度系统

| 级别 | 含义 |
|------|------|
| L1 | 识记（基础记忆和理解） |
| L2 | 理解（深层理解、应用） |
| L3 | 应用（综合运用、问题解决） |

- 首次出题强制 L1 起步
- 答对升级（最高 L3），答错降级（最低 L1）

## Workflow

1. **Generate / Import**：从学习资料或题目文件创建知识点 + 题目
2. **Run**：生成测验
3. **Submit**：用户答题 → 自动评分 → 更新掌握度 / 薄弱标记
4. **Sync**：薄弱知识点写入 USER.md 第 3 节
