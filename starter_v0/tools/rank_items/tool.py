from __future__ import annotations

from typing import Any

from tools._shared import terms

SORT_KEYS = {"recency", "relevance", "score"}


def _error(message: str) -> dict[str, Any]:
    return {"tool": "rank_items", "error": "ValueError", "message": message}


def _to_int(value: Any, default: int) -> int:
    # Models often send numbers as strings ("5"). bool is a subclass of int: reject it.
    if isinstance(value, bool):
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _score(item: dict[str, Any]) -> float:
    # Each source names its popularity field differently.
    for key in ("score", "points", "likes", "stars"):
        if item.get(key) is not None:
            return _to_float(item.get(key))
    return 0.0


def _date(item: dict[str, Any]) -> str:
    return str(item.get("date") or item.get("published") or item.get("created_at") or "")


def rank_items(
    items: list[dict[str, Any]] | None = None,
    sort_by: str = "recency",
    query: str = "",
    dedupe: bool = True,
    top_k: int = 10,
) -> dict[str, Any]:
    """Dedupe and rank items ALREADY collected by other tools. Never fetches data."""
    if not isinstance(items, list):
        return _error("items must be a list")
    if sort_by not in SORT_KEYS:
        return _error(f"unsupported sort_by: {sort_by!r} (use recency, relevance, score)")
    if sort_by == "relevance" and not (query or "").strip():
        return _error("sort_by=relevance needs a query")

    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("url") or item.get("title") or "").strip().lower().rstrip("/")
        if dedupe and key:
            if key in seen:
                continue
            seen.add(key)
        cleaned.append(item)

    if sort_by == "recency":
        cleaned.sort(key=_date, reverse=True)
    elif sort_by == "score":
        cleaned.sort(key=_score, reverse=True)
    else:
        query_terms = terms(query)
        cleaned.sort(
            key=lambda it: len(query_terms & terms(f"{it.get('title') or ''} {it.get('summary') or ''}")),
            reverse=True,
        )

    removed = len(items) - len(cleaned)
    result = cleaned[: _to_int(top_k, default=10)]
    return {"tool": "rank_items", "sort_by": sort_by, "items": result, "count": len(result), "removed": removed}
