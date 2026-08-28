---
name: gaokao-recommend-schools
description: >-
  基于推荐专业列表、考生画像与志愿列表，由 Agent 分析推荐院校并给出个性化理由，
  输出结构化 school_recommendation.json。适用于高考院校推荐、选大学、冲稳保院校布局。
---

# 推荐院校与理由

本 Skill 是流水线的**第四步**：在已确定专业方向的基础上，从 `parsed.json` 中推荐院校并说明理由。

## 上下游

- **上游**：`student.json` + `parsed.json` + `major_recommendation.json`
- **下游**：[gaokao-generate-report](../gaokao-generate-report/SKILL.md)

## 输入

1. `student.json` — 意向城市、家庭、就业方向等
2. `parsed.json` — 院校标签、城市、冲稳保档位、录取概率
3. `major_recommendation.json` — 已推荐专业及方向，用于判断院校专业契合度

## Agent 分析任务

1. 优先推荐**包含已推荐专业**或**优势学科与专业方向契合**的院校。
2. 结合 `preferred_cities`、城市产业机会（可参考 [career_reference.md](career_reference.md) 城市表）、院校层次（985/211/双一流等）。
3. 兼顾冲/稳/保布局：核心目标放稳档，冲顶名校与保底院校均需有代表。
4. 挑选 **6–12 所**院校，每所撰写个性化 `modal` 推荐理由。

## 推荐理由应覆盖

- **地域优势**：城市产业与实习就业资源
- **院校层次**：标签与社会认可度
- **专业契合**：与 `major_recommendation.json` 的关联
- **录取性价比**：档位与概率是否匹配考生诉求

## 硬性约束

`recommended_schools` 每项的 `university_name`、`university_code` 必须与 `parsed.json` **完全一致**。

## 输出

保存为 `output/school_recommendation.json`，结构见 [examples/school_recommendation_template.json](examples/school_recommendation_template.json)。

```json
{
  "school_strategy": "院校布局策略（冲/稳/保如何分配）",
  "recommended_schools": [
    {
      "university_name": "...",
      "university_code": "...",
      "modal": {
        "title": "学校推荐原因：...",
        "body": "<h4>推荐原因</h4><ul><li>...</li></ul>"
      }
    }
  ]
}
```

## 向用户交付

- 保存 JSON 绝对路径
- 用自然语言解读院校推荐逻辑与梯度布局

## 附加资源

- [career_reference.md](career_reference.md) — 城市产业与院校层次参考
