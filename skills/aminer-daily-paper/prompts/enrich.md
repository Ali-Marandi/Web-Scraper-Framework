# Paper Enrichment Prompt

You are enriching academic papers with Chinese content before they are sent as Feishu cards.

For each paper in the `papers` array that is missing a Chinese summary (i.e., the `summary` field contains only English text or is empty), generate:

1. **summary** — A concise Chinese summary (1-2 sentences, starting with "本文"). Describe the core contribution and significance. Keep English terms (e.g., RAG, LLM, Transformer) as-is.
2. **keywords** — 2-4 Chinese keywords. Keep well-known English acronyms as-is.
3. **comment** — If the paper's venue is a well-known conference/journal, annotate its tier, e.g., "已发表在 AAAI（CCF-A）". Leave empty if unknown.

Rules:
- Do NOT fabricate information not present in the paper's title/abstract.
- Do NOT generate or modify `famous_authors`.
- If the abstract is missing or too short to summarize, write "摘要信息不足，请查看原文。"
- Preserve all other fields unchanged.

## Input

The papers are in `papers_summarized.json` at the path provided. The file structure:

```json
{
  "status": "success",
  "profile_topics": ["topic1", "topic2"],
  "papers": [
    {
      "title": "...",
      "summary": "...(may be English-only)...",
      "keywords": ["kw1", "kw2"],
      "authors": ["..."],
      "comment": "",
      ...other fields preserved as-is...
    }
  ]
}
```

## Output

Write the enriched data back to the same `papers_summarized.json` path, preserving all fields. Only update `summary`, `keywords`, and `comment` for papers that need enrichment.
