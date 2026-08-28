/**
 * types.ts — 统一类型定义
 */

export type Market = "CN" | "HK" | "US";
export type FetchMode = "full" | "quote";
export type OutputFormat = "markdown" | "pdf" | "word";
export type Verdict = "买入" | "强烈买入" | "观望" | "卖出";
export type PositionStatus = "empty" | "holding";

// ── 持仓信息 ──────────────────────────────────────────────

export interface PositionInfo {
  status: PositionStatus;
  cost?: number;
  shares?: number;
}

// ── 股票数据 ──────────────────────────────────────────────

export interface StockData {
  code: string;
  market: Market;
  timestamp: string;
  name?: string;
  price?: number | null;
  prev_close?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  change_pct?: number | null;
  change_amount?: number | null;
  amplitude?: number | null;
  volume?: number | null;
  amount?: number | null;
  turnover?: number | null;
  volume_ratio?: number | null;
  market_cap?: number | null;
  pe_ttm?: number | null;
  pb?: number | null;
  high_52w?: number | null;
  low_52w?: number | null;
  dividend_yield?: number | null;
  ma5?: number | null;
  ma10?: number | null;
  ma20?: number | null;
  bias_pct?: number | null;
  trend?: string;
  overbought_warning?: boolean;
  support?: number | null;
  resistance?: number | null;
  rsi?: number | null;
  kline_recent_10?: Record<string, any>[];
  profit_ratio?: number | null;
  avg_cost?: number | null;
  chip_concentration?: number | null;
  roe?: number | null;
  gross_margin?: number | null;
  net_margin?: number | null;
  debt_ratio?: number | null;
  eps?: number | null;
  revenue_growth?: number | null;
  main_net?: number | null;
  main_net_pct?: number | null;
  error?: string;
}

// ── 分析结果 ──────────────────────────────────────────────

export interface AnalysisResult {
  code: string;
  market: Market;
  name: string;
  verdict: Verdict;
  analysis: string;
  warnings: string[];
  outputFormat: OutputFormat;
  generatedAt: string;
}

// ── 股息分析 ──────────────────────────────────────────────

export type PayoutStatus = "safe" | "moderate" | "high" | "unsustainable" | "no_dividend" | "unknown";
export type IncomeRating = "excellent" | "good" | "moderate" | "poor" | "no_dividend";

export interface DividendAnalysis {
  ticker: string;
  name: string;
  currentPrice: number | null;
  dividendYield: number | null;        // %
  annualDividend: number | null;
  payoutRatio: number | null;          // %
  payoutStatus: PayoutStatus;
  dividendGrowth5y: number | null;     // CAGR %
  consecutiveYears: number | null;
  exDividendDate: string | null;
  paymentFrequency: string | null;
  safetyScore: number;                 // 0-100
  safetyFactors: string[];
  incomeRating: IncomeRating;
  dividendHistory: { year: number; total: number }[];
  summary: string;
}

// ── 传闻扫描 ──────────────────────────────────────────────

export type RumorType = "ma" | "insider" | "analyst" | "regulatory" | "earnings" | "general";

export interface RumorItem {
  type: RumorType;
  ticker: string | null;        // 相关股票代码（可能为 null）
  headline: string;
  source: string;
  impactScore: number;          // 1-10
  impactReason: string;
  sentiment: "positive" | "negative" | "neutral";
  date: string;
}

export interface RumorScanResult {
  scannedAt: string;
  rumors: RumorItem[];
  topTickers: { ticker: string; count: number }[];  // 最受关注的股票
  summary: string;
}

// ── 自选股 ────────────────────────────────────────────────

export type AlertType = "target_hit" | "stop_hit" | "signal_change";

export interface WatchlistItem {
  ticker: string;
  name?: string;
  market: Market;
  addedAt: string;
  priceAtAdd: number | null;
  targetPrice: number | null;
  stopPrice: number | null;
  alertOnSignal: boolean;
  lastSignal: Verdict | null;
  lastCheck: string | null;
  notes: string | null;
}

export interface WatchlistAlert {
  ticker: string;
  alertType: AlertType;
  message: string;
  currentPrice: number;
  triggerValue: number | string;
  timestamp: string;
}

// ── Skill 入参 ────────────────────────────────────────────

export interface StockInput {
  code: string;
  position?: PositionInfo;
}

export interface SkillInput {
  stocks?: (string | StockInput)[];
  outputFormat?: OutputFormat;
  mode?: FetchMode;
  includeMarketReview?: boolean;
  includeGlobalMacro?: boolean;
}
