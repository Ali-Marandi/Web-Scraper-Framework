# AMiner Free Search API Catalog

**Base URL**: `https://publicapi.chatglm.cn/chatglm_public/skill/aminer`  
**Authentication**: All endpoints should default to `Authorization: ${AMINER_API_KEY}`. In workflow execution, also include `X-Platform: openclaw` when required by the gateway.  
**Scope**: This catalog only documents the free APIs used by `aminer-free-academic`.

---

## Table of Contents

- [Paper APIs](#paper-apis)
- [Scholar APIs](#scholar-apis)
- [Institution APIs](#institution-apis)
- [Venue APIs](#venue-apis)
- [Patent APIs](#patent-apis)

---

## Paper APIs

### 1. Paper Search

- **URL**: `GET /api/paper/search`
- **Price**: Free
- **Description**: Search papers by title and return low-cost screening fields suitable for fast paper triage.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| page | number | Yes | Page number. Current online definition says it starts from `1`. |
| size | number | No | Page size, maximum `20` |
| title | string | Yes | Paper title |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Paper ID |
| title | Paper title |
| title_zh | Paper title in Chinese |
| doi | DOI |
| first_author | First author |
| venue_name | Venue title |
| n_citation_bucket | Citation bucket: `0`, `1-10`, `11-50`, `51-200`, `200-1000`, `1000-5000`, `5000+` |
| year | Publication year |
| total | Total count |

**curl Example:**
```bash
curl -X GET \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/paper/search?page=1&size=10&title=Looking+at+CTR+Prediction+Again%3A+Is+Attention+All+You+Need' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw'
```

---

### 2. Paper Info

- **URL**: `POST /api/paper/info`
- **Price**: Free
- **Description**: Batch query paper basic cards by paper IDs. Suitable for enriching search results with lightweight metadata.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| ids | []string | Yes | Paper ID list, maximum `100` |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Paper ID |
| title | Paper title |
| abstract_slice | Partial abstract |
| authors | Author array |
| author_count | Total author count |
| issue | Volume / issue field |
| raw | Venue raw name |
| venue | Venue object |
| venue_id | Venue ID |
| year | Publication year |

**curl Example:**
```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/paper/info' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"ids":["5ce2c5a5ced107d4c61c839b"]}'
```

---

## Scholar APIs

### 3. Scholar Search

- **URL**: `POST /api/person/search`
- **Price**: Free
- **Description**: Search scholar candidates by name and optional institution condition.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| name | string | No | Scholar name |
| offset | number | No | Starting position (fixed at 0; pagination not supported) |
| org | string | No | Institution name |
| size | number | No | Number of results, maximum `10` |
| org_id | []string | No | Institution entity ID list |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Scholar ID |
| interests | Research interests |
| n_citation | Citation count |
| name | Name |
| name_zh | Chinese name |
| org | Institution in English |
| org_id | Institution ID |
| org_zh | Institution in Chinese |
| total | Total count |

**curl Example:**
```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/person/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"name":"王曙","offset":0,"org":"Shanghai Jiaotong","size":10}'
```

---

## Institution APIs

### 4. Org Search

- **URL**: `POST /api/organization/search`
- **Price**: Free
- **Description**: Search institution IDs and standard names from institution keywords.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| orgs | []string | No | Institution names |

**Response Fields:**

| Field | Description |
|--------|------|
| aliases | Alias list, partial and typically top 3 |
| org_id | Institution ID |
| org_name | Institution name |
| total | Total count |

**curl Example:**
```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/organization/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"orgs":["清华大学"]}'
```

---

## Venue APIs

### 5. Venue Search

- **URL**: `POST /api/venue/search`
- **Price**: Free
- **Description**: Search venue IDs and standard names by venue keyword, including aliases and venue type.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| name | string | No | Venue name |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Venue ID |
| name_en | Venue English name |
| name_zh | Venue Chinese name |
| aliases | Alias list, partial and typically top 3 |
| venue_type | Venue type: `journal` or `conference` |
| total | Total count |

**curl Example:**
```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/venue/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"name":"tkde"}'
```

---

## Patent APIs

### 6. Patent Search

- **URL**: `POST /api/patent/search`
- **Price**: Free
- **Description**: Search patents by title or keyword and return lightweight trend fields.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| query | string | Yes | Query text such as patent title or keywords |
| page | number | Yes | Page number |
| size | number | Yes | Page size |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Patent ID |
| title | Patent title in English |
| title_zh | Patent title in Chinese |
| inventor_name | First inventor name |
| app_year | Application year |
| pub_year | Publication year |

**curl Example:**
```bash
curl -X POST \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/patent/search' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw' \
  -d '{"page":0,"query":"Si02","size":20}'
```

---

### 7. Patent Info

- **URL**: `GET /api/patent/info`
- **Price**: Free
- **Description**: Retrieve a patent basic card by patent ID.

**Request Parameters:**

| Parameter | Type | Required | Description |
|--------|------|------|------|
| id | string | Yes | Patent ID |

**Response Fields:**

| Field | Description |
|--------|------|
| id | Patent ID |
| title / en | Patent title |
| app_num | Application number |
| pub_num | Publication number |
| pub_kind | Publication kind |
| inventor | Inventor |
| country | Country |
| sequence | Sequence |
| app_year | Application year |
| pub_year | Publication year |

**curl Example:**
```bash
curl -X GET \
  'https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/patent/info?id=<PATENT_ID>' \
  -H "Authorization: ${AMINER_API_KEY}" \
  -H 'X-Platform: openclaw'
```
