from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err

GITHUB_API = "https://api.github.com"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Day03-Research-Agent/1.0"}
    token = os.getenv("GITHUB_TOKEN")  # optional: 60 -> 5000 requests/hour
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _check(response: requests.Response) -> None:
    """Turn GitHub's rate-limit 403/429 into an actionable message for the agent."""
    if response.status_code in (403, 429) and response.headers.get("x-ratelimit-remaining") == "0":
        raise RuntimeError(
            "GitHub rate limit exceeded (no token: 60 req/hour, search 10 req/min). "
            "Set GITHUB_TOKEN in .env, or pass repo as 'owner/name' to skip the search call."
        )
    response.raise_for_status()


def _normalize_repo(repo: Any) -> str:
    """Accept 'owner/name', 'github.com/owner/name', a full URL, or a bare project name."""
    if not isinstance(repo, str):
        return ""
    repo = repo.strip().removesuffix(".git").strip("/")
    match = re.search(r"github\.com/([^/\s]+/[^/\s?#]+)", repo)
    return match.group(1).removesuffix(".git") if match else repo


def _item(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": data.get("full_name"),
        "url": data.get("html_url"),
        "source": "github.com",
        "summary": data.get("description") or "",
        "stars": data.get("stargazers_count") or 0,
        "forks": data.get("forks_count") or 0,
        "open_issues": data.get("open_issues_count") or 0,
        "language": data.get("language"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "topics": data.get("topics") or [],
        "last_push": data.get("pushed_at"),
        "archived": bool(data.get("archived")),
    }


def github_repo(repo: str = "") -> dict[str, Any]:
    """Return stars, activity and license of ONE GitHub repository, in ONE request."""
    try:
        name = _normalize_repo(repo)
        if not name:
            raise ValueError("repo must be a non-empty string like 'owner/name'")
        headers = _headers()

        if REPO_RE.match(name):
            # Stable path: direct lookup (60 req/hour without token).
            response = requests.get(f"{GITHUB_API}/repos/{name}", headers=headers, timeout=TIMEOUT)
            if response.status_code == 404:
                return {"tool": "github_repo", "repo": name, "found": False, "items": []}
            _check(response)
            return {"tool": "github_repo", "repo": name, "found": True, "items": [_item(response.json())]}

        # Fallback: bare project name ("langchain"). Search results carry the same repo
        # fields, so this is still one request. Do NOT sort by stars: that ranks any huge
        # repo merely mentioning the word first (langchain -> microsoft/markitdown).
        response = requests.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": f"{name} in:name", "per_page": 5},
            headers=headers,
            timeout=TIMEOUT,
        )
        _check(response)
        found = response.json().get("items", [])
        if not found:
            return {"tool": "github_repo", "repo": name, "found": False, "items": []}
        exact = [it for it in found if str(it.get("name", "")).lower() == name.lower()]
        best = max(exact, key=lambda it: it.get("stargazers_count") or 0) if exact else found[0]
        return {"tool": "github_repo", "repo": best.get("full_name"), "found": True, "items": [_item(best)]}
    except Exception as exc:
        return err("github_repo", exc)
