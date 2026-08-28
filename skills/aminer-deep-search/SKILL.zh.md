---
name: aminer-deep-search
version: 2.0.0
author: AMiner
contact: report@aminer.cn
description: >
  当用户需要为综述或文献回顾做深度、多轮的学术论文收集时激活本 skill。
  由宿主模型（正在运行本 skill 的模型）亲自驱动循环：扩展查询、判断相关性、做引用滚雪球、决定何时终止。
  附带脚本只是纯工具命令，调用 AMiner 开放平台的正规接口并只输出 JSON tool-result，无需配置任何额外 LLM。
  适用于大范围主题探索、综述参考文献构建、收集数百篇带 AMiner ID 与标题的候选论文。
  不适用于单篇论文查询或轻量推荐，请分别使用 aminer-free-academic 或 aminer-daily-paper。
metadata:
  {
    "openclaw":
      {
        "requires": {
          "bins": ["python3"],
          "env": ["AMINER_API_KEY"]
        },
        "primaryEnv": "AMINER_API_KEY"
      }
  }
---

# AMiner 深度收集

宿主模型直驱的综述文献收集。你（正在读这份文档的模型）就是控制器：运行工具脚本、阅读 JSON 输出、自己判断相关性、迭代直到达成收集目标。

## 适用边界

- 适用：综述级文献收集（数百篇）、关键词扩展、后向引用滚雪球。
- 不适用：单篇查询或问答（走 `aminer-free-academic`）、个性化推荐（走 `aminer-daily-paper`）。

## Pre-flight

1. 检查 key（不打印值）：

```bash
[ -z "${AMINER_API_KEY:-}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

缺失时停止并让用户设置 `AMINER_API_KEY`（控制台：https://open.aminer.cn/open/board?tab=control）。绝不打印 key。

2. 确认 `topic` 和 `target-size`（默认 400）。若轮次计划预估费用 ≥¥5，先告知用户并获得确认再开始。

## 工具

两个脚本都在本 skill 目录的 `scripts/` 下。stdout 只输出一个 JSON 文档（即 tool-result）；诊断信息与 `[cost]` 费用行走 stderr。脚本不做任何相关性打分——那是你的工作。

### `scripts/aminer_api.py` — AMiner 接口调用

| 子命令 | 端点 | 价格 |
|---|---|---|
| `search --query Q [--size 20] [--year YYYY] [--order n_citation\|year] [--max-pages 3]` | GET `/api/paper/search/pro` + 免费 `paper/info` 补全 | ¥0.01/页 |
| `qa-search [--query "自然语言问题"] [--topic-high '[["词A","词B"],["词C"]]'] [--size 20] [--year-from Y] [--year-to Y] [--citation-sort]` | POST `/api/paper/qa/search`（固定 `use_topic=true`：`use_topic=false` 时后端忽略 `query`）+ 免费补全 | ¥0.05/次 |
| `info --ids id1 id2 ...` | POST `/api/paper/info`（≤100 个 id 分批） | 免费 |
| `references --ids id1 id2 ... [--per-seed 20]` | 每个 seed 调 GET `/api/paper/relation` + 免费补全 | ¥0.10/篇 seed |

输出形状：`search`/`qa-search`/`info` 输出 `[{id, title, year?, venue?, abstract_slice?}]`；`references` 额外带 `source_paper_ids`（哪些 seed 引用了该论文），且结果中排除 seed 本身。

### `scripts/paper_set.py` — 跨轮状态文件（无网络）

状态文件默认是工作目录下的 `outputs/paper_set.json`。

```bash
# 把保留的结果管道进去（可直接接在搜索后面），按 id 去重
python3 scripts/aminer_api.py search --query "..." | python3 scripts/paper_set.py add
# → {"added": N, "duplicates": M, "total": T}

python3 scripts/paper_set.py stats     # 总量、expanded_seeds、按年分布
python3 scripts/paper_set.py mark-expanded --ids id1 id2   # 记录已滚雪球的 seed
python3 scripts/paper_set.py export -o outputs/final_papers.json
```

`add` 也接受 `--ids id1 id2 ...` 直接加裸 id。带 `source_paper_ids` 的条目（来自 `references`）会自动把对应 seed 记为已扩展。

如需先筛选再入库，先阅读搜索输出，再只把保留的条目管道进去：

```bash
printf '%s' '[{"id":"...","title":"..."}]' | python3 scripts/paper_set.py add
```

## 每轮协议（核心）

### 第 0 轮 — 规划

- 从 topic 派生 4–8 个种子查询：同义词、子领域、方法名、数据集/基准、常用英文缩写。
- 预估轮数与费用（搜索约 ¥0.01–0.05/次，references 约 ¥0.10/seed）。预估 ≥¥5 时先向用户确认。

### 每一轮（默认最多 12 轮），固定五步

1. **搜索**：对待查队列执行 1–4 个 `search` / `qa-search`。优先用 `search`（更便宜）；查询是自然语言问题时用 `qa-search`。
2. **筛选入库**：阅读 stdout 结果，自己判断与主题的相关性，只把保留的条目管道进 `paper_set.py add`。绝不入库你认为跑题的论文。
3. **查看进度**：跑 `stats` 查看总量与本轮增量。
4. **滚雪球**：从本轮新增的相关论文里挑 ≤5 个强种子（高相关、`--order n_citation` 排前、不在 `expanded_seeds` 中），跑 `references --ids ...`。对输出再做相关性筛选后入库。没有可入库产出的 seed 用 `mark-expanded` 记录。
5. **决策下一轮**：
   - 某个搜索结果 <5 条或质量差 → 换一个改写后的查询（每个方向最多试 2 个变体，之后转滚雪球）；
   - references 持续产出大量相关论文 → 继续从新 seed 滚雪球；
   - 达到 `target-size`、结果枯竭、或连续 2 轮新增 <5 篇 → 终止。

### 收尾

跑 `export`，然后报告：最终篇数、总费用（累加 stderr 的 `[cost]` 行）、输出文件路径。

## 规则

1. 绝不编造论文 ID 或标题；只引用工具实际返回的数据。
2. 免费优先：元数据一律来自免费的 `paper/info`（脚本已内置）；绝不为批量元数据调付费的 `paper/detail`。
3. 不要把原始工具输出塞进最终回答；只报告数量与导出文件路径。
4. 绝不打印或记录 `AMINER_API_KEY`。
5. 如果 AMiner 返回的论文少于目标，如实报告实际数量，不要编造。
