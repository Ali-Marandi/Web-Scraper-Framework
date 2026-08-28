/**
 * dividend.ts
 * 股息分析模块（适配 finance skill）
 * 移植原版评分逻辑：安全评分 / CAGR / 连续增长年数 / 派息可持续性
 */

import ZAI from "z-ai-web-dev-sdk";
import { DividendAnalysis, PayoutStatus, IncomeRating } from "./types";

// ── 核心评分逻辑（与原版完全一致）──────────────────────────

function calcPayoutStatus(payoutRatio: number | null): PayoutStatus {
  if (payoutRatio === null) return "unknown";
  if (payoutRatio < 40) return "safe";
  if (payoutRatio < 60) return "moderate";
  if (payoutRatio < 80) return "high";
  return "unsustainable";
}

function calcSafetyScore(data: {
  payoutRatio: number | null;
  dividendGrowth5y: number | null;
  consecutiveYears: number | null;
  dividendYield: number | null;
}): { score: number; factors: string[] } {
  let score = 50;
  const factors: string[] = [];

  // 派息率（±20）
  if (data.payoutRatio !== null) {
    if (data.payoutRatio < 40) { score += 20; factors.push(`派息率健康（${data.payoutRatio.toFixed(0)}%）`); }
    else if (data.payoutRatio < 60) { score += 10; factors.push(`派息率适中（${data.payoutRatio.toFixed(0)}%）`); }
    else if (data.payoutRatio < 80) { score -= 10; factors.push(`派息率偏高（${data.payoutRatio.toFixed(0)}%）`); }
    else { score -= 20; factors.push(`派息率不可持续（${data.payoutRatio.toFixed(0)}%）`); }
  }

  // 5年增长率（±15）
  if (data.dividendGrowth5y !== null) {
    if (data.dividendGrowth5y > 10) { score += 15; factors.push(`股息增长强劲（${data.dividendGrowth5y.toFixed(1)}% CAGR）`); }
    else if (data.dividendGrowth5y > 5) { score += 10; factors.push(`股息增长良好（${data.dividendGrowth5y.toFixed(1)}% CAGR）`); }
    else if (data.dividendGrowth5y > 0) { score += 5; factors.push(`股息小幅增长（${data.dividendGrowth5y.toFixed(1)}% CAGR）`); }
    else { score -= 15; factors.push(`股息下降（${data.dividendGrowth5y.toFixed(1)}% CAGR）`); }
  }

  // 连续增长年数（±15）
  if (data.consecutiveYears !== null) {
    if (data.consecutiveYears >= 25) { score += 15; factors.push(`股息贵族（连续${data.consecutiveYears}年增长）`); }
    else if (data.consecutiveYears >= 10) { score += 10; factors.push(`长期稳定股息（${data.consecutiveYears}年）`); }
    else if (data.consecutiveYears >= 5) { score += 5; factors.push(`股息稳定（${data.consecutiveYears}年）`); }
  }

  // 高收益率风险（-10）
  if (data.dividendYield !== null) {
    if (data.dividendYield > 8) { score -= 10; factors.push(`收益率过高（${data.dividendYield.toFixed(1)}%），需核实可持续性`); }
    else if (data.dividendYield < 1) { factors.push(`收益率偏低（${data.dividendYield.toFixed(2)}%）`); }
  }

  return { score: Math.max(0, Math.min(100, score)), factors };
}

function calcIncomeRating(safetyScore: number): IncomeRating {
  if (safetyScore >= 80) return "excellent";
  if (safetyScore >= 60) return "good";
  if (safetyScore >= 40) return "moderate";
  return "poor";
}

// ── 通过 finance skill 获取股息数据 ──────────────────────

async function fetchDividendData(ticker: string): Promise<Record<string, any>> {
  const zai = await ZAI.create();

  const completion = await zai.chat.completions.create({
    messages: [{
      role: "user",
      content: `请查询 ${ticker} 的股息数据，只返回 JSON，包含：
name（公司名称）, currentPrice（当前股价）,
dividendYield（年化股息率%）, annualDividend（年度每股股息）,
trailingEps（过去12月每股收益）,
exDividendDate（除权日 YYYY-MM-DD 格式）,
paymentFrequency（"monthly"/"quarterly"/"annual"，根据派息频率判断）,
dividendHistory（近5年年度股息数组，每项含 year 和 total，从新到旧排序）,
consecutiveYears（连续股息增长年数，整数）,
dividendGrowth5y（近5年股息 CAGR %）。
缺失字段填 null，不得捏造。`,
    }],
    thinking: { type: "disabled" },
  });

  const raw = completion.choices[0]?.message?.content ?? "{}";
  return JSON.parse(raw.replace(/```json|```/g, "").trim());
}

// ── 主分析函数 ────────────────────────────────────────────

