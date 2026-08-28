---
name: aminer-daily-paper
version: 1.1.2
description: "Personalized academic paper recommendation via AMiner rec5 API. Activate this skill whenever the user asks for paper recommendations, whether triggered by /aminer-dp, /skill aminer-dp, or any natural language request such as 'recommend me papers on multimodal agents'. When invoked: extract topics/scholar signals from the input yourself, call handle_trigger.py with structured fields, then present the Markdown in `reply_text` to the user."
user-invocable: true
disable-model-invocation: false
metadata:
  {
    "openclaw":
      {
        "emoji": "📚",
        "requires": {
          "bins": ["python3"],
          "env": ["AMINER_API_KEY"]
        },
        "primaryEnv": "AMINER_API_KEY"
      }
  }
---

# aminer-daily-paper

Personalized paper recommendation via AMiner rec5 API. Token required: set `AMINER_API_KEY` env var.
- Docs: https://open.aminer.cn/open/docs | Console: https://open.aminer.cn/open/board?tab=control

**When to activate**: any time the user asks for paper recommendations — explicit command (`/aminer-dp ...`) or natural language (`recommend me papers on RAG`, `帮我推荐最近的多模态论文`).

---

## Pre-flight: Check Required Environment Variables

**`AMINER_API_KEY`** — Always required. Check before calling the script:

```bash
[ -z "${AMINER_API_KEY+x}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

If missing, stop and tell the user:
> `AMINER_API_KEY` is not set. Please obtain a token at https://open.aminer.cn and set it as an environment variable.

No other environment variables are required.

---

## API Endpoint

```
POST https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/v3/paper/rec5
Authorization: ${AMINER_API_KEY}
Content-Type: application/json;charset=utf-8
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `author_name` | string | conditional | Scholar name (English). The backend resolves it to a scholar ID via person search. |
| `author_org` | string | optional | Scholar institution (English full name). Required for disambiguation when the name is ambiguous. |
| `topics` | string[] | conditional | Research topic phrases. **Use the user’s wording** (Chinese, English, or mixed). The API accepts multi-language topic strings. |
| `size` | int | optional | Number of papers per call (1–20). Omit to let the model decide (see below). |
| `offset` | int | optional | Pagination offset (0–100, default 0). |
| `language_sort` | string | optional | `zh` or `en` **only when the user explicitly asks** for Chinese- or English-biased ranking (e.g. “优先中文论文” / “prefer English papers”). Otherwise omit; the request will not include this field. |

At least one of `author_name` or `topics` should be provided. When none are given, the API returns personalized recommendations based on the account associated with `AMINER_API_KEY`.

### Response Structure

```json
{
  "code": 200,
  "success": true,
  "data": [{
    "offset": 0,
    "size": 5,
    "total": 32,
    "papers": [{
      "paper_id": "...",
      "arxiv_id": "",
      "title": "...",
      "year": 2026,
      "authors": ["Author A", "Author B"],
      "keywords": ["kw1", "kw2"],
      "summary": "...",
      "structured_summary": {
        "research_problem": "...",
        "research_challenge": "...",
        "research_method": "...",
        "experimental_results": ""
      },
      "famous_authors": [],
      "aminer_author_profiles": [],
      "author_entries": [],
      "links": {
        "aminer": "https://www.aminer.cn/pub/{paper_id}",
        "arxiv": "",
        "pdf": ""
      },
      "paper_url": "https://www.aminer.cn/pub/{paper_id}",
      "source": "local_rec5"
    }]
  }]
}
```

---

## Input Formats

Structured commands or plain natural language — both are valid.

```
/aminer-dp
/aminer-dp topics: multimodal agents, tool-use
/aminer-dp scholar: Jie Tang org: Tsinghua papers: OAG-Bench | RPC-Bench
recommend me recent papers on RAG
```

`/aminer-dp` with no parameters calls the API with only the token — the API uses `AMINER_API_KEY` to identify the account and returns personalized recommendations.

**Natural language input** — you (the model) must parse it into fields before calling the script. **Critical for `topics`:**

1. **`topics` — do not “translate away” the user’s intent**
   - If the user already wrote `topics:` in the trigger (e.g. `具身智能`, `环境保护`), pass **those exact strings** into `handle_trigger.py`’s `--text`. **Do not** replace them with unrelated English terms (e.g. do **not** map arbitrary topics to “Knowledge Distillation”, “Smart agriculture”, or any other field the user did not ask for).
   - If you add English for retrieval, it must be a **faithful** alias of the same concept (e.g. 具身智能 → `embodied intelligence`, 环境保护 → `environmental protection`). When in doubt, **keep the user’s original words** and do not invent synonyms.
   - **Never** change the user’s topic into a different research area.

