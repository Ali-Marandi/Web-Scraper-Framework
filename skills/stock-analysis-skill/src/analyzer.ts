/**
 * analyzer.ts — LLM/VLM 分析层
 * 七段式决策仪表盘 + 美股可附加股息分析
 */

import ZAI from "z-ai-web-dev-sdk";
import { StockData, AnalysisResult, OutputFormat, Market, Verdict, PositionInfo } from "./types";
import { validateStockData } from "./dataFetcher";
import { analyzeDividend, formatDividendMarkdown } from "./dividend";

const MARKET_LABEL: Record<Market, string> = { CN: "A股", HK: "港股", US: "美股" };

// ── 仪表盘 Prompt ─────────────────────────────────────────

function buildDashboardPrompt(
  data: StockData,
  position: PositionInfo | undefined,
  warnings: string[]
): string {
  const warningBlock = warnings.length > 0
    ? `⚠️ 数据预警（必须在报告中体现）：\n${warnings.map((w) => `- ${w}`).join("\n")}\n\n`
    : "";

  const positionBlock = position
    ? position.status === "holding"
      ? `用户持仓：持仓中，成本价 ${position.cost ?? "未知"} 元${position.shares ? `，${position.shares} 股` : ""}。请给出盈亏分析和针对性建议。`
      : `用户持仓：当前空仓。`
    : `用户持仓：未提供（请同时给出空仓者和持仓者两套建议）。`;

  return `${warningBlock}${positionBlock}

股票数据：
\`\`\`json
${JSON.stringify(data, null, 2)}
\`\`\`

请输出以下格式的完整决策仪表盘（严格按结构，不增删章节）：

---

## 决策仪表盘 · {名称}({代码}) · {市场}

---

### 📰 重要信息速览
**💭 舆情情绪：** 一句话描述
**📊 业绩预期：** 结合 PE/ROE/行业简述，数据缺失标"暂缺"
**🚨 风险警报：**
- 风险1（技术面或宏观）
- 风险2（基本面或行业）
**✨ 利好催化：**
- 利好1（技术面）
- 利好2（基本面或行业）
**📢 最新动态：** 结合行业背景，补充1条关键信息

---

### 📌 核心结论
**[emoji] 结论：强烈买入 / 买入 / 观望 / 卖出**（四选一，乖离率>5%不得为买入）
**💬 一句话决策：** 核心逻辑
**⏰ 时效性：** 立即行动 / 今日内 / 不急

（根据持仓状态输出）
- **🆕 空仓者：** 是否进场、建仓点位、仓位比例
- **💼 持仓者：** 持有/加仓/减仓/止损建议${position?.status === "holding" && position.cost ? "，含成本盈亏分析" : ""}

---

### 📈 当日行情
列出：收盘价、昨收、开盘、最高、最低、涨跌幅、涨跌额、振幅、成交量、成交额（缺失标"暂缺"）

---

### 📊 数据透视

**技术面：**
表格（指标 | 数值 | 解读）：MA5、MA10、MA20、乖离率(BIAS20)、RSI（如有）、支撑位、压力位
结论：均线状态 + 趋势强度（xx/100）

**基本面（注明报告期）：**
表格（指标 | 数值 | 行业对比）：ROE、毛利率、净利率、资产负债率、PE、PB
数据缺失标"暂缺"，不得捏造

**资金面：**（A股/港股适用，美股可略）
- 主力净流入：金额（占比%），一句话解读
- 筹码：获利比例 | 平均成本 | 集中度

---

### 🎯 作战计划

| 点位类型 | 价格 | 说明 |
|---------|------|------|
| 🎯 理想买入 | xxx | |
| 🔵 次优买入 | xxx | |
| 🛑 止损位   | xxx | |
| 🎊 目标位   | xxx | |

**💰 仓位建议：** x成
**建仓策略：** 分批策略
**风控策略：** 止损纪律

---

### ✅ 检查清单
- ✅/⚠️/❌ 均线状态
- ✅/⚠️/❌ 乖离率安全（<5%）
- ✅/⚠️/❌ 量能配合
- ✅/⚠️/❌ 估值合理
- ✅/⚠️/❌ 资金流向
- ✅/⚠️/❌ 筹码健康

**综合结论：** 一句话总结当前状态和建议。

---
*以上分析仅供参考，不构成投资建议，据此操作风险自担。*`;
}

// ── 研报 Prompt（PDF/Word）──────────────────────────────

