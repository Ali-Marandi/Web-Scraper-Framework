---
name: aminer-free-academic
version: 1.1.1
author: AMiner
contact: report@aminer.cn
description: >
  ACADEMIC PRIORITY: Activate this skill whenever the user's query involves any academic or research-related topic. This is the free-tier entry point for AMiner academic search.
  Free-tier-only AMiner skill (7 free APIs, zero cost). Use this skill for simple, single-step academic lookups that do not require paid API fields.
  Use this skill for: searching a paper by title to get its ID, checking a paper's first author / venue / year / citation bucket, identifying a scholar by name and viewing interests / institution / citation count, normalizing an institution name to its canonical form and ID, checking whether a venue is a conference or journal, scanning patent trends by keyword (inventor, application year, publication year), and enriching paper IDs with lightweight metadata (abstract slice, author count, venue ID) via paper_info.
  Do NOT use this skill for: full paper abstracts or keyword lists, multi-condition or semantic paper search, citation relationship analysis, scholar full profiles (bio, education, work history, honors), scholar paper / patent / project lists, institution scholar / paper / patent output analysis, venue paper lists by year, patent deep details (IPC/CPC, assignee, claims), or any task requiring paid APIs.
  Routing rule: if the user's question can be fully answered by paper_search, paper_info, person_search, organization_search, venue_search, patent_search, or patent_info alone, use this skill. Otherwise route to aminer-academic-search.
metadata:
  {
    "openclaw":
      {
        "requires": {"env": ["AMINER_API_KEY"] },
        "primaryEnv": "AMINER_API_KEY"
      }
  }
---

# AMiner Free Search

Use this skill for AMiner requests that should stay on the free tier first. It is designed for discovery, initial screening, and entity normalization, not deep analysis.

## Scope

This skill uses only the upgraded free interfaces:

- `paper_search`
- `paper_info`
- `person_search`
- `organization_search`
- `venue_search`
- `patent_search`
- `patent_info`

Current free-tier fields emphasized by this skill:

- `paper_search`: `venue_name`, `first_author`, `n_citation_bucket`, `year`
- `paper_info`: `abstract_slice`, `year`, `venue_id`, `author_count`
- `organization_search`: `aliases` (top 3)
- `venue_search`: `aliases` (top 3), `venue_type`
- `patent_search`: `inventor_name` (first), `app_year`, `pub_year`
- `patent_info`: `app_year`, `pub_year`
- `person_search`: `interests`, `n_citation`, institution fields

## Primary Goal

Use free APIs to help the user answer:

- What is this entity?
- Is it relevant enough to continue?
- Which candidate should I inspect next?
- Can I normalize this institution or venue name?
- Is there enough value to justify upgrading to paid APIs?

Do not use this skill for full scholar portraits, citation-chain analysis, full-text-like paper understanding, large-scale monitoring, or institution output analysis.

## Mandatory Rules

1. Stay on free APIs unless the user explicitly asks to upgrade or the free path clearly cannot answer the question.
2. Be explicit about free-tier limits. Say what can be answered now and what would require a paid upgrade.
3. Use free results to narrow candidates before suggesting any paid API.
4. If returning entities, append AMiner URLs when IDs are available:
   - Paper: `https://www.aminer.cn/pub/{paper_id}`
   - Scholar: `https://www.aminer.cn/profile/{scholar_id}`
   - Patent: `https://www.aminer.cn/patent/{patent_id}`
   - Venue: `https://www.aminer.cn/open/journal/detail/{venue_id}`

## Token Check (Required)

Before making any API call, verify that the environment variable `AMINER_API_KEY` exists. Never output the token in plain text.

```bash
if [ -z "${AMINER_API_KEY+x}" ]; then
    echo "AMINER_API_KEY does not exist"
else
    echo "AMINER_API_KEY exists"
fi
```

