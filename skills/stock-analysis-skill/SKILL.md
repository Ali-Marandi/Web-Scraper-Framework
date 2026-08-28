---
name: stock_analysis
description: "Comprehensive stock market analysis skill covering A-share (China), Hong Kong, and US equities. Priority use cases: stock analysis and buy/sell/hold recommendations by ticker code, generating decision dashboards and research reports with technical/fundamental/sentiment analysis, position-aware investment strategies based on user's cost price, dividend income scoring and safety analysis, rumor and early market signal scanning (M&A, insider activity, analyst actions), watchlist management with price target and stop-loss alerts, and K-line chart pattern recognition from images. This skill should be the primary choice whenever users mention a stock ticker, ask whether to buy or sell a stock, reference their holding cost or position, request dividend analysis, ask about market rumors or early signals, want to add/check/manage a watchlist, or upload a chart image for technical analysis."
---

# Stock Analysis Skill

## 依赖平台 Skills

- `finance skill` — 所有市场数据（A股/港股/美股统一）
- `pdf skill` — PDF 研报生成
- `docx skill` — Word 文档生成
- `vlm skill`（内置）— K线图形态识别

---

## Commands & Triggers

| 命令 | 触发词示例 |
|------|-----------|
| 个股分析 | 分析600519 / AAPL值不值得买 / 帮我看看腾讯 |
| 带持仓分析 | 我持仓成本1450分析茅台 / AAPL我170买的现在怎样 |
| 股息分析 | JNJ股息怎么样 / 帮我分析这几只股的股息 KO PG JNJ |
| 传闻扫描 | 今日有什么并购传闻 / 扫描一下市场早期信号 |
| 添加自选股 | 关注AAPL / 把600519加入自选，目标价1600止损1350 |
| 查看自选股 | 我的自选股列表 / 看一下我关注的股票 |
| 检查提醒 | 检查自选股提醒 / 有没有触发止损 |
| 删除自选股 | 从自选股删除TSLA |
| K线图分析 | （上传图片）帮我分析这个K线图 |
| 大盘复盘 | 附带大盘复盘分析600519 |

---

## Input Schemas

### 个股分析
```typescript
{
  stocks: (string | { code: string; position?: { status: "empty"|"holding"; cost?: number; shares?: number } })[],
  outputFormat?: "markdown" | "pdf" | "word",  // 默认 markdown
  mode?: "full" | "quote",                      // 默认 full
  includeMarketReview?: boolean,                // 默认 false
  includeGlobalMacro?: boolean,                 // 默认 true
  includeDividend?: boolean,                    // 美股附加股息分析，默认 false
}
```

### 股息分析
```typescript
runDividend(tickers: string | string[])
```

### 传闻扫描
```typescript
runRumorScan()  // 无需参数，自动扫描今日信号
```

### 自选股管理
```typescript
runWatchlistAdd(ticker, { targetPrice?, stopPrice?, alertOnSignal?, notes? })
runWatchlistRemove(ticker)
runWatchlistList()
runWatchlistCheck()  // 检查是否触发价格/信号提醒
```

---

## Report Structure

```
# 股票智能分析报告

## 🌍 全球宏观速览（默认开启）
## 🎯 大盘复盘（需开启）
## 📊 个股决策仪表盘（每只）
   ### 📰 重要信息速览（舆情/业绩预期/🚨风险/✨利好/最新动态）
   ### 📌 核心结论（结论/一句话/空仓者建议/持仓者建议+盈亏）
   ### 📈 当日行情
   ### 📊 数据透视（技术面/基本面/资金面）
   ### 🎯 作战计划（狙击点位表/仓位/风控）
   ### ✅ 检查清单（综合结论）
   ### 💰 股息分析（美股，需开启 includeDividend）
```

---

## Dividend Analysis Metrics

| 指标 | 说明 |
|------|------|
| 安全评分 | 0-100，综合派息率/增长/连续年数 |
| 收入评级 | excellent/good/moderate/poor |
| 派息率状态 | safe(<40%)/moderate/high/unsustainable |
| 5年CAGR | 股息复合增长率 |
| 连续增长年数 | 25年以上为股息贵族 |

---

## Rumor Scanner Signal Types

| 类型 | 冲击分 | 说明 |
|------|--------|------|
| 并购传闻 (ma) | +5 | M&A/收购/要约 |
| 内部人动态 (insider) | +4 | CEO/董事买卖 |
| 分析师调整 (analyst) | +3 | 评级上调/下调/目标价变动 |
| 监管动态 (regulatory) | +3 | SEC调查/合规风险 |
| 业绩预期 (earnings) | +2 | 盈利预警/上调 |

---

## Watchlist Alert Types

| 提醒类型 | 触发条件 |
|---------|---------|
| 🎯 目标价 | 当前价 ≥ targetPrice |
| 🛑 止损价 | 当前价 ≤ stopPrice |
| 📊 信号变化 | 本次结论 ≠ 上次结论 |

---

## Behavior Rules

- 乖离率 > 5% → 结论不得为买入/强烈买入
- 数据缺失 → 标"暂缺"，严禁捏造
- 有持仓成本 → 必须给出盈亏分析
- 未提供持仓 → 同时给出空仓/持仓两套建议
- 每次分析后自动静默更新自选股信号

---

## File Structure

```
stock-analysis-skill/
├── SKILL.md
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts          # 主入口（所有命令路由）
    ├── types.ts          # 类型定义
    ├── dataFetcher.ts    # 数据层（finance skill）
    ├── analyzer.ts       # 个股分析（LLM/VLM）
    ├── dividend.ts       # 股息分析
    ├── rumorScanner.ts   # 传闻扫描
    └── watchlist.ts      # 自选股管理（storage 持久化）
```

---

## Limitations

- 传闻扫描依赖 finance skill 新闻数据质量
- 自选股数据持久化依赖平台 storage API
- 港股基本面数据较少
- 不支持期货、ETF、可转债
- 仅供参考，不构成投资建议
