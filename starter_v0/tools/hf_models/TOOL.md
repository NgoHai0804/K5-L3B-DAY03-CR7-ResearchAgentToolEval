---
name: hf_models
track: bonus
kind: live_api
provider: Hugging Face Hub API
requires_env: []
inputs: [query, model_id, task, sort_by, limit]
outputs: [items, found]
side_effect: false
---
# hf_models

Searches open models on the Hugging Face Hub, or looks up one model by id.
ONE request either way. No API key needed (optional `HF_TOKEN`).

- `model_id="org/name"` -> `GET /api/models/{org}/{name}` (one model).
  The Hub answers `401` (not 404) for a missing or private model -> `found=false`.
- otherwise `GET /api/models?search=&pipeline_tag=&sort=&direction=-1&limit=`.
  `sort_by`: downloads (default) / likes / trending / recent.
- `limit` is coerced to int and clamped to 1..20.
- Each item: id, url, task, library, downloads (last 30 days), likes,
  license (from `license:*` tag), arxiv ids (from `arxiv:*` tags), gated, date.
- Bad input or HTTP errors return an error dict, never raise.

Use it for "model open-weight nào phổ biến cho task X", "model Y bao nhiêu
lượt tải / license gì". NOT for papers (`papers`) and NOT for code repos
(`github_repo`).