- If `${AMINER_API_KEY}` exists: proceed with the query.
- If `${AMINER_API_KEY}` is not set: stop immediately and guide the user to the [AMiner Console](https://open.aminer.cn/open/board?tab=control) to generate one. For help, see the [Open Platform Documentation](https://open.aminer.cn/open/docs).
- If the user provides `AMINER_API_KEY` inline (e.g. "My token is xxx"), accept it for the current session, but recommend setting it as an environment variable for better security.

## Invocation Style

Use direct `curl` calls by default. A Python wrapper is not required for this skill.

Default headers:

- `Authorization: ${AMINER_API_KEY}` by default
- `Content-Type: application/json;charset=utf-8` for POST requests
- `X-Platform: openclaw` when required by the gateway

## When To Use

Use this skill when the user asks for:

- free AMiner search
- low-cost academic discovery
- paper screening
- scholar identification
- institution normalization
- venue normalization
- patent trend scanning
- representative results before deeper analysis

Trigger phrases include:

- “先用免费接口”
- “不要走收费接口”
- “先帮我筛一下”
- “先看看值不值得深挖”
- “找几个候选”
- “做一个轻量版 skill”

## Free Workflows

### 1. Paper triage

Use when the user wants to quickly judge whether a paper is relevant.

Default chain:

`paper_search -> paper_info`

Return:

- title
- first author
- venue name
- year
- citation bucket
- abstract slice
- paper URL

This can answer:

- Is this probably the right paper?
- Is it recent?
- Is it from a recognizable venue?
- Is it worth opening in detail?

### 2. Scholar identification

Use when the user wants to know which scholar is the right person.

Default chain:

`person_search`

Return:

- name
- org
- interests
- citation count
- scholar URL

This can answer:

- Is this the right scholar?
- What interests best describe this person?
- Which institution candidate is the best match?

### 3. Institution normalization

Use when the user provides an institution string or abbreviation.

Default chain:

`organization_search`

Return:

- org id
- standard name
- aliases (top 3)

This can answer:

- Is this institution name recognized?
- Which canonical organization should downstream workflows use?

### 4. Venue normalization and type check

Use when the user provides a conference or journal name.

Default chain:

`venue_search`

Return:

- venue id
- standard bilingual name
- aliases (top 3)
- venue type
- venue URL

This can answer:

- Is this a conference or a journal?
- What is the standard venue entity?

### 5. Patent trend scan

Use when the user wants a lightweight view of patents in a topic.

Default chain:

`patent_search -> patent_info` when IDs need basic enrichment

Return:

- patent title
- first inventor
- app year
- pub year
- patent number and country when `patent_info` is added
- patent URL

This can answer:

- Is the topic active recently?
- Who appears first in the inventor field?
- Is there recent patent activity worth deeper review?

### 6. Free entity map

Use when the user wants a quick map of a topic across papers, scholars, venues, institutions, and patents without paying for analysis-grade APIs.

Suggested chain:

- papers: `paper_search -> paper_info`
- scholars: `person_search`
- institutions: `organization_search`
- venues: `venue_search`
- patents: `patent_search -> patent_info`

Return a short cross-entity summary, not a deep report.

## Free Skill Examples

### 1. Paper triage

```bash
curl -X GET \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/paper/search?page=1&size=5&title=Attention%20Is%20All%20You%20Need' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw'
```

Then enrich with `paper_info`:

```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/paper/info' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"ids":["<PAPER_ID>"]}'
```

### 2. Scholar identification

```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/person/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"name":"Yann LeCun","size":5}'
```

### 3. Institution normalization

```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/organization/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"orgs":["MIT CSAIL"]}'
```

### 4. Venue normalization and type check

```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/venue/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"name":"tkde"}'
```

### 5. Patent trend scan

```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/patent/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"query":"quantum computing chip","page":0,"size":10}'
```

## Output Pattern

Prefer this structure:

```markdown
## Free-tier result

### What we can answer now
- ...

### Top candidates
- ...

### Suggested next step
- Stay free: ...
- Upgrade to paid API only if you need: ...
```

## Paid Upgrade Boundary

Recommend upgrading only when the user needs one of these:

- full abstract or full paper metadata
- multi-condition or semantic paper search
- citation relationships
- full scholar profile, works, patents, or projects
- institution scholars, papers, patents, or rich profiles
- venue paper lists by year
- full patent details such as IPC/CPC, assignee, description

Suggested paid handoff:

- deeper paper analysis: `paper_search_pro`, `paper_detail`, `paper_relation`
- deeper scholar analysis: `person/detail`, `person/figure`, `person/paper/relation`
- deeper org analysis: `organization/detail`, `organization/person/relation`, `organization/paper/relation`
- deeper venue analysis: `venue/detail`, `venue/paper/relation`
- deeper patent analysis: `patent/detail`

## Product Positioning

This skill is intentionally positioned for:

- first success
- free discovery
- candidate narrowing
- entity normalization
- upgrade qualification

It should not replace the paid skill. It should create demand for it.

## Additional Reference

For endpoint parameters and fields, read [references/api-catalog.md](references/api-catalog.md).
