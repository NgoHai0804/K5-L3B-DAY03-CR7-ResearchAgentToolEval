---
name: rank_items
track: core
kind: local_formatter
provider:
requires_env: []
inputs: [items, sort_by, query, dedupe, top_k]
outputs: [items, count, removed]
side_effect: false
---
# rank_items

Dedupes and ranks items that were ALREADY collected by other tools
(`lookup`, `social_search`, `papers`, ...). It does NOT fetch data. Offline.

Typical chain in `chat.py`: `lookup` / `papers` -> `rank_items` -> `format`.

- Dedupe key: `url`, falling back to `title` (case-insensitive, trailing `/` ignored).
- `sort_by=recency`: by `date` / `published` / `created_at`, newest first.
- `sort_by=score`: by `score`, falling back to `points` / `likes` / `stars`.
- `sort_by=relevance`: keyword overlap of `query` with title + summary. Needs `query`.
- `top_k` is coerced to int, so `"5"` works; invalid values fall back to 10.
- Bad input returns an error dict, never raises.

Built from the PLAN-v3 skeleton, with 4 bugs fixed:

| Input | Skeleton behavior | Now |
|---|---|---|
| `sort_by="relevance"` | accepted, but did not sort at all | sorts by keyword overlap with `query` |
| `top_k="5"` | silently became 10 | 5 |
| `score: "abc"` | `float()` raised `ValueError` (crash) | treated as 0 |
| `top_k=True` | accepted as 1 | falls back to 10 |
