# 智能推荐志愿表 API 速查

## 接口

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
| batch | string | ✓ | 填报批次 |
| subjects | string \| null | 模式相关 | 逗号分隔选科 |
| gradeType | string \| null | 京沪津 | 本科 / 专科 |
| rank | integer \| null | | 位次 |
| universitys | string \| null | | 心仪高校，`,` 分隔 |
| provinces | string \| null | | 省份意向 |
| tags | string \| null | | 院校属性意向 |
| majorClass | string \| null | | 专业类意向 |
| universityNum | integer | | 推荐院校数，默认 30 |
| majorNum | integer | | 每组专业数，默认 6 |
| isAdjust | boolean | | 是否调剂 |
| volunteerType | string | | ACADEMY_GROUP / ACADEMY_MAJOR / MAJOR_GROUP |
| returnUniversityNum | integer | | 已填志愿数 |
| intentionNum | integer | | 已填意向数 |

## 省份与选科模式

详见 [gaokao-fetch-volunteers/reference.md](../gaokao-fetch-volunteers/reference.md) 实测规律。采集 `student.json` 时务必按省填对 `classify` / `subjects` / `gradeType`：

| 模式 | 省份 | classify | subjects | gradeType |
|------|------|----------|----------|-----------|
| 老高考 | 新疆 | 文科/理科 | 不传 | 不传 |
| 3+1+2 | 23省 | 物理/历史 | **完整三科**（含首选，如 `物理,化学,生物`） | 不传 |
| 3+3 | 沪京津鲁浙琼 | 综合 | 三科（浙可选技术） | 仅京沪津：本科/专科 |

**西藏**：测试环境不支持。 **新疆**：score 必传，勿仅传 rank。

**批次 batch（静态兜底，优先走 batch/list API）**：

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
