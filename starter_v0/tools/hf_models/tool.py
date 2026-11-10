from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err

HF_API = "https://huggingface.co/api/models"
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SORT_KEYS = {"downloads", "likes", "trending", "recent"}
SORT_PARAM = {"downloads": "downloads", "likes": "likes", "trending": "trendingScore", "recent": "createdAt"}


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "Day03-Research-Agent/1.0"}
    token = os.getenv("HF_TOKEN")  # optional
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _to_int(value: Any, default: int, low: int, high: int) -> int:
    """Models often send numbers as strings ("3"). bool is a subclass of int: reject it."""
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _tag_values(tags: list[str], prefix: str) -> list[str]:
    return [tag[len(prefix):] for tag in tags if isinstance(tag, str) and tag.startswith(prefix)]


def _item(data: dict[str, Any]) -> dict[str, Any]:
    model_id = data.get("id") or data.get("modelId") or ""
    tags = data.get("tags") or []
    licenses = _tag_values(tags, "license:")
    return {
        "title": model_id,
        "url": f"https://huggingface.co/{model_id}",
        "source": "huggingface.co",
        "task": data.get("pipeline_tag"),
        "library": data.get("library_name"),
        "downloads": data.get("downloads") or 0,  # last 30 days
        "likes": data.get("likes") or 0,
        "license": licenses[0] if licenses else None,
        "arxiv": _tag_values(tags, "arxiv:"),
        "gated": bool(data.get("gated")),
        "date": data.get("lastModified") or data.get("createdAt"),
    }


def hf_models(query: str = "", model_id: str = "", task: str = "", sort_by: str = "downloads", limit: int = 5) -> dict[str, Any]:
    """Search Hugging Face Hub models, or look up one model by id. ONE request either way."""
    try:
        model_id = model_id.strip() if isinstance(model_id, str) else ""
        query = query.strip() if isinstance(query, str) else ""
        task = task.strip() if isinstance(task, str) else ""

        if model_id:
            if not MODEL_ID_RE.match(model_id):
                raise ValueError(f"model_id must look like 'org/name', got {model_id!r}")
            response = requests.get(f"{HF_API}/{model_id}", headers=_headers(), timeout=TIMEOUT)
            # The Hub answers 401 (not 404) for a model that does not exist or is private.
            if response.status_code in (401, 404):
                return {"tool": "hf_models", "model_id": model_id, "found": False, "items": []}
            response.raise_for_status()
            return {"tool": "hf_models", "model_id": model_id, "found": True, "items": [_item(response.json())]}

        if not query and not task:
            raise ValueError("give a query, a task, or a model_id")
        if sort_by not in SORT_KEYS:
            raise ValueError(f"unsupported sort_by: {sort_by!r} (use downloads, likes, trending, recent)")

        params: dict[str, Any] = {
            "sort": SORT_PARAM[sort_by],
            "direction": -1,
            "limit": _to_int(limit, default=5, low=1, high=20),
        }
        if query:
            params["search"] = query
        if task:
            params["pipeline_tag"] = task
        response = requests.get(HF_API, params=params, headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
        items = [_item(model) for model in response.json() if isinstance(model, dict)]
        return {"tool": "hf_models", "query": query, "task": task or None, "sort_by": sort_by, "found": bool(items), "items": items}
    except Exception as exc:
        return err("hf_models", exc)
