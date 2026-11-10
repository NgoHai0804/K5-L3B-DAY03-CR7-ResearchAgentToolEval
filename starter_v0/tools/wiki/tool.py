from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

# Wikimedia asks API clients to send a descriptive User-Agent.
HEADERS = {"User-Agent": "Day03-Research-Agent/1.0 (educational lab)"}
LANGS = {"en", "vi"}


def _to_int(value: Any, default: int, low: int, high: int) -> int:
    """Models often send numbers as strings ("3"). bool is a subclass of int: reject it."""
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def wiki_summary(query: str = "", lang: str = "en", sentences: int = 5) -> dict[str, Any]:
    """Find the best-matching Wikipedia article and return its intro, in ONE API call."""
    try:
        query = query.strip() if isinstance(query, str) else ""
        if not query:
            raise ValueError("query must be a non-empty string")
        if lang not in LANGS:
            raise ValueError(f"unsupported lang: {lang!r} (use en or vi)")

        # generator=search finds the title (the model rarely knows the exact one);
        # prop=extracts returns the plain-text intro of that same page.
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 1,
            "prop": "extracts|info|pageprops",
            "exintro": 1,
            "explaintext": 1,
            "exsentences": _to_int(sentences, default=5, low=1, high=10),
            "inprop": "url",
            "ppprop": "disambiguation",
            "redirects": 1,
        }
        response = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", [])
        if not pages:
            return {"tool": "wiki_summary", "query": query, "lang": lang, "found": False, "items": []}
        page = pages[0]
        item = {
            "title": page.get("title"),
            "url": page.get("fullurl"),
            "source": f"{lang}.wikipedia.org",
            "summary": (page.get("extract") or "").strip(),
            # "Mercury" -> a list of meanings, not an answer: the agent should clarify.
            "is_disambiguation": "disambiguation" in (page.get("pageprops") or {}),
        }
        return {"tool": "wiki_summary", "query": query, "lang": lang, "found": True, "items": [item]}
    except Exception as exc:
        return err("wiki_summary", exc)
