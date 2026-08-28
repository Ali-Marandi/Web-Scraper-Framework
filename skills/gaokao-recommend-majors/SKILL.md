---
name: gaokao-recommend-majors
description: >-
  基于考生画像与 API 志愿列表，由 Agent 分析推荐适合的专业方向、就业出口与具体专业清单，
  输出结构化 major_recommendation.json。适用于高考专业推荐、选专业、就业方向分析。
---

# 推荐专业与就业方向

本 Skill 是流水线的**第三步**：纯 Agent 分析，无规则脚本。结合考生兴趣、成绩、就业意向与 `parsed.json` 中的真实专业，产出个性化专业推荐。

## 上下游

- **上游**：`student.json` + `parsed.json`（来自信息采集与获取志愿）
- **下游**：[gaokao-recommend-schools](../gaokao-recommend-schools/SKILL.md) 读取 `major_recommendation.json`

## 输入

1. `student.json` — 考生完整画像
2. `parsed.json` — 冲/稳/保志愿及每校 `majors`（含 `claim` 选科要求、录取概率）

## Agent 分析任务

1. 阅读 [career_reference.md](career_reference.md) 了解常见专业大类与就业出口（**参考，非硬规则**）。
2. 综合选科要求、各科成绩、兴趣、家庭、就业方向，判断 2–4 个**专业方向**（`major_directions`）。
3. 从 `parsed.json` 中挑选 **8–15 个**最契合的具体专业，写入 `recommended_majors`。
4. 撰写综合开篇 `intro` 与整体策略 `strategy`（专业优先视角）。

## 硬性约束

`recommended_majors` 每项的 `university_name`、`university_code`、`major_name`、`major_code` 必须与 `parsed.json` **完全一致**，否则最终报告无法显示 🔥 标签。

生成前在 `parsed.json` 中检索确认字段值。

## 输出

保存为 `output/major_recommendation.json`，结构见 [examples/major_recommendation_template.json](examples/major_recommendation_template.json)。

```json
{
  "student": { "...辅助画像字段..." },
  "intro": "综合测评开篇（HTML 可用 <strong>）",
  "strategy": "填报策略（专业视角）",
  "major_directions": [
    { "icon": "🧑‍💻", "title": "...", "match_level": "极高", "description": "..." }
  ],
  "recommended_majors": [
    {
      "major_name": "...",
      "major_code": "...",
      "university_name": "...",
      "university_code": "...",
      "modal": { "title": "...", "body": "<h4>...</h4><ul>...</ul>" }
    }
  ]
}
```

## 向用户交付

- 保存 JSON 绝对路径
- 用自然语言解读推荐的专业方向与 Top 专业理由

## 附加资源

- [career_reference.md](career_reference.md) — 专业/职业方向参考
