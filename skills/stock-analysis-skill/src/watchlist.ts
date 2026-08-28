/**
 * watchlist.ts
 * 自选股管理 + 价格提醒（使用平台 storage 持久化）
 * 移植原版三种提醒类型：目标价 / 止损价 / 信号变化
 */

import ZAI from "z-ai-web-dev-sdk";
import { WatchlistItem, WatchlistAlert, Market, Verdict } from "./types";

const STORAGE_KEY = "watchlist-data";

// ── Storage 封装 ──────────────────────────────────────────

async function loadWatchlist(): Promise<WatchlistItem[]> {
  try {
    const result = await (window as any).storage?.get(STORAGE_KEY);
    if (result?.value) return JSON.parse(result.value) as WatchlistItem[];
  } catch {}
  return [];
}

async function saveWatchlist(items: WatchlistItem[]): Promise<void> {
  try {
    await (window as any).storage?.set(STORAGE_KEY, JSON.stringify(items));
  } catch (err: any) {
    console.error("[watchlist] 保存失败:", err.message);
  }
}

// ── 获取当前价格 ──────────────────────────────────────────

async function fetchCurrentPrice(ticker: string): Promise<number | null> {
  try {
    const zai = await ZAI.create();
    const completion = await zai.chat.completions.create({
      messages: [{
        role: "user",
        content: `查询 ${ticker} 当前股价，只返回一个 JSON：{"price": 数字}，不要其他内容。`,
      }],
      thinking: { type: "disabled" },
    });
    const raw = completion.choices[0]?.message?.content ?? "{}";
    const parsed = JSON.parse(raw.replace(/```json|```/g, "").trim());
    return typeof parsed.price === "number" ? parsed.price : null;
  } catch {
    return null;
  }
}

function detectMarket(code: string): Market {
  if (/^\d{6}$/.test(code)) return "CN";
  if (/^\d{4,5}\.HK$/i.test(code)) return "HK";
  return "US";
}

// ── 添加自选股 ────────────────────────────────────────────

export async function addToWatchlist(
  ticker: string,
  opts: {
    targetPrice?: number;
    stopPrice?: number;
    alertOnSignal?: boolean;
    notes?: string;
  } = {}
): Promise<{ success: boolean; action: string; message: string; item?: WatchlistItem }> {
  ticker = ticker.toUpperCase();
  const currentPrice = await fetchCurrentPrice(ticker);

  if (currentPrice === null) {
    return { success: false, action: "error", message: `无法获取 ${ticker} 的价格，请确认代码正确` };
  }

  const watchlist = await loadWatchlist();
  const existingIdx = watchlist.findIndex((i) => i.ticker === ticker);

  if (existingIdx >= 0) {
    // 更新已有记录
    const existing = watchlist[existingIdx];
    if (opts.targetPrice !== undefined) existing.targetPrice = opts.targetPrice;
    if (opts.stopPrice !== undefined) existing.stopPrice = opts.stopPrice;
    if (opts.alertOnSignal !== undefined) existing.alertOnSignal = opts.alertOnSignal;
    if (opts.notes !== undefined) existing.notes = opts.notes;
    watchlist[existingIdx] = existing;
    await saveWatchlist(watchlist);

    return { success: true, action: "updated", message: `已更新 ${ticker} 的自选股设置`, item: existing };
  }

  // 新增
  const item: WatchlistItem = {
    ticker,
    market: detectMarket(ticker),
    addedAt: new Date().toISOString(),
    priceAtAdd: currentPrice,
    targetPrice: opts.targetPrice ?? null,
    stopPrice: opts.stopPrice ?? null,
    alertOnSignal: opts.alertOnSignal ?? false,
    lastSignal: null,
    lastCheck: null,
    notes: opts.notes ?? null,
  };

  watchlist.push(item);
  await saveWatchlist(watchlist);

  const alertDesc = [
    opts.targetPrice ? `目标价 $${opts.targetPrice}` : null,
    opts.stopPrice ? `止损价 $${opts.stopPrice}` : null,
    opts.alertOnSignal ? "信号变化提醒" : null,
  ].filter(Boolean).join("，");

  return {
    success: true, action: "added",
    message: `已添加 ${ticker} 到自选股（当前价 $${currentPrice}${alertDesc ? `，设置了：${alertDesc}` : ""}）`,
    item,
  };
}

// ── 删除自选股 ────────────────────────────────────────────

export async function removeFromWatchlist(
  ticker: string
): Promise<{ success: boolean; message: string }> {
  ticker = ticker.toUpperCase();
  const watchlist = await loadWatchlist();
  const filtered = watchlist.filter((i) => i.ticker !== ticker);

  if (filtered.length === watchlist.length) {
    return { success: false, message: `${ticker} 不在自选股列表中` };
  }

  await saveWatchlist(filtered);
  return { success: true, message: `已从自选股中删除 ${ticker}` };
}

// ── 查看自选股列表 ────────────────────────────────────────

