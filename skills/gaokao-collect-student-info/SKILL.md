---
name: gaokao-collect-student-info
description: >-
  高考志愿填报信息采集：以考生原生表述为准，收集省份、分数、选科等 API 必填项及兴趣、
  家庭、就业方向等辅助信息，尽量不做改写与过度归纳，输出结构化 student.json。
  适用于高考志愿咨询开场、考生信息登记、志愿填报前的信息收集。
---

# 高考考生信息采集

本 Skill 是志愿推荐流水线的**第一步**，仅负责与用户对话并产出 `student.json`，不调用 API、不做推荐。

## 核心原则：还原原生描述

**只负责收集，不负责加工。** 下游专业推荐、院校推荐依赖考生**自己怎么说**，过度改写会造成信息 gap。

| 做法 | 说明 |
|------|------|
| ✅ 保留原话 | `interests`、`family_situation`、`career_direction`、`notes` 等文本字段，**尽量使用考生原句或贴近原意的完整表述**，不润色、不升华、不替考生总结 |
| ✅ 如实记录 | 考生口语、重复、模糊表述均可保留；可在 `notes` 中补充其原话，而非改写成「标准答案」 |
| ✅ 仅做必要结构化 | `province`、`score`、`classify`、`subjects` 等 API 必填项，只做格式归一（如分数取整数、选科逗号分隔） |
| ✅ 显式信息才入库 | `preferred_*` 仅记录考生**明确说出**的院校、城市、层次、专业类；未提及则不臆造 |
| ❌ 禁止过度干预 | 不把「想搞代码」改写成「计算机科学与技术方向」；不替考生补充其未表达的职业规划；不在本阶段做专业/院校推荐或倾向推断 |

向用户复述确认时，也应**引用其原话**核对，而非用你改写后的版本代替。

## 上下游

- **上游**：无
- **下游**：[gaokao-fetch-volunteers](../gaokao-fetch-volunteers/SKILL.md) 读取本 Skill 输出，将倾向映射为 API 选填参数

## 采集清单

### API 必填（写入 `student.json` 顶层）

| 字段 | 说明 | 示例 |
|------|------|------|
| `province` | 高考省份 | 山东 |
| `classify` | 文科/理科/物理/历史/综合 | 综合 |
| `score` | 高考成绩（整数） | 650 |
| `batch` | 填报批次 | 本科批 |
| `subjects` | 3+1+2：**完整三科**（首选科目+两门再选）；3+3：完整三科；老高考 `null` | `物理,化学,生物` |
| `gradeType` | 仅北京/上海/天津：本科/专科 | 本科 |
| `rank` | 位次，无则 `null` | 5000 |

### 辅助画像（原话优先，供下游分析）

| 字段 | 说明 | 填写要求 |
|------|------|----------|
| `interests` | 兴趣爱好 | **考生原话**，逗号或自然句均可，勿概括 |
| `family_situation` | 家庭情况 | **考生原话**，保留其表述的经济、地域、深造态度等 |
| `career_direction` | 未来就业/发展方向 | **考生原话**，哪怕模糊也照录，不下结论 |
| `subject_scores` | 各科分数 | 数字字段，按考生填报 |
| `preferred_cities` | 意向城市 | 仅列考生**明确提到**的城市 |
| `preferred_provinces` | 意向省份 | 考生明确提到则录入；否则可留空，由下游从城市推导 |
| `preferred_universities` | 心仪院校 | 使用考生口中的**校名全称或原称**，不擅自替换简称 |
| `preferred_tags` | 院校层次意向 | 仅录考生**亲口说过**的（如「想上 985」），勿自行推断 |
| `preferred_major_classes` | 专业类意向 | 仅录考生**明确提到**的专业/方向，勿从兴趣推断改写 |
| `notes` | 其他补充 | 不适合归入上述字段的**原话**、禁忌、特殊诉求 |

倾向字段的 API 映射由下游 [gaokao-fetch-volunteers](../gaokao-fetch-volunteers/SKILL.md) 处理；本阶段**不必**为凑 API 参数而改写或补全 `preferred_*`。

## 工作流程

1. 用自然语言逐项询问，缺什么问什么；可分批提问。
2. **按省份确定选科模式并填对 API 字段**（见下表与 [reference.md](reference.md)）。
3. 将考生回答**按原意录入**对应字段；仅对 API 必填项做格式归一。
4. 信息齐全后保存 `output/student.json`，**用考生原话复述**关键内容并请其确认。

### 按省份填 classify / subjects / gradeType（SOP）

| 模式 | 省份 | classify | subjects | gradeType |
|------|------|----------|----------|-----------|
| 老高考 | 新疆 | 文科 **或** 理科 | `null`（不传选科） | `null` |
| 3+1+2 | 粤苏冀鄂湘闽辽渝甘黑吉皖赣贵桂云蒙川宁晋豫陕青 | 物理 **或** 历史 | **完整三科**：`物理,化学,生物`（须含首选科目，不能只写两门再选） | `null` |
| 3+3 | 沪京津鲁浙琼 | **综合**（不能填物理/历史） | 三科；浙江可选 `技术` | 仅京沪津：`本科`/`专科` |

**采集要点**：

- 问清考生是**文科还是理科**（新疆），或**物理类还是历史类**（3+1+2），或直接记选科（3+3 填 `classify=综合`）。
- **3+1+2 的 `subjects` 须录完整三科**（如物化生），包含与 `classify` 一致的首选科目，不能只录化学、生物两门。
- 京沪津需确认报**本科还是专科**（专科仅语数外 450 分制）。
- 新疆必须采集 **score**；仅有位次不够。
- **西藏**：测试环境不支持志愿接口，采集时应告知用户。
- `batch` 可填考生口中的「本科批」，下游 batch/list 会自动解析。

## 输出格式

参考 [examples/student_template.json](examples/student_template.json)、[examples/student_shandong.json](examples/student_shandong.json)。

```json
{
  "province": "山东",
  "classify": "综合",
  "subjects": "物理,化学,生物",
  "score": 650,
  "batch": "本科批",
  "rank": null,
  "gradeType": null,
  "interests": "考生原话，勿改写",
  "career_direction": "考生原话，勿改写",
  "family_situation": "考生原话，勿改写",
  "preferred_cities": ["北京", "上海", "深圳"],
  "preferred_provinces": ["北京", "上海", "广东"],
  "preferred_universities": ["北京航空航天大学"],
  "preferred_tags": ["985", "211"],
  "preferred_major_classes": ["计算机类", "电子信息类"],
  "notes": "不接受偏远地区"
}
```

## 注意事项

- `batch` 下游会通过 batch/list 自动解析，此处可填用户口中的「本科批」。
- **classify 必须与省份模式一致**（最常见错误：山东填了物理）。完整踩坑见 [gaokao-fetch-volunteers/reference.md](../gaokao-fetch-volunteers/reference.md)。
- 排斥性偏好（如不要偏远）用考生原话写入 `notes`，**不要**写入 `preferred_provinces`，也不要改写成书面语。
- 复述确认时展示的是**考生自己的表述**，不是 Agent 润色后的版本。
- 输出路径使用绝对路径交付用户。

## 附加资源

- [reference.md](reference.md) — 省份选科模式与 batch 对照
- [preference_mapping.md](../gaokao-fetch-volunteers/preference_mapping.md) — 倾向 → API 参数映射
