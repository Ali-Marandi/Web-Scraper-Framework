---
description: AMiner 个性化论文推荐 — 按主题或学者画像
argument-hint: [topics: 主题1, 主题2 | scholar: 姓名 org: 机构 | 自然语言]
allowed-tools: Read, Bash, Glob, Grep
---

# /aminer-dp — AMiner Daily Paper

User invoked the AMiner daily paper recommendation skill with the following arguments:

```
$ARGUMENTS
```

## Your task

Strictly follow `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (English) or `${CLAUDE_PLUGIN_ROOT}/SKILL.zh.md` (Chinese). Key rules summarized below — but read the SKILL file if you need detail.

### 1. Pre-flight

Verify the `AMINER_API_KEY` env var is set:

```bash
[ -z "${AMINER_API_KEY+x}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

If missing, stop and tell the user to set it (token from <https://open.aminer.cn>). Do not call the script.

### 2. Parse `$ARGUMENTS` into structured fields

Extract any of: `topics`, `scholar` / `author_name`, `org` / `author_org`, `papers`, `size`, `language_sort`.

**Critical rules — do NOT violate:**

- **`topics`**: keep the user's exact wording. If they wrote `具身智能, 环境保护`, pass those Chinese strings through. **Never** translate them into unrelated English fields (e.g. don't map them to "Knowledge Distillation" or "Smart agriculture"). If you add an English alias, it must be a faithful translation of the same concept (e.g. 具身智能 → embodied intelligence).
- **`language_sort`**: include `zh` or `en` **only when the user explicitly asks** for Chinese-/English-biased ranking (e.g. "优先中文论文" / "prefer English papers"). Otherwise omit it entirely.
- **`scholar` / `org`**: use English-canonical names where reasonable (e.g. `Jie Tang`, `Tsinghua University`). If a Chinese name is ambiguous and no org is given, ask the user before guessing.
- If `$ARGUMENTS` is empty, call the script with no extra fields — the API will return personalized recs based on the API key.

### 3. Run the entrypoint

Reconstruct the trigger and execute (one call per topic group; ≤3 closely related terms per group):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/handle_trigger.py" \
  --base-dir "${CLAUDE_PLUGIN_ROOT}" \
  --text "/aminer-dp <reconstructed fields>"
```

### 4. Present the result

Parse the JSON output. When `final_response == "TEXT"`, render the `reply_text` (Markdown) directly to the user. On error, surface the error message; do not fall back to other skills.
