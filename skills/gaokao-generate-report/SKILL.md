---
name: gaokao-generate-report
description: >-
  合并考生信息、志愿列表、专业推荐与院校推荐，生成融合分析与冲稳保志愿列表的 HTML 志愿填报报告。
  适用于高考志愿报告生成、志愿填报方案输出、志愿表可视化。
---

# 生成志愿填报报告

本 Skill 是流水线的**第五步**：合并前序 JSON，渲染 HTML 报告。

## 上下游

- **上游**：
  - `parsed.json`（志愿列表）
  - `major_recommendation.json`（专业推荐）
  - `school_recommendation.json`（院校推荐）
- **输出**：`volunteer_report.html`

## 环境准备

```bash
cd gaokao-generate-report
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 执行步骤

### 1. 合并为 analysis.json

```bash
python3 scripts/merge_analysis.py \
  --majors output/major_recommendation.json \
  --schools output/school_recommendation.json \
  -o output/analysis.json
```

`merge_analysis.py` 将专业推荐与院校推荐合并为 `generate_html.py` 所需的 `analysis.json` 结构。

### 2. 生成 HTML

```bash
python3 scripts/generate_html.py \
  -i output/parsed.json \
  -a output/analysis.json \
  -o output/volunteer_report.html
```

### 3. 交付用户

提供 `volunteer_report.html` 的**绝对路径**，并简要说明报告结构：

1. **综合测评与建议**（专业方向 + 院校策略）
2. **志愿推荐列表**（冲/稳/保，⭐ 推荐学校 / 🔥 推荐专业可点击查看详情）

## 合并前检查

| 检查项 | 说明 |
|--------|------|
| 专业字段一致 | `recommended_majors` 的 name/code 与 `parsed.json` 一致 |
| 院校字段一致 | `recommended_schools` 的 name/code 与 `parsed.json` 一致 |
| 文案完整 | `intro`、`strategy`、`school_strategy` 非空 |

若合并前发现推荐字段不匹配，应回到对应 Skill 修正 JSON。

## 附加资源

- [examples/analysis_merged_example.json](examples/analysis_merged_example.json) — 合并后的完整结构示例
