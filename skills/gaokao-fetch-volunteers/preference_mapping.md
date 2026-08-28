# 考生倾向 → API 选填参数映射参考

Agent 在**第二步获取志愿前**，须从 `student.json` 辅助信息中提取倾向，写入结构化字段，再构建 API 请求。

## 映射总表

| student.json 字段 | API 字段 | 格式 | 说明 |
|-------------------|----------|------|------|
| `preferred_universities` | `universitys` | 逗号分隔字符串 | 心仪高校全称，如 `北京航空航天大学,华东师范大学` |
| `preferred_provinces` | `provinces` | 逗号分隔字符串 | 意向就读省份；若未填，由 `preferred_cities` 自动推导 |
| `preferred_cities` | `provinces`（推导） | — | 城市映射见下方；脚本 `build_api_request.py` 自动处理 |
| `preferred_tags` | `tags` | 逗号分隔字符串 | 院校属性，如 `985,211,双一流` |
| `preferred_major_classes` | `majorClass` | 逗号分隔字符串 | 教育部专业类名称，如 `计算机类,电子信息类` |

## Agent 提取规则

从自然语言中识别倾向，**写入 student.json 对应字段**（可在 Step1 采集时写入，或在 Step2 调用 API 前补全）：

### 院校倾向 → `preferred_universities`

用户提及的具体学校、「想上清北复交」「考虑国防科大」等。

### 城市倾向 → `preferred_cities` + `preferred_provinces`

- 收集城市列表到 `preferred_cities`
- 同时推导省份写入 `preferred_provinces`（可与城市映射结果合并去重）

常见城市→省份：深圳/广州→广东，武汉→湖北，杭州→浙江，南京/苏州→江苏，成都→四川，西安→陕西。

### 院校层次倾向 → `preferred_tags`

| 用户表述 | tags 值 |
|----------|---------|
| 985 / 顶尖 | `985` |
| 211 | `211` |
| 双一流 | `双一流` |
| 保研 | `保研资格` |
| 师范 | `师范` |
| 医学强校 | 结合具体院校，或 tag 填 `医学院`（若 API 支持） |

### 专业倾向 → `preferred_major_classes`

结合 `interests`、`career_direction`、`subject_scores` 推断：

| 兴趣/就业方向 | 建议 majorClass |
|--------------|-----------------|
| 编程、互联网、AI | `计算机类,软件工程,电子信息类` |
| 电子、芯片、通信 | `电子信息类,微电子科学与工程,集成电路` |
| 医学、临床 | `临床医学类,口腔医学类,药学类` |
| 机械、制造、航天 | `机械类,航空航天类,自动化类` |
| 经济、金融、管理 | `经济学类,金融学类,工商管理类` |
| 法学 | `法学类` |
| 师范、教育 | `教育学类,中国语言文学类,数学类` |

> 使用教育部本科专业类标准名称；多个类用英文逗号分隔，不超过 5 个为宜。

### 禁忌与排除 → `notes` + 不传参

「不接受偏远地区」等**排除性**偏好写入 `notes`，供后续推荐 Skill 使用；**不要**把排斥省份填入 `provinces`。

## 工作流

```
student.json（含倾向字段）
    → Agent 核对/补全 preferred_* 字段
    → build_api_request.py
    → api_request.json
    → fetch_volunteers.py
    → parsed.json
```

## 山东示例

考生：兴趣编程/AI，意向北京上海深圳，希望 985，专业偏计算机。

```json
{
  "preferred_cities": ["北京", "上海", "深圳"],
  "preferred_provinces": ["北京", "上海", "广东"],
  "preferred_universities": ["北京航空航天大学", "华东师范大学"],
  "preferred_tags": ["985", "211"],
  "preferred_major_classes": ["计算机类", "电子信息类", "自动化类"]
}
```

生成的 API 片段：

```json
{
  "universitys": "北京航空航天大学,华东师范大学",
  "provinces": "北京,上海,广东",
  "tags": "985,211",
  "majorClass": "计算机类,电子信息类,自动化类"
}
```