export async function analyzeDividend(ticker: string): Promise<DividendAnalysis> {
  ticker = ticker.toUpperCase();

  let raw: Record<string, any> = {};
  try {
    raw = await fetchDividendData(ticker);
  } catch (err: any) {
    return {
      ticker, name: ticker, currentPrice: null,
      dividendYield: null, annualDividend: null,
      payoutRatio: null, payoutStatus: "unknown",
      dividendGrowth5y: null, consecutiveYears: null,
      exDividendDate: null, paymentFrequency: null,
      safetyScore: 0, safetyFactors: [`数据获取失败：${err.message}`],
      incomeRating: "poor", dividendHistory: [],
      summary: `${ticker} 股息数据获取失败。`,
    };
  }

  // 无股息
  if (!raw.annualDividend || raw.annualDividend === 0) {
    return {
      ticker, name: raw.name ?? ticker,
      currentPrice: raw.currentPrice ?? null,
      dividendYield: null, annualDividend: null,
      payoutRatio: null, payoutStatus: "no_dividend",
      dividendGrowth5y: null, consecutiveYears: null,
      exDividendDate: null, paymentFrequency: null,
      safetyScore: 0, safetyFactors: ["该股票不派息"],
      incomeRating: "no_dividend", dividendHistory: [],
      summary: `${ticker} 目前不派发股息。`,
    };
  }

  // 计算派息率
  const payoutRatio = (raw.trailingEps && raw.trailingEps > 0 && raw.annualDividend)
    ? parseFloat(((raw.annualDividend / raw.trailingEps) * 100).toFixed(1))
    : null;

  const payoutStatus = calcPayoutStatus(payoutRatio);
  const { score: safetyScore, factors: safetyFactors } = calcSafetyScore({
    payoutRatio,
    dividendGrowth5y: raw.dividendGrowth5y ?? null,
    consecutiveYears: raw.consecutiveYears ?? null,
    dividendYield: raw.dividendYield ?? null,
  });

  const incomeRating = calcIncomeRating(safetyScore);

  // 生成摘要
  const parts: string[] = [];
  if (raw.dividendYield) parts.push(`收益率 ${Number(raw.dividendYield).toFixed(2)}%`);
  if (payoutRatio) parts.push(`派息率 ${payoutRatio.toFixed(0)}%`);
  if (raw.dividendGrowth5y) parts.push(`5年增长 ${Number(raw.dividendGrowth5y) > 0 ? "+" : ""}${Number(raw.dividendGrowth5y).toFixed(1)}%`);
  if (raw.consecutiveYears && raw.consecutiveYears >= 5) parts.push(`连续增长 ${raw.consecutiveYears} 年`);

  const ratingLabel: Record<IncomeRating, string> = {
    excellent: "优秀", good: "良好", moderate: "一般", poor: "较差", no_dividend: "无股息",
  };

  return {
    ticker,
    name: raw.name ?? ticker,
    currentPrice: raw.currentPrice ?? null,
    dividendYield: raw.dividendYield ? Number(Number(raw.dividendYield).toFixed(2)) : null,
    annualDividend: raw.annualDividend ?? null,
    payoutRatio,
    payoutStatus,
    dividendGrowth5y: raw.dividendGrowth5y ? Number(Number(raw.dividendGrowth5y).toFixed(2)) : null,
    consecutiveYears: raw.consecutiveYears ?? null,
    exDividendDate: raw.exDividendDate ?? null,
    paymentFrequency: raw.paymentFrequency ?? null,
    safetyScore,
    safetyFactors,
    incomeRating,
    dividendHistory: raw.dividendHistory ?? [],
    summary: `${ticker}（${raw.name ?? ""}）：${parts.join("，")}。评级：${ratingLabel[incomeRating]}`,
  };
}

// ── 格式化输出（Markdown 仪表盘）─────────────────────────

export function formatDividendMarkdown(analysis: DividendAnalysis): string {
  if (analysis.incomeRating === "no_dividend") {
    return `### 💰 股息分析 · ${analysis.ticker}\n\n该股票目前不派发股息。`;
  }

  const ratingEmoji: Record<IncomeRating, string> = {
    excellent: "🏆", good: "✅", moderate: "⚠️", poor: "❌", no_dividend: "—",
  };

  const payoutLabel: Record<string, string> = {
    safe: "✅ 安全", moderate: "⚠️ 适中", high: "⚠️ 偏高", unsustainable: "❌ 不可持续", unknown: "暂缺",
  };

  let md = `### 💰 股息分析 · ${analysis.ticker}（${analysis.name}）

| 指标 | 数值 |
|------|------|
| 股息收益率 | ${analysis.dividendYield ? `${analysis.dividendYield}%` : "暂缺"} |
| 年度每股股息 | ${analysis.annualDividend ? `$${analysis.annualDividend}` : "暂缺"} |
| 派息频率 | ${analysis.paymentFrequency ?? "暂缺"} |
| 除权日 | ${analysis.exDividendDate ?? "暂缺"} |
| 派息率 | ${analysis.payoutRatio ? `${analysis.payoutRatio}%（${payoutLabel[analysis.payoutStatus]}）` : "暂缺"} |
| 5年股息增长 | ${analysis.dividendGrowth5y ? `${analysis.dividendGrowth5y > 0 ? "+" : ""}${analysis.dividendGrowth5y}%` : "暂缺"} |
| 连续增长年数 | ${analysis.consecutiveYears ?? "暂缺"} |

**安全评分：${analysis.safetyScore}/100　${ratingEmoji[analysis.incomeRating]} 收入评级：${analysis.incomeRating.toUpperCase()}**

评分依据：
${analysis.safetyFactors.map((f) => `- ${f}`).join("\n")}
`;

  if (analysis.dividendHistory.length > 0) {
    md += `\n近年股息历史：\n`;
    md += analysis.dividendHistory.slice(0, 5).map((h) => `- ${h.year}年：$${h.total}`).join("\n");
  }

  return md;
}

// ── 批量分析 ──────────────────────────────────────────────

export async function analyzeDividends(tickers: string[]): Promise<DividendAnalysis[]> {
  const results: DividendAnalysis[] = [];
  for (const ticker of tickers) {
    results.push(await analyzeDividend(ticker));
    await new Promise((r) => setTimeout(r, 200));
  }
  return results;
}