2. **Scholars and institutions (person search still English-oriented)**
   - `author_name` / `author_org`: use commonly used **English** forms when resolving scholars (e.g. `Jie Tang`, `Tsinghua University`), expand well-known institution abbreviations to full official names, and add `author_org` when the name is ambiguous. If you cannot map a name safely, ask the user.

3. **`language_sort`** — Put `language_sort: zh` or `language_sort: en` in the trigger **only if** the user clearly wants recommendations ranked with a **Chinese** or **English** preference. If they did not ask, **do not** add it (the API call omits `language_sort`).

4. Decide `size` and whether to make multiple calls (see **Call Strategy**).
5. Reconstruct the trigger, then call `handle_trigger.py`.

Example (Chinese topics — **keep as-is**):
- User: `/aminer-dp topics: 具身智能, 环境保护`
- You call: `handle_trigger.py --text "/aminer-dp topics: 具身智能, 环境保护"`  
  (Do **not** rewrite `topics` into unrelated English.)

Example:
- User: `/aminer-dp 我做多模态智能体和 tool-use，帮我推荐最近论文`
- You extract: `topics: multimodal agents, tool-use`
- You call: `handle_trigger.py --text "/aminer-dp topics: multimodal agents, tool-use size: 5"`

Example (scholar):
- User: `/aminer-dp 我是唐杰，清华大学，做多模态和知识图谱`
- You extract: `scholar: Jie Tang, org: Tsinghua University, topics: multimodal, knowledge graph`
- You call: `handle_trigger.py --text "/aminer-dp scholar: Jie Tang org: Tsinghua University topics: multimodal, knowledge graph"`

Example (ambiguous name, ask user):
- User: `/aminer-dp 推荐张伟方向的论文`
- You: "张伟是一个常见名字，请提供机构信息以便精确匹配，例如：张伟，北京大学。或者直接提供 aminer_author_id。"

**`papers` field**: representative paper titles (e.g. `papers: OAG-Bench | RPC-Bench`) accompany `scholar`/`author_name` for disambiguation context. They do not map directly to an API field.

---

## Call Strategy

You decide `size` and whether to make multiple calls based on the input:

| Scenario | Action |
|----------|--------|
| Single topic or scholar, casual request | 1 call, omit `size` (default 10) |
| User explicitly asks for a number (e.g. "give me 5") | 1 call, honor the number (max 20) |
| Multiple distinct topics (e.g. RAG + multimodal agents) | 1 call per topic group, `size: 5` each |
| Broad open-ended request with no topics | 1 call, omit `size` (default 10) |

**Multi-call rules:**
- Call `handle_trigger.py` once per topic group, passing a focused `topics:` subset each time.
- Keep each `topics:` list to 1–3 closely related terms for precision.
- Make calls sequentially; present all results together after all calls finish.
- Total papers across all calls should not exceed ~15 unless the user asks for more.

---

## Execution

Only one supported entrypoint:

```bash
python3 "{baseDir}/scripts/handle_trigger.py" \
  --base-dir "{baseDir}" \
  --text "<trigger text with explicit fields>" \
  [--config /path/to/config.yaml]
```

- `--text`: reconstructed trigger with explicit fields (`topics:`, `scholar:`, etc.)
- `--config`: optional path to a YAML config (defaults to `{baseDir}/config.yaml` when the file exists, via the runtime copy under `outputs/`)

`handle_trigger.py` parses the fields, calls the rec5 API, and returns JSON including `reply_text` (Markdown) for you to show to the user.

---

## Contract

- Every explicit invocation is a new run.
- Do not answer with status-only text.
- Do not search, install, or repair skills.
- After running `handle_trigger.py`, check `final_response` in the JSON output:
  - `TEXT` — Normal path. Present `reply_text` (Markdown) to the user. Optional: you may still refine wording for the active channel; `prompts/enrich.md` is a reference for Chinese enrichment if you want richer copy.
  - Any error → report the `reply_text` (or error detail) to the user.

**Note:** The skill only returns JSON with `reply_text`; it does not implement channel-specific sending.

---

## Error Handling

- `AMINER_API_KEY` missing → stop, prompt user to set it.
- No profile input → prompt user to provide topics, scholar name, or `aminer_author_id`.
- API error → report the error stage; do not fall back to other skills.