function buildReportPrompt(data: StockData, position: PositionInfo | undefined): string {
  const positionBlock = position?.status === "holding"
    ? `用户持仓成本：${position.cost ?? "未知"}`
    : "用户当前空仓";

  return `${positionBlock}

股票数据：
\`\`\`json
${JSON.stringify(data, null, 2)}
\`\`\`

请生成结构化研报：

【研究报告】{名称}({代码}) · {市场} · {日期}

一、投资结论（买入/强烈买入/观望/卖出，含目标价、止损价，分空仓/持仓两套建议）
二、重要信息速览（舆情/业绩预期/风险/利好/最新动态）
三、数据透视（技术面/基本面/资金面）
四、作战计划（点位表/仓位/持仓周期）
五、风险提示（2-3条）

免责声明：本报告由AI辅助生成，仅供参考，不构成投资建议，据此操作风险自担。`;
}

// ── 提取结论 ──────────────────────────────────────────────

function extractVerdict(text: string): Verdict {
  const patterns = [
    /结论[：:]\s*[💚🟢🟡🔴⚪]?\s*(强烈买入|买入|观望|卖出)/,
    /核心结论[：:]\s*[💚🟢🟡🔴⚪]?\s*(强烈买入|买入|观望|卖出)/,
    /\*\*(强烈买入|买入|观望|卖出)\*\*/,
  ];
  for (const p of patterns) {
    const m = text.match(p);
    if (m) return m[1] as Verdict;
  }
  return "观望";
}

// ── 核心分析 ──────────────────────────────────────────────

export async function analyzeStock(
  data: StockData,
  outputFormat: OutputFormat = "markdown",
  position?: PositionInfo,
  includeDividend = false
): Promise<AnalysisResult> {
  const { valid, warnings } = validateStockData(data);
  const name = data.name ?? data.code;

  if (!valid) {
    return {
      code: data.code, market: data.market, name,
      verdict: "观望",
      analysis: `## ⚠️ 数据获取失败\n\n${data.code} 数据无法获取（${data.error ?? "未知错误"}），建议手动核实。`,
      warnings, outputFormat,
      generatedAt: new Date().toISOString(),
    };
  }

  const zai = await ZAI.create();
  const userPrompt = outputFormat === "markdown"
    ? buildDashboardPrompt(data, position, warnings)
    : buildReportPrompt(data, position);

  let analysisText = "⚠️ LLM 未返回内容，请重试。";
  try {
    const completion = await zai.chat.completions.create({
      messages: [
        { role: "system", content: `你是一位资深${MARKET_LABEL[data.market]}股票分析师。数据缺失标"暂缺"，严禁捏造。乖离率>5%不得建议买入。结论四选一：强烈买入/买入/观望/卖出。输出语言：中文。` },
        { role: "user", content: userPrompt },
      ],
      thinking: { type: "disabled" },
    });
    analysisText = completion.choices[0]?.message?.content ?? analysisText;
  } catch (err: any) {
    analysisText = `## ⚠️ 分析失败\n\nLLM 调用出错：${err.message}`;
  }

  // 美股附加股息分析
  if (includeDividend && data.market === "US" && outputFormat === "markdown") {
    try {
      const dividend = await analyzeDividend(data.code);
      const dividendMd = formatDividendMarkdown(dividend);
      analysisText += `\n\n${dividendMd}`;
    } catch {}
  }

  return {
    code: data.code, market: data.market, name,
    verdict: extractVerdict(analysisText),
    analysis: analysisText,
    warnings, outputFormat,
    generatedAt: new Date().toISOString(),
  };
}

// ── 批量分析 ──────────────────────────────────────────────

export async function analyzeMultipleStocks(
  stockDataList: StockData[],
  outputFormat: OutputFormat = "markdown",
  positions?: Record<string, PositionInfo>,
  includeDividend = false
): Promise<AnalysisResult[]> {
  const results: AnalysisResult[] = [];
  for (const data of stockDataList) {
    const position = positions?.[data.code];
    results.push(await analyzeStock(data, outputFormat, position, includeDividend));
  }
  return results;
}

// ── K线图分析（VLM）──────────────────────────────────────

export async function analyzeChartImage(
  imageUrlOrBase64: string,
  stockCode: string,
  isBase64 = false
): Promise<string> {
  try {
    const zai = await ZAI.create();
    const imageContent = isBase64
      ? { type: "base64" as const, data: imageUrlOrBase64, mediaType: "image/png" as const }
      : { type: "url" as const, url: imageUrlOrBase64 };

    const completion = await zai.chat.completions.create({
      messages: [
        { role: "system", content: "你是技术分析专家，擅长K线形态识别。请用中文回答。" },
        {
          role: "user",
          content: [
            { type: "image", image: imageContent },
            { type: "text", text: `这是 ${stockCode} 的K线图，请分析：\n1. 当前K线形态\n2. 趋势方向\n3. 关键支撑位和压力位\n4. 成交量配合\n5. 短期操作建议` },
          ],
        },
      ],
    });
    return completion.choices[0]?.message?.content ?? "⚠️ VLM 未返回内容";
  } catch (err: any) {
    return `K线图分析失败：${err.message}`;
  }
}
