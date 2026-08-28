# 智能推荐志愿表 API 速查

## 两阶段调用流程

`fetch_volunteers.py` 默认先调批次接口，再调志愿推荐接口：

1. **批次列表** `GET /zp/volunteer/batch/list?province=山东&classify=综合&score=651`
2. **志愿推荐** `POST /zp/volunteer/intelligenceVolunteer`（请求体中的 `batch`、`volunteerType` 来自第 1 步选中项）

`classify` 取值：`文科`、`理科`、`物理`、`历史`、`综合`，按省份与选科模式填写（见下文）。

批次选中规则：精确批次名 → 按 `gradeType`/本科批·专科批过滤 → 在达线批次中取控制线最高者。

解析结果 `parsed.json` 含 `batch_resolution` 字段，记录批次来源与可选项。

## 批次列表接口

| 项 | 值 |
|----|-----|
| 路径 | `GET /zp/volunteer/batch/list` |
| 参数 | `province`、`classify`、`score`；京沪津另加 `gradeType` |
| 响应 | `{ status, message, result: [{ batch, score, gradeType, type, ... }] }` |

`result[].type` 对应志愿接口的 `volunteerType`（如 `MAJOR_GROUP`）。`gradeType` 仅用于筛选批次；**仅京沪津**才写入志愿请求体。

## 志愿推荐接口

| 项 | 值 |
|----|-----|
| 路径 | `POST /zp/volunteer/intelligenceVolunteer` |
| Content-Type | `application/json` |
| 认证 | 无（公网 skill-test 接口） |
| 默认 BASE_URL | `https://publicapi.chatglm.cn/chatglm_public/skill-test` |
| 完整地址 | `{BASE_URL}/zp/volunteer/intelligenceVolunteer` |

## 请求体字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| province | string | ✓ | 高考省份 |
| classify | string | ✓ | 文科/理科/物理/历史/综合 |
| score | integer | ✓ | 高考成绩 |
| batch | string | ✓ | 填报批次（可由 batch/list 自动解析） |
| subjects | string \| null | 模式相关 | 逗号分隔选科 |
| gradeType | string \| null | 京沪津 | 本科 / 专科 |
| rank | integer \| null | | 位次 |
| universitys | string \| null | | 心仪高校，`,` 分隔；来自 `student.preferred_universities` |
| provinces | string \| null | | 省份意向；来自 `preferred_provinces` 或由 `preferred_cities` 推导 |
| tags | string \| null | | 院校属性意向；来自 `preferred_tags`（如 985,211） |
| majorClass | string \| null | | 专业类意向；来自 `preferred_major_classes` |
| universityNum | integer | | 推荐院校数，默认 30 |
| majorNum | integer | | 每组专业数，默认 6 |
| isAdjust | boolean | | 是否调剂 |
| volunteerType | string | | ACADEMY_GROUP / ACADEMY_MAJOR / MAJOR_GROUP |
| returnUniversityNum | integer | | 已填志愿数 |
| intentionNum | integer | | 已填意向数 |

## 省份与选科模式（实测规律）

### 老高考（仅新疆）

| 字段 | 值 |
|------|-----|
| classify | `文科` 或 `理科`（二选一，不能填物理/历史/综合） |
| subjects | 不传或 `null`（**不要**传字符串 `"null"`） |
| gradeType | 不传 |
| score | **必传**（新疆无一分一段表，仅传 rank 无法反查分数） |

### 3+1+2（23 省）

广东,江苏,河北,湖北,湖南,福建,辽宁,重庆,甘肃,黑龙江,吉林,安徽,江西,贵州,广西,云南,内蒙古,四川,宁夏,山西,河南,陕西,青海

| 字段 | 值 |
|------|-----|
| classify | `物理` 或 `历史`（对应 3+1+2 首选科目） |
| subjects | **完整三科**，逗号分隔：`首选科目,再选1,再选2`。须包含与 `classify` 一致的首选科目，**不能只传两门再选** |

例：`classify=物理`，`subjects=物理,化学,生物`（✓）；`subjects=化学,生物`（✗ 缺少物理）

再选科目仅限：化学、生物、政治、地理。
| gradeType | 不传 |

### 3+3（6 省）

上海,北京,天津,山东,浙江,海南

| 字段 | 值 |
|------|-----|
| classify | 固定 `综合` |
| subjects | 三科逗号分隔；浙江可选 `技术` |
| gradeType | **仅京沪津**需要：`本科` / `专科` |

**满分差异**：山东/浙江 750；海南 900；上海本科 660；北京/天津本科 750；京沪津专科语数外 450。

### 京沪津 gradeType 规则

批次接口 `batch/list` 与志愿接口**均需**传 `gradeType`：

```
GET .../batch/list?province=北京&classify=综合&score=650&gradeType=本科
```

未填时脚本按以下规则推断：`batch=专科批` → 专科；`score≤450` → 专科；否则 → 本科。

| 场景 | subjects | gradeType |
|------|----------|-----------|
| 北京本科 | `物理,化学,生物` | `本科` |
| 北京专科 | 字符串 `"null"`（API 要求，非 JSON null） | `专科` |
| 浙江/山东/海南 | 三科组合 | 不传 |

### 西藏

测试环境**平台未接入**，任意 classify 均返回 `status=500`，非参数错误。脚本会在校验阶段直接提示不支持。

### 常见踩坑（批次接口）

| 现象 | 原因 | 处理 |
|------|------|------|
| `status=0` 但 `result=[]` | classify 与省份模式不匹配（如山东传 `物理`） | 按上表改 classify |
| 志愿接口 500（山东等） | 误传 `gradeType` | 仅京沪津传，其他省移除 |
| 志愿接口 500（山东等） | 缺少 `subjects` 或只有两门 | 3+1+2 须传**完整三科**（含物理/历史） |
| 志愿接口 500（新疆） | `subjects` 为字符串 `"null"` | 不传 subjects 字段 |
| 北京专科 500 | subjects 为 JSON null 或省略 | 改为字符串 `"null"` |

`scripts/province_config.py` 封装了上述校验与参数规范化；`scripts/test_batch_api.py` 可批量回归 31 省。

### 批次静态兜底（batch/list 失败时）

| 省份 | batch |
|------|-------|
| 天津 | 本科批A段 |
| 浙江 | 普通类一段 |
| 山东 | 普通类一段 |
| 四川、云南 | 本科批B段 |
| 甘肃 | 本科批 |
| 宁夏 | 本科批B段 |
| 新疆 | 本科一批 |
| 西藏 | 测试环境暂不支持（2222010 高考省份错误） |

## 响应结构

公网 skill-test 接口返回 `{ status, message, result }`（`status=0` 为成功），脚本会自动转换为统一格式。

```json
{
  "status": 0,
  "message": "success",
  "result": {
    "province": "...",
    "schoolList": [
      {
        "universityName": "",
        "universityCode": "",
        "universityMajorGroup": "",
        "enrollProbability": 20,
        "type": "CHONG",
        "majorList": [ { "majorName": "", "claim": "", "type": "CHONG" } ]
      }
    ]
  }
}
```

旧版接口格式 `{ code, msg, body }`（`code=200`）同样兼容。

`type` 枚举：`CHONG` 冲、`WEN` 稳、`BAO` 保、`NAN` 难、`YI` 易。

`score` / `parityScore` 常为 JSON 字符串，如 `[{"2025":"660,2153,60"}]`（分,位次,计划数）。