export async function listWatchlist(): Promise<{
  items: Array<WatchlistItem & {
    currentPrice: number | null;
    changePct: number | null;
    toTargetPct: number | null;
    toStopPct: number | null;
  }>;
  count: number;
}> {
  const watchlist = await loadWatchlist();
  if (!watchlist.length) return { items: [], count: 0 };

  const items = await Promise.all(watchlist.map(async (item) => {
    const currentPrice = await fetchCurrentPrice(item.ticker);

    const changePct = currentPrice && item.priceAtAdd
      ? parseFloat((((currentPrice - item.priceAtAdd) / item.priceAtAdd) * 100).toFixed(2))
      : null;

    const toTargetPct = currentPrice && item.targetPrice
      ? parseFloat((((item.targetPrice - currentPrice) / currentPrice) * 100).toFixed(2))
      : null;

    const toStopPct = currentPrice && item.stopPrice
      ? parseFloat((((item.stopPrice - currentPrice) / currentPrice) * 100).toFixed(2))
      : null;

    return { ...item, currentPrice, changePct, toTargetPct, toStopPct };
  }));

  return { items, count: items.length };
}

// ── 检查提醒 ──────────────────────────────────────────────

export async function checkAlerts(
  currentSignals?: Record<string, Verdict>
): Promise<{ alerts: WatchlistAlert[]; count: number }> {
  const watchlist = await loadWatchlist();
  const alerts: WatchlistAlert[] = [];
  const now = new Date().toISOString();

  for (const item of watchlist) {
    const currentPrice = await fetchCurrentPrice(item.ticker);
    if (currentPrice === null) continue;

    // 目标价提醒
    if (item.targetPrice && currentPrice >= item.targetPrice) {
      alerts.push({
        ticker: item.ticker,
        alertType: "target_hit",
        message: `🎯 ${item.ticker} 已触达目标价！当前 $${currentPrice.toFixed(2)} ≥ 目标 $${item.targetPrice}`,
        currentPrice,
        triggerValue: item.targetPrice,
        timestamp: now,
      });
    }

    // 止损价提醒
    if (item.stopPrice && currentPrice <= item.stopPrice) {
      alerts.push({
        ticker: item.ticker,
        alertType: "stop_hit",
        message: `🛑 ${item.ticker} 已触达止损价！当前 $${currentPrice.toFixed(2)} ≤ 止损 $${item.stopPrice}`,
        currentPrice,
        triggerValue: item.stopPrice,
        timestamp: now,
      });
    }

    // 信号变化提醒
    if (item.alertOnSignal && currentSignals?.[item.ticker]) {
      const newSignal = currentSignals[item.ticker];
      if (item.lastSignal && newSignal !== item.lastSignal) {
        alerts.push({
          ticker: item.ticker,
          alertType: "signal_change",
          message: `📊 ${item.ticker} 信号变化：${item.lastSignal} → ${newSignal}`,
          currentPrice,
          triggerValue: `${item.lastSignal} → ${newSignal}`,
          timestamp: now,
        });
      }
      // 更新最新信号
      item.lastSignal = newSignal;
    }

    item.lastCheck = now;
  }

  // 保存更新后的 lastSignal 和 lastCheck
  await saveWatchlist(watchlist);

  return { alerts, count: alerts.length };
}

// ── 格式化自选股列表（Markdown）─────────────────────────

export function formatWatchlistMarkdown(data: Awaited<ReturnType<typeof listWatchlist>>): string {
  if (data.count === 0) {
    return `## 📋 自选股列表\n\n_自选股为空。使用 \`/stock_watch AAPL\` 添加股票。_\n`;
  }

  let md = `## 📋 自选股列表（共 ${data.count} 只）\n\n`;
  md += `| 代码 | 当前价 | 较买入 | 目标价 | 止损价 | 距目标 | 最新信号 |\n`;
  md += `|------|--------|--------|--------|--------|--------|----------|\n`;

  for (const item of data.items) {
    const price = item.currentPrice ? `$${item.currentPrice.toFixed(2)}` : "暂缺";
    const change = item.changePct !== null
      ? `${item.changePct > 0 ? "🟢+" : "🔴"}${item.changePct.toFixed(2)}%`
      : "—";
    const target = item.targetPrice ? `$${item.targetPrice}` : "—";
    const stop = item.stopPrice ? `$${item.stopPrice}` : "—";
    const toTarget = item.toTargetPct !== null ? `${item.toTargetPct > 0 ? "+" : ""}${item.toTargetPct.toFixed(1)}%` : "—";
    const signal = item.lastSignal ?? "—";

    md += `| ${item.ticker} | ${price} | ${change} | ${target} | ${stop} | ${toTarget} | ${signal} |\n`;
  }

  // 已触发的提醒
  const triggered = data.items.filter(
    (i) => (i.targetPrice && i.currentPrice && i.currentPrice >= i.targetPrice) ||
            (i.stopPrice && i.currentPrice && i.currentPrice <= i.stopPrice)
  );

  if (triggered.length > 0) {
    md += `\n### ⚡ 已触发提醒\n`;
    for (const item of triggered) {
      if (item.targetPrice && item.currentPrice && item.currentPrice >= item.targetPrice) {
        md += `- 🎯 **${item.ticker}** 已达目标价 $${item.targetPrice}\n`;
      }
      if (item.stopPrice && item.currentPrice && item.currentPrice <= item.stopPrice) {
        md += `- 🛑 **${item.ticker}** 已触止损 $${item.stopPrice}\n`;
      }
    }
  }

  return md;
}

// ── 格式化提醒结果（Markdown）────────────────────────────

export function formatAlertsMarkdown(result: Awaited<ReturnType<typeof checkAlerts>>): string {
  if (result.count === 0) {
    return `## 🔔 自选股提醒检查\n\n_当前没有触发任何提醒。_\n`;
  }

  let md = `## 🔔 自选股提醒（${result.count} 条触发）\n\n`;
  for (const alert of result.alerts) {
    md += `- ${alert.message}\n`;
  }
  return md;
}
