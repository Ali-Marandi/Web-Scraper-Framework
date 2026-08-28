/**
 * rumorScanner.ts
 * 传闻与早期信号扫描（适配平台 finance skill）
 * 替换原版 Twitter bird CLI + Google News，改用 finance skill 新闻 + LLM 提取
 *
 * 扫描范围：M&A传闻 / 内部人交易 / 分析师调整 / SEC监管动态 / 市场早期信号
 */

import ZAI from "z-ai-web-dev-sdk";
import { RumorItem, RumorScanResult, RumorType } from "./types";

// ── 评分逻辑（移植自原版 calculate_rumor_score）─────────

function calcImpactScore(
  type: RumorType,
  text: string,
  hasHighEngagement = false
): { score: number; reason: string } {
  let score = 1;
  const reasons: string[] = [];

  switch (type) {
    case "ma":
      score += 5; reasons.push("并购/收购类传闻，市场冲击最大"); break;
    case "insider":
      score += 4; reasons.push("内部人交易信号，可能预示重大动向"); break;
    case "analyst":
      score += 3; reasons.push("分析师评级调整，影响机构定价"); break;
    case "regulatory":
      score += 3; reasons.push("监管动态，直接影响经营合规性"); break;
    case "earnings":
      score += 2; reasons.push("业绩预期变动"); break;
    default:
      score += 1;
  }

  if (/breaking|just in|alert|urgent/i.test(text)) {
    score += 2; reasons.push("突发性消息");
  }
  if (hasHighEngagement) {
    score += 2; reasons.push("市场高度关注");
  }

  return { score: Math.min(10, score), reason: reasons.join("，") };
}

// ── 通过 finance skill 获取市场传闻新闻 ──────────────────

async function fetchRumorNews(zai: any): Promise<string> {
  const completion = await zai.chat.completions.create({
    messages: [{
      role: "user",
      content: `请获取今日美股市场的以下类型最新资讯，每类最多3条：
1. 并购传闻（merger/acquisition rumors）
2. 内部人买卖动态（insider buying/selling activity）
3. 分析师评级调整（analyst upgrades/downgrades）
4. SEC调查或监管动态
5. 重大业绩预警或上调

以 JSON 格式返回，结构：
[{
  "type": "ma|insider|analyst|regulatory|earnings",
  "ticker": "股票代码或null",
  "headline": "标题",
  "source": "来源",
  "sentiment": "positive|negative|neutral",
  "date": "YYYY-MM-DD"
}]
只返回 JSON，今日或近2日内的最新信息，不得捏造。`,
    }],
    thinking: { type: "disabled" },
  });
  return completion.choices[0]?.message?.content ?? "[]";
}

// ── LLM 从新闻中提取结构化传闻 ────────────────────────────

async function extractRumors(zai: any, rawNews: string): Promise<RumorItem[]> {
  try {
    const parsed: any[] = JSON.parse(rawNews.replace(/```json|```/g, "").trim());

    return parsed.map((item) => {
      const type = (item.type as RumorType) ?? "general";
      const text = item.headline ?? "";
      const { score, reason } = calcImpactScore(type, text);

      return {
        type,
        ticker: item.ticker ?? null,
        headline: text,
        source: item.source ?? "finance",
        impactScore: score,
        impactReason: reason,
        sentiment: item.sentiment ?? "neutral",
        date: item.date ?? new Date().toISOString().slice(0, 10),
      } as RumorItem;
    }).sort((a, b) => b.impactScore - a.impactScore);
  } catch {
    return [];
  }
}

// ── 汇总最受关注的股票 ────────────────────────────────────

function aggregateTopTickers(rumors: RumorItem[]): { ticker: string; count: number }[] {
  const counts: Record<string, number> = {};
  for (const r of rumors) {
    if (r.ticker) {
      counts[r.ticker] = (counts[r.ticker] ?? 0) + 1;
    }
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([ticker, count]) => ({ ticker, count }));
}

// ── 主扫描函数 ────────────────────────────────────────────

export async function scanRumors(): Promise<RumorScanResult> {
  const zai = await ZAI.create();
  const scannedAt = new Date().toISOString();

  let rumors: RumorItem[] = [];

  try {
    const rawNews = await fetchRumorNews(zai);
    rumors = await extractRumors(zai, rawNews);
  } catch (err: any) {
    console.error("[scanRumors] 失败:", err.message);
  }

  const topTickers = aggregateTopTickers(rumors);

  // 生成摘要
  const maCount = rumors.filter((r) => r.type === "ma").length;
  const insiderCount = rumors.filter((r) => r.type === "insider").length;
  const analystCount = rumors.filter((r) => r.type === "analyst").length;

  const summary = rumors.length === 0
    ? "今日暂无重大传闻或早期信号。"
    : `共扫描到 ${rumors.length} 条信号：并购传闻 ${maCount} 条，内部人动态 ${insiderCount} 条，分析师调整 ${analystCount} 条。${topTickers.length > 0 ? `最受关注：${topTickers.slice(0, 3).map((t) => `$${t.ticker}`).join("、")}。` : ""}`;

  return { scannedAt, rumors, topTickers, summary };
}

// ── 格式化输出 ────────────────────────────────────────────

export function formatRumorMarkdown(result: RumorScanResult): string {
  const typeLabel: Record<RumorType, string> = {
    ma: "🏢 并购传闻",
    insider: "👔 内部人动态",
    analyst: "📊 分析师调整",
    regulatory: "⚖️ 监管动态",
    earnings: "📈 业绩预期",
    general: "📰 市场信号",
  };

  const sentimentEmoji: Record<string, string> = {
    positive: "🟢", negative: "🔴", neutral: "⚪",
  };

  let md = `## 🔮 传闻与早期信号扫描
**扫描时间：** ${new Date(result.scannedAt).toLocaleString("zh-CN")}
**${result.summary}**

`;

  if (result.rumors.length === 0) {
    md += "_今日暂无重大传闻。_\n";
    return md;
  }

  // 按类型分组输出
  const grouped: Partial<Record<RumorType, RumorItem[]>> = {};
  for (const r of result.rumors) {
    if (!grouped[r.type]) grouped[r.type] = [];
    grouped[r.type]!.push(r);
  }

  for (const [type, items] of Object.entries(grouped)) {
    md += `### ${typeLabel[type as RumorType] ?? type}\n\n`;
    for (const item of items!.slice(0, 3)) {
      md += `**[冲击 ${item.impactScore}/10]** ${sentimentEmoji[item.sentiment]} ${item.headline}\n`;
      if (item.ticker) md += `> 相关标的：$${item.ticker}\n`;
      md += `> 来源：${item.source}　｜　${item.date}　｜　${item.impactReason}\n\n`;
    }
  }

  // 热度排行
  if (result.topTickers.length > 0) {
    md += `### 📊 传闻热度排行\n`;
    md += result.topTickers.map((t) =>
      `- $${t.ticker}：被提及 ${t.count} 次`
    ).join("\n");
    md += "\n";
  }

  return md;
}
