# 输出 JSON Schema

解梦结果的完整 JSON 格式。前端根据此格式渲染"梦境解析卡"。

## 完整结构

```json
{
  "dream_summary": "string — 一句话概括梦境内容（20字以内）",
  "keywords": ["string — 梦境关键词，3-6个"],
  "mood": "string — 情绪分类，枚举值见下方",
  "color_scheme": "string — 配色方案名，与 mood 对应",
  "visual_elements": ["string — 视觉元素标识，最多5个，见 visual-mapping.md"],
  "interpretations": {
    "zhouGong": {
      "icon": "🔮",
      "title": "周公解梦",
      "content": "string — 主体解读，100-200字",
      "fortune": "string — 吉凶判断：大吉/吉/中性/中性偏凶/凶",
      "advice": "string — 一句话建议，宜忌格式"
    },
    "freud": {
      "icon": "🧠",
      "title": "心理分析",
      "content": "string — 心理分析，100-200字",
      "insight": "string — 一句话核心洞察",
      "advice": "string — 一个具体的自我关照建议"
    },
    "cyber": {
      "icon": "🌀",
      "title": "赛博神棍",
      "content": "string — 赛博解读，100-200字",
      "prediction": "string — 一句离谱预言",
      "advice": "string — 一个搞笑但具体的行动建议"
    }
  },
  "overall_advice": "string — 综合建议，1-2句话，中立语气",
  "shareable_text": "string — 可分享文案，包含emoji，适合发朋友圈，50字以内"
}
```

## mood 枚举值

| 值 | 含义 |
|----|------|
| anxious | 焦虑、恐惧、紧张 |
| peaceful | 平静、美好、舒适 |
| sad | 悲伤、失落、遗憾 |
| surreal | 奇幻、荒诞、超现实 |
| exciting | 兴奋、刺激、冒险 |
| nostalgic | 怀旧、温馨、思念 |

## color_scheme 与 mood 的对应

mood 和 color_scheme 值相同。前端根据 color_scheme 值从 visual-mapping.md 的配色表中取色。

## 输出要求

1. JSON 必须合法，可直接 JSON.parse
2. 用 ```json 代码块包裹
3. 所有 string 字段不能为空
4. keywords 数组 3-6 个元素
5. visual_elements 数组 1-5 个元素
6. 三个 interpretation 的 content 长度保持接近（都是100-200字）
7. shareable_text 要有趣，让人想转发
