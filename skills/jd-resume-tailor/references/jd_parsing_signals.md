# JD 解析信号词参考

## must-have 强信号词

只要 JD 句子里出现这些词，后面的技能 / 经验大概率是硬门槛：

- 必须 / 必备 / 要求 / 应当
- 至少 X 年 / X+ years / 不少于
- "需要" / "需具备"
- "必要条件" / "硬性要求"
- 工科背景 / 985 / 211 / 硕士及以上 / 博士

英文 JD：
- Required / Must have / Mandatory / Essential
- Minimum X years
- Strong proficiency in / Expert in
- Demonstrated experience with

## nice-to-have 弱信号词

- 加分 / 优先 / 优先考虑
- 熟悉 ___ 者优先
- 有 ___ 经验者优先
- "了解 ___ 即可"
- 加分项

英文：
- Preferred / Nice to have / Plus / Bonus / Desirable
- Familiar with / Exposure to
- A plus / Would be a plus

## 职责动词（写在 bullet 里能呼应 JD）

中文：负责、主导、推动、设计、搭建、优化、规划、迭代、孵化、复盘、运营、管理、协调、执行
英文：Lead / Drive / Build / Design / Architect / Develop / Implement / Optimize / Manage / Coordinate / Execute / Own

## 特殊要求

- **学历**：本科 / 硕士 / 博士及以上；学校 tier
- **工作年限**：X-Y 年（写明 range，不写满则有弹性）
- **语言**：英语口语流利 / CET-6 / 雅思 X / 母语
- **证书**：CFA / CPA / PMP / AWS Solutions Architect 等
- **出差 / 派驻 / 加班**："接受出差"、"奇偶周末调休"、"项目制 996"
- **工作地点**：城市 + 是否 remote / hybrid

## 反信号（看到这些要警觉）

- "其他领导交办的任务" → 工作边界模糊
- "良好的抗压能力" → 加班多
- "拥抱变化 / 快速迭代" → 业务方向不稳定
- "扁平化沟通 / 没有层级" → 实际可能更乱
- "5 险一金 + 节日福利" 写在 JD 显眼位置 → 福利可能就这些

## 输出格式（Step 1 给用户看的）

```json
{
  "company": "XX 公司",
  "position": "XX 岗位",
  "must_have": [
    {"item": "5 年以上 C 端产品经验", "evidence": "JD 第 X 行"},
    {"item": "熟练 SQL", "evidence": "JD 第 Y 行"}
  ],
  "nice_to_have": [
    {"item": "海外业务经验", "evidence": "JD 第 Z 行"}
  ],
  "soft_skills": ["跨部门推动", "数据驱动决策"],
  "responsibilities": [
    "主导 ___ 业务线产品规划",
    "通过数据分析驱动迭代"
  ],
  "special_requirements": {
    "education": "本科及以上",
    "years": "5+",
    "language": "英语口语流利",
    "location": "上海，可接受短期出差"
  }
}
```
