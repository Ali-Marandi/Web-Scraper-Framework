# aminer-daily-paper

Personalized academic paper recommendation via the AMiner rec5 API. Intended for OpenClaw or similar hosts: the scripts return JSON with Markdown in `reply_text`; the host sends or displays that content.

## Requirements

- Python 3.10+
- `AMINER_API_KEY` environment variable — obtain at https://open.aminer.cn/open/board?tab=control

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```
/aminer-dp
/aminer-dp topics: multimodal agents, tool-use
/aminer-dp scholar: Jie Tang org: Tsinghua
/aminer-dp aminer_author_id: 696259801cb939bc391d3a37 topics: RAG, LLM
recommend me recent papers on multimodal agents
```

The model (running the skill) extracts `topics`, `author_name`, `author_org`, or `aminer_author_id` from natural language input before calling the script.

## How It Works

1. `handle_trigger.py` parses the trigger text and runs `run_pipeline.py` as a subprocess.
2. `run_pipeline.py` calls the AMiner rec5 API and writes `papers_summarized.json` under the output directory.
3. The pipeline returns `final_response: "TEXT"` and `reply_text` (Markdown). No Feishu card builders or `openclaw` dispatch live in this skill.

## API

```
POST https://publicapi.chatglm.cn/chatglm_public/skill/aminer/api/v3/paper/rec5
Authorization: <AMINER_API_KEY>
```

Key request fields: `aminer_author_id`, `author_name`, `author_org`, `topics`, `size`, `language_sort`.  
At least one of `aminer_author_id`, `author_name`, or `topics` should be provided. When none are given, the API returns personalized recommendations via the token-linked account.
