---
name: gaokao-fetch-volunteers
description: >-
  调用高考智能推荐志愿表 API，根据考生基本信息及专业/城市/院校倾向（映射为 API 选填参数）
  获取冲稳保志愿列表，解析为 parsed.json。适用于获取推荐院校、冲稳保志愿表、志愿 API 调用。
---

# 获取推荐志愿表

本 Skill 是流水线的**第二步**：读取 `student.json`，**提取并映射考生倾向到 API 选填参数**，调用志愿接口，输出 `parsed.json`。

## 上下游

- **上游**：[gaokao-collect-student-info](../gaokao-collect-student-info/SKILL.md) → `student.json`
- **下游**：[gaokao-recommend-majors](../gaokao-recommend-majors/SKILL.md)、[gaokao-recommend-schools](../gaokao-recommend-schools/SKILL.md)、[gaokao-generate-report](../gaokao-generate-report/SKILL.md)

## 环境准备

```bash
cd gaokao-fetch-volunteers
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 执行步骤

### 1. 从辅助信息提取倾向（Agent 必做）

读取 `student.json`，根据 [preference_mapping.md](preference_mapping.md) 将考生倾向补全/写入以下字段：

| 字段 | 映射到 API |
|------|-----------|
| `preferred_universities` | `universitys` |
| `preferred_provinces` / `preferred_cities` | `provinces` |
| `preferred_tags` | `tags` |
| `preferred_major_classes` | `majorClass` |

提取来源：`interests`、`career_direction`、`preferred_cities`、`notes` 及对话中的院校/专业/层次偏好。

若 Step1 已结构化写入，本步核对并补全；**调用 API 前倾向字段不得为空数组**（考生无偏好时除外）。

### 2. 构建 API 请求

```bash
python3 scripts/build_api_request.py \
  -i output/student.json \
  -o output/api_request.json \
  --summary output/preference_summary.json
```

脚本将 `preferred_*` 转为 API 选填参数；`preferred_cities` 会自动推导 `provinces`（见 `preference_mapping.md`）。

`build_api_request.py` 会调用 `province_config.validate_classify` 校验 `classify` 是否与省份模式匹配。

### 2.5 调用前参数核对（必做）

在调用 API 前，对照 [reference.md](reference.md) 核对 `student.json` / `api_request.json`：

| 检查项 | 规则 |
|--------|------|
| `classify` | 新疆→文科/理科；3+1+2 省→物理/历史；3+3 省→综合。**传错会导致批次列表为空** |
| `subjects` | 3+1+2：**完整三科**（首选+两门再选，如 `物理,化学,生物`）；3+3：完整三科；新疆不传；京沪津专科由脚本处理 |
| `gradeType` | **仅北京/上海/天津**填本科或专科；其他省必须为 `null` 或不传 |
| `score` | 新疆**必传**（无一分一段表，仅 rank 无效） |
| `batch` | 可填泛称「本科批」/「专科批」，由 batch/list 解析为各省具体批次名 |
| 西藏 | 测试环境不支持，应退回采集环节说明 |

**批次 batch**：用户侧可填泛称 `本科批` / `专科批`，脚本通过 batch/list 解析为各省具体批次名（如山东 → `普通类一段`）。接口失败时使用 [reference.md](reference.md) 中的静态兜底表。

### 3. 调用志愿 API（两阶段：批次 → 志愿列表）

```bash
python3 scripts/fetch_volunteers.py \
  --config output/api_request.json \
  -o output/parsed.json
```

或一步完成（内置构建逻辑）：

```bash
python3 scripts/fetch_volunteers.py \
  --student output/student.json \
  -o output/parsed.json
```

脚本会先调用 `batch/list` 根据分数与选科解析具体 `batch` 和 `volunteerType`，再请求志愿推荐接口。参数规范化由 `scripts/province_config.py` 自动完成。可用 `--no-auto-batch` 关闭自动解析。

**两阶段 SOP**：

```
1. GET  batch/list  →  得到各省可选批次 + volunteerType
2. POST intelligenceVolunteer  →  用选中批次的 batch / volunteerType 拉志愿
```

京沪津在步骤 1 还需传 `gradeType`（脚本按 score / batch 自动推断）。

### 4. 向用户说明

结合 `preference_summary.json` 与 `parsed.json` 的 `stats`，说明：

- 传入了哪些倾向参数（院校/省份/层次/专业类）
- 冲/稳/保各多少所

## API 选填参数说明

| API 字段 | 含义 | 来源 |
|----------|------|------|
| `universitys` | 心仪高校 | `preferred_universities` |
| `provinces` | 省份意向 | `preferred_provinces` 或由城市推导 |
| `tags` | 院校属性 | `preferred_tags`（985/211 等） |
| `majorClass` | 专业类意向 | `preferred_major_classes` |

完整 API 文档见 [reference.md](reference.md)。

## 输出结构（parsed.json）

| 字段 | 说明 |
|------|------|
| `profile` | 含传入的选填参数回显 |
| `stats` | 冲/稳/保数量 |
| `schools_by_type` | 分组院校列表 |
| `request` | 实际 API 请求体（含倾向参数） |
| `batch_resolution` | 批次解析来源、选中项与可选项 |

## 故障排查

| 现象 | 处理 |
|------|------|
| 推荐结果与倾向不符 | 检查 `api_request.json` 中选填参数是否正确 |
| 没有可填报的批次 | 查 [reference.md](reference.md)；确认 classify 与省份模式一致 |
| 批次列表为空 | classify 错误（如 3+3 省传了物理）— 脚本会明确报错 |
| 西藏考生 | 测试环境不支持，需换省份或等待平台接入 |
| 志愿接口 500 | 查 reference：gradeType/subjects 是否按省传对 |
| 缺少 subjects | 3+3/3+1+2 必填选科；新疆/京沪津专科除外 |
| subjects 只有两门 | 3+1+2 须传**完整三科**（含物理/历史），不能只传化学,生物 |
| 倾向未传入 | 确认 Step1/本步已填写 `preferred_*` 字段 |

## 附加资源

- [preference_mapping.md](preference_mapping.md) — 倾向 → API 参数映射规则
- [reference.md](reference.md) — API、选科模式、批次接口踩坑速查
- [scripts/province_config.py](scripts/province_config.py) — 各省 classify/subjects/gradeType 校验与规范化
- [scripts/test_batch_api.py](scripts/test_batch_api.py) — 31 省批次接口回归测试
- [examples/api_request_shandong.json](examples/api_request_shandong.json) — 含选填参数示例
